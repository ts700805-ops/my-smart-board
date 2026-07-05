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

# =========================================================
# 🏠 側邊欄配置：中秋佳節新氣象
# =========================================================
with st.sidebar:
    # 📌 流水碼更新為 20260705025
    st.markdown("<h4 style='color: #F1C40F; margin-bottom: 5px;'>系統版本：20260705025</h4>", unsafe_allow_html=True)
    
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
    
    # 🎀 助理績效考核資料表 (結構升級：包含考核指標與考核紀錄)
    c.execute('''CREATE TABLE IF NOT EXISTS assistant_evaluations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    eval_date TEXT,
                    assistant_name TEXT,
                    eval_item TEXT,
                    eval_target TEXT DEFAULT '',
                    eval_content TEXT DEFAULT '',
                    is_deleted INTEGER DEFAULT 0)''')
    
    # 檢查並補齊可能遺漏的欄位
    try:
        c.execute("ALTER TABLE assistant_evaluations ADD COLUMN eval_target TEXT DEFAULT ''")
    except: pass
    conn.commit()
    conn.close()

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
            "🛠️ 製造部待處理清單",
            "🔴 專案管理首頁",
            "🎀 助理績效考核區",
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
            sync_to_github("New Post - 20260705013"); st.balloons(); st.success("發布成功！"); time.sleep(1.5);
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
            sync_to_github("New Quality Alert - 20260705013"); st.balloons(); st.success("紀錄已存檔！"); time.sleep(1.5);
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
    conn.close()

# 7. 管理後台
elif menu == "⚙️ 管理後台":
    st.subheader("🛠️ 管理系統")
    if st.text_input("請輸入管理密碼", type="password") == "0000":
        t1, t2, t3, t4 = st.tabs(["公告管理", "品質紀錄管理", "人員管理", "待處理事項管理"])
     
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
                        sync_to_github("Edit Post - 20260705013"); st.rerun()
                if c3.button("🗑️ 刪除", key=f"dp_{r['id']}"):
                    conn = get_conn(); conn.execute("UPDATE posts SET is_deleted = 1 WHERE id = ?", (r['id'],)); conn.commit(); conn.close(); sync_to_github("Del Post - 20260705013"); st.rerun()

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
                        conn.commit(); conn.close(); sync_to_github("Edit Quality - 20260705013"); st.rerun()
                if qc3.button("🗑️ 刪除", key=f"dq_{r['id']}"):
                    conn = get_conn(); conn.execute("UPDATE quality_posts SET is_deleted = 1 WHERE id = ?", (r['id'],)); conn.commit(); conn.close(); sync_to_github("Del Quality - 20260705013"); st.rerun()

        with t3:
            st.write("### 👥 人員名單管理")
            new_n = st.text_input("輸入新人員姓名")
            if st.button("➕ 新增人員"):
                if new_n:
                    conn = get_conn()
                    try:
                        conn.execute("INSERT INTO staff (name) VALUES (?)", (new_n,))
                        conn.commit(); conn.close(); sync_to_github(f"Add {new_n} - 20260705013"); st.rerun()
                    except: conn.close(); st.error("人員已存在")
            st.markdown("---")
            conn = get_conn()
            curr_df = pd.read_sql("SELECT * FROM staff", conn)
            conn.close()
            for _, row in curr_df.iterrows():
                col1, col2 = st.columns([8, 2])
                col1.write(f"👤 {row['name']}")
                if col2.button("🗑️ 刪除人員", key=f"ds_{row['id']}"):
                    conn = get_conn(); conn.execute("DELETE FROM staff WHERE id = ?", (row['id'],)); conn.commit(); conn.close(); sync_to_github("Remove Staff - 20260705013"); st.rerun()

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
                        conn.commit(); conn.close(); sync_to_github("Add Task - 20260705013"); st.rerun()

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
                        conn.commit(); conn.close(); sync_to_github("Edit Task - 20260705013"); st.rerun()

                if tc3.button("✅ 完成", key=f"finish_{task['id']}"):
                    now_t = (datetime.utcnow() + timedelta(hours=8)).strftime("%Y-%m-%d %H:%M")
                    conn = get_conn()
                    conn.execute("UPDATE pending_tasks SET status='已完成', complete_date=? WHERE id=?", (now_t, task['id']))
                    conn.commit(); conn.close(); sync_to_github("Finish Task - 20260705013"); st.rerun()

