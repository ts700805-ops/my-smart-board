import streamlit as st
import sqlite3
import pandas as pd
import time
import os
from git import Repo
from datetime import datetime, timedelta
from PIL import Image

# 1. 網頁基本設定 (維持原樣)
st.set_page_config(page_title="超慧製造部-雲端公佈欄", page_icon="🏭", layout="wide")

# --- 🚀 安全讀取金鑰 ---
try:
    MY_TOKEN = st.secrets["MY_TOKEN"] if "MY_TOKEN" in st.secrets else ""
except Exception:
    MY_TOKEN = ""

GITHUB_REPO = f"https://{MY_TOKEN}@github.com/ts700805-ops/my-smart-board.git"
IMAGE_FOLDER = "images"
if not os.path.exists(IMAGE_FOLDER): os.makedirs(IMAGE_FOLDER)

# --- 同步功能 ---
def sync_to_github(msg="Update"):
    if not MY_TOKEN: return
    try:
        os.environ["GIT_ASKPASS"] = "echo"
        os.environ["GIT_TERMINAL_PROMPT"] = "0"
        repo = Repo(".")
        if 'origin' in repo.remotes: repo.delete_remote('origin')
        origin = repo.create_remote('origin', GITHUB_REPO)
        repo.git.add("--all") 
        now = (datetime.utcnow() + timedelta(hours=8)).strftime('%m/%d %H:%M')
        repo.index.commit(f"{msg} - {now}")
        origin.push(refspec='main:main', force=True)
        st.toast("✅ GitHub 同步完成")
    except: pass

# --- 資料庫工具 ---
def get_conn():
    return sqlite3.connect('bulletin.db', check_same_thread=False)

def init_db():
    conn = get_conn()
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS posts (id INTEGER PRIMARY KEY AUTOINCREMENT, date TEXT, author TEXT, content TEXT, image_path TEXT, is_deleted INTEGER DEFAULT 0)')
    c.execute('''CREATE TABLE IF NOT EXISTS quality_posts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, 
                    date TEXT, 
                    order_no TEXT, 
                    content TEXT, 
                    category TEXT, 
                    staff_name TEXT, 
                    image_path TEXT, 
                    is_deleted INTEGER DEFAULT 0)''')
    c.execute('CREATE TABLE IF NOT EXISTS staff (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT UNIQUE)')
    
    # 新增：製造部待處理事項資料表
    c.execute('''CREATE TABLE IF NOT EXISTS pending_tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT,
                    order_no TEXT,
                    task_content TEXT,
                    status TEXT DEFAULT '待處理',
                    complete_date TEXT)''')
    conn.commit(); conn.close()

init_db()

# --- 側邊選單 ---
with st.sidebar:
    st.markdown("### 👤 目前登入\n## 管理員")
    st.markdown("---")
    
    st.markdown("🔍 **公告瀏覽區 (主要點閱)**")
    menu = st.radio(
        "功能選單",
        [
            "🏠 公佈欄首頁", 
            "⚠️ 品質異常首頁",
            "🛠️ 製造部待處理清單", # 新增頁面選項
            "🔴 專案管理首頁",
            "--------------------", 
            "✍️ 撰寫新公告", 
            "📝 撰寫品質",
            "📜 所有紀錄", 
            "⚙️ 管理後台"
        ],
        label_visibility="collapsed"
    )
    
    st.markdown("<br>" * 10, unsafe_allow_html=True) 
    st.caption("⚠️ 底部功能僅供管理/記錄使用")

st.title("🏭 <超慧>製造部-雲端公佈欄")

# --- 頁面邏輯 ---

# 1. 一般公佈欄首頁 (維持原樣)
if menu == "🏠 公佈欄首頁":
    search_q = st.text_input("🔍 搜尋公告內容或發布人", "")
    conn = get_conn()
    query = "SELECT * FROM posts WHERE is_deleted = 0"
    if search_q:
        query += f" AND (content LIKE '%{search_q}%' OR author LIKE '%{search_q}%')"
    df = pd.read_sql(f"{query} ORDER BY id DESC", conn)
    conn.close()
    
    for _, r in df.iterrows():
        with st.container():
            st.markdown(f"**{r['date']} | 發布人：{r['author']}**")
            st.info(r['content'])
            if r['image_path'] and os.path.exists(r['image_path']):
                with st.popover("🖼️ 檢視照片"):
                    st.image(r['image_path'], use_container_width=True)
            st.markdown("---")

