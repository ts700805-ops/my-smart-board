import streamlit as st
import sqlite3
import pandas as pd
import time
import os
from git import Repo
from datetime import datetime, timedelta
from PIL import Image
import base64

# =========================================================
# 1. 網頁基本設定 (全域唯一配置)
# =========================================================
st.set_page_config(
    page_title="超慧製造部-雲端公佈欄", 
    page_icon="🥮", 
    layout="wide"
)

# --- 🖼️ 處理圖片背景轉為 Base64 ---
def get_base64_image(image_path):
    try:
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    except:
        return ""

img_base64 = get_base64_image("image_b13023.jpg")

# --- 🎑 高質感 CSS 注入 ---
st.markdown("""
    <style>
    .stApp {
        background-color: #FDFBF0 !important;
    }
    header[data-testid="stHeader"] {
        background-color: #0D1B2A !important;
        border-bottom: 3px solid #F1C40F !important;
    }
    [data-testid="stSidebar"] {
        background-color: #112233 !important;
    }
    [data-testid="stSidebar"] *, [data-testid="stSidebar"] span, [data-testid="stSidebar"] p {
        color: #FFFFFF !important;
    }
    h1, h2, h3 {
        color: #0D1B2A !important;
        font-family: "Microsoft JhengHei", sans-serif;
    }
    .stAlert, div[data-testid="stImageFilterBackground"] {
        border-radius: 12px !important;
        box-shadow: 0 2px 8px rgba(0,0,0,0.04) !important;
    }
    /* 頁籤標題加大加粗 */
    button[data-baseweb="tab"] {
        font-size: 18px !important;
        font-weight: bold !important;
    }
    </style>
    """, unsafe_allow_html=True)

# =========================================================
# 🏠 側邊欄資訊展示 (純展示，不放任何導航選單)
# =========================================================
with st.sidebar:
    st.markdown("<h4 style='color: #F1C40F; margin-bottom: 5px;'>系統版本：20260705029</h4>", unsafe_allow_html=True)
    
    try:
        festive_img = Image.open("image_b13023.jpg")
        st.image(festive_img, use_container_width=True)
    except:
        st.caption("🌕 歲歲年年 ‧ 月圓人安 🌕")
    
    st.markdown("<hr style='border-color: rgba(255,255,255,0.2);'>", unsafe_allow_html=True)
    st.markdown("### 🥮 製造部雲端公佈欄")
    st.caption("告別端午，喜迎 9/25 中秋佳節 ─ 柚香傳情，事事圓滿！")
    st.markdown("---")
    st.markdown("### 👤 目前登入\n## 管理員")

# =========================================================
# 🚀 唯一主頁標題區
# =========================================================
st.markdown("""
    <div style="padding: 10px 0px 10px 0px;">
        <h1 style="margin: 0; padding: 0; display: flex; align-items: center; font-size: 32px;">
            🏭 &lt;超慧&gt;製造部-雲端公佈欄
        </h1>
        <p style="margin: 5px 0 0 0; color: #1B263B; font-size: 15px; font-weight: 500;">
            🌕 <b>花好月圓 ‧ 粽去柚來</b> ｜ 專業效率如滿月，製造品質皆圓滿
        </p>
    </div>
""", unsafe_allow_html=True)

st.markdown("---")

# --- 🚀 安全讀取金鑰 ---
try:
    MY_TOKEN = st.secrets["MY_TOKEN"] if "MY_TOKEN" in st.secrets else ""
except Exception:
    MY_TOKEN = ""

GITHUB_REPO = f"https://{MY_TOKEN}@github.com/ts700805-ops/my-smart-board.git"
IMAGE_FOLDER = "images"
if not os.path.exists(IMAGE_FOLDER): os.makedirs(IMAGE_FOLDER)

# --- 安全整數轉型函式 ---
def safe_int(val, default=0):
    try:
        if pd.isna(val):
            return default
        return int(val)
    except Exception:
        return default

# --- GitHub 同步功能 ---
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
    except: pass

