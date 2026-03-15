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
    # 一般公告
    c.execute('CREATE TABLE IF NOT EXISTS posts (id INTEGER PRIMARY KEY AUTOINCREMENT, date TEXT, author TEXT, content TEXT, image_path TEXT, is_deleted INTEGER DEFAULT 0)')
    # ⚠️ 品質異常公告表
    c.execute('''CREATE TABLE IF NOT EXISTS quality_posts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, 
                    date TEXT, 
                    order_no TEXT, 
                    content TEXT, 
                    category TEXT, 
                    staff_name TEXT, 
                    image_path TEXT, 
                    is_deleted INTEGER DEFAULT 0)''')
    # 人員名單
    c.execute('CREATE TABLE IF NOT EXISTS staff (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT UNIQUE)')
    c.execute("INSERT OR IGNORE INTO staff (name) VALUES ('賴智文')")
    c.execute("INSERT OR IGNORE INTO staff (name) VALUES ('黃沂澂')")
    conn.commit()
    conn.close()

init_db()

# --- 側邊選單 ---
with st.sidebar:
    st.markdown(f"### 👤 目前登入\n## {st.session_state.get('user', '管理員')}")
    st.markdown("---")
    menu = st.radio("功能選單", [
        "🏠 公佈欄首頁", "✍️ 撰寫新公告", 
        "⚠️ 品質異常公告", "📝 撰寫品質公告",
        "📜 所有紀錄", "⚙️ 管理後台"
    ])

st.title("🏭 <超慧>製造部-雲端公佈欄")

# --- 介面邏輯 ---

# 1. 🏠 公佈欄首頁 (一般公告)
if menu == "🏠 公佈欄首頁":
    st.subheader("📢 一般公告訊息")
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

# 2. ✍️ 撰寫新公告 (一般公告)
elif menu == "✍️ 撰寫新公告":
    st.subheader("📝 發布一般訊息")
    conn = get_conn()
    s_df = pd.read_sql("SELECT name FROM staff", conn)
    conn.close()
    author = st.selectbox("發布人", s_df['name'].tolist())
    msg = st.text_area("公告內容")
    file = st.file_uploader("🖼️ 上傳照片 (選填)", type=['jpg', 'png', 'jpeg'], key="normal_up")
    
    if st.button("🚀 立即發布"):
        if msg:
            p = ""
            if file:
                p = f"{IMAGE_FOLDER}/normal_{datetime.now().strftime('%Y%m%d%H%M%S')}_{file.name}"
                with open(p, "wb") as f: f.write(file.getbuffer())
            conn = get_conn()
            t = (datetime.utcnow() + timedelta(hours=8)).strftime("%Y-%m-%d %H:%M")
            conn.execute("INSERT INTO posts (date, author, content, image_path, is_deleted) VALUES (?, ?, ?, ?, 0)", (t, author, msg, p))
            conn.commit()
            conn.close()
            sync_to_github("New General Post")
            st.balloons()
            st.success("公告發布成功！")
            time.sleep(1.5); st.rerun()
        else: st.warning("請填寫內容")

# 3. ⚠️ 品質異常公告 (展示頁面)
elif menu == "⚠️ 品質異常公告":
    st.subheader("⚠️ 品質異常追蹤")
    conn = get_conn()
    df = pd.read_sql("SELECT * FROM quality_posts WHERE is_deleted = 0 ORDER BY id DESC", conn)
    conn.close()
    
    if df.empty: st.write("目前尚無異常紀錄")
    for _, r in df.iterrows():
        with st.expander(f"🔴 [{r['date']}] 製令：{r['order_no']} | 分類：{r['category']}"):
            c1, c2 = st.columns([7, 3])
            with c1:
                st.write(f"**負責人員：** {r['staff_name']}")
                st.error(f"**異常內容：**\n{r['content']}")
            with c2:
                if r['image_path'] and os.path.exists(r['image_path']):
                    st.image(Image.open(r['image_path']), caption="現場照片", use_container_width=True)
                else:
                    st.write("無照片紀錄")

# 4. 📝 撰寫品質公告 (編輯頁面)
elif menu == "📝 撰寫品質公告":
    st.subheader("✍️ 記錄品質異常")
    col1, col2 = st.columns(2)
    with col1:
        order_no = st.text_input("工單/製令編號")
        q_cat = st.selectbox("異常分類", ["尺寸不符", "外觀瑕疵", "組裝錯誤", "材料問題", "其他"])
    with col2:
        conn = get_conn()
        s_list = pd.read_sql("SELECT name FROM staff", conn)['name'].tolist()
        conn.close()
        q_staff = st.selectbox("相關人員", s_list)
    
    q_content = st.text_area("異常詳細描述")
    q_file = st.file_uploader("🖼️ 異常現場照片 (選填)", type=['jpg', 'png', 'jpeg'], key="quality_up")

    if st.button("🚨 確認提交異常紀錄"):
        if order_no and q_content:
            p = ""
            if q_file:
                p = f"{IMAGE_FOLDER}/quality_{datetime.now().strftime('%Y%m%d%H%M%S')}_{q_file.name}"
                with open(p, "wb") as f: f.write(q_file.getbuffer())
            
            conn = get_conn()
            t = (datetime.utcnow() + timedelta(hours=8)).strftime("%Y-%m-%d %H:%M")
            conn.execute("INSERT INTO quality_posts (date, order_no, content, category, staff_name, image_path, is_deleted) VALUES (?, ?, ?, ?, ?, ?, 0)", 
                         (t, order_no, q_content, q_cat, q_staff, p))
            conn.commit()
            conn.close()
            sync_to_github(f"Quality Alert: {order_no}")
            st.balloons()
            st.success("異常紀錄已存檔！")
            time.sleep(1.5); st.rerun()
        else: st.warning("請填寫製令編號與異常描述。")

# 5. 📜 所有紀錄 (包含一般與品質)
elif menu == "📜 所有紀錄":
    st.subheader("📜 全系統歷史紀錄")
    conn = get_conn()
    st.write("--- 一般公告 ---")
    df1 = pd.read_sql("SELECT date, author, content, CASE WHEN is_deleted=1 THEN '已刪除' ELSE '正常' END as 狀態 FROM posts ORDER BY id DESC", conn)
    st.dataframe(df1, use_container_width=True)
    
    st.write("--- 品質異常 ---")
    df2 = pd.read_sql("SELECT date, order_no as 製令, category as 分類, staff_name as 人員, content as 內容 FROM quality_posts ORDER BY id DESC", conn)
    st.dataframe(df2, use_container_width=True)
    conn.close()

# 6. ⚙️ 管理後台
elif menu == "⚙️ 管理後台":
    st.subheader("🛠️ 管理系統")
    if st.text_input("請輸入管理密碼", type="password") == "0000":
        t1, t2, t3 = st.tabs(["公告管理", "品質紀錄管理", "人員管理"])
        # ... (後續管理邏輯與之前雷同，省略細節以保持簡潔)
