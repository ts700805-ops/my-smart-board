import streamlit as st
import sqlite3
import pandas as pd
import time
import os
from git import Repo
from datetime import datetime, timedelta
from PIL import Image

# 1. 網頁基本設定
st.set_page_config(page_title="超慧製造部-雲端公佈欄", page_icon="🏭", layout="wide")

# --- 🚀 雲端保險箱模式：從 Streamlit Secrets 讀取金鑰 ---
try:
    if "MY_TOKEN" in st.secrets:
        MY_TOKEN = st.secrets["MY_TOKEN"]
    else:
        st.error("❌ 找不到金鑰！請至 Streamlit Settings > Secrets 設定 MY_TOKEN")
        MY_TOKEN = ""
except Exception:
    MY_TOKEN = ""

GITHUB_REPO = f"https://{MY_TOKEN}@github.com/ts700805-ops/my-smart-board.git"
IMAGE_FOLDER = "images"

if not os.path.exists(IMAGE_FOLDER):
    os.makedirs(IMAGE_FOLDER)

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
        st.toast("✅ GitHub 同步成功")
    except: pass

# --- 資料庫工具 ---
def get_conn():
    return sqlite3.connect('bulletin.db', check_same_thread=False)

def init_db():
    conn = get_conn()
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS posts (id INTEGER PRIMARY KEY AUTOINCREMENT, date TEXT, author TEXT, content TEXT, image_path TEXT, is_deleted INTEGER DEFAULT 0)')
    c.execute('CREATE TABLE IF NOT EXISTS staff (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT UNIQUE)')
    c.execute("INSERT OR IGNORE INTO staff (name) VALUES ('賴智文')")
    c.execute("INSERT OR IGNORE INTO staff (name) VALUES ('黃沂澂')")
    conn.commit()
    conn.close()

init_db()

# --- 側邊選單 ---
with st.sidebar:
    st.markdown("### 👤 目前狀態\n## 管理員")
    st.markdown("---")
    menu = st.radio("功能選單", ["🏠 公佈欄首頁", "✍️ 撰寫新公告", "📜 所有紀錄", "⚙️ 管理後台"])

st.title("🏭 <超慧>製造部-雲端公佈欄")

# --- 介面邏輯 ---
if menu == "🏠 公佈欄首頁":
    try:
        conn = get_conn()
        df = pd.read_sql("SELECT * FROM posts WHERE is_deleted = 0 ORDER BY id DESC", conn)
        conn.close()
        if df.empty: st.write("目前尚無公告")
        for _, r in df.iterrows():
            with st.container():
                st.markdown(f"**{r['date']} | 發布人：{r['author']}**")
                st.info(r['content'])
                if r['image_path'] and os.path.exists(r['image_path']):
                    with st.popover("🖼️ 檢視照片"):
                        st.image(Image.open(r['image_path']), use_container_width=True)
                st.markdown("---")
    except: st.write("載入中...")

elif menu == "✍️ 撰寫新公告":
    st.subheader("📝 發布新訊息")
    conn = get_conn()
    s_df = pd.read_sql("SELECT name FROM staff", conn)
    conn.close()
    author = st.selectbox("發布人", s_df['name'].tolist())
    msg = st.text_area("公告內容")
    file = st.file_uploader("🖼️ 上傳照片", type=['jpg', 'png', 'jpeg'])
    if st.button("🚀 立即發布"):
        if msg and file:
            p = f"{IMAGE_FOLDER}/{datetime.now().strftime('%Y%m%d%H%M%S')}_{file.name}"
            with open(p, "wb") as f: f.write(file.getbuffer())
            conn = get_conn()
            t = (datetime.utcnow() + timedelta(hours=8)).strftime("%Y-%m-%d %H:%M")
            conn.execute("INSERT INTO posts (date, author, content, image_path, is_deleted) VALUES (?, ?, ?, ?, 0)", (t, author, msg, p))
            conn.commit()
            conn.close()
            sync_to_github(f"Post by {author}")
            st.success("發布成功！")
            time.sleep(1)
            st.rerun()
        else: st.warning("請填寫內容並上傳。")

elif menu == "📜 所有紀錄":
    conn = get_conn()
    df = pd.read_sql("SELECT date, author, content FROM posts WHERE is_deleted = 0 ORDER BY id DESC", conn)
    conn.close()
    st.dataframe(df, use_container_width=True)

elif menu == "⚙️ 管理後台":
    st.subheader("🛠️ 管理系統")
    if st.text_input("請輸入管理密碼", type="password") == "0000":
        t1, t2 = st.tabs(["公告管理", "人員管理"])
        with t1:
            conn = get_conn()
            df = pd.read_sql("SELECT * FROM posts WHERE is_deleted = 0 ORDER BY id DESC", conn)
            conn.close()
            for _, r in df.iterrows():
                c1, c2 = st.columns([8, 2])
                c1.write(f"[{r['date']}] {r['content'][:20]}...")
                if c2.button("🗑️", key=f"d_{r['id']}"):
                    conn = get_conn()
                    conn.execute("UPDATE posts SET is_deleted = 1 WHERE id = ?", (r['id'],))
                    conn.commit()
                    conn.close()
                    sync_to_github(f"Del {r['id']}")
                    st.rerun()
        with t2:
            st.write("### 👥 人員名單管理")
            conn = get_conn()
            curr_staff = pd.read_sql("SELECT name FROM staff", conn)
            st.table(curr_staff)
            
            new_n = st.text_input("輸入新人員姓名", key="add_staff_input")
            if st.button("➕ 確認新增"):
                if new_n:
                    try:
                        conn.execute("INSERT INTO staff (name) VALUES (?)", (new_n,))
                        conn.commit()
                        conn.close()
                        sync_to_github(f"Add {new_n}")
                        st.success(f"✅ 已成功新增：{new_n}")
                        time.sleep(0.5)
                        st.rerun() # 立即更新螢幕
                    except:
                        st.error("❌ 人員已存在於名單中")
                        conn.close()
                else: st.warning("請輸入姓名")
            else: conn.close()