# --- 資料庫工具與初始化 ---
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
    
    c.execute('''CREATE TABLE IF NOT EXISTS pending_tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT,
                    order_no TEXT,
                    task_content TEXT,
                    status TEXT DEFAULT '待處理',
                    complete_date TEXT)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS assistant_evaluations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    eval_date TEXT,
                    assistant_name TEXT,
                    eval_item TEXT,
                    eval_target TEXT DEFAULT '',
                    eval_content TEXT DEFAULT '',
                    is_deleted INTEGER DEFAULT 0)''')

    c.execute('''CREATE TABLE IF NOT EXISTS project_tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, 
                    order_no TEXT, 
                    assign_date TEXT,
                    author_name TEXT, 
                    worker_name TEXT, 
                    expected_date TEXT,
                    task_content TEXT DEFAULT '', 
                    finish_date TEXT DEFAULT '',
                    is_finished INTEGER DEFAULT 0, 
                    is_deleted INTEGER DEFAULT 0)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS project_settings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    config_key TEXT UNIQUE,
                    config_value TEXT)''')
    
    try:
        c.execute("ALTER TABLE assistant_evaluations ADD COLUMN eval_target TEXT DEFAULT ''")
    except: pass
    
    c.execute("PRAGMA table_info(project_tasks)")
    existing = {col[1] for col in c.fetchall()}
    required = {
        "order_no": "TEXT", "assign_date": "TEXT", "author_name": "TEXT",
        "worker_name": "TEXT", "expected_date": "TEXT", "task_content": "TEXT DEFAULT ''",
        "finish_date": "TEXT DEFAULT ''", "is_finished": "INTEGER DEFAULT 0",
        "is_deleted": "INTEGER DEFAULT 0"
    }
    for col_name, col_type in required.items():
        if col_name not in existing:
            c.execute(f"ALTER TABLE project_tasks ADD COLUMN {col_name} {col_type}")

    c.execute("UPDATE project_tasks SET is_finished = 0 WHERE is_finished IS NULL")
    c.execute("UPDATE project_tasks SET is_deleted = 0 WHERE is_deleted IS NULL")

    conn.commit()
    conn.close()

init_db()

# =========================================================
# 📌 全新無卡死頂部分頁導航 (Tabs)
# =========================================================
tab_home, tab_quality, tab_pending, tab_project, tab_eval, tab_write_post, tab_write_quality, tab_history, tab_admin = st.tabs([
    "🏠 公佈欄首頁", 
    "⚠️ 品質異常首頁",
    "🛠️ 製造部待處理清單",
    "🔴 專案管理首頁",
    "🎀 助理績效考核區",
    "✍️ 撰寫新公告", 
    "📝 撰寫品質",
    "📜 所有紀錄", 
    "⚙️ 管理後台"
])

# ---------------------------------------------------------
# 1. 🏠 公佈欄首頁
# ---------------------------------------------------------
with tab_home:
    if "home_font_scale" not in st.session_state:
        st.session_state.home_font_scale = 130

    st.session_state.home_font_scale = st.slider(
        "📢 現場看板字體大小微調 (%)", 
        min_value=100, max_value=200, value=st.session_state.home_font_scale, step=10, key="home_font_slider"
    )
    
    font_scale = st.session_state.home_font_scale
    info_label_size = int(18 * (font_scale / 100))    
    info_content_size = int(20 * (font_scale / 100))  

    st.markdown(f"""
        <style>
        .home-info-label {{ font-size: {info_label_size}px !important; font-weight: bold !important; color: #0D1B2A; margin-bottom: 8px; }}
        .home-info-content {{ font-size: {info_content_size}px !important; line-height: 1.7 !important; font-weight: 500 !important; color: #111111 !important; background-color: #FFFEEF; padding: 15px; border-radius: 8px; border-left: 5px solid #F1C40F; margin-bottom: 12px; white-space: pre-wrap; }}
        </style>
    """, unsafe_allow_html=True)

    search_q = st.text_input("🔍 搜尋公告內容或發布人", "", key="search_home")
    conn = get_conn()
    query = "SELECT * FROM posts WHERE is_deleted = 0"
    if search_q:
        query += f" AND (content LIKE '%{search_q}%' OR author LIKE '%{search_q}%')"
    df = pd.read_sql(f"{query} ORDER BY id DESC", conn)
    conn.close()
    
    if df.empty:
        st.info("目前尚無公告內容。")
    else:
        for _, r in df.iterrows():
            with st.container():
                st.markdown(f"<div class='home-info-label'>📅 {r['date']} ｜ 👤 發布人：{r['author']}</div>", unsafe_allow_html=True)
                st.markdown(f"<div class='home-info-content'>{r['content']}</div>", unsafe_allow_html=True)
                if r['image_path'] and os.path.exists(r['image_path']):
                    with st.popover("🖼️ 檢視照片"):
                        st.image(r['image_path'], use_container_width=True)

