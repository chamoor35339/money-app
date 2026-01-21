import streamlit as st
import pandas as pd
import requests
import uuid
from datetime import datetime

# ==========================================
# 🔧 ส่วนตั้งค่า (วางลิงก์ Apps Script ของคุณที่นี่)
# ==========================================
WEB_APP_URL = "https://script.google.com/macros/s/AKfycbzbEluMkn-mnr74QYavb5K7AbnvOAy-YkvYrsytsFNfq8bft8ACQnAPWv9akUdkycU/exec"
# ==========================================

st.set_page_config(page_title="Chanon Budget Pro", layout="wide", page_icon="💰")

# --- CSS: ปรับแต่งความสวยงามและปุ่ม ---
st.markdown("""
<style>
    /* ซ่อนปุ่ม +/- */
    button[data-testid="stNumberInputStepDown"], button[data-testid="stNumberInputStepUp"] {display: none !important;}
    div[data-testid="stNumberInput"] input {-moz-appearance: textfield;}
    
    /* สไตล์ตารางธุรกรรม */
    .trans-table {
        width: 100%; border-collapse: collapse; font-family: 'Sarabun', sans-serif;
        margin-top: 5px; margin-bottom: 20px; border-radius: 8px; overflow: hidden; border: 1px solid #eee;
    }
    .trans-row { border-bottom: 1px solid #eee; }
    .trans-cell { padding: 8px 12px; font-size: 14px; color: #333; }
    .trans-amount { text-align: right; font-weight: bold; white-space: nowrap; }
    
    /* สีพื้นหลังพาสเทล + !important */
    .bg-green { background-color: #d1e7dd !important; color: #0f5132 !important; }   
    .bg-red { background-color: #f8d7da !important; color: #842029 !important; }     
    .bg-blue { background-color: #cff4fc !important; color: #055160 !important; }    
    .bg-yellow { background-color: #fff3cd !important; color: #664d03 !important; }
    
    /* ปรับแต่งปุ่มเลือกหมวดหมู่ (Category Buttons) */
    div.stButton > button {
        width: 100%;
        border-radius: 8px;
        height: 50px;
        font-weight: bold;
        border: 1px solid #ddd;
    }
    /* ไฮไลท์ปุ่มที่ถูกเลือก (ใช้ CSS Hack เล็กน้อย) */
    /* (Streamlit ควบคุมสีปุ่มยาก แต่เราใช้ Logic ใน Python ช่วยแสดงสถานะ) */

</style>
""", unsafe_allow_html=True)

# --- ฟังก์ชันจัดการข้อมูล (เพิ่ม Cache เพื่อความเร็ว) ---
@st.cache_data(ttl=60) # จำข้อมูลไว้ 60 วินาที เพื่อลดการโหลดซ้ำ
def load_data_from_server():
    try:
        response = requests.get(WEB_APP_URL)
        data = response.json()
        df = pd.DataFrame(data)
        
        expected_cols = ["ID", "Date", "Type", "Category", "Amount", "Note"]
        if df.empty: return pd.DataFrame(columns=expected_cols)
            
        for col in expected_cols:
            if col not in df.columns: df[col] = ""

        df = df[expected_cols] 
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce').dt.date
        df = df.dropna(subset=['Date'])
        return df
    except Exception:
        return pd.DataFrame(columns=["ID", "Date", "Type", "Category", "Amount", "Note"])

def send_data_to_sheet(payload):
    try:
        # ส่งข้อมูลแบบไม่รอผลลัพธ์นาน (Fire and Forget style simulation)
        requests.post(WEB_APP_URL, json=payload, timeout=5) 
        return True
    except:
        return False # อาจจะ Time out แต่ข้อมูลมักจะไปถึง

# ระบบโหลดข้อมูลแบบ Hybrid (Local + Server)
if 'df' not in st.session_state:
    st.session_state.df = load_data_from_server()

# ปุ่มรีเฟรชด้วยมือ (Force Refresh)
if st.sidebar.button("🔄 ดึงข้อมูลล่าสุด"):
    st.cache_data.clear()
    st.session_state.df = load_data_from_server()

# --- กฎงบประมาณ ---
budget_rules = {
    "ค่าผ่อนคอนโด": 17.0, "หนี้สหกรณ์": 18.0, "หนี้บัตรเครดิต": 29.0,
    "ค่าน้ำมัน": 7.5, "ค่าไฟ": 5.7, "ค่าโทรศัพท์": 5.0,
    "ค่าใช้จ่ายในครอบครัว": 7.6, "ค่าใช้จ่ายของตนเอง": 9.4, "ค่าน้ำ": 0.38
}
income_cats = ["เงินเดือน", "เงินค่าจ้าง", "เงินค่าเช่า", "เงินปันผล", "อื่น ๆ"]
expense_cats = list(budget_rules.keys()) + ["อื่น ๆ"]