# 2. 品質異常首頁 (維持原樣)
elif menu == "⚠️ 品質異常首頁":
    st.subheader("⚠️ 品質異常管理首頁")
    search_q = st.text_input("🔍 搜尋製令、人員 or 異常內容", "")
    conn = get_conn()
    query = "SELECT * FROM quality_posts WHERE is_deleted = 0"
    if search_q:
        query += f" AND (order_no LIKE '%{search_q}%' OR content LIKE '%{search_q}%' OR staff_name LIKE '%{search_q}%' OR category LIKE '%{search_q}%')"
    df = pd.read_sql(f"{query} ORDER BY id DESC", conn)
    conn.close()
    
    for _, r in df.iterrows():
        with st.expander(f"🔴 [{r['date']}] 製令：{r['order_no']} | 分類：{r['category']}", expanded=True):
            st.write(f"**相關人員：** {r['staff_name']}")
            st.error(f"**異常內容：** {r['content']}")
            if r['image_path'] and os.path.exists(r['image_path']):
                st.image(r['image_path'], width=800)

# 3. 新增頁面：製造部待處理事項清單
elif menu == "🛠️ 製造部待處理清單":
    st.subheader("🛠️ 製造部待處理事項清單")
    conn = get_conn()
    df_task = pd.read_sql("SELECT date, order_no, task_content FROM pending_tasks WHERE status = '待處理' ORDER BY date ASC", conn)
    conn.close()
    
    if df_task.empty:
        st.success("目前暫無待處理事項！")
    else:
        st.table(df_task)

# 4. 撰寫一般公告 (維持原樣)
elif menu == "✍️ 撰寫新公告":
    st.subheader("📝 發布新訊息")
    conn = get_conn()
    s_df = pd.read_sql("SELECT name FROM staff", conn)
    conn.close()
    author = st.selectbox("發布人", s_df['name'].tolist())
    msg = st.text_area("公告內容")
    file = st.file_uploader("🖼️ 上傳照片", type=['jpg', 'png', 'jpeg'])
    if st.button("🚀 立即發布"):
        if msg:
            p = ""
            if file:
                p = f"{IMAGE_FOLDER}/n_{datetime.now().strftime('%Y%m%d%H%M%S')}_{file.name}"
                with open(p, "wb") as f: f.write(file.getbuffer())
            conn = get_conn()
            t = (datetime.utcnow() + timedelta(hours=8)).strftime("%Y-%m-%d %H:%M")
            conn.execute("INSERT INTO posts (date, author, content, image_path, is_deleted) VALUES (?, ?, ?, ?, 0)", (t, author, msg, p))
            conn.commit(); conn.close()
            sync_to_github("New Post"); st.balloons(); st.success("發布成功！"); time.sleep(1.5); st.rerun()

# 5. 撰寫品質 (維持原樣)
elif menu == "📝 撰寫品質":
    st.subheader("✍️ 記錄品質異常")
    col1, col2 = st.columns(2)
    with col1:
        order_no = st.text_input("工單/製令編號")
        q_cat = st.selectbox("異常分類", ["零件異常", "外觀異常", "組裝問題", "流程問題", "其他"])
    with col2:
        conn = get_conn()
        s_list = pd.read_sql("SELECT name FROM staff", conn)['name'].tolist()
        conn.close()
        q_staff = st.selectbox("相關人員", s_list)
    q_content = st.text_area("異常描述")
    q_file = st.file_uploader("🖼️ 現場照片", type=['jpg', 'png', 'jpeg'])
    if st.button("🚨 提交紀錄"):
        if order_no and q_content:
            p = ""
            if q_file:
                p = f"{IMAGE_FOLDER}/q_{datetime.now().strftime('%Y%m%d%H%M%S')}_{q_file.name}"
                with open(p, "wb") as f: f.write(q_file.getbuffer())
            conn = get_conn()
            t = (datetime.utcnow() + timedelta(hours=8)).strftime("%Y-%m-%d %H:%M")
            conn.execute("INSERT INTO quality_posts (date, order_no, content, category, staff_name, image_path, is_deleted) VALUES (?, ?, ?, ?, ?, ?, 0)", (t, order_no, q_content, q_cat, q_staff, p))
            conn.commit(); conn.close()
            sync_to_github("New Quality Alert"); st.balloons(); st.success("紀錄已存檔！"); time.sleep(1.5); st.rerun()

