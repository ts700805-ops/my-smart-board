import streamlit as st
import sqlite3
import pandas as pd
import time
import os
from git import Repo
from datetime import datetime, timedelta
from PIL import Image

# 1. 網頁基本設定 (標題已修改為製造部)
st.set_page_config(page_title="超慧製造部-雲端公佈欄", page_icon="🏭", layout="wide")

# --- 🚀 安全修改：讀取雲端金鑰 ---
try:
    if "MY_TOKEN" in st.secrets:
        MY_TOKEN = st.secrets["MY_TOKEN"]
    else:
        st.error("❌ 找不到雲端金鑰！請在 Streamlit Settings > Secrets 設定 MY_TOKEN。")
        MY_TOKEN = ""
except Exception as e:
    st.error(f"讀取金鑰失敗: {e}")
    MY_TOKEN = ""

GITHUB_REPO = f"https://{MY_TOKEN}@github.com/ts700805-ops/my-smart-board.git"
IMAGE_FOLDER = "images"

if not os.path.exists(IMAGE_FOLDER):
    os.makedirs(IMAGE_FOLDER)

# --- 標準同步功能 ---
def sync_to_github(commit_msg="Update"):
    if not MY_TOKEN:
        return
    try:
        os.environ["GIT_ASKPASS"] = "echo"
        os.environ["GIT_TERMINAL_PROMPT"] = "0"
        repo = Repo(".")
        if 'origin' in repo.remotes:
            repo.delete_remote('origin')
        origin = repo.create_remote('origin', GITHUB_REPO)
        repo.git.add("--all") 
        tw_now = (datetime.utcnow() + timedelta(hours=8)).strftime('%m/%d %H:%M')
        repo.index.commit(f"{commit_msg} - {tw_now}")
        origin.push(refspec='main:main', force=True)
        st.toast("✅ GitHub 同步備份成功")
    except:
        pass # 靜默處理同步問題，避免干擾網頁顯示

# --- 資料庫工具 ---
def get_db_conn():
    return sqlite3.connect('bulletin.db', check_same_thread=False)

def init_db():
    conn = get_db_conn()
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS posts 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  date TEXT, author TEXT, content TEXT, 
                  image_path TEXT, is_deleted INTEGER DEFAULT 0)''')
    c.execute('''CREATE TABLE IF NOT EXISTS staff 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT UNIQUE)''')
    c.execute("INSERT OR IGNORE INTO staff (name) VALUES ('賴智文')")
    c.execute("INSERT OR IGNORE INTO staff (name) VALUES ('黃沂澂')")
    conn.commit()
    conn.close()

init_db()

# --- 側邊選單 ---
with st.sidebar:
    st.markdown("### 👤 目前狀態\n## 管理模式")
    st.markdown("---")
    menu = st.radio("功能選單", ["🏠 公佈欄首頁", "✍️ 撰寫新公告", "📜 所有公佈歷史紀錄", "⚙️ 管理後台"])

st.title("🏭 <超慧>製造部-雲端公佈欄")

# --- 介面邏輯 ---
if menu == "🏠 公佈欄首頁":
    try:
        conn = get_db_conn()
        df = pd.read_sql("SELECT * FROM posts WHERE is_deleted = 0 ORDER BY id DESC", conn)
        conn.close()
        if df.empty:
            st.write("目前尚無公告")
        for _, row in df.iterrows():
            with st.container():
                st.markdown(f"**{row['date']} | 發布人：{row['author']}**")
                st.info(row['content'])
                if row['image_path'] and os.path.exists(row['image_path']):
                    with st.popover("🖼️ 檢視照片"):
                        st.image(Image.open(row['image_path']), use_container_width=True)
                st.markdown("---")
    except:
        st.write("資料載入中...")

elif menu == "✍️ 撰寫新公告":
    st.subheader("📝 發布新訊息")
    conn = get_db_conn()
    staff_df = pd.read_sql("SELECT name FROM staff", conn)
    conn.close()
    author_list = staff_df['name'].tolist()
    
    author = st.selectbox("發布人", author_list)
    msg = st.text_area("公告內容", placeholder="請輸入內容...")
    file = st.file_uploader("🖼️ 上傳照片 (必填)", type=['jpg', 'png', 'jpeg'])
    
    if st.button("🚀 立即發布"):
        if msg and file:
            img_p = f"{IMAGE_FOLDER}/{datetime.now().strftime('%Y%m%d%H%M%S')}_{file.name}"
            with open(img_p, "wb") as f:
                f.write(file.getbuffer())
            conn = get_db_conn()
            tw_time = (datetime.utcnow() + timedelta(hours=8)).strftime("%Y-%m-%d %H:%M")
            conn.execute("INSERT INTO posts (date, author, content, image_path, is_deleted) VALUES (?, ?, ?, ?, 0)", 
                         (tw_time, author, msg, img_p))
            conn.commit()
            conn.close()
            sync_to_github(f"Post by {author}")
            st.success("發布成功！")
            time.sleep(1)
            st.rerun()
        else:
            st.warning("請填寫內容並上傳照片。")

elif menu == "📜 所有公佈歷史紀錄":
    st.subheader("📅 歷史公告查詢")
    conn = get_db_conn()
    df = pd.read_sql("SELECT date, author, content FROM posts WHERE is_deleted = 0 ORDER BY id DESC", conn)
    conn.close()
    st.dataframe(df, use_container_width=True)

elif menu == "⚙️ 管理後台":
    st.subheader("🛠️ 管理系統")
    pwd = st.text_input("請輸入管理密碼", type="password")
    
    if pwd == "0000":
        tab1, tab2 = st.tabs(["公告管理", "人員管理"])
        with tab1:
            conn = get_db_conn()
            df = pd.read_sql("SELECT * FROM posts WHERE is_deleted = 0 ORDER BY id DESC", conn)
            conn.close()
            for _, row in df.iterrows():
                col1, col2 = st.columns([8, 2])
                col1.write(f"[{row['date']}] {row['content'][:30]}...")
                if col2.button("🗑️