# ---------------------------------------------------------
# 2. ⚠️ 品質異常首頁
# ---------------------------------------------------------
with tab_quality:
    st.subheader("⚠️ 品質異常管理首頁")
    
    if "quality_font_scale" not in st.session_state:
        st.session_state.quality_font_scale = 130
        
    st.session_state.quality_font_scale = st.slider(
        "🔍 現場看板字體大小微調 (%)", min_value=100, max_value=200, value=st.session_state.quality_font_scale, step=10, key="quality_font_slider"
    )
    
    font_scale = st.session_state.quality_font_scale
    q_label_size = int(18 * (font_scale / 100))    
    q_content_size = int(20 * (font_scale / 100))  

    st.markdown(f"""
        <style>
        .quality-staff {{ font-size: {q_label_size}px !important; font-weight: bold !important; color: #333333; margin-bottom: 5px; }}
        .quality-error-content {{ font-size: {q_content_size}px !important; line-height: 1.6 !important; font-weight: 600 !important; color: #B71C1C !important; background-color: #FFEBEE; padding: 12px; border-radius: 6px; border-left: 5px solid #D32F2F; margin-bottom: 10px; white-space: pre-wrap; }}
        </style>
    """, unsafe_allow_html=True)

    search_q = st.text_input("🔍 搜尋製令、人員 or 異常內容", "", key="search_quality")
    conn = get_conn()
    query = "SELECT * FROM quality_posts WHERE is_deleted = 0"
    if search_q:
        query += f" AND (order_no LIKE '%{search_q}%' OR content LIKE '%{search_q}%' OR staff_name LIKE '%{search_q}%' OR category LIKE '%{search_q}%')"
    df = pd.read_sql(f"{query} ORDER BY id DESC", conn)
    conn.close()
    
    if df.empty:
        st.info("目前無異常紀錄。")
    else:
        for _, r in df.iterrows():
            with st.expander(f"🔴 [{r['date']}] 製令：{r['order_no']} | 分類：{r['category']}", expanded=True):
                st.markdown(f"<div class='quality-staff'>👤 <b>相關人員：</b> {r['staff_name']}</div>", unsafe_allow_html=True)
                st.markdown(f"<div class='quality-error-content'>🚨 <b>異常內容：</b> {r['content']}</div>", unsafe_allow_html=True)
                if r['image_path'] and os.path.exists(r['image_path']):
                    with st.popover("🖼️ 檢視異常照片"):
                        st.image(r['image_path'], width=800)