# 6. 所有紀錄 (更新：新增待處理清單歷史)
elif menu == "📜 所有紀錄":
    st.subheader("📜 歷史紀錄查詢")
    conn = get_conn()
    
    st.markdown("--- 🛠️ 待處理事項紀錄 (含已完成) ---")
    df_history_task = pd.read_sql("SELECT date, order_no, task_content, status, complete_date FROM pending_tasks ORDER BY id DESC", conn)
    st.dataframe(df_history_task, use_container_width=True)

    st.markdown("--- 📢 一般公告清單 (全部歷史) ---")
    df_posts = pd.read_sql("SELECT date, author, content, is_deleted FROM posts ORDER BY id DESC", conn)
    df_posts['狀態'] = df_posts['is_deleted'].apply(lambda x: "正常" if x == 0 else "❌ 已刪除")
    st.dataframe(df_posts[['date', 'author', 'content', '狀態']], use_container_width=True)
    
    st.markdown("--- ⚠️ 品質異常清單 (全部歷史) ---")
    df_quality = pd.read_sql("SELECT date, order_no, category, staff_name, content, is_deleted FROM quality_posts ORDER BY id DESC", conn)
    df_quality['狀態'] = df_quality['is_deleted'].apply(lambda x: "正常" if x == 0 else "❌ 已刪除")
    st.dataframe(df_quality[['date', 'order_no', 'category', 'staff_name', 'content', '狀態']], use_container_width=True)
    conn.close()

