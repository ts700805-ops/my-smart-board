import streamlit as st
import sqlite3
import pandas as pd
import time
import os
import base64
from datetime import datetime, timedelta
from PIL import Image

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
        background-color: #1A2A3A !important;
        height: 4px !important;
    }

    /* 針對所有輸入框、下拉選單、文字區域進行圓角與暖色邊框優化 */
    .stSelectbox, .stTextInput, .stTextArea, .stDateInput {
        border: 1px solid #E6D5B8 !important;
        border-radius: 8px !important;
        background-color: #FFFFFF !important;
    }

    /* 按鈕的高質感漸層：中秋滿月金黃與典雅橘 */
    .stButton>button {
        background: linear_gradient(135deg, #F4C430 0%, #E67E22 100%) !important;
        color: white !important;
        font-weight: bold !important;
        border: none !important;
        border-radius: 20px !important;
        padding: 0.5rem 2rem !important;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1) !important;
        transition: all 0.3s ease !important;
    }

    .stButton>button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 12px rgba(230,126,34,0.3) !important;
    }
    </style>
""", unsafe_allow_html=True)

# =========================================================
# 2. 資料庫初始化 (SQLite)
# =========================================================
def init_db():
    conn = sqlite3.connect("bulletin.db", check_same_thread=False)
    cursor = conn.cursor()
    
    # 建立公告資料表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS system_bulletin (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            publish_date TEXT,
            category TEXT,
            title TEXT,
            content TEXT,
            is_urgent INTEGER DEFAULT 0,
            attachment_path TEXT,
            views INTEGER DEFAULT 0,
            status TEXT DEFAULT '進行中',
            close_reason TEXT
        )
    """)
    
    # 建立簽到歷史紀錄表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sign_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            bulletin_id INTEGER,
            user_name TEXT,
            sign_time TEXT,
            FOREIGN KEY(bulletin_id) REFERENCES system_bulletin(id)
        )
    """)
    
    # 建立人員管理清單
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS staff_list (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE,
            role TEXT,
            status TEXT DEFAULT '在職'
        )
    """)
    
    # 建立品質異常歷史紀錄表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS quality_abnormalities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            report_date TEXT,
            category TEXT,
            item_name TEXT,
            problem_description TEXT,
            photo_path TEXT,
            status TEXT DEFAULT '未解決',
            handler TEXT,
            solution_description TEXT,
            close_date TEXT,
            is_deleted INTEGER DEFAULT 0
        )
    """)
    
    # 建立助理考核紀錄表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS assistant_evaluations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            eval_date TEXT,
            assistant_name TEXT,
            eval_item TEXT,
            eval_target TEXT,
            eval_content TEXT,
            created_at TEXT
        )
    """)
    
    # 預填預設人員
    default_staff = [
        ("張瑞哲", "製程工程師"), ("林俊賢", "製造課長"), ("劉代理", "技術員"),
        ("王小明", "技術員"), ("陳大華", "技術員"), ("五權店", "外部端"),
        ("崇德店", "外部端"), ("中清店", "外部端"), ("西屯店", "外部端"),
        ("南屯店", "外部端"), ("李明輝", "助理"), ("陳美玲", "助理"),
        ("黃淑芬", "助理")
    ]
    for name, role in default_staff:
        try:
            cursor.execute("INSERT OR IGNORE INTO staff_list (name, role, status) VALUES (?, ?, '在職')", (name, role))
        except:
            pass
            
    conn.commit()
    conn.close()

init_db()

def get_conn():
    return sqlite3.connect("bulletin.db", check_same_thread=False)

# =========================================================
# 3. 專案導航與頁面控制
# =========================================================
if "current_page" not in st.session_state:
    st.session_state.current_page = "🔴 專案管理首頁"

# 側邊欄導航 (按鈕樣式)
st.sidebar.markdown("### 🥮 雲端功能導航")

if st.sidebar.button("🔴 專案管理首頁", use_container_width=True):
    st.session_state.current_page = "🔴 專案管理首頁"