# ---------------------------------------------------------
# 3. 🛠️ 製造部待處理清單
# ---------------------------------------------------------
with tab_pending:
    if "task_font_scale" not in st.session_state:
        st.session_state.task_font_scale = 170
        
    st.session_state.task_font_scale = st.slider(
        "🔍 現場看板字體大小微調 (%)", min_value=100, max_value=200, value=st.session_state.task_font_scale, step=10, key="task_font_slider"
    )
    
    font_scale = st.session_state.task_font_scale
    title_size = int(24 * (font_scale / 100))
    label_size = int(18 * (font_scale / 100))
    value_size = int(20 * (font_scale / 100))
    content_size = int(18 * (font_scale / 100))

    st.markdown(f"""
        <style>
        .duanwu-header {{ background: linear-gradient(135deg, #0D1B2A 0%, #1B263B 100%); padding: 20px; border-radius: 12px; color: #FFFFFF; margin-bottom: 25px; box-shadow: 0 4px 15px rgba(13,27,42,0.2); border-left: 6px solid #F1C40F; }}
        .duanwu-title {{ font-size: {title_size}px !important; font-weight: 700 !important; margin: 0 !important; padding: 0 !important; letter-spacing: 1px; }}
        .large-text-label {{ font-size: {label_size}px !important; font-weight: bold !important; color: #333333; }}
        .large-text-value {{ font-size: {value_size}px !important; font-weight: 800 !important; color: #0D1B2A; background-color: #FFFEE0; padding: 2px 8px; border-radius: 6px; }}
        .large-text-content {{ font-size: {content_size}px !important; color: #111111 !important; line-height: 1.7 !important; font-weight: 600 !important; white-space: pre-wrap; }}
        </style>
    """, unsafe_allow_html=True)

    st.markdown("""
        <div class="duanwu-header">
            <div class="duanwu-title">🌕 🛠️ 製造部待處理事項清單 (月圓看板)</div>
        </div>
    """, unsafe_allow_html=True)

    conn = get_conn()
    df_task = pd.read_sql("SELECT date, order_no, task_content FROM pending_tasks WHERE status = '待處理' ORDER BY date ASC", conn)
    conn.close()
    
    if df_task.empty:
        st.markdown(f"""
            <div style="background-color: #FFFDF3; border: 1px solid #F1C40F; padding: 25px; border-radius: 8px; text-align: center; color: #0D1B2A; font-size: {value_size}px; font-weight: bold;">
                🎉 <b>目前暫無待處理事項！所有任務皆已順利完工圓滿！</b>
            </div>
        """, unsafe_allow_html=True)
    else:
        for _, row in df_task.iterrows():
            t_date = row['date'] if row['date'] else "未排程"
            t_order = row['order_no'] if row['order_no'] else "無製令"
            t_content = row['task_content'] if row['task_content'] else "未填寫內容"
            
            with st.container(border=True):
                c1, c2, c3 = st.columns([3.5, 3.5, 1])
                c1.markdown(f"<span class='large-text-label'>🌕 📅 發佈日期：</span><span class='large-text-value'>{t_date}</span>", unsafe_allow_html=True)
                c2.markdown(f"<span class='large-text-label'>🔢 製令：</span><span class='large-text-value'>{t_order}</span>", unsafe_allow_html=True)
                c3.markdown(f"<div style='text-align: right; font-size: {value_size}px;'>🥮</div>", unsafe_allow_html=True)
                st.markdown("<div style='margin-top: 10px; margin-bottom: 10px; border-top: 1px dashed #DDD;'></div>", unsafe_allow_html=True)
                st.markdown(f"<div class='large-text-content'><b>📋 任務內容：</b>\n{t_content}</div>", unsafe_allow_html=True)