# 7. 管理後台
elif menu == "⚙️ 管理後台":
    st.subheader("🛠️ 管理系統")
    if st.text_input("請輸入管理密碼", type="password") == "0000":
        t1, t2, t3, t4 = st.tabs(["公告管理", "品質紀錄管理", "人員管理", "待處理事項管理"])
        
        with t1: # (維持原樣)
            conn = get_conn()
            df = pd.read_sql("SELECT * FROM posts WHERE is_deleted = 0 ORDER BY id DESC", conn)
            conn.close()
            for _, r in df.iterrows():
                c1, c2, c3 = st.columns([6, 2, 2])
                c1.write(f"[{r['date']}] {r['content'][:20]}...")
                with c2.popover("📝 編輯"):
                    nc = st.text_area("修改內容", value=r['content'], key=f"ep_{r['id']}")
                    if st.button("💾 儲存", key=f"sp_{r['id']}"):
                        conn = get_conn(); conn.execute("UPDATE posts SET content = ? WHERE id = ?", (nc, r['id'])); conn.commit(); conn.close()
                        sync_to_github("Edit Post"); st.rerun()
                if c3.button("🗑️ 刪除", key=f"dp_{r['id']}"):
                    conn = get_conn(); conn.execute("UPDATE posts SET is_deleted = 1 WHERE id = ?", (r['id'],)); conn.commit(); conn.close(); sync_to_github("Del Post"); st.rerun()

        with t2: # (維持原樣)
            conn = get_conn()
            df_q = pd.read_sql("SELECT * FROM quality_posts WHERE is_deleted = 0 ORDER BY id DESC", conn)
            staff_list = pd.read_sql("SELECT name FROM staff", conn)['name'].tolist()
            conn.close()
            cat_options = ["零件異常", "外觀異常", "組裝問題", "流程問題", "其他"]
            for _, r in df_q.iterrows():
                qc1, qc2, qc3 = st.columns([6, 2, 2])
                qc1.write(f"[{r['date']}] 製令:{r['order_no']} | 人員:{r['staff_name']}")
                with qc2.popover("📝 編輯"):
                    new_order = st.text_input("製令編號", value=r['order_no'], key=f"uo_{r['id']}")
                    try: curr_cat_idx = cat_options.index(r['category'])
                    except: curr_cat_idx = 0
                    new_cat = st.selectbox("分類", cat_options, index=curr_cat_idx, key=f"uc_{r['id']}")
                    try: curr_staff_idx = staff_list.index(r['staff_name'])
                    except: curr_staff_idx = 0
                    new_staff = st.selectbox("人員", staff_list, index=curr_staff_idx, key=f"us_{r['id']}")
                    new_content = st.text_area("內容", value=r['content'], key=f"ucont_{r['id']}")
                    new_img = st.file_uploader("🖼️ 更新照片 (不選則保留原圖)", type=['jpg', 'png', 'jpeg'], key=f"uimg_{r['id']}")
                    if st.button("💾 儲存修改", key=f"save_q_{r['id']}"):
                        p = r['image_path']
                        if new_img:
                            p = f"{IMAGE_FOLDER}/q_{datetime.now().strftime('%Y%m%d%H%M%S')}_{new_img.name}"
                            with open(p, "wb") as f: f.write(new_img.getbuffer())
                        conn = get_conn(); conn.execute("UPDATE quality_posts SET order_no=?, category=?, staff_name=?, content=?, image_path=? WHERE id=?", 
                                     (new_order, new_cat, new_staff, new_content, p, r['id'])); conn.commit(); conn.close(); sync_to_github("Edit Quality"); st.rerun()
                if qc3.button("🗑️ 刪除", key=f"dq_{r['id']}"):
                    conn = get_conn(); conn.execute("UPDATE quality_posts SET is_deleted = 1 WHERE id = ?", (r['id'],)); conn.commit(); conn.close(); sync_to_github("Del Quality"); st.rerun()

        with t3: # (維持原樣)
            st.write("### 👥 人員名單管理")
            new_n = st.text_input("輸入新人員姓名")
            if st.button("➕ 新增人員"):
                if new_n:
                    conn = get_conn()
                    try:
                        conn.execute("INSERT INTO staff (name) VALUES (?)", (new_n,))
                        conn.commit(); conn.close(); sync_to_github(f"Add {new_n}"); st.rerun()
                    except: conn.close(); st.error("人員已存在")
            st.markdown("---")
            conn = get_conn()
            curr_df = pd.read_sql("SELECT * FROM staff", conn)
            conn.close()
            for _, row in curr_df.iterrows():
                col1, col2 = st.columns([8, 2])
                col1.write(f"👤 {row['name']}")
                if col2.button("🗑️ 刪除人員", key=f"ds_{row['id']}"):
                    conn = get_conn(); conn.execute("DELETE FROM staff WHERE id = ?", (row['id'],)); conn.commit(); conn.close(); sync_to_github("Remove Staff"); st.rerun()

        with t4: # 新增：待處理事項管理 (加入編輯功能)
            st.write("### 📝 新增待處理事項")
            with st.form("task_form", clear_on_submit=True):
                col_a, col_b = st.columns(2)
                t_date = col_a.date_input("日期")
                t_order = col_b.text_input("製令編號")
                t_msg = st.text_area("待處理項目內容")
                if st.form_submit_button("➕ 新增到清單"):
                    if t_order and t_msg:
                        conn = get_conn()
                        conn.execute("INSERT INTO pending_tasks (date, order_no, task_content) VALUES (?, ?, ?)", 
                                     (str(t_date), t_order, t_msg))
                        conn.commit(); conn.close(); sync_to_github("Add Task"); st.rerun()

            st.markdown("---")
            st.write("### ⏳ 目前待處理清單")
            conn = get_conn()
            active_tasks = pd.read_sql("SELECT * FROM pending_tasks WHERE status = '待處理' ORDER BY date ASC", conn)
            conn.close()
            for _, task in active_tasks.iterrows():
                # 修改欄位比例以放入編輯按鈕
                tc1, tc2, tc3 = st.columns([6, 2, 2])
                tc1.warning(f"📅 {task['date']} | 製令: {task['order_no']} \n\n內容: {task['task_content']}")
                
                # 新增的編輯按鈕
                with tc2.popover("📝 編輯"):
                    try:
                        curr_d = datetime.strptime(task['date'], '%Y-%m-%d')
                    except:
                        curr_d = datetime.now()
                    
                    e_date = st.date_input("修改日期", value=curr_d, key=f"edt_{task['id']}")
                    e_order = st.text_input("修改製令", value=task['order_no'], key=f"eord_{task['id']}")
                    e_task = st.text_area("修改內容", value=task['task_content'], key=f"etxt_{task['id']}")
                    
                    if st.button("💾 儲存修改", key=f"esv_{task['id']}"):
                        conn = get_conn()
                        conn.execute("UPDATE pending_tasks SET date=?, order_no=?, task_content=? WHERE id=?", 
                                     (str(e_date), e_order, e_task, task['id']))
                        conn.commit(); conn.close(); sync_to_github("Edit Task"); st.rerun()

                # 原有的完成按鈕
                if tc3.button("✅ 完成", key=f"finish_{task['id']}"):
                    now_t = (datetime.utcnow() + timedelta(hours=8)).strftime("%Y-%m-%d %H:%M")
                    conn = get_conn()
                    conn.execute("UPDATE pending_tasks SET status='已完成', complete_date=? WHERE id=?", (now_t, task['id']))
                    conn.commit(); conn.close(); sync_to_github("Finish Task"); st.rerun()