if st.sidebar.button("📢 製造部公告大廳", use_container_width=True):
    st.session_state.current_page = "📢 製造部公告大廳"
if st.sidebar.button("🛠️ 公告後台管理系統", use_container_width=True):
    st.session_state.current_page = "🛠️ 公告後台管理系統"
if st.sidebar.button("👥 人員權限名單維護", use_container_width=True):
    st.session_state.current_page = "👥 人員權限名單維護"
if st.sidebar.button("⚠️ 品質異常公告系統", use_container_width=True):
    st.session_state.current_page = "⚠️ 品質異常公告系統"
if st.sidebar.button("🕵️ 品質異常後台管理", use_container_width=True):
    st.session_state.current_page = "🕵️ 品質異常後台管理"
if st.sidebar.button("📊 助理考核紀錄系統", use_container_width=True):
    st.session_state.current_page = "📊 助理考核紀錄系統"

st.sidebar.markdown("---")
st.sidebar.caption("系統版本：20260705017")
st.sidebar.caption("超慧製造部 數位管理小組 榮譽出品")

# 獲取最新的人員名單
conn = get_conn()
staff_df = pd.read_sql_query("SELECT name FROM staff_list WHERE status='在職'", conn)
staff_list = staff_df["name"].tolist()
if not staff_list:
    staff_list = ["暫無在職人員"]
conn.close()

# =========================================================
# 4. 各頁面邏輯實作
# =========================================================