# ---------------------------------------------------------
# 4. 🔴 專案管理首頁
# ---------------------------------------------------------
with tab_project:
    st.subheader("📋 專案進度追蹤看板")
    
    conn = get_conn()
    s_df = pd.read_sql("SELECT name FROM staff", conn)
    staff_options = s_df['name'].tolist() if not s_df.empty else ["無人員資料"]
    
    cursor = conn.cursor()
    cursor.execute("SELECT config_value FROM project_settings WHERE config_key = 'team_mapping'")
    row_mapping = cursor.fetchone()
    conn.close()
    
    mapping_text = row_mapping[0] if row_mapping else "林威呈:陳文山,李俊霖,陳育信,陳凱彥,蘇雍盛,鄭至賢\n組長B:成員3,成員4"
    
    author_options, worker_options = [], []
    for line in mapping_text.split("\n"):
        if ":" in line:
            leader, members = line.split(":", 1)
            leader = leader.strip()
            if leader and leader not in author_options: author_options.append(leader)
            if leader not in worker_options: worker_options.append(leader)
            for m in members.split(","):
                if m.strip(): worker_options.append(m.strip())

    if not author_options: author_options = staff_options
    if not worker_options: worker_options = staff_options

    with st.expander("✍️ 新增專案任務", expanded=True):
        c1, c2, c3 = st.columns(3)
        p_order = c1.text_input("製令編號", key="add_p_order")
        p_assign = c2.date_input("指派日", value=datetime.today(), key="add_p_assign")
        p_expect = c3.date_input("預計完工日", value=datetime.today() + timedelta(days=7), key="add_p_expect")
        c4, c5 = st.columns(2)
        p_author = c4.selectbox("發布人", author_options, key="add_p_author")
        p_worker = c5.selectbox("執行人", worker_options, key="add_p_worker")
        p_content = st.text_area("📝 執行內容", key="add_p_content")
        
        if st.button("➕ 確定新增專案", type="primary", use_container_width=True, key="btn_add_project_direct"):
            if p_order.strip() and p_content.strip():
                conn_add = get_conn()
                c_add = conn_add.cursor()
                c_add.execute("""
                    INSERT INTO project_tasks 
                    (order_no, assign_date, author_name, worker_name, expected_date, task_content, finish_date, is_finished, is_deleted) 
                    VALUES (?, ?, ?, ?, ?, ?, '', 0, 0)
                """, (p_order.strip(), str(p_assign), p_author, p_worker, str(p_expect), p_content.strip()))
                conn_add.commit()
                conn_add.close()
                sync_to_github("Add Project Task")
                st.success("✅ 專案任務已成功新增！")
                time.sleep(0.5)
                st.rerun()
            else:
                st.error("⚠️ 「製令編號」與「執行內容」為必填項目！")

    st.markdown("---")
    st.markdown("### 🟡 進行中專案清單")
    
    conn_read = get_conn()
    df_active = pd.read_sql("""
        SELECT * FROM project_tasks 
        WHERE COALESCE(is_finished, 0) = 0 
          AND COALESCE(is_deleted, 0) = 0 
        ORDER BY id DESC
    """, conn_read)
    conn_read.close()

    if df_active.empty:
        st.info("目前沒有進行中的專案任務。")
    else:
        for _, row in df_active.iterrows():
            tid = safe_int(row.get('id'))
            if tid == 0: continue
            desc = row.get('task_content') or "未填寫執行內容"
            m1, m2, m3, m4 = st.columns([5, 1.5, 1.5, 1.5])
            m1.info(f"**製令：** {row.get('order_no','')} | **指派日：** {row.get('assign_date','')} | **發布：** {row.get('author_name','')} | **執行：** {row.get('worker_name','')} | **預計完工：** {row.get('expected_date','')}\n\n**📝 內容：** {desc}")

            with m2:
                if st.button("🟢 點我完工", key=f"p_finish_btn_{tid}", use_container_width=True):
                    try:
                        conn = get_conn()
                        conn.execute("UPDATE project_tasks SET is_finished=1, finish_date=? WHERE id=?", (datetime.now().strftime("%Y-%m-%d"), tid))
                        conn.commit()
                        conn.close()
                        sync_to_github("Finish Project Task")
                        st.rerun()
                    except Exception as e:
                        st.error(f"完工更新失敗：{e}")

            with m3.popover("📝 編輯", use_container_width=True):
                e_order = st.text_input("修改製令", value=row.get('order_no') or "", key=f"e_ord_{tid}")
                e_author = st.selectbox("修改發布人", author_options, index=author_options.index(row['author_name']) if row.get('author_name') in author_options else 0, key=f"e_auth_{tid}")
                e_worker = st.selectbox("修改執行人", worker_options, index=worker_options.index(row['worker_name']) if row.get('worker_name') in worker_options else 0, key=f"e_work_{tid}")
                e_content = st.text_area("修改執行內容", value=row.get('task_content') or "", key=f"e_cont_{tid}")
                if st.button("💾 儲存修改", key=f"save_{tid}", use_container_width=True):
                    try:
                        conn = get_conn()
                        conn.execute("UPDATE project_tasks SET order_no=?, author_name=?, worker_name=?, task_content=? WHERE id=?", (e_order, e_author, e_worker, e_content, tid))
                        conn.commit()
                        conn.close()
                        sync_to_github("Edit Project Task")
                        st.rerun()
                    except Exception as e:
                        st.error(f"儲存修改失敗：{e}")

            with m4.popover("🗑️ 刪除", use_container_width=True):
                if st.button("🚨 確定刪除", key=f"del_{tid}", use_container_width=True):
                    try:
                        conn = get_conn()
                        conn.execute("UPDATE project_tasks SET is_deleted=1 WHERE id=?", (tid,))
                        conn.commit()
                        conn.close()
                        sync_to_github("Delete Project Task")
                        st.rerun()
                    except Exception as e:
                        st.error(f"刪除失敗：{e}")

    st.markdown("---")
    st.markdown("### 🟢 已完工歷史專案清單")
    conn = get_conn()
    df_finished = pd.read_sql("""
        SELECT * FROM project_tasks 
        WHERE COALESCE(is_finished, 0) = 1 
          AND COALESCE(is_deleted, 0) = 0 
        ORDER BY id DESC
    """, conn)
    conn.close()

    if df_finished.empty:
        st.caption("目前尚無已完工的歷史專案。")
    else:
        for _, row in df_finished.iterrows():
            tid = safe_int(row.get('id'))
            if tid == 0: continue
            desc = row.get('task_content') or "無執行內容"
            m1, m2, m3 = st.columns([8, 1.5, 1.5])
            m1.success(f"✅ **製令：** {row.get('order_no','')} | **發布：** {row.get('author_name','')} | **執行：** {row.get('worker_name','')} | **實際完工：** {row.get('finish_date','')}\n\n**📝 內容：** {desc}")

