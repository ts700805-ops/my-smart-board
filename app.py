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
# 1. 網頁基本設定 (全域唯一配置，確保最上方不重疊)
# =========================================================
st.set_page_config(
    page_title="超慧製造部-雲端公佈欄", 
    page_icon="🥮", 
    layout="wide"
)

# --- 🖼️ 處理圖片背景轉為 Base64 (安全不卡死機制) ---
def get_base64_image(image_path):
    try:
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    except:
        return ""

# 讀取圖片背景
img_base64 = get_base64_image("image_b13023.jpg")

# --- 🎑 中秋節高質感金秋月夜氣氛 CSS 注入 ---
st.markdown("""
    <style>
    /* 全域背景顏色：淡淡的柔和月光黃 */
    .stApp {
        background-color: #FDFBF0 !important;
    }

    /* 頂部導航列細條裝飾顏色：深邃月夜藍 */
    header[data-testid="stHeader"] {
        background-color: #0D1B2A !important;
        border-bottom: 3px solid #F1C40F !important;
    }

    /* 側邊欄風格：高質感深藍月夜底 */
    [data-testid="stSidebar"] {
        background-color: #112233 !important;
    }
    
    /* 確保側邊欄文字、選單全部清晰呈現白色與金黃色 */
    [data-testid="stSidebar"] *, [data-testid="stSidebar"] span, [data-testid="stSidebar"] p {
        color: #FFFFFF !important;
    }

    /* 網頁主標題與各級標題字體顏色統一為深藍夜色 */
    h1, h2, h3 {
        color: #0D1B2A !important;
        font-family: "Microsoft JhengHei", sans-serif;
    }

    /* 提示卡片與容器圓角美化 */
    .stAlert, div[data-testid="stImageFilterBackground"] {
        border-radius: 12px !important;
        box-shadow: 0 2px 8px rgba(0,0,0,0.04) !important;
    }
    </style>
    """, unsafe_allow_html=True)

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
    
    # 製造部待處理事項資料表
    c.execute('''CREATE TABLE IF NOT EXISTS pending_tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT,
                    order_no TEXT,
                    task_content TEXT,
                    status TEXT DEFAULT '待處理',
                    complete_date TEXT)''')
    
    # 🔴 專案管理資料表
    c.execute('''CREATE TABLE IF NOT EXISTS projects (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT,
                    project_name TEXT,
                    content TEXT,
                    status TEXT DEFAULT '進行中',
                    is_deleted INTEGER DEFAULT 0)''')
    
    # 🎀 助理績效考核資料表
    c.execute('''CREATE TABLE IF NOT EXISTS assistant_evaluations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    eval_date TEXT,
                    assistant_name TEXT,
                    eval_item TEXT,
                    eval_target TEXT DEFAULT '',
                    eval_content TEXT DEFAULT '',
                    is_deleted INTEGER DEFAULT 0)''')
    
    # 🎀 助理姓名獨立名單資料表
    c.execute('CREATE TABLE IF NOT EXISTS assistant_staff (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT UNIQUE)')
    
    conn.commit()
    conn.close()

init_db()

# --- 🚀 動態計算最新版本流水碼 (依指定版本每次流水碼遞增+1) ---
def get_current_version():
    return "20260705014"

current_sys_version = get_current_version()

# =========================================================
# 🏠 側邊欄配置：中秋佳節新氣象
# =========================================================
with st.sidebar:
    # 系統版本號與最新流水碼連動
    st.markdown(f"<h4 style='color: #F1C40F; margin-bottom: 5px;'>系統版本：{current_sys_version}</h4>", unsafe_allow_html=True)
    
    menu = st.selectbox(
        "功能選單",
        ["🏠 公佈欄首頁", "⚠️ 品質異常首頁", "🛠️ 製造部待處理清單", "✍️ 撰寫新公告", "📝 撰寫品質", "🔴 專案管理首頁", "🎀 助理績效考核區", "📜 所有紀錄", "⚙️ 管理後台"]
    )
    
    # 渲染照片區
    try:
        festive_img = Image.open("image_b13023.jpg")
        st.image(festive_img, use_container_width=True)
    except:
        st.caption("🌕 歲歲年年 ‧ 月圓人安 🌕")
    
    st.markdown("<hr style='border-color: rgba(255,255,255,0.2);'>", unsafe_allow_html=True)
    st.markdown("### 🥮 製造部中秋公告")
    st.caption("告別端午，喜迎 9/25 中秋佳節 ─ 柚香傳情，事事圓滿！")