# --- 頁面 1：🔴 專案管理首頁 ---
if st.session_state.current_page == "🔴 專案管理首頁":
    st.markdown("<h1 style='color: #8B4513; text-align: center;'>🔴 超慧製造部-專案管理首頁</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #666;'>歡迎來到超慧製造部雲端核心管理系統。請使用左側導航選單切換功能區塊。</p>", unsafe_allow_html=True)
    
    st.markdown("---")
    
    # 顯示製造部當前最新動態或摘要
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div style='background-color: #FFF; padding: 20px; border-radius: 10px; border-left: 5px solid #F4C430; box-shadow: 0 2px 4px rgba(0,0,0,0.05);'>
            <h4 style='margin-top:0; color: #8B4513;'>📢 最新公告摘要</h4>
            <p style='font-size: 14px; color: #555;'>即時掌握製造部最新方針、排班調整與重大決策宣導。</p>
        </div>
        """, unsafe_allow_html=True)
        
    with col2:
        st.markdown("""
        <div style='background-color: #FFF; padding: 20px; border-radius: 10px; border-left: 5px solid #E67E22; box-shadow: 0 2px 4px rgba(0,0,0,0.05);'>
            <h4 style='margin-top:0; color: #8B4513;'>⚠️ 品質異常追蹤</h4>
            <p style='font-size: 14px; color: #555;'>生產線現場瑕疵、製程異常即時回報與跨部門協調結案進度。</p>
        </div>
        """, unsafe_allow_html=True)
        
    with col3:
        st.markdown("""
        <div style='background-color: #FFF; padding: 20px; border-radius: 10px; border-left: 5px solid #A0522D; box-shadow: 0 2px 4px rgba(0,0,0,0.05);'>
            <h4 style='margin-top:0; color: #8B4513;'>📊 核心績效與考核</h4>
            <p style='font-size: 14px; color: #555;'>全方位記錄行政助理與現場同仁的工作指標、執行進度與定期評語。</p>
        </div>
        """, unsafe_allow_html=True)

# --- 頁面 2：📢 製造部公告大廳 ---
elif st.session_state.current_page == "📢 製造部公告大廳":
    st.markdown("<h1 style='color: #8B4513;'>📢 製造部公告大廳</h1>", unsafe_allow_html=True)
    st.markdown("<p style='color: #666;'>請同仁點擊各項公告進行『讀畢簽到』，以落實資訊傳達率。</p>", unsafe_allow_html=True)
    st.markdown("---")
    
    conn = get_conn()
    # 僅撈取「進行中」的公告
    df_bulletin = pd.read_sql_query("SELECT * FROM system_bulletin WHERE status='進行中' ORDER BY is_urgent DESC, id DESC", conn)
    
    if df_bulletin.empty:
        st.info("✨ 目前暫無進行中的重大公告。")
    else:
        for idx, row in df_bulletin.iterrows():
            urgent_tag = "<span style='background-color: #FF4D4D; color: white; padding: 3px 8px; border-radius: 4px; font-size: 12px; font-weight: bold; margin-right: 8px;'>🚨 重大緊急</span>" if row['is_urgent'] == 1 else ""
            
            st.markdown(f"""
                <div style='background-color: #FFFFFF; padding: 20px; border-radius: 12px; border: 1px solid #E6D5B8; box-shadow: 0 4px 10px rgba(0,0,0,0.03); margin-bottom: 20px;'>
                    <div style='display: flex; justify-content: space-between; align-items: center;'>
                        <h3 style='margin: 0; color: #8B4513;'>{urgent_tag}【{row['category']}】{row['title']}</h3>
                        <span style='color: #999; font-size: 13px;'>📅 發佈日期：{row['publish_date']}</span>
                    </div>
                    <hr style='border-color: #FDFBF0; margin: 12px 0;'>
                    <p style='font-size: 16px; color: #333; white-space: pre-wrap; line-height: 1.6;'>{row['content']}</p>
                </div>
            """, unsafe_allow_html=True)
            
            # 處理附檔下載
            if row['attachment_path'] and os.path.exists(row['attachment_path']):
                with open(row['attachment_path'], "rb") as file:
                    st.download_button(
                        label=f"💾 下載公告相關附件 ({os.path.basename(row['attachment_path'])})",
                        data=file,
                        file_name=os.path.basename(row['attachment_path']),
                        key=f"dl_{row['id']}"
                    )
            
            # 簽到區與已簽到名單並排
            sign_col1, sign_col2 = st.columns([1, 2])
            with sign_col1:
                st.markdown("#### ✍️ 讀畢簽到確認")
                with st.form(key=f"sign_form_{row['id']}", clear_on_submit=False):
                    sel_user = st.selectbox("請選擇您的姓名", staff_list, key=f"user_sel_{row['id']}")
                    submit_sign = st.form_submit_button("🎯 確認已詳閱並簽到")
                    
                    if submit_sign:
                        # 檢查是否重複簽到
                        c = conn.cursor()
                        c.execute("SELECT id FROM sign_logs WHERE bulletin_id=? AND user_name=?", (row['id'], sel_user))
                        if c.fetchone():
                            st.warning(f"⚠️ {sel_user} 同仁，您先前已經完成本篇簽到了喔！")
                        else:
                            now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            c.execute("INSERT INTO sign_logs (bulletin_id, user_name, sign_time) VALUES (?, ?, ?)", 
                                      (row['id'], sel_user, now_str))
                            conn.commit()
                            st.success(f"🎉 {sel_user} 簽到成功！感謝配合。")
                            time.sleep(0.5)
                            st.rerun()
                            
            with sign_col2:
                st.markdown("#### 👥 本篇已簽到同仁")
                df_signs = pd.read_sql_query("SELECT user_name, sign_time FROM sign_logs WHERE bulletin_id=? ORDER BY sign_time DESC", conn, params=(int(row['id']),))
                if df_signs.empty:
                    st.caption("🔍 目前尚無同仁簽到。")
                else:
                    sign_names = df_signs["user_name"].tolist()
                    st.markdown(f"<div style='background-color: #F9F6F0; padding: 10px; border-radius: 8px; border: 1px dashed #E6D5B8; color: #555;'><strong>已閱同仁：</strong> {', '.join(sign_names)}</div>", unsafe_allow_html=True)
                    with st.expander("查看詳細簽到時間"):
                        st.dataframe(df_signs, use_container_width=True)
                        
            st.markdown("<br><hr style='border-color: rgba(139,69,19,0.1);'><br>", unsafe_allow_html=True)
    conn.close()

# --- 頁面 3：🛠️ 公告後台管理系統 ---
elif st.session_state.current_page == "🛠️ 公告後台管理系統":
    st.markdown("<h1 style='color: #8B4513;'>🛠️ 公告後台管理系統</h1>", unsafe_allow_html=True)
    st.markdown("---")
    
    tab1, tab2 = st.tabs(["🆕 發佈全新公告", "🗃️ 歷程公告維護與結案"])
    
    with tab1:
        st.markdown("### 📝 填寫公告內容")
        with st.form("add_bulletin_form", clear_on_submit=True):
            col_b1, col_b2 = st.columns(2)
            with col_b1:
                b_category = st.selectbox("公告分類", ["政策宣導", "排班更動", "製程變更", "活動通知", "其他緊急事宜"])
                b_title = st.text_input("公告標題主題")
            with col_b2:
                b_urgent = st.checkbox("設定為 🚨 重大緊急公告 (將置頂並顯眼標示)")
                b_file = st.file_uploader("上傳附加檔案 (如PDF, Excel, 圖片等)", type=None)
                
            b_content = st.text_area("公告詳細內文 (支持換行輸入)", height=200)
            submit_b = st.form_submit_button("🚀 立即推送公告至大廳")
            
            if submit_b:
                if not b_title.strip() or not b_content.strip():
                    st.error("❌ 標題與內文皆不能為空白！")
                else:
                    saved_path = ""
                    if b_file is not None:
                        os.makedirs("uploaded_attachments", exist_ok=True)
                        saved_path = os.path.join("uploaded_attachments", f"{int(time.time())}_{b_file.name}")
                        with open(saved_path, "wb") as f:
                            f.write(b_file.getbuffer())
                            
                    conn = get_conn()
                    today_str = datetime.now().strftime("%Y-%m-%d")
                    conn.execute("""
                        INSERT INTO system_bulletin (publish_date, category, title, content, is_urgent, attachment_path, status)
                        VALUES (?, ?, ?, ?, ?, ?, '進行中')
                    """, (today_str, b_category, b_title, b_content, 1 if b_urgent else 0, saved_path))
                    conn.commit()
                    conn.close()
                    st.success("🎉 公告已成功發佈，同仁可於公告大廳即時查閱與簽到！")
                    time.sleep(1)
                    st.rerun()
                    
    with tab2:
        st.markdown("### 🗃️ 所有公告清單管理")
        conn = get_conn()
        df_all = pd.read_sql_query("SELECT id, publish_date, category, title, status, close_reason FROM system_bulletin ORDER BY id DESC", conn)
        
        if df_all.empty:
            st.caption("目前無 any 公告紀錄。")
        else:
            st.dataframe(df_all, use_container_width=True)
            
            st.markdown("---")
            st.markdown("### ⚙️ 單筆公告維護作業")
            sel_b_id = st.selectbox("選擇要處理的公告流水號 (ID)", df_all["id"].tolist())
            
            row_data = df_all[df_all["id"] == sel_b_id].iloc[0]
            st.write(f"**當前選擇：** 【{row_data['category']}】{row_data['title']} | **目前狀態：** `{row_data['status']}`")
            
            col_act1, col_act2 = st.columns(2)
            with col_act1:
                if row_data['status'] == '進行中':
                    reason_input = st.text_input("結案原因/備註 (例如：活動已結束、已有新公告代替)", key="reason")
                    if st.button("🔒 執行下架結案", use_container_width=True):
                        conn.execute("UPDATE system_bulletin SET status='已結案', close_reason=? WHERE id=?", (reason_input, int(sel_b_id)))
                        conn.commit()
                        st.success(f"🚫 公告 ID {sel_b_id} 已成功下架結案。")
                        time.sleep(0.5)
                        st.rerun()
                else:
                    if st.button("🔓 重新上架啟用", use_container_width=True):
                        conn.execute("UPDATE system_bulletin SET status='進行中', close_reason=NULL WHERE id=?", (int(sel_b_id),))
                        conn.commit()
                        st.success(f"✅ 公告 ID {sel_b_id} 已重新上架為進行中。")
                        time.sleep(0.5)
                        st.rerun()
                        
            with col_act2:
                if st.button("🗑️ 澈底刪除此公告與簽到紀錄", use_container_width=True):
                    conn.execute("DELETE FROM system_bulletin WHERE id=?", (int(sel_b_id),))
                    conn.execute("DELETE FROM sign_logs WHERE bulletin_id=?", (int(sel_b_id),))
                    conn.commit()
                    st.error(f"💥 公告 ID {sel_b_id} 及其附隨簽到紀錄已全數澈底從系統刪除！")
                    time.sleep(0.5)
                    st.rerun()
        conn.close()

# --- 頁面 4：👥 人員權限名單維護 ---
elif st.session_state.current_page == "👥 人員權限名單維護":
    st.markdown("<h1 style='color: #8B4513;'>👥 人員權限名單維護</h1>", unsafe_allow_html=True)
    st.markdown("---")
    
    p_col1, p_col2 = st.columns([1, 1])
    
    with p_col1:
        st.markdown("### ➕ 新增製造部編制人員")
        with st.form("add_staff_form", clear_on_submit=True):
            new_name = st.text_input("人員姓名 (不可重複)")
            new_role = st.selectbox("人員職稱/角色", ["技術員", "製程工程師", "製造課長", "助理", "外部端", "其他"])
            submit_s = st.form_submit_button("➕ 確認加入名單")
            
            if submit_s:
                if not new_name.strip():
                    st.error("❌ 姓名不能空白！")
                else:
                    conn = get_conn()
                    try:
                        conn.execute("INSERT INTO staff_list (name, role, status) VALUES (?, ?, '在職')", (new_name.strip(), new_role))
                        conn.commit()
                        st.success(f"🎉 {new_name} 成功加入製造部在職名單！")
                        time.sleep(0.5)
                        st.rerun()
                    except sqlite3.IntegrityError:
                        st.error("⚠️ 該人員姓名已經存在於名單系統中，無法重複新增！")
                    finally:
                        conn.close()
                        
    with p_col2:
        st.markdown("### 📋 當前在職人員名單")
        conn = get_conn()
        df_staff_show = pd.read_sql_query("SELECT id, name, role, status FROM staff_list WHERE status='在職' ORDER BY id DESC", conn)
        st.dataframe(df_staff_show, use_container_width=True)
        
        st.markdown("---")
        st.markdown("### 離職/除名人員變更作業")
        if not df_staff_show.empty:
            del_name = st.selectbox("選擇要辦理離職除名的人員", df_staff_show["name"].tolist())
            if st.button("🏃 設定該人員為離職狀態", use_container_width=True):
                conn.execute("UPDATE staff_list SET status='離職' WHERE name=?", (del_name,))
                conn.commit()
                st.warning(f"💼 {del_name} 已設定為離職，系統簽到與下拉選單已同步將其除名。")
                time.sleep(0.5)
                st.rerun()
        conn.close()

# --- 頁面 5：⚠️ 品質異常公告系統 ---
elif st.session_state.current_page == "⚠️ 品質異常公告系統":
    st.markdown("<h1 style='color: #8B4513;'>⚠️ 品質異常公告系統</h1>", unsafe_allow_html=True)
    st.markdown("<p style='color: #666;'>此處供現場同仁即時登錄生產中發現的各項品質異常瑕疵，以便即時追蹤處理。</p>", unsafe_allow_html=True)
    st.markdown("---")
    
    # 填寫異常表單
    st.markdown("### 📝 填報新製程品質異常")
    with st.form("add_quality_form", clear_on_submit=True):
        qa_col1, qa_col2 = st.columns(2)
        with qa_col1:
            qa_category = st.selectbox("異常分類", ["零件異常", "外觀異常", "組裝問題", "流程問題", "其他"])
            qa_item = st.text_input("異常品項/機種名稱", placeholder="例如：A01面板、B款上蓋、機座組件")
        with qa_col2:
            qa_photo = st.file_uploader("📸 上傳現場異常照片 (選填)", type=["png", "jpg", "jpeg"])
            
        qa_desc = st.text_area("❌ 異常狀況詳細描述", placeholder="請具體寫出瑕疵點（例如：表面嚴重刮傷超過5cm、孔位偏移無法鎖附...）")
        
        submit_qa = st.form_submit_button("🚨 立即發佈異常通報")
        
        if submit_qa:
            if not qa_item.strip() or not qa_desc.strip():
                st.error("❌ 異常品項與描述內容為必填，不可留空！")
            else:
                saved_img_path = ""
                if qa_photo is not None:
                    os.makedirs("uploaded_qa_photos", exist_ok=True)
                    saved_img_path = os.path.join("uploaded_qa_photos", f"qa_{int(time.time())}_{qa_photo.name}")
                    with open(saved_img_path, "wb") as f:
                        f.write(qa_photo.getbuffer())
                        
                conn = get_conn()
                today_str = datetime.now().strftime("%Y-%m-%d")
                conn.execute("""
                    INSERT INTO quality_abnormalities (report_date, category, item_name, problem_description, photo_path, status)
                    VALUES (?, ?, ?, ?, ?, '未解決')
                """, (today_str, qa_category, qa_item, qa_desc, saved_img_path))
                conn.commit()
                conn.close()
                st.success("🎯 品質異常通報成功！後台管理系統已同步列入追蹤項目。")
                time.sleep(0.5)
                st.rerun()

    st.markdown("---")
    st.markdown("### 🔍 當前異常通報看板 (進行中與已解決)")
    
    conn = get_conn()
    df_qa_board = pd.read_sql_query("SELECT * FROM quality_abnormalities WHERE is_deleted=0 ORDER BY id DESC", conn)
    conn.close()
    
    if df_qa_board.empty:
        st.info("✨ 太棒了！目前沒有任何懸而未決的品質異常紀錄。")
    else:
        for idx, row in df_qa_board.iterrows():
            status_color = "#FF4D4D" if row['status'] == '未解決' else "#2ECC71"
            status_tag = f"<span style='background-color: {status_color}; color: white; padding: 3px 8px; border-radius: 4px; font-size: 13px; font-weight: bold;'>{row['status']}</span>"
            
            st.markdown(f"""
                <div style='background-color: #FFFFFF; padding: 20px; border-radius: 12px; border: 1px solid #E6D5B8; box-shadow: 0 4px 10px rgba(0,0,0,0.03); margin-bottom: 20px;'>
                    <div style='display: flex; justify-content: space-between; align-items: center;'>
                        <h4 style='margin: 0; color: #8B4513;'>流水號 #{row['id']} 【{row['category']}】 - {row['item_name']}</h4>
                        <div>
                            {status_tag}
                            <span style='color: #999; font-size: 13px; margin-left: 15px;'>📅 通報日期：{row['report_date']}</span>
                        </div>
                    </div>
                    <hr style='border-color: #FDFBF0; margin: 12px 0;'>
                    <p style='font-size: 15px; color: #333;'><strong>❌ 異常描述：</strong><br>{row['problem_description']}</p>
            """, unsafe_allow_html=True)
            
            if row['photo_path'] and os.path.exists(row['photo_path']):
                try:
                    img = Image.open(row['photo_path'])
                    st.image(img, caption="現場回傳異常照片", width=350)
                except Exception as e:
                    st.caption("📷 圖片載入失敗")
                    
            if row['status'] == '已解決':
                st.markdown(f"""
                    <div style='background-color: #F0FBF5; padding: 12px; border-radius: 6px; border-left: 4px solid #2ECC71; margin-top: 10px;'>
                        <p style='margin: 0; font-size: 14px; color: #27AE60;'><strong>✅ 解決對策：</strong> {row['solution_description']}</p>
                        <p style='margin: 3px 0 0 0; font-size: 13px; color: #7F8C8D;'><strong>🔧 經手負責人：</strong> {row['handler']} | <strong>🏁 結案日期：</strong> {row['close_date']}</p>
                    </div>
                """, unsafe_allow_html=True)
                
            st.markdown("</div>", unsafe_allow_html=True)

# --- 頁面 6：🕵️ 品質異常後台管理 ---
elif st.session_state.current_page == "🕵️ 品質異常後台管理":
    st.markdown("<h1 style='color: #8B4513;'>🕵️ 品質異常後台管理</h1>", unsafe_allow_html=True)
    st.markdown("---")
    
    conn = get_conn()
    show_deleted = st.checkbox("🔍 顯示包含刪除的所有紀錄(歷史紀錄找回模式)", value=False)
    
    if show_deleted:
        df_m_qa = pd.read_sql_query("SELECT id, report_date, category, item_name, status, handler, is_deleted FROM quality_abnormalities ORDER BY id DESC", conn)
    else:
        df_m_qa = pd.read_sql_query("SELECT id, report_date, category, item_name, status, handler, is_deleted FROM quality_abnormalities WHERE is_deleted=0 ORDER BY id DESC", conn)
        
    st.markdown("### 📋 系統內品質異常總清單")
    st.dataframe(df_m_qa, use_container_width=True)
    
    if not df_m_qa.empty:
        st.markdown("---")
        st.markdown("### 🛠️ 處置與維護特定流水號項目")
        sel_qa_id = st.selectbox("請選擇欲處理的異常 ID", df_m_qa["id"].tolist())
        
        c = conn.cursor()
        c.execute("SELECT * FROM quality_abnormalities WHERE id=?", (int(sel_qa_id),))
        curr_row = c.fetchone()
        
        if curr_row:
            st.write(f"**目前處置對象：** ID #{curr_row[0]} | 品項：`{curr_row[3]}` | 狀態：`{curr_row[6]}` | 刪除狀態：`{'已刪除' if curr_row[10]==1 else '正常'}`")
            
            if curr_row[10] == 1:
                if st.button("🔄 找回此被刪除的紀錄", use_container_width=True):
                    conn.execute("UPDATE quality_abnormalities SET is_deleted=0 WHERE id=?", (int(sel_qa_id),))
                    conn.commit()
                    st.success(f"🎉 成功找回 ID #{sel_qa_id} 異常紀錄！")
                    time.sleep(0.5)
                    st.rerun()
            else:
                if curr_row[6] == '未解決':
                    st.markdown("#### 🟢 填寫處置結案對策")
                    with st.form(f"solve_form_{sel_qa_id}", clear_on_submit=False):
                        sol_handler = st.selectbox("指定結案負責人", staff_list)
                        sol_desc = st.text_area("輸入解決對策與根本原因分析", placeholder="例如：已更換全新零組件、調整製程參數、並於今日覆驗合格。")
                        submit_sol = st.form_submit_button("🏁 提交處置並完工結案")
                        
                        if submit_sol:
                            if not sol_desc.strip():
                                st.error("❌ 必須輸入解決對策描述才能結案！")
                            else:
                                today_str = datetime.now().strftime("%Y-%m-%d")
                                conn.execute("""
                                    UPDATE quality_abnormalities 
                                    SET status='已解決', handler=?, solution_description=?, close_date=?
                                    WHERE id=?
                                """, (sol_handler, sol_desc.strip(), today_str, int(sel_qa_id)))
                                conn.commit()
                                st.success(f"✅ ID #{sel_qa_id} 異常品項已成功處置結案！")
                                time.sleep(0.5)
                                st.rerun()
                else:
                    st.success("🌟 本項目已是結案完成狀態。")
                    
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("🗑️ 刪除此異常紀錄(轉入歷史紀錄庫)", use_container_width=True):
                    conn.execute("UPDATE quality_abnormalities SET is_deleted=1 WHERE id=?", (int(sel_qa_id),))
                    conn.commit()
                    st.warning(f"🚨 ID #{sel_qa_id} 紀錄已自看板移除，可開啟下方找回模式查看。")
                    time.sleep(0.5)
                    st.rerun()
    conn.close()

# --- 頁面 7：📊 助理考核紀錄系統 ---
elif st.session_state.current_page == "📊 助理考核紀錄系統":
    st.markdown("<h1 style='color: #8B4513;'>📊 助理考核紀錄系統</h1>", unsafe_allow_html=True)
    st.markdown("<p style='color: #666;'>專用於記錄、追蹤製造部行政與現線助理的每日考核項目、達成指標以及實際表現紀錄。</p>", unsafe_allow_html=True)
    st.markdown("---")
    
    conn = get_conn()
    df_evals = pd.read_sql_query("SELECT id, eval_date, assistant_name, eval_item, eval_target, eval_content FROM assistant_evaluations ORDER BY id DESC", conn)
    conn.close()
    
    st.markdown("### 📋 歷史考核追蹤清單")
    if df_evals.empty:
        st.info("💡 目前系統中尚無助理考核紀錄，請於下方表單建立第一筆資料。")
    else:
        for idx, row in df_evals.iterrows():
            with st.container():
                st.markdown(f"""
                    <div style='background-color: #FFFFFF; padding: 18px; border-radius: 10px; border: 1px solid #F0E6D2; box-shadow: 0 2px 5px rgba(0,0,0,0.02); margin-bottom: 15px;'>
                        <div style='display: flex; justify-content: space-between; align-items: center;'>
                            <span style='font-size: 16px; font-weight: bold; color: #D2691E;'>🎀 助理姓名：{row['assistant_name']}</span>
                            <span style='font-size: 13px; color: #999;'>📅 考核日期：{row['eval_date']}</span>
                        </div>
                        <div style='margin-top: 8px; font-size: 14px; color: #333;'>
                            <strong>📊 考核項目：</strong> {row['eval_item']}
                        </div>
                        <div style='margin-top: 4px; font-size: 14px; color: #555;'>
                            <strong>🎯 考核指標：</strong> {row['eval_target']}
                        </div>
                        <div style='margin-top: 4px; font-size: 14px; color: #444; background-color: #FFFDF9; padding: 8px; border-radius: 4px; border-left: 3px solid #F4C430;'>
                            <strong>✨ 考核紀錄與評語：</strong><br>{row['eval_content']}
                        </div>
                """, unsafe_allow_html=True)
                
                del_eva_col1, del_eva_col2 = st.columns([5, 1])
                with del_eva_col2:
                    if st.button("🗑️ 刪除", key=f"del_eva_{row['id']}", use_container_width=True):
                        conn = get_conn()
                        conn.execute("DELETE FROM assistant_evaluations WHERE id=?", (int(row['id']),))
                        conn.commit()
                        conn.close()
                        st.error(f"已刪除該筆考核紀錄")
                        time.sleep(0.5)
                        st.rerun()
                        
                st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown("---")
    
    # --- 新增考核表單區 ---
    st.markdown("### ✍️ 新增助理考核紀錄")
    with st.form("assistant_add_form", clear_on_submit=True):
        # 🟢 排成一整排顯示
        row_col1, row_col2, row_col3, row_col4 = st.columns([1.5, 2, 2.5, 4])
        
        with row_col1:
            sel_assistant = st.selectbox("🎀 選擇助理姓名", staff_list)
        with row_col2:
            txt_item = st.text_area("📊 考核項目", placeholder="考核主題...", height=68)
        with row_col3:
            txt_target = st.text_area("🎯 考核指標", placeholder="達成指標或要求準則...", height=68)
        with row_col4:
            txt_content = st.text_area("✨ 考核紀錄", placeholder="實際進度、表現狀況與評語...", height=68)
        
        if st.form_submit_button("💝 💝 立即存檔紀錄 💝 💝"):
            if txt_item.strip() and txt_target.strip() and txt_content.strip():
                conn = get_conn()
                conn.execute("INSERT INTO assistant_evaluations (eval_date, assistant_name, eval_item, eval_target, eval_content, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                             (datetime.now().strftime("%Y-%m-%d"), sel_assistant, txt_item.strip(), txt_target.strip(), txt_content.strip(), datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
                conn.commit()
                conn.close()
                st.success(f"🎉 成功存檔 {sel_assistant} 的考核紀錄！")
                time.sleep(0.5)
                st.rerun()
            else:
                st.error("❌ 請完整填寫項目、指標與考核紀錄內容，不可留空！")