# ---------------------------------------------------------
# 5. 🎀 助理績效考核區
# ---------------------------------------------------------
with tab_eval:
    st.subheader("🎀 助理績效考核管理系統")

    db_conn = sqlite3.connect("bulletin.db")
    staff_df = pd.read_sql("SELECT name FROM staff ORDER BY name", db_conn)
    staff_list = staff_df["name"].tolist()

    eval_df = pd.read_sql("""
        SELECT * FROM assistant_evaluations
        WHERE is_deleted = 0
        ORDER BY assistant_name ASC, eval_date DESC, id DESC
    """, db_conn)
    db_conn.close()

    st.markdown("### ✍️ 新增績效考核紀錄")

    with st.form("add_eval_form_tab", clear_on_submit=True):
        top_c1, top_c2 = st.columns(2)
        sel_assistant = top_c1.selectbox("🎀 選擇助理姓名", staff_list if staff_list else ["⚠️ 請先新增人員"])
        sel_date = top_c2.date_input("📅 完成日期", value=datetime.today())

        c1, c2, c3 = st.columns(3)
        txt_item = c1.text_area("📊 考核項目")
        txt_target = c2.text_area("🎯 考核指標")
        txt_content = c3.text_area("✨ 考核紀錄")

        if st.form_submit_button("💝 立即存檔紀錄"):
            if not staff_list:
                st.error("請先至管理後台新增人員")
            else:
                db_conn = sqlite3.connect("bulletin.db")
                db_conn.execute("""
                    INSERT INTO assistant_evaluations (eval_date, assistant_name, eval_item, eval_target, eval_content)
                    VALUES (?, ?, ?, ?, ?)
                """, (sel_date.strftime("%Y-%m-%d"), sel_assistant, txt_item, txt_target, txt_content))
                db_conn.commit()
                db_conn.close()
                sync_to_github("Add Evaluation")
                st.success("✅ 存檔成功")
                st.rerun()

    st.markdown("---")
    st.markdown("### 📜 績效考核列表與編輯")

    if eval_df.empty:
        st.info("目前尚無任何考核紀錄")
    else:
        display_df = eval_df[['id', 'eval_date', 'assistant_name', 'eval_item', 'eval_target', 'eval_content']].copy()
        display_df['🗑️ 刪除'] = False 

        edited_df = st.data_editor(
            display_df,
            column_config={
                "id": None, 
                "eval_date": st.column_config.TextColumn("📅 日期"),
                "assistant_name": st.column_config.SelectboxColumn("👤 姓名", options=staff_list), 
                "eval_item": st.column_config.TextColumn("📊 考核項目"),
                "eval_target": st.column_config.TextColumn("🎯 考核指標"),
                "eval_content": st.column_config.TextColumn("✨ 考核紀錄"),
                "🗑️ 刪除": st.column_config.CheckboxColumn("🗑️ 刪除", default=False) 
            },
            hide_index=True,          
            use_container_width=True, 
            key="eval_grid_editor_tab"
        )

        if st.button("💾 儲存表格所有修改", type="primary", key="save_eval_grid"):
            db_conn = sqlite3.connect("bulletin.db")
            for index, row in edited_df.iterrows():
                if row['🗑️ 刪除']:
                    db_conn.execute("UPDATE assistant_evaluations SET is_deleted = 1 WHERE id = ?", (row["id"],))
                else:
                    db_conn.execute("""
                        UPDATE assistant_evaluations 
                        SET eval_date=?, assistant_name=?, eval_item=?, eval_target=?, eval_content=? 
                        WHERE id=?
                    """, (row['eval_date'], row['assistant_name'], row['eval_item'], row['eval_target'], row['eval_content'], row['id']))
            db_conn.commit()
            db_conn.close()
            sync_to_github("Update Evaluation via Grid")
            st.success("✅ 所有修改已成功儲存！")
            time.sleep(0.5)
            st.rerun()