# --- 🔴 專案管理首頁 (獨立功能活頁) ---
if menu == "🔴 專案管理首頁":
    st.subheader("📋 專案進度追蹤看板")
    
    # 確保資料庫有建立獨立表
    conn = get_conn()
    conn.execute('''CREATE TABLE IF NOT EXISTS project_tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    order_no TEXT,
                    assign_date TEXT,
                    author_name TEXT,
                    worker_name TEXT,
                    expected_date TEXT,
                    finish_date TEXT DEFAULT '',
                    is_finished INTEGER DEFAULT 0,
                    is_deleted INTEGER DEFAULT 0)''')
    conn.commit(); conn.close()
    
    # --- 區塊 1：➕ 指派新任務 (手動輸入) ---
    with st.expander("➕ 點擊指派新任務 (獨立手動輸入區)", expanded=False):
        c1, c2, c3 = st.columns(3)
        with c1:
            p_order = st.text_input("工單/製令編號", key="p_order_add")
            p_author = st.text_input("發布人員 (手動輸入姓名)", key="p_author_add")
        with c2:
            p_worker = st.text_input("執行人員 (手動輸入姓名)", key="p_worker_add")
            p_date = st.date_input("指派日期", value=datetime.now())
        with c3:
            p_exp_date = st.date_input("預計完工日期", value=datetime.now() + timedelta(days=7))
            
        if st.button("🚀 提交指派專案"):
            if p_order and p_author and p_worker:
                conn = get_conn()
                conn.execute('''INSERT INTO project_tasks (order_no, assign_date, author_name, worker_name, expected_date, is_finished, is_deleted) 
                                VALUES (?, ?, ?, ?, ?, 0, 0)''', 
                             (p_order, str(p_date), p_author, p_worker, str(p_exp_date)))
                conn.commit(); conn.close()
                sync_to_github("Add Project Task"); st.success("專案指派成功！"); time.sleep(1); st.rerun()
            else:
                st.error("請完整填寫製令、發布人員與執行人員！")

    st.markdown("---")
    
    # --- 區塊 2：🟡 進行中專案清單 ---
    st.markdown("### 🟡 進行中專案清單")
    conn = get_conn()
    df_active = pd.read_sql("SELECT * FROM project_tasks WHERE is_finished = 0 AND is_deleted = 0 ORDER BY id DESC", conn)
    conn.close()
    
    if df_active.empty:
        st.info("目前沒有進行中的專案任務。")
    else:
        for _, row in df_active.iterrows():
            m1, m2, m3, m4 = st.columns([5, 1.5, 1.5, 1.5])
            m1.info(f"**製令：** {row['order_no']} | **指派日：** {row['assign_date']} | **發布：** {row['author_name']} | **執行：** {row['worker_name']} | **預計完工：** {row['expected_date']}")
            
            # 🟢 免密碼完工
            if m2.button("🟢 點我完工", key=f"f_btn_{row['id']}"):
                conn = get_conn()
                f_time = (datetime.utcnow() + timedelta(hours=8)).strftime("%Y-%m-%d %H:%M")
                conn.execute("UPDATE project_tasks SET is_finished = 1, finish_date = ? WHERE id = ?", (f_time, row['id']))
                conn.commit(); conn.close(); sync_to_github("Finish Project Task"); st.rerun()
                
            # 📝 編輯修改 (密碼 0000)
            with m3.popover("📝 編輯"):
                pwd_edit = st.text_input("驗證管理密碼", type="password", key=f"pwd_e_{row['id']}")
                if pwd_edit == "0000":
                    e_order = st.text_input("修改製令", value=row['order_no'], key=f"eo_{row['id']}")
                    e_author = st.text_input("修改發布人", value=row['author_name'], key=f"ea_{row['id']}")
                    e_worker = st.text_input("修改執行人", value=row['worker_name'], key=f"ew_{row['id']}")
                    e_exp = st.date_input("修改預計完工日", value=datetime.strptime(row['expected_date'], "%Y-%m-%d"), key=f"ex_{row['id']}")
                    if st.button("💾 儲存修改", key=f"save_e_{row['id']}"):
                        conn = get_conn()
                        conn.execute("UPDATE project_tasks SET order_no=?, author_name=?, worker_name=?, expected_date=? WHERE id=?", 
                                     (e_order, e_author, e_worker, str(e_exp), row['id']))
                        conn.commit(); conn.close(); sync_to_github("Edit Project Task"); st.rerun()
                elif pwd_edit:
                    st.error("密碼錯誤")

            # 🗑️ 刪除進行中 (密碼 0000)
            with m4.popover("🗑️ 刪除"):
                pwd_del = st.text_input("驗證管理密碼", type="password", key=f"pwd_d_{row['id']}")
                if pwd_del == "0000":
                    if st.button("🚨 確認刪除", key=f"conf_d_{row['id']}"):
                        conn = get_conn()
                        conn.execute("UPDATE project_tasks SET is_deleted = 1 WHERE id = ?", (row['id'],))
                        conn.commit(); conn.close(); sync_to_github("Delete Project Task"); st.rerun()
                elif pwd_del:
                    st.error("密碼錯誤")

    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown("---")
    
    # --- 區塊 3：🟢 已完工歷史紀錄 ---
    st.markdown("### 🟢 已完工歷史紀錄")
    conn = get_conn()
    df_finished = pd.read_sql("SELECT * FROM project_tasks WHERE is_finished = 1 AND is_deleted = 0 ORDER BY finish_date DESC", conn)
    conn.close()
    
    if df_finished.empty:
        st.caption("暫無完工紀錄。")
    else:
        for _, row in df_finished.iterrows():
            m1, m3, m4 = st.columns([6.5, 1.5, 1.5])
            m1.success(f"**製令：** {row['order_no']} | **執行：** {row['worker_name']} | **發布：** {row['author_name']} | **原預計完工：** {row['expected_date']} | ⏰ **實際完工時間：{row['finish_date']}**")
            
            # 修改完工歷史 (密碼 0000)
            with m3.popover("📝 修改歷史"):
                pwd_hedit = st.text_input("驗證管理密碼", type="password", key=f"pwd_he_{row['id']}")
                if pwd_hedit == "0000":
                    he_order = st.text_input("修改製令", value=row['order_no'], key=f"heo_{row['id']}")
                    he_author = st.text_input("修改發布人", value=row['author_name'], key=f"hea_{row['id']}")
                    he_worker = st.text_input("修改執行人", value=row['worker_name'], key=f"hew_{row['id']}")
                    if st.button("💾 儲存修改歷史", key=f"hsave_e_{row['id']}"):
                        conn = get_conn()
                        conn.execute("UPDATE project_tasks SET order_no=?, author_name=?, worker_name=? WHERE id=?", 
                                     (he_order, he_author, he_worker, row['id']))
                        conn.commit(); conn.close(); sync_to_github("Edit Finished Task History"); st.rerun()
                elif pwd_hedit:
                    st.error("密碼錯誤")
                    
            # 刪除完工歷史 (密碼 0000)
            with m4.popover("🗑️ 刪除紀錄"):
                pwd_hdel = st.text_input("驗證管理密碼", type="password", key=f"pwd_hd_{row['id']}")
                if pwd_hdel == "0000":
                    if st.button("🚨 確認刪除歷史", key=f"hconf_d_{row['id']}"):
                        conn = get_conn()
                        conn.execute("UPDATE project_tasks SET is_deleted = 1 WHERE id = ?", (row['id'],))
                        conn.commit(); conn.close(); sync_to_github("Delete Finished Task History"); st.rerun()
                elif pwd_hdel:
                    st.error("密碼錯誤")
