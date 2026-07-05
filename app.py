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
    # 📌 流水碼更新為 20260705013
    st.markdown("<h4 style='color: #F1C40F; margin-bottom: 5px;'>系統版本：20260705013</h4>", unsafe_allow_html=True)
    
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
    
    # 🎀 助理績效考核資料表
    c.execute('''CREATE TABLE IF NOT EXISTS assistant_evaluations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    eval_date TEXT,
                    assistant_name TEXT,
                    eval_item TEXT,
