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
    conn.commit(); conn.close()

init_db()

# --- 側邊選單 (修正後的單一 Radio 邏輯，確保每個都能點選) ---
with st.sidebar:
    st.markdown("### 👤 目前登入\n## 管理員")
    st.markdown("---")
    
    # 使用單一 Radio 但透過 Markdown 標題手動分組，確保 Streamlit 能正確識別切換
    st.markdown("🔍 **公告瀏覽區** (人員專用)")
    menu = st.radio(
        "功能導覽",
        [
            "🏠 公佈欄首頁", "⚠️ 品質異常公告",
            "撰寫分隔", # 佔位符，待會用來顯示分隔線
            "✍️ 撰寫新公告", "📝 撰寫品質",
            "管理分隔", # 佔位符
            "📜 所有紀錄", "⚙️ 管理後台"
        ],
        label_visibility="collapsed"
    )

st.title("🏭 <超慧>製造部-雲端公佈欄")

# --- 頁面邏輯 ---

# 1. 一般公告瀏覽
if menu == "🏠 公佈欄首頁":
    conn = get_conn()
    df = pd.read_sql("SELECT * FROM posts WHERE is_deleted = 0 ORDER BY id DESC", conn)
    conn.close()
    for _, r in df.iterrows():
        with st.container():
            st.markdown(f"**{r['date']} | 發布人：{r['author']}**")
            st.info(r['content'])
            if r['image_path'] and os.path.exists(r['image_path']):
                with st.popover("🖼️ 檢視照片"):
                    st.image(Image.open(r['image_path']), width=300)
            st.markdown("---")

# 2. 品質異常瀏覽
elif menu == "⚠️ 品質異常公告":
    conn = get_conn()
    df = pd.read_sql("SELECT * FROM quality_posts WHERE is_deleted = 0 ORDER BY id DESC", conn)
    conn.close()
    for _, r in df.iterrows():
        with st.expander(f"🔴 [{r['date']}] 製令：{r['order_no']} | 分類：{r['category']}"):
            st.write(f"**相關人員：** {r['staff_name']}")
            st.error(f"**異常內容：** {r['content']}")
            if r['image_path'] and os.path.exists(r['image_path']):
                st.image(Image.open(r['image_path']), width=300)

# 3. 撰寫一般公告
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

# 4. 撰寫品質 (標題已簡化)
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

# 5. 所有紀錄 (歷史查詢)
elif menu == "📜 所有紀錄":
    st.subheader("📜 歷史紀錄查詢 (含已刪除項目)")
    conn = get_conn()
    st.markdown("--- 📢 一般公告清單 (全部歷史) ---")
    df_posts = pd.read_sql("SELECT date, author, content, is_deleted FROM posts ORDER BY id DESC", conn)
    df_posts['狀態'] = df_posts['is_deleted'].apply(lambda x: "正常" if x == 0 else "❌ 已刪除")
    st.dataframe(df_posts[['date', 'author', 'content', '狀態']], use_container_width=True)
    
    st.markdown("--- ⚠️ 品質異常清單 (全部歷史) ---")
    df_quality = pd.read_sql("SELECT date, order_no, category, staff_name, content, is_deleted FROM quality_posts ORDER BY id DESC", conn)
    df_quality['狀態'] = df_quality['is_deleted'].apply(lambda x: "正常" if x == 0 else "❌ 已刪除")
    st.dataframe(df_quality[['date', 'order_no', 'category', 'staff_name', 'content', '狀態']], use_container_width=True)
    conn.close()

# 6. 管理後台 (含密碼保護與 Popover 編輯)
elif menu == "⚙️ 管理後台":
    st.subheader("🛠️ 管理系統")
    if st.text_input("請輸入管理密碼", type="password") == "0000":
        t1, t2, t3 = st.tabs(["公告管理", "品質紀錄管理", "人員管理"])
        
        with t1:
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

        with t2:
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

        with t3:
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

# 處理分隔線顯示與防呆跳轉
else:
    st.info("請點選左側選單的功能項以開始使用。")