# --- 🔴 專案管理首頁 (獨立功能活頁) ---
if menu == "🔴 專案管理首頁":
    st.subheader("📋 專案進度追蹤看板")
    
    if "project_font_scale" not in st.session_state:
        st.session_state.project_font_scale = 130
        
    st.session_state.project_font_scale = st.slider(
        "🔍 現場看板字體大小微調 (%)", 
        min_value=100, 
        max_value=200, 
        value=st.session_state.project_font_scale, 
        step=10,
        key="project_font_slider"
    )
    
    p_font_scale = st.session_state.project_font_scale
    
    st.markdown(f"""
        <style>
        div[data-testid="stNotification"] *, 
        div[data-testid="stNotificationContent"], 
        div[data-testid="stNotificationContent"] p, 
        div[data-testid="stNotificationContent"] span {{
            font-size: {int(16 * (p_font_scale / 100))}px !important;
            line-height: 1.6 !important;
        }}
        </style>
    """, unsafe_allow_html=True)
    
    db_conn = sqlite3.connect('bulletin.db')
    try:
        db_conn.execute('''CREATE TABLE IF NOT EXISTS project_tasks (
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
        
        db_conn.execute('''CREATE TABLE IF NOT EXISTS project_settings (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        config_key TEXT UNIQUE,
                        config_value TEXT)''')
        db_conn.commit()
        
        cursor = db_conn.cursor()
        cursor.execute("PRAGMA table_info(project_tasks)")
        columns = [row[1] for row in cursor.fetchall()]
        
        if "task_content" not in columns:
            db_conn.execute("ALTER TABLE project_tasks ADD COLUMN task_content TEXT DEFAULT ''")
            db_conn.commit()
    finally:
        db_conn.close()

    db_conn = sqlite3.connect('bulletin.db')
    try:
        c = db_conn.cursor()
        c.execute("SELECT config_value FROM project_settings WHERE config_key = 'team_mapping'")
        row_mapping = c.fetchone()
    finally:
        db_conn.close()
    
    mapping_text = row_mapping[0] if row_mapping else "組長A:成員1,成員2\n組長B:成員3,成員4"
    
    author_options = []  
    worker_options = []  
    
    for line in mapping_text.split("\n"):
        if ":" in line:
            leader, members = line.split(":", 1)
            leader = leader.strip()
            if leader and leader not in author_options:
                author_options.append(leader)
            if leader not in worker_options:
                worker_options.append(leader)
            
            for m in members.split(","):
                m = m.strip()
                if m and m not in worker_options:
                    worker_options.append(m)
                    
    if not author_options: author_options = ["請先到下方設定對照表"]
    if not worker_options: worker_options = ["請先到下方設定對照表"]

    st.markdown("### 🟡 進行中專案清單")
    
    db_conn = sqlite3.connect('bulletin.db')
    try:
        df_active = pd.read_sql("SELECT * FROM project_tasks WHERE is_finished = 0 AND is_deleted = 0 ORDER BY id DESC", db_conn)
    finally:
        db_conn.close()
    
    if df_active.empty:
        st.info("目前沒有進行中的專案任務。")
    else:
        for _, row in df_active.iterrows():
            m1, m2, m3, m4 = st.columns([5, 1.5, 1.5, 1.5])
            
            task_desc = row['task_content'] if ('task_content' in row and row['task_content']) else "未填寫執行內容"
            m1.info(f"**製令：** {row['order_no']} | **指派日：** {row['assign_date']} | **發布：** {row['author_name']} | **執行：** {row['worker_name']} | **預計完工：** {row['expected_date']}\n\n**📝 執行內容：** {task_desc}")
            
            if m2.button("🟢 點我完工", key=f"f_btn_{row['id']}"):
                f_time = (datetime.utcnow() + timedelta(hours=8)).strftime("%Y-%m-%d %H:%M")
                db_conn = sqlite3.connect('bulletin.db')
                try:
                    db_conn.execute("UPDATE project_tasks SET is_finished = 1, finish_date = ? WHERE id = ?", (f_time, row['id']))
                    db_conn.commit()
                finally:
                    db_conn.close()
                sync_to_github("Finish Project Task - 20260705013"); st.rerun()
                
            with m3.popover("📝 編輯"):
                pwd_edit = st.text_input("驗證管理密碼", type="password", key=f"pwd_e_{row['id']}")
                if pwd_edit == "0000":
                    e_order = st.text_input("修改製令", value=row['order_no'], key=f"eo_{row['id']}")
                    
                    try: def_auth_idx = author_options.index(row['author_name'])
                    except: def_auth_idx = 0
                    try: def_work_idx = worker_options.index(row['worker_name'])
                    except: def_work_idx = 0
                    
                    e_author = st.selectbox("修改發布人", author_options, index=def_auth_idx, key=f"ea_{row['id']}")
                    e_worker = st.selectbox("修改執行人", worker_options, index=def_work_idx, key=f"ew_{row['id']}")
                    e_exp = st.date_input("修改預計完工日", value=datetime.strptime(row['expected_date'], "%Y-%m-%d"), key=f"ex_{row['id']}")
                    
                    curr_content = row['task_content'] if ('task_content' in row and row['task_content']) else ""
                    e_content = st.text_area("修改執行內容", value=curr_content, key=f"ec_{row['id']}")
                    
                    if st.button("💾 儲存修改", key=f"save_e_{row['id']}"):
                        db_conn = sqlite3.connect('bulletin.db')
                        try:
                            db_conn.execute("UPDATE project_tasks SET order_no=?, author_name=?, worker_name=?, expected_date=?, task_content=? WHERE id=?", 
                                         (e_order, e_author, e_worker, str(e_exp), e_content, row['id']))
                            db_conn.commit()
                        finally:
                            db_conn.close()
                        sync_to_github("Edit Project Task - 20260705013"); st.rerun()
                elif pwd_edit:
                    st.error("密碼錯誤")

            with m4.popover("🗑️ 刪除"):
                pwd_del = st.text_input("驗證管理密碼", type="password", key=f"pwd_d_{row['id']}")
                if pwd_del == "0000":
                    if st.button("🚨 確定刪除", key=f"d_btn_{row['id']}"):
                        db_conn = sqlite3.connect('bulletin.db')
                        try:
                            db_conn.execute("UPDATE project_tasks SET is_deleted = 1 WHERE id = ?", (row['id'],))
                            db_conn.commit()
                        finally:
                            db_conn.close()
                        sync_to_github("Delete Project Task - 20260705013"); st.rerun()
                elif pwd_del:
                    st.error("密碼錯誤")

    # =========================================================
    # 完整保留：🟢 已完工歷史專案清單顯示於頁面下方
    # =========================================================
    st.markdown("---")
    st.markdown("### 🟢 已完工歷史專案清單")
    
    db_conn = sqlite3.connect('bulletin.db')
    try:
        db_finished = pd.read_sql("SELECT * FROM project_tasks WHERE is_finished = 1 AND is_deleted = 0 ORDER BY finish_date DESC", db_conn)
    finally:
        db_conn.close()
        
    if db_finished.empty:
        st.caption("目前尚無已完工的歷史專案。")
    else:
        for _, row in db_finished.iterrows():
            with st.container(border=True):
                task_desc = row['task_content'] if ('task_content' in row and row['task_content']) else "無執行內容"
                st.markdown(f"✅ **製令：** {row['order_no']} ｜ **指派：** {row['author_name']} ｜ **執行：** {row['worker_name']}")
                st.markdown(f"📅 **指派日期：** {row['assign_date']} ｜ **預計完工：** {row['expected_date']} ｜ 🏁 **實際完工時間：** `{row['finish_date']}`")
                st.markdown(f"📝 **完整執行內容：**\n{task_desc}")

if menu == "🎀 助理績效考核區":
    # 密碼保護
    if 'eval_auth' not in st.session_state: st.session_state.eval_auth = False
    if not st.session_state.eval_auth:
        pwd = st.text_input("🔑 請輸入密碼 (0000)", type="password")
        if pwd == "0000": st.session_state.eval_auth = True; st.rerun()
        st.stop()

    st.subheader("🎀 助理績效考核管理系統")
    
    # 字體大小設定 (僅作用於本頁)
    font_size = st.slider("調整顯示文字大小", 16, 28, 20)
    st.markdown(f"<style>.custom-text {{ font-size: {font_size}px !important; font-weight: bold !important; }}</style>", unsafe_allow_html=True)

    # 讀取資料
    conn = get_conn()
    eval_df = pd.read_sql("SELECT * FROM assistant_evaluations WHERE is_deleted = 0 ORDER BY eval_date DESC", conn)
    # 讀取「本頁專用」助理名單
    staff_df = pd.read_sql("SELECT name FROM staff", conn) 
    staff_list = staff_df['name'].tolist()
    conn.close()

    # 1. 績效考核紀錄總覽
    st.markdown("### 📜 績效考核紀錄總覽")
    for _, row in eval_df.iterrows():
        st.markdown("---")
        # [日期] [姓名] [項目] [指標] [紀錄] [編輯/刪除]
        c1, c2, c3, c4, c5, c6 = st.columns([1, 1, 1.5, 1.5, 1.5, 1])
        c1.markdown(f"<div class='custom-text'>{row['eval_date']}</div>", unsafe_allow_html=True)
        c2.markdown(f"<div class='custom-text'>{row['assistant_name']}</div>", unsafe_allow_html=True)
        c3.markdown(f"<div class='custom-text'>{row['eval_item']}</div>", unsafe_allow_html=True)
        c4.markdown(f"<div class='custom-text'>{row['eval_target']}</div>", unsafe_allow_html=True)
        c5.markdown(f"<div class='custom-text'>{row['eval_content']}</div>", unsafe_allow_html=True)
        
        # 編輯與刪除在最右側
        with c6:
            if st.button("✏️", key=f"edit_{row['id']}"): st.session_state[f"edit_mode_{row['id']}"] = True
            if st.button("🗑️", key=f"del_{row['id']}"):
                conn = get_conn()
                conn.execute("UPDATE assistant_evaluations SET is_deleted = 1 WHERE id = ?", (row['id'],))
                conn.commit()
                conn.close()
                st.rerun()
            
            # 編輯介面
            if st.session_state.get(f"edit_mode_{row['id']}"):
                with st.form(f"f_{row['id']}"):
                    n_item = st.text_area("項目", row['eval_item'])
                    n_target = st.text_area("指標", row['eval_target'])
                    n_content = st.text_area("紀錄", row['eval_content'])
                    if st.form_submit_button("儲存"):
                        conn = get_conn()
                        conn.execute("UPDATE assistant_evaluations SET eval_item=?, eval_target=?, eval_content=? WHERE id=?", (n_item, n_target, n_content, row['id']))
                        conn.commit()
                        conn.close()
                        st.session_state[f"edit_mode_{row['id']}"] = False
                        st.rerun()

    # 2. 新增考核區 (包含本頁助理姓名下拉選單)
    st.markdown("---")
    st.markdown("### ✍️ 新增績效考核紀錄")
    with st.form("add_form", clear_on_submit=True):
        sel_assistant = st.selectbox("🎀 選擇助理姓名", staff_list if staff_list else ["請先至下方新增名單"])
        c1, c2, c3 = st.columns(3)
        txt_item = c1.text_area("📊 考核項目")
        txt_target = c2.text_area("🎯 考核指標")
        txt_content = c3.text_area("✨ 考核紀錄")
        if st.form_submit_button("💝 立即存檔紀錄"):
            conn = get_conn()
            conn.execute("INSERT INTO assistant_evaluations (eval_date, assistant_name, eval_item, eval_target, eval_content) VALUES (?, ?, ?, ?, ?)",
                         (datetime.today().strftime('%Y-%m-%d'), sel_assistant, txt_item, txt_target, txt_content))
            conn.commit()
            conn.close()
            st.rerun()

    # 3. 獨立助理名單維護
    st.markdown("---")
    st.markdown("### ⚙️ 助理名單維護 (本頁專用)")
    new_staff = st.text_input("輸入新助理姓名")
    if st.button("➕ 加入名單"):
        conn = get_conn()
        conn.execute("INSERT INTO staff (name) VALUES (?)", (new_staff,))
        conn.commit()
        conn.close()
        st.rerun()