# ---------------------------------------------------------
# 6. ✍️ 撰寫新公告
# ---------------------------------------------------------
with tab_write_post:
    st.subheader("📝 發布新訊息")
    conn = get_conn()
    s_df = pd.read_sql("SELECT name FROM staff", conn)
    conn.close()
    author = st.selectbox("發布人", s_df['name'].tolist()) if not s_df.empty else st.text_input("發布人")
    msg = st.text_area("公告內容", key="new_post_msg")
    file = st.file_uploader("🖼️ 上傳照片", type=['jpg', 'png', 'jpeg'], key="new_post_img")
    if st.button("🚀 確定並發布", type="primary"):
        if msg:
            p = ""
            if file:
                p = f"{IMAGE_FOLDER}/n_{datetime.now().strftime('%Y%m%d%H%M%S')}_{file.name}"
                with open(p, "wb") as f: f.write(file.getbuffer())
            conn = get_conn()
            t = (datetime.utcnow() + timedelta(hours=8)).strftime("%Y-%m-%d %H:%M")
            conn.execute("INSERT INTO posts (date, author, content, image_path, is_deleted) VALUES (?, ?, ?, ?, 0)", (t, author, msg, p))
            conn.commit()
            conn.close()
            sync_to_github("New Post - 20260705029")
            st.success("🎉 發布成功！檔案已即時更新存檔。")
            time.sleep(1)
            st.rerun()

# ---------------------------------------------------------
# 7. 📝 撰寫品質
# ---------------------------------------------------------
with tab_write_quality:
    st.subheader("✍️ 記錄品質異常")
    col1, col2 = st.columns(2)
    with col1:
        order_no = st.text_input("工單/製令編號", key="q_order_in")
        q_cat = st.selectbox("異常分類", ["零件異常", "外觀異常", "組裝問題", "流程問題", "其他"], key="q_cat_in")
    with col2:
        conn = get_conn()
        s_list = pd.read_sql("SELECT name FROM staff", conn)['name'].tolist()
        conn.close()
        q_staff = st.selectbox("相關人員", s_list) if s_list else st.text_input("相關人員", key="q_staff_in")
    
    q_content = st.text_area("異常描述", key="q_desc_in")
    q_file = st.file_uploader("🖼️ 現場照片", type=['jpg', 'png', 'jpeg'], key="q_img_in")
    if st.button("🚨 提交紀錄", type="primary"):
        if order_no and q_content:
            p = ""
            if q_file:
                p = f"{IMAGE_FOLDER}/q_{datetime.now().strftime('%Y%m%d%H%M%S')}_{q_file.name}"
                with open(p, "wb") as f: f.write(q_file.getbuffer())
            conn = get_conn()
            t = (datetime.utcnow() + timedelta(hours=8)).strftime("%Y-%m-%d %H:%M")
            conn.execute("INSERT INTO quality_posts (date, order_no, content, category, staff_name, image_path, is_deleted) VALUES (?, ?, ?, ?, ?, ?, 0)", (t, order_no, q_content, q_cat, q_staff, p))
            conn.commit()
            conn.close()
            sync_to_github("New Quality Alert - 20260705029")
            st.success("🚨 品質紀錄已成功存檔！")
            time.sleep(1)
            st.rerun()

# ---------------------------------------------------------
# 8. 📜 所有紀錄
# ---------------------------------------------------------
with tab_history:
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