# --- Sidebar ---
st.sidebar.title("💰 เมนูหลัก")
page = st.sidebar.radio("เลือกหน้า", ["1. บันทึกและภาพรวม", "2. จัดสรรและโอนงบ", "3. ประวัติและแก้ไขข้อมูล"])

# ==========================================
# หน้า 1: บันทึกและภาพรวม
# ==========================================
if page == "1. บันทึกและภาพรวม":
    st.header("📝 บันทึกรายการ")
    
    with st.container():
        entry_date = st.date_input("1. วันที่", datetime.now())
        entry_type = st.radio("2. ประเภท", ["รายรับ", "รายจ่าย"], horizontal=True)
        
        if entry_type == "รายรับ": entry_cat = st.selectbox("3. รายการ", income_cats)
        else: entry_cat = st.selectbox("3. รายการ", expense_cats)
        
        entry_amount = st.number_input("4. จำนวนเงิน (บาท)", min_value=0.0, step=None, format="%.2f")
        entry_note = st.text_input("หมายเหตุ")
        
        if st.button("✅ ยืนยันการบันทึก", use_container_width=True, type="primary"):
            if entry_amount > 0:
                new_id = str(uuid.uuid4())
                payload = {
                    "action": "add", "id": new_id,
                    "date": entry_date.strftime("%Y-%m-%d"),
                    "type": entry_type, "category": entry_cat,
                    "amount": entry_amount, "note": entry_note
                }
                
                # เทคนิคความเร็ว: อัปเดตหน้าจอทันที (Optimistic UI)
                new_row = pd.DataFrame([{
                    "ID": new_id, "Date": entry_date, "Type": entry_type, 
                    "Category": entry_cat, "Amount": entry_amount, "Note": entry_note
                }])
                st.session_state.df = pd.concat([st.session_state.df, new_row], ignore_index=True)
                
                # ส่งข้อมูลไปหลังบ้าน (ไม่ต้องรอโหลดใหม่)
                send_data_to_sheet(payload)
                st.success("บันทึกเรียบร้อย!")
                st.rerun() # รีเฟรชหน้าจอทันทีโดยใช้ข้อมูลในเครื่อง
            else:
                st.error("เกิดข้อผิดพลาด")
    
    st.markdown("---")
    if not st.session_state.df.empty:
        valid = st.session_state.df[st.session_state.df['Type'].isin(['รายรับ', 'รายจ่าย'])]
        inc = valid[valid['Type']=="รายรับ"]['Amount'].sum()
        exp = valid[valid['Type']=="รายจ่าย"]['Amount'].sum()
        c1, c2, c3 = st.columns(3)
        c1.metric("รายรับ", f"{inc:,.2f}")
        c2.metric("รายจ่าย", f"{exp:,.2f}")
        c3.metric("คงเหลือ", f"{inc-exp:,.2f}")