# =========================================================
# 🚀 唯一主頁標題區
# =========================================================
st.markdown("""
    <div style="padding: 10px 0px 20px 0px;">
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

# --- 頁面邏輯 ---
# 1. 一般公佈欄首頁
if menu == "🏠 公佈欄首頁":
    if "home_font_scale" not in st.session_state:
        st.session_state.home_font_scale = 130

    st.session_state.home_font_scale = st.slider(
        "📢 現場看板字體大小微調 (%)", 
        min_value=100, 
        max_value=200, 
        value=st.session_state.home_font_scale, 
        step=10,
        key="home_font_slider"
    )
    
    font_scale = st.session_state.home_font_scale
    info_label_size = int(18 * (font_scale / 100))    
    info_content_size = int(20 * (font_scale / 100))  

    st.markdown(f"""
        <style>
        .home-info-label {{
            font-size: {info_label_size}px !important;
            font-weight: bold !important;
            color: #0D1B2A;
            margin-bottom: 8px;
        }}
        .home-info-content {{
            font-size: {info_content_size}px !important;
            line-height: 1.7 !important;
            font-weight: 500 !important;
            color: #111111 !important;
            background-color: #FFFEEF;
            padding: 15px;
            border-radius: 8px;
            border-left: 5px solid #F1C40F;
            margin-bottom: 12px;
            white-space: pre-wrap;
        }}
        </style>
    """, unsafe_allow_html=True)
    st.markdown("---")

    search_q = st.text_input("🔍 搜尋公告內容或發布人", "")
    conn = get_conn()
    query = "SELECT * FROM posts WHERE is_deleted = 0"
    if search_q:
        query += f" AND (content LIKE '%{search_q}%' OR author LIKE '%{search_q}%')"
    df = pd.read_sql(f"{query} ORDER BY id DESC", conn)
    conn.close()
    
    for _, r in df.iterrows():
        with st.container():
            st.markdown(f"<div class='home-info-label'>📅 {r['date']} ｜ 👤 發布人：{r['author']}</div>", unsafe_allow_html=True)
            st.markdown(f"<div class='home-info-content'>{r['content']}</div>", unsafe_allow_html=True)
            if r['image_path'] and os.path.exists(r['image_path']):
                with st.popover("🖼️ 檢視照片"):
                    st.image(r['image_path'], use_container_width=True)
        
    st.markdown("---")

# 2. 品質異常首頁
elif menu == "⚠️ 品質異常首頁":
    st.subheader("⚠️ 品質異常管理首頁")
    
    if "quality_font_scale" not in st.session_state:
        st.session_state.quality_font_scale = 130
        
    st.session_state.quality_font_scale = st.slider(
        "🔍 現場看板字體大小微調 (%)", 
        min_value=100, 
        max_value=200, 
        value=st.session_state.quality_font_scale, 
        step=10,
        key="quality_font_slider"
    )
    
    font_scale = st.session_state.quality_font_scale
    q_label_size = int(18 * (font_scale / 100))    
    q_content_size = int(20 * (font_scale / 100))  

    st.markdown(f"""
        <style>
        .stExpander p {{
            font-size: {int(18 * (font_scale / 100))}px !important;
            font-weight: bold !important;
        }}
        .quality-staff {{
            font-size: {q_label_size}px !important;
            font-weight: bold !important;
            color: #333333;
            margin-bottom: 5px;
        }}
        .quality-error-content {{
            font-size: {q_content_size}px !important;
            line-height: 1.6 !important;
            font-weight: 600 !important;
            color: #B71C1C !important;
            background-color: #FFEBEE;
            padding: 12px;
            border-radius: 6px;
            border-left: 5px solid #D32F2F;
            margin-bottom: 10px;
            white-space: pre-wrap;
        }}
        </style>
    """, unsafe_allow_html=True)

    search_q = st.text_input("🔍 搜尋製令、人員 or 異常內容", "")
    conn = get_conn()
    query = "SELECT * FROM quality_posts WHERE is_deleted = 0"
    if search_q:
        query += f" AND (order_no LIKE '%{search_q}%' OR content LIKE '%{search_q}%' OR staff_name LIKE '%{search_q}%' OR category LIKE '%{search_q}%')"
    df = pd.read_sql(f"{query} ORDER BY id DESC", conn)
    conn.close()
    
    for _, r in df.iterrows():
        with st.expander(f"🔴 [{r['date']}] 製令：{r['order_no']} | 分類：{r['category']}", expanded=True):
            st.markdown(f"<div class='quality-staff'>👤 <b>相關人員：</b> {r['staff_name']}</div>", unsafe_allow_html=True)
            st.markdown(f"<div class='quality-error-content'>🚨 <b>異常內容：</b> {r['content']}</div>", unsafe_allow_html=True)
            if r['image_path'] and os.path.exists(r['image_path']):
                with st.popover("🖼️ 檢視異常照片"):
                    st.image(r['image_path'], width=800)

# 3. 製造部待處理事項清單
elif menu == "🛠️ 製造部待處理清單":
    if "task_font_scale" not in st.session_state:
        st.session_state.task_font_scale = 170
        
    st.session_state.task_font_scale = st.slider(
        "🔍 現場看板字體大小微調 (%)", 
        min_value=100, 
        max_value=200, 
        value=st.session_state.task_font_scale, 
        step=10,
        key="task_font_slider"
    )
    
    font_scale = st.session_state.task_font_scale
    title_size = int(24 * (font_scale / 100))
    label_size = int(18 * (font_scale / 100))
    value_size = int(20 * (font_scale / 100))
    content_size = int(18 * (font_scale / 100))

    st.markdown(f"""
        <style>
        .duanwu-header {{
            background: linear-gradient(135deg, #0D1B2A 0%, #1B263B 100%);
            padding: 20px;
            border-radius: 12px;
            color: #FFFFFF;
            margin-bottom: 25px;
            box-shadow: 0 4px 15px rgba(13,27,42,0.2);
            border-left: 6px solid #F1C40F;
        }}
        .duanwu-title {{
            font-size: {title_size}px !important;
            font-weight: 700 !important;
            margin: 0 !important;
            padding: 0 !important;
            letter-spacing: 1px;
        }}
        .duanwu-subtitle {{
            font-size: {max(13, int(15 * (font_scale/100)))}px;
            color: #E0E0E0;
            margin-top: 5px;
            font-style: italic;
        }}
        .large-text-label {{
            font-size: {label_size}px !important;
            font-weight: bold !important;
            color: #333333;
        }}
        .large-text-value {{
            font-size: {value_size}px !important;
            font-weight: 800 !important;
            color: #0D1B2A;
            background-color: #FFFEE0;
            padding: 2px 8px;
            border-radius: 6px;
        }}
        .large-text-content {{
            font-size: {content_size}px !important;
            color: #111111 !important;
            line-height: 1.7 !important;
            font-weight: 600 !important;
            white-space: pre-wrap;
        }}
        </style>
    """, unsafe_allow_html=True)

    st.markdown("""
        <div class="duanwu-header">
            <div class="duanwu-title">🌕 🛠️ 製造部待處理事項清單 (月圓看板)</div>
            <div class="duanwu-subtitle">眾志成城 · 事事圓滿 ｜ 如同秋節精準製餅，每項任務皆能完美達標</div>
        </div>
    """, unsafe_allow_html=True)
    
    col_info, col_img = st.columns([3, 1])
    with col_info:
        st.markdown("<p style='font-size: 15px; color:#555555;'>💡 <b>提示：</b>本清單僅顯示狀態為「待處理」之製造任務，依據日期由遠至近排序，請優先處理急件。</p>", unsafe_allow_html=True)
    with col_img:
        st.markdown("""
            <div style="text-align: right; font-size: 14px; color: #0D1B2A; line-height: 1.3;">
                ▲ <b>中秋佳節</b><br>
                <span style="color:#F1C40F; font-weight:bold;">✨ 任務圓滿 ✨</span>
            </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    conn = get_conn()
    df_task = pd.read_sql("SELECT date, order_no, task_content FROM pending_tasks WHERE status = '待處理' ORDER BY date ASC", conn)
    conn.close()
    
    if df_task.empty:
        st.markdown(f"""
            <div style="background-color: #FFFDF3;
            border: 1px solid #F1C40F; padding: 25px; border-radius: 8px; text-align: center; color: #0D1B2A; font-size: {value_size}px;
            font-weight: bold;">
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
                
                st.markdown("<div style='text-align: right; margin-top: 10px; margin-bottom: 10px; border-top: 1px dashed #DDD;'></div>", unsafe_allow_html=True)
                st.markdown(f"<div class='large-text-content'><b>📋 任務內容：</b>\n{t_content}</div>", unsafe_allow_html=True)

# 4. 撰寫一般公告
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
            conn.commit()
            conn.close()
            sync_to_github(f"New Post - {current_sys_version}"); st.balloons(); st.success("發布成功！"); time.sleep(1.5);
            st.rerun()

# 5. 撰寫品質
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
            conn.commit()
            conn.close()
            sync_to_github(f"New Quality Alert - {current_sys_version}"); st.balloons(); st.success("紀錄已存檔！"); time.sleep(1.5);
            st.rerun()

# 6. 所有紀錄
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
    
    st.markdown("--- 🔴 專案管理清單 (全部歷史) ---")
    df_proj_hist = pd.read_sql("SELECT date, project_name, content, status, is_deleted FROM projects ORDER BY id DESC", conn)
    df_proj_hist['狀態'] = df_proj_hist['is_deleted'].apply(lambda x: "正常" if x == 0 else "❌ 已刪除")
    st.dataframe(df_proj_hist[['date', 'project_name', 'content', 'status', '狀態']], use_container_width=True)
    conn.close()

# 7. 管理後台
elif menu == "⚙️ 管理後台":
    st.subheader("🛠️ 管理系統")
    if st.text_input("請輸入管理密碼", type="password") == "0000":
        t1, t2, t3, t4, t5 = st.tabs(["公告管理", "品質紀錄管理", "人員管理", "待處理事項管理", "專案管理後台"])
    
        with t1:
            conn = get_conn()
            df = pd.read_sql("SELECT * FROM posts WHERE is_deleted = 0 ORDER BY id DESC", conn)
            conn.close()
            for _, r in df.iterrows():
                c1, c2, c3 = st.columns([6, 2, 2])
                c1.write(f"[{r['date']}] {r['content'][:20]}...")
                with c2.popover("📝 編輯"):
                    try:
                        curr_date_val = datetime.strptime(r['date'].split(" ")[0], '%Y-%m-%d').date()
                    except:
                        curr_date_val = datetime.today().date()
                    new_post_date = st.date_input("修改日期", value=curr_date_val, key=f"ep_date_{r['id']}")
                    
                    nc = st.text_area("修改內容", value=r['content'], key=f"ep_{r['id']}")
                    if st.button("💾 儲存", key=f"sp_{r['id']}"):
                        conn = get_conn()
                        formatted_date = new_post_date.strftime('%Y-%m-%d')
                        if " " in r['date']: 
                            formatted_date += " " + r['date'].split(" ", 1)[1]
                        conn.execute("UPDATE posts SET date = ?, content = ? WHERE id = ?", (formatted_date, nc, r['id']))
                        conn.commit(); conn.close()
                        sync_to_github(f"Edit Post - {current_sys_version}"); st.rerun()
                if c3.button("🗑️ 刪除", key=f"dp_{r['id']}"):
                    conn = get_conn(); conn.execute("UPDATE posts SET is_deleted = 1 WHERE id = ?", (r['id'],)); conn.commit(); conn.close(); sync_to_github(f"Del Post - {current_sys_version}"); st.rerun()

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
                    try:
                        curr_q_date_val = datetime.strptime(r['date'].split(" ")[0], '%Y-%m-%d').date()
                    except:
                        curr_q_date_val = datetime.today().date()
                    new_q_date = st.date_input("修改日期", value=curr_q_date_val, key=f"uq_date_{r['id']}")
                    
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
                        conn = get_conn()
                        formatted_q_date = new_q_date.strftime('%Y-%m-%d')
                        if " " in r['date']: 
                            formatted_q_date += " " + r['date'].split(" ", 1)[1]
                        conn.execute("UPDATE quality_posts SET date=?, order_no=?, category=?, staff_name=?, content=?, image_path=? WHERE id=?", 
                                     (formatted_q_date, new_order, new_cat, new_staff, new_content, p, r['id']))
                        conn.commit(); conn.close(); sync_to_github(f"Edit Quality - {current_sys_version}"); st.rerun()
                if qc3.button("🗑️ 刪除", key=f"dq_{r['id']}"):
                    conn = get_conn(); conn.execute("UPDATE quality_posts SET is_deleted = 1 WHERE id = ?", (r['id'],)); conn.commit(); conn.close(); sync_to_github(f"Del Quality - {current_sys_version}"); st.rerun()

        with t3:
            st.write("### 👥 人員名單管理")
            new_n = st.text_input("輸入新人員姓名")
            if st.button("➕ 新增人員"):
                if new_n:
                    conn = get_conn()
                    try:
                        conn.execute("INSERT INTO staff (name) VALUES (?)", (new_n,))
                        conn.commit(); conn.close(); sync_to_github(f"Add {new_n} - {current_sys_version}"); st.rerun()
                    except: conn.close(); st.error("人員已存在")
            st.markdown("---")
            conn = get_conn()
            curr_df = pd.read_sql("SELECT * FROM staff", conn)
            conn.close()
            for _, row in curr_df.iterrows():
                col1, col2 = st.columns([8, 2])
                col1.write(f"👤 {row['name']}")
                if col2.button("🗑️ 刪除人員", key=f"ds_{row['id']}"):
                    conn = get_conn(); conn.execute("DELETE FROM staff WHERE id = ?", (row['id'],)); conn.commit(); conn.close(); sync_to_github(f"Remove Staff - {current_sys_version}"); st.rerun()

        with t4:
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
                        conn.commit(); conn.close(); sync_to_github(f"Add Task - {current_sys_version}"); st.rerun()

            st.markdown("---")
            st.write("### ⏳ 目前待處理清單")
            conn = get_conn()
            active_tasks = pd.read_sql("SELECT * FROM pending_tasks WHERE status = '待處理' ORDER BY date ASC", conn)
            conn.close()
            for _, task in active_tasks.iterrows():
                tc1, tc2, tc3 = st.columns([6, 2, 2])
                tc1.warning(f"📅 {task['date']} | 製令: {task['order_no']} \n\n內容: {task['task_content']}")
                
                with tc2.popover("📝 編輯"):
                    try: curr_d = datetime.strptime(task['date'], '%Y-%m-%d')
                    except: curr_d = datetime.now()
                    
                    e_date = st.date_input("修改日期", value=curr_d, key=f"edt_{task['id']}")
                    e_order = st.text_input("修改製令", value=task['order_no'], key=f"eord_{task['id']}")
                    e_task = st.text_area("修改內容", value=task['task_content'], key=f"etxt_{task['id']}")
                    
                    if st.button("💾 儲存修改", key=f"esv_{task['id']}"):
                        conn = get_conn()
                        conn.execute("UPDATE pending_tasks SET date=?, order_no=?, task_content=? WHERE id=?", 
                                     (str(e_date), e_order, e_task, task['id']))
                        conn.commit(); conn.close(); sync_to_github(f"Edit Task - {current_sys_version}"); st.rerun()
                if tc3.button("✅ 完成", key=f"finish_{task['id']}"):
                    now_t = (datetime.utcnow() + timedelta(hours=8)).strftime("%Y-%m-%d %H:%M")
                    conn = get_conn()
                    conn.execute("UPDATE pending_tasks SET status='已完成', complete_date=? WHERE id=?", (now_t, task['id']))
                    conn.commit(); conn.close(); sync_to_github(f"Finish Task - {current_sys_version}"); st.rerun()

        with t5:
            st.write("### 🔴 專案項目管理與結案")
            conn = get_conn()
            active_projs = pd.read_sql("SELECT * FROM projects WHERE is_deleted = 0 ORDER BY id DESC", conn)
            conn.close()
            for _, proj in active_projs.iterrows():
                pc1, pc2, pc3 = st.columns([6, 2, 2])
                status_color = "🟢" if proj['status'] == "已結案" else "🟡"
                pc1.write(f"{status_color} [{proj['date']}] **{proj['project_name']}**\n\n{proj['content']}")
                
                with pc2.popover("📝 編輯"):
                    edit_pname = st.text_input("專案名稱", value=proj['project_name'], key=f"epj_n_{proj['id']}")
                    edit_pcont = st.text_area("專案內容", value=proj['content'], key=f"epj_c_{proj['id']}")
                    edit_pstat = st.selectbox("狀態", ["進行中", "已結案"], index=0 if proj['status']=="進行中" else 1, key=f"epj_s_{proj['id']}")
                    if st.button("💾 儲存專案", key=f"save_pj_{proj['id']}"):
                        conn = get_conn()
                        conn.execute("UPDATE projects SET project_name=?, content=?, status=? WHERE id=?", (edit_pname, edit_pcont, edit_pstat, proj['id']))
                        conn.commit(); conn.close(); sync_to_github(f"Edit Project - {current_sys_version}"); st.rerun()
                        
                if pc3.button("🗑️ 刪除", key=f"del_pj_{proj['id']}"):
                    conn = get_conn(); conn.execute("UPDATE projects SET is_deleted = 1 WHERE id = ?", (proj['id'],)); conn.commit(); conn.close(); sync_to_github(f"Del Project - {current_sys_version}"); st.rerun()

# 4. 專案管理首頁 (完全保留，不被任何異動影響)
elif menu == "🔴 專案管理首頁":
    st.subheader("📋 專案進度追蹤看板")
    
    with st.expander("➕ 發布/新增重大內部專案項目", expanded=False):
        p_name = st.text_input("專案/工程項目名稱")
        p_content = st.text_area("專案詳細內容與目標階段")
        if st.button("🚀 立即成立專案"):
            if p_name and p_content:
                conn = get_conn()
                t_now = (datetime.utcnow() + timedelta(hours=8)).strftime("%Y-%m-%d %H:%M")
                conn.execute("INSERT INTO projects (date, project_name, content, status, is_deleted) VALUES (?, ?, ?, '進行中', 0)", (t_now, p_name, p_content))
                conn.commit(); conn.close()
                sync_to_github(f"New Project Created - {current_sys_version}"); st.success("專案創立成功！"); time.sleep(1.0); st.rerun()
                
    st.markdown("---")
    
    conn = get_conn()
    df_p = pd.read_sql("SELECT * FROM projects WHERE is_deleted = 0 ORDER BY status DESC, id DESC", conn)
    conn.close()
    
    if df_p.empty:
        st.info("目前暫無進行中或列管之專案。")
    else:
        col_p1, col_p2 = st.columns(2)
        with col_p1:
            st.markdown("### 🟡 進行中專案")
            df_ongoing = df_p[df_p['status'] == '進行中']
            if df_ongoing.empty:
                st.caption("暫無進行中專案")
            for _, r in df_ongoing.iterrows():
                with st.container(border=True):
                    st.markdown(f"**📅 成立時間：** {r['date']}")
                    st.markdown(f"**📌 專案名稱：** <span style='color:#D35400; font-size:18px; font-weight:bold;'>{r['project_name']}</span>", unsafe_allow_html=True)
                    st.markdown(f"**📋 內容目標：**\n{r['content']}")
                    
        with col_p2:
            st.markdown("### 🟢 已結案里程碑")
            df_closed = df_p[df_p['status'] == '已結案']
            if df_closed.empty:
                st.caption("暫無已結案專案")
            for _, r in df_closed.iterrows():
                with st.container(border=True):
                    st.markdown(f"**📅 成立時間：** {r['date']}")
                    st.markdown(f"**📌 專案名稱：** <span style='color:#27AE60; font-size:18px; font-weight:bold;'>{r['project_name']}</span>", unsafe_allow_html=True)
                    st.markdown(f"**📋 結案總結：**\n{r['content']}")

# =========================================================
# 🎀 8. 助理績效考核區 (依圖示一整排並排完全版 20260705014)
# =========================================================
elif menu == "🎀 助理績效考核區":
    # 少女風格 CSS 氣氛注入
    st.markdown("""
        <style>
        .stApp {
            background-color: #FFF0F5 !important; /* 夢幻粉白背景 */
        }
        h2, h3 {
            color: #FF69B4 !important; /* 浪漫粉 */
        }
        .pink-header-row {
            background-color: #FFC0CB;
            padding: 10px;
            border-radius: 8px;
            font-weight: bold;
            color: #FF1493;
            text-align: center;
            margin-bottom: 5px;
        }
        .pink-data-row {
            background-color: #FFFFFF;
            border: 1px solid #FFB6C1;
            padding: 12px 10px;
            border-radius: 8px;
            margin-bottom: 5px;
            box-shadow: 0 2px 5px rgba(255,182,193,0.2);
            min-height: 50px;
            display: flex;
            align-items: center;
        }
        .pink-text-cell {
            color: #333333;
            font-size: 14px;
            white-space: pre-wrap; /* 支援完整換行 */
            word-break: break-all;
        }
        </style>
    """, unsafe_allow_html=True)
    
    # 密碼靜態驗證邏輯
    if "assistant_authed" not in st.session_state:
        st.session_state.assistant_authed = False
        
    if not st.session_state.assistant_authed:
        input_pwd = st.text_input("", type="password", placeholder="請驗證權限...", key="assistant_pwd_gate")
        if input_pwd == "0000":
            st.session_state.assistant_authed = True
            st.rerun()
        else:
            if input_pwd: st.error("驗證失敗 🌸")
            st.stop()

    # 讀取現有助理人員名單
    conn = get_conn()
    as_df = pd.read_sql("SELECT name FROM assistant_staff ORDER BY id ASC", conn)
    assistant_list = as_df['name'].tolist()
    conn.close()

    # --- 頂部獨立編輯區 ---
    st.markdown("### ✍ dust 新增助理考核紀錄")
    
    # 建立日期與基本輸入
    col_date, col_name = st.columns([1.5, 2.5])
    with col_date:
        eval_date = st.date_input("🌸 考核日期", value=datetime.today().date())
    with col_name:
        if not assistant_list:
            st.warning("請先於頁面下方建立助理人員名單 🎀")
            sel_assistant = None
        else:
            sel_assistant = st.selectbox("🎀 選擇助理姓名", assistant_list)

    txt_item = st.text_input("📊 考核項目")
    txt_target = st.text_area("🎯 考核指標 (支援換行)")
    txt_content = st.text_area("✨ 考核紀錄 (支援換行)")
    
    if st.button("💝 💝 立即存檔紀錄 💝 💝"):
        if txt_item.strip() and txt_target.strip() and txt_content.strip():
            conn = get_conn()
            
            # 使用當前指定的版本號直接入庫，完美達成今日流水號指定
            serial_no = "20260705014"
            saved_date_str = f"[{serial_no}] {eval_date.strftime('%Y-%m-%d')}"
            
            conn.execute(
                "INSERT INTO assistant_evaluations (eval_date, assistant_name, eval_item, eval_target, eval_content, is_deleted) VALUES (?, ?, ?, ?, ?, 0)",
                (saved_date_str, str(sel_assistant if sel_assistant else ""), txt_item, txt_target, txt_content)
            )
            conn.commit()
            conn.close()
            
            # 同步並刷新
            sync_to_github(f"Add Assistant Evaluation - {serial_no}")
            st.toast("按完成是要顯示在這個介面")
            time.sleep(1.0)
            st.rerun()

    st.markdown("<hr style='border-color: #FFB6C1;'>", unsafe_allow_html=True)
    
    # --- 📜 顯示區 (完美一整排並排，完全對齊圖示) ---
    st.markdown("### 📋 助理紀錄看板")
    
    conn = get_conn()
    eval_df = pd.read_sql("SELECT * FROM assistant_evaluations WHERE is_deleted = 0 ORDER BY id DESC", conn)
    conn.close()
    
    if eval_df.empty:
        st.caption("目前尚無任何考核紀錄 🌸")
    else:
        # 表頭排版一整排完全並排
        h_col1, h_col2, h_col3, h_col4, h_col5, h_col6 = st.columns([2.2, 1.2, 2.0, 3.2, 3.2, 1.2])
        h_col1.markdown("<div class='pink-header-row'>📅 日期/流水號</div>", unsafe_allow_html=True)
        h_col2.markdown("<div class='pink-header-row'>👤 助理姓名</div>", unsafe_allow_html=True)
        h_col3.markdown("<div class='pink-header-row'>📊 考核項目</div>", unsafe_allow_html=True)
        h_col4.markdown("<div class='pink-header-row'>🎯 考核指標</div>", unsafe_allow_html=True)
        h_col5.markdown("<div class='pink-header-row'>✨ 考核紀錄</div>", unsafe_allow_html=True)
        h_col6.markdown("<div class='pink-header-row'>⚙️ 操作</div>", unsafe_allow_html=True)
        
        for _, r in eval_df.iterrows():
            # 內容排版完全並排在一整排上
            d_col1, d_col2, d_col3, d_col4, d_col5, d_col6 = st.columns([2.2, 1.2, 2.0, 3.2, 3.2, 1.2])
            
            d_col1.markdown(f"<div class='pink-data-row'><span class='pink-text-cell'>{r['eval_date']}</span></div>", unsafe_allow_html=True)
            d_col2.markdown(f"<div class='pink-data-row'><span class='pink-text-cell'>{r['assistant_name']}</span></div>", unsafe_allow_html=True)
            d_col3.markdown(f"<div class='pink-data-row'><span class='pink-text-cell'>{r['eval_item']}</span></div>", unsafe_allow_html=True)
            d_col4.markdown(f"<div class='pink-data-row'><span class='pink-text-cell'>{r['eval_target']}</span></div>", unsafe_allow_html=True)
            d_col5.markdown(f"<div class='pink-data-row'><span class='pink-text-cell'>{r['eval_content']}</span></div>", unsafe_allow_html=True)
            
            # 操作按鈕區 (右側並排編輯、刪除按鈕)
            with d_col6:
                st.markdown("<div style='margin-top: 12px;'></div>", unsafe_allow_html=True)
                c_edit, c_del = st.columns([1, 1])
                with c_edit:
                    with st.popover("📝", help="編輯此紀錄"):
                        try:
                            raw_date_part = r['eval_date'].split(" ")[1]
                            curr_eval_date = datetime.strptime(raw_date_part, '%Y-%m-%d').date()
                        except:
                            curr_eval_date = datetime.today().date()
                        
                        edit_date = st.date_input("修改日期", value=curr_eval_date, key=f"ee_date_{r['id']}")
                        edit_item = st.text_input("修改項目", value=r['eval_item'], key=f"ee_item_{r['id']}")
                        edit_target = st.text_area("修改指標", value=r['eval_target'], key=f"ee_target_{r['id']}")
                        edit_content = st.text_area("修改紀錄", value=r['eval_content'], key=f"ee_content_{r['id']}")
                        
                        if st.button("💾 儲存", key=f"save_ee_{r['id']}"):
                            conn = get_conn()
                            # 儲存時版本流水號自動加1更新
                            new_saved_date_str = f"[{current_sys_version}] {edit_date.strftime('%Y-%m-%d')}"
                            
                            conn.execute(
                                "UPDATE assistant_evaluations SET eval_date=?, eval_item=?, eval_target=?, eval_content=? WHERE id=?",
                                (new_saved_date_str, edit_item, edit_target, edit_content, r['id'])
                            )
                            conn.commit()
                            conn.close()
                            sync_to_github(f"Edit Assistant Evaluation - {current_sys_version}")
                            st.rerun()
                with c_del:
                    if st.button("🗑️", key=f"del_ee_{r['id']}", help="刪除此紀錄"):
                        conn = get_conn()
                        conn.execute("UPDATE assistant_evaluations SET is_deleted = 1 WHERE id = ?", (r['id'],))
                        conn.commit()
                        conn.close()
                        sync_to_github(f"Delete Assistant Evaluation - {current_sys_version}")
                        st.rerun()

    # --- 👤 下拉式選單人員後台管理 ---
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown("### ⚙️ 助理名單後台管理")
    
    col_add_input, col_add_btn = st.columns([7, 3])
    with col_add_input:
        new_assistant_name = st.text_input("輸入新助理姓名", placeholder="請輸入欲新增的助理姓名...")
    with col_add_btn:
        st.markdown("<div style='margin-top: 28px;'></div>", unsafe_allow_html=True)
        if st.button("➕ 新增助理人員", use_container_width=True):
            if new_assistant_name.strip():
                conn = get_conn()
                try:
                    conn.execute("INSERT INTO assistant_staff (name) VALUES (?)", (new_assistant_name.strip(),))
                    conn.commit()
                    conn.close()
                    sync_to_github(f"Add Assistant Staff - {current_sys_version}")
                    st.success(f"成功加入：{new_assistant_name} 🌸")
                    time.sleep(1.0)
                    st.rerun()
                except:
                    conn.close()
                    st.error("該助理姓名已存在於清單中")

    if assistant_list:
        st.markdown("#### 📋 目前助理清單")
        conn = get_conn()
        curr_as_df = pd.read_sql("SELECT * FROM assistant_staff ORDER BY id ASC", conn)
        conn.close()
        
        for _, row in curr_as_df.iterrows():
            c_st_name, c_st_del = st.columns([8.5, 1.5])
            c_st_name.write(f"🎀 {row['name']}")
            if c_st_del.button("🗑️ 刪除", key=f"del_as_staff_{row['id']}"):
                conn = get_conn()
                conn.execute("DELETE FROM assistant_staff WHERE id = ?", (row['id'],))
                conn.commit()
                conn.close()
                sync_to_github(f"Remove Assistant Staff - {current_sys_version}")
                st.rerun()