# ---------------------------------------------------------
# 9. ⚙️ 管理後台
# ---------------------------------------------------------
with tab_admin:
    st.subheader("🛠️ 管理系統")
    t1, t2, t3, t4 = st.tabs(["公告管理", "品質紀錄管理", "人員管理", "待處理事項管理"])
 
    with t1:
        conn = get_conn()
        df = pd.read_sql("SELECT * FROM posts WHERE is_deleted = 0 ORDER BY id DESC", conn)
        conn.close()
        for _, r in df.iterrows():
            c1, c2, c3 = st.columns([6, 2, 2])
            c1.write(f"[{r['date']}] {r['content'][:20]}...")
            with c2.popover("📝 編輯"):
                nc = st.text_area("修改內容", value=r['content'], key=f"adm_ep_{r['id']}")
                if st.button("💾 儲存", key=f"adm_sp_{r['id']}"):
                    conn = get_conn()
                    conn.execute("UPDATE posts SET content = ? WHERE id = ?", (nc, r['id']))
                    conn.commit(); conn.close()
                    sync_to_github("Edit Post - 20260705029"); st.rerun()
            if c3.button("🗑️ 刪除", key=f"adm_dp_{r['id']}"):
                conn = get_conn(); conn.execute("UPDATE posts SET is_deleted = 1 WHERE id = ?", (r['id'],)); conn.commit(); conn.close(); sync_to_github("Del Post - 20260705029"); st.rerun()

    with t2:
        conn = get_conn()
        df_q = pd.read_sql("SELECT * FROM quality_posts WHERE is_deleted = 0 ORDER BY id DESC", conn)
        conn.close()
        for _, r in df_q.iterrows():
            qc1, qc2, qc3 = st.columns([6, 2, 2])
            qc1.write(f"[{r['date']}] 製令:{r['order_no']} | 人員:{r['staff_name']}")
            with qc2.popover("📝 編輯"):
                new_content = st.text_area("內容", value=r['content'], key=f"adm_ucont_{r['id']}")
                if st.button("💾 儲存修改", key=f"adm_save_q_{r['id']}"):
                    conn = get_conn()
                    conn.execute("UPDATE quality_posts SET content=? WHERE id=?", (new_content, r['id']))
                    conn.commit(); conn.close(); sync_to_github("Edit Quality - 20260705029"); st.rerun()
            if qc3.button("🗑️ 刪除", key=f"adm_dq_{r['id']}"):
                conn = get_conn(); conn.execute("UPDATE quality_posts SET is_deleted = 1 WHERE id = ?", (r['id'],)); conn.commit(); conn.close(); sync_to_github("Del Quality - 20260705029"); st.rerun()

    with t3:
        st.write("### 👥 人員名單管理")
        new_n = st.text_input("輸入新人員姓名", key="adm_new_staff")
        if st.button("➕ 新增人員", key="adm_add_staff_btn"):
            if new_n:
                conn = get_conn()
                try:
                    conn.execute("INSERT INTO staff (name) VALUES (?)", (new_n,))
                    conn.commit(); conn.close(); sync_to_github(f"Add {new_n} - 20260705029"); st.rerun()
                except: conn.close(); st.error("人員已存在")
        st.markdown("---")
        conn = get_conn()
        curr_df = pd.read_sql("SELECT * FROM staff", conn)
        conn.close()
        for _, row in curr_df.iterrows():
            col1, col2 = st.columns([8, 2])
            col1.write(f"👤 {row['name']}")
            if col2.button("🗑️ 刪除人員", key=f"adm_ds_{row['id']}"):
                conn = get_conn(); conn.execute("DELETE FROM staff WHERE id = ?", (row['id'],)); conn.commit(); conn.close(); sync_to_github("Remove Staff - 20260705029"); st.rerun()

    with t4:
        st.write("### 📝 新增待處理事項")
        with st.form("task_form_adm", clear_on_submit=True):
            col_a, col_b = st.columns(2)
            t_date = col_a.date_input("日期")
            t_order = col_b.text_input("製令編號")
            t_msg = st.text_area("待處理項目內容")
            if st.form_submit_button("➕ 新增到清單"):
                if t_order and t_msg:
                    conn = get_conn()
                    conn.execute("INSERT INTO pending_tasks (date, order_no, task_content) VALUES (?, ?, ?)", (str(t_date), t_order, t_msg))
                    conn.commit(); conn.close(); sync_to_github("Add Task - 20260705029"); st.rerun()