# ==========================================
# หน้า 2: จัดสรรและโอนงบ (แก้ไขเป็นปุ่มกด)
# ==========================================
elif page == "2. จัดสรรและโอนงบ":
    st.header("🧱 บริหารงบประมาณ")

    with st.expander("💸 โอนย้ายงบประมาณ (Transfer)"):
        c1, c2 = st.columns(2)
        with c1: from_c = st.selectbox("จาก", expense_cats)
        with c2: to_c = st.selectbox("ไป", expense_cats)
        amt = st.number_input("จำนวนเงิน", min_value=0.0, step=None, format="%.2f")
        if st.button("ยืนยันการโอน"):
            if amt > 0 and from_c != to_c:
                payload = {
                    "action": "add", "id": str(uuid.uuid4()),
                    "date": datetime.now().strftime("%Y-%m-%d"),
                    "type": "โอนงบ", "category": f"From:{from_c},To:{to_c}",
                    "amount": amt, "note": "โอน"
                }
                
                # Optimistic Update
                new_row = pd.DataFrame([{
                    "ID": str(uuid.uuid4()), "Date": datetime.now().date(), "Type": "โอนงบ", 
                    "Category": f"From:{from_c},To:{to_c}", "Amount": amt, "Note": "โอน"
                }])
                st.session_state.df = pd.concat([st.session_state.df, new_row], ignore_index=True)
                
                send_data_to_sheet(payload)
                st.success("โอนสำเร็จ")
                st.rerun()

    st.markdown("---")
    
    if not st.session_state.df.empty:
        sum_pct = sum(budget_rules.values())
        all_rules = budget_rules.copy()
        all_rules["อื่น ๆ"] = 100 - sum_pct
        
        st.subheader("🔍 เลือกรายการเพื่อตรวจสอบสถานะ")
        
        # --- สร้างปุ่มกด (Button Grid) ---
        # เตรียมตัวแปรเก็บค่าที่เลือก (ถ้ายังไม่มีให้เริ่มที่ตัวแรก)
        if 'selected_budget_cat' not in st.session_state:
            st.session_state.selected_budget_cat = list(all_rules.keys())[0]

        # สร้าง Grid 3 คอลัมน์สำหรับปุ่ม
        btn_cols = st.columns(3)
        cats_list = list(all_rules.keys())
        
        for i, cat in enumerate(cats_list):
            # ตรวจสอบว่าปุ่มนี้ถูกเลือกอยู่หรือไม่ เพื่อเปลี่ยนสีปุ่ม
            is_selected = (st.session_state.selected_budget_cat == cat)
            
            # ถ้ากดปุ่ม ให้อัปเดตค่า selected_budget_cat
            if btn_cols[i % 3].button(
                f"{'🔵' if is_selected else '⚪'} {cat}", 
                key=f"btn_{cat}", 
                use_container_width=True,
                type="primary" if is_selected else "secondary"
            ):
                st.session_state.selected_budget_cat = cat
                st.rerun()

        # --- แสดงข้อมูลของรายการที่เลือก ---
        cat_name = st.session_state.selected_budget_cat
        pct = all_rules[cat_name]
        
        st.markdown(f"### 📊 สถานะ: {cat_name} (งบ {pct}%)")
        
        html_rows = ""
        total_budget = 0
        total_spent = 0
        
        for index, row in st.session_state.df.iterrows():
            note_txt = f" ({row['Note']})" if pd.notna(row['Note']) and str(row['Note']).strip() != "" else ""

            # 1. รายรับ
            if row['Type'] == "รายรับ":
                allocated = row['Amount'] * (pct / 100)
                if allocated > 0:
                    total_budget += allocated
                    html_rows += f"<tr class='trans-row bg-green'><td class='trans-cell'>จัดสรรจาก {row['Category']}{note_txt}</td><td class='trans-cell trans-amount'>+{allocated:,.2f}</td></tr>"

            # 2. โอนงบ
            elif row['Type'] == "โอนงบ":
                if f"To:{cat_name}" in row['Category']: # รับโอน
                    src = row['Category'].split(",")[0].replace("From:", "")
                    total_budget += row['Amount']
                    html_rows += f"<tr class='trans-row bg-blue'><td class='trans-cell'>โอนมาจาก {src}{note_txt}</td><td class='trans-cell trans-amount'>+{row['Amount']:,.2f}</td></tr>"
                
                elif f"From:{cat_name}" in row['Category']: # โอนออก
                    dst = row['Category'].split(",")[1].replace("To:", "")
                    total_budget -= row['Amount']
                    html_rows += f"<tr class='trans-row bg-yellow'><td class='trans-cell'>โอนไปยัง {dst}{note_txt}</td><td class='trans-cell trans-amount'>-{row['Amount']:,.2f}</td></tr>"

            # 3. รายจ่าย
            elif row['Type'] == "รายจ่าย" and row['Category'] == cat_name:
                total_spent += row['Amount']
                html_rows += f"<tr class='trans-row bg-red'><td class='trans-cell'>จ่ายค่า {row['Category']}{note_txt}</td><td class='trans-cell trans-amount'>-{row['Amount']:,.2f}</td></tr>"
        
        if html_rows == "":
            html_rows = "<tr><td colspan='2' style='padding:20px; text-align:center; color:#999;'>ยังไม่มีรายการเคลื่อนไหว</td></tr>"

        st.markdown(f"""<table class='trans-table'>{html_rows}</table>""", unsafe_allow_html=True)
        
        remaining = total_budget - total_spent
        c_res1, c_res2 = st.columns(2)
        with c_res1: st.metric("งบสุทธิ", f"{total_budget:,.2f}")
        with c_res2: st.metric("ใช้ไปจริง", f"{total_spent:,.2f}")
            
        if remaining >= 0:
            st.success(f"✅ **คงเหลือ:** {remaining:,.2f} บาท")
        else:
            st.error(f"⚠️ **เกินงบ:** {remaining:,.2f} บาท")
        
        st.markdown("---")

# ==========================================
# หน้า 3: ประวัติ
# ==========================================
elif page == "3. ประวัติและแก้ไขข้อมูล":
    st.header("ประวัติรายการ")
    if not st.session_state.df.empty:
        df_show = st.session_state.df.sort_values(by="Date", ascending=False)
        for _, row in df_show.iterrows():
            
            note_display = f" | 📝 {row['Note']}" if pd.notna(row['Note']) and row['Note'] != "" else ""
            title_text = f"{row['Date']} | {row['Category']} | {row['Amount']:,.2f} บาท{note_display}"
            
            with st.expander(title_text):
                st.write(f"**ประเภท:** {row['Type']}")
                st.write(f"**หมายเหตุ:** {row['Note']}")
                
                if st.button("ลบรายการ", key=f"del_{row['ID']}"):
                    if send_data_to_sheet({"action": "delete", "id": row['ID']}):
                        st.success("ลบแล้ว")
                        st.cache_data.clear() # สั่งเคลียร์ Cache เมื่อมีการลบ
                        st.session_state.df = load_data_from_server()
                        st.rerun()
