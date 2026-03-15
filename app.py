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

# --- 🚀 安全讀取金鑰 ---
try:
    MY_TOKEN = st.secrets["MY_TOKEN"] if "MY_TOKEN" in st.secrets else ""
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
                c1, c2, c3 = st.columns([6, 2, 2])
                c1.write(f"[{r['date']}] {r['content'][:20]}...")
                
                # 編輯功能 (彈出式視窗)
                with c2.popover("📝 編輯"):
                    new_content = st.text_area("修改內容", value=r['content'], key=f"edit_txt_{r['id']}")
                    new_file = st.file_uploader("更換照片 (若不更換請留空)", type=['jpg', 'png', 'jpeg'], key=f"edit_img_{r['id']}")
                    if st.button("💾 儲存修改", key=f"save_{r['id']}"):
                        conn = get_conn()
                        final_path = r['image_path']
                        if new_file:
                            final_path = f"{IMAGE_FOLDER}/edit_{datetime.now().strftime('%H%M%S')}_{new_file.name}"
                            with open(final_path, "wb") as f: f.write(new_file.getbuffer())
                        conn.execute("UPDATE posts SET content = ?, image_path = ? WHERE id = ?", (new_content, final_path, r['id']))
                        conn.commit()
                        conn.close()
                        sync_to_github(f"Edit Post {r['id']}")
                        st.success("已更新！")
                        time.sleep(0.5)
                        st.rerun()

                # 刪除功能
                if c3.button("🗑️ 刪除", key=f"d_{r['id']}"):
                    conn = get_conn()
                    conn.execute("UPDATE posts SET is_deleted = 1 WHERE id = ?", (r['id'],))
                    conn.commit()
                    conn.close()
                    sync_to_github(f"Del {r['id']}")
                    st.rerun()
        with t2:
            st.write("### 👥 人員名單")
            conn = get_conn()
            curr = pd.read_sql("SELECT name FROM staff", conn)
            st.table(curr)
            new_n = st.text_input("輸入新人員姓名")
            if st.button("➕ 新增"):
                if new_n:
                    try:
                        conn.execute("INSERT INTO staff (name) VALUES (?)", (new_n,))
                        conn.commit()
                        conn.close()
                        sync_to_github(f"Add {new_n}")
                        st.success(f"已新增：{new_n}")
                        time.sleep(0.5)
                        st.rerun()
                    except: st.error("人員已存在")
                else: st.warning("請輸入姓名")
            else: conn.close()
