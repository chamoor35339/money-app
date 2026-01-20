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

# --- CSS: ปรับแต่งความสวยงาม ---
st.markdown("""
<style>
    /* ซ่อนปุ่ม +/- */
    button[data-testid="stNumberInputStepDown"], button[data-testid="stNumberInputStepUp"] {display: none !important;}
    div[data-testid="stNumberInput"] input {-moz-appearance: textfield;}
    
    /* สไตล์ตารางธุรกรรม (Transaction Table) */
    .trans-table {
        width: 100%;
        border-collapse: collapse;
        font-family: 'Sarabun', sans-serif;
        margin-top: 5px;
        margin-bottom: 20px;
        border-radius: 8px;
        overflow: hidden;
        border: 1px solid #eee;
    }
    .trans-row {
        border-bottom: 1px solid #eee;
    }
    .trans-cell {
        padding: 10px 15px;
        font-size: 14px;
        color: #333;
    }
    .trans-amount {
        text-align: right;
        font-weight: bold;
    }
    /* สีพื้นหลังพาสเทล (อ่านง่าย) */
    .bg-green { background-color: #d1e7dd !important; color: #0f5132 !important; }   /* รายรับ */
    .bg-red { background-color: #f8d7da !important; color: #842029 !important; }     /* รายจ่าย */
    .bg-blue { background-color: #cff4fc !important; color: #055160 !important; }    /* โอนเข้า */
    .bg-yellow { background-color: #fff3cd !important; color: #664d03 !important; }  /* โอนออก */
    
</style>
""", unsafe_allow_html=True)

# --- ฟังก์ชันจัดการข้อมูล (Real-time) ---
def load_data():
    try:
        response = requests.get(WEB_APP_URL)
        data = response.json()
        df = pd.DataFrame(data)
        
        expected_cols = ["ID", "Date", "Type", "Category", "Amount", "Note"]
        if df.empty:
            return pd.DataFrame(columns=expected_cols)
            
        # เช็คคอลัมน์และแปลงวันที่
        # ถ้าคอลัมน์ขาดเกิน ให้เติมให้ครบป้องกัน Error
        for col in expected_cols:
            if col not in df.columns:
                df[col] = ""

        df = df[expected_cols] 
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce').dt.date
        
        # กรองแถวที่วันที่เป็น NaT (เผื่อมีขยะ)
        df = df.dropna(subset=['Date'])
        return df
    except Exception as e:
        return pd.DataFrame(columns=["ID", "Date", "Type", "Category", "Amount", "Note"])

def send_data_to_sheet(payload):
    try:
        requests.post(WEB_APP_URL, json=payload)
        return True
    except:
        return False

# โหลดข้อมูล
if 'df' not in st.session_state or st.sidebar.button("🔄 ดึงข้อมูลล่าสุด"):
    st.session_state.df = load_data()

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
        
        if st.button("✅ ยืนยันการบันทึก", use_container_width=True):
            if entry_amount > 0:
                new_id = str(uuid.uuid4())
                payload = {
                    "action": "add", "id": new_id,
                    "date": entry_date.strftime("%Y-%m-%d"),
                    "type": entry_type, "category": entry_cat,
                    "amount": entry_amount, "note": entry_note
                }
                with st.spinner('กำลังบันทึก...'):
                    if send_data_to_sheet(payload):
                        st.success("บันทึกเรียบร้อย!")
                        st.session_state.df = load_data()
                        st.rerun()
                    else:
                        st.error("เกิดข้อผิดพลาดในการเชื่อมต่อ")
    
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
# หน้า 2: จัดสรรและโอนงบ (แก้ไข HTML Indentation)
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
                if send_data_to_sheet(payload):
                    st.success("โอนสำเร็จ")
                    st.session_state.df = load_data()
                    st.rerun()

    st.markdown("---")
    
    # --- แสดงตารางแบบใหม่ (HTML Table Corrected) ---
    if not st.session_state.df.empty:
        sum_pct = sum(budget_rules.values())
        all_rules = budget_rules.copy()
        all_rules["อื่น ๆ"] = 100 - sum_pct
        
        cols = st.columns(2)
        
        for i, (cat_name, pct) in enumerate(all_rules.items()):
            with cols[i % 2]:
                st.subheader(f"📌 {cat_name} ({pct}%)")
                
                html_rows = ""
                total_budget = 0
                total_spent = 0
                
                # 1. รายรับ (สีเขียว)
                incomes = st.session_state.df[st.session_state.df['Type'] == "รายรับ"]
                for _, row in incomes.iterrows():
                    allocated = row['Amount'] * (pct / 100)
                    if allocated > 0:
                        total_budget += allocated
                        # เขียน HTML บรรทัดเดียวติดกันเพื่อป้องกัน Markdown แปลงเป็น Code
                        html_rows += f"<tr class='trans-row bg-green'><td class='trans-cell'>จัดสรรจาก {row['Category']}</td><td class='trans-cell trans-amount'>+{allocated:,.2f}</td></tr>"

                # 2. โอน (ฟ้า/เหลือง)
                transfers = st.session_state.df[st.session_state.df['Type'] == "โอนงบ"]
                for _, row in transfers.iterrows():
                    if f"To:{cat_name}" in row['Category']: 
                        src = row['Category'].split(",")[0].replace("From:", "")
                        total_budget += row['Amount']
                        html_rows += f"<tr class='trans-row bg-blue'><td class='trans-cell'>โอนมาจาก {src}</td><td class='trans-cell trans-amount'>+{row['Amount']:,.2f}</td></tr>"
                    
                    if f"From:{cat_name}" in row['Category']: 
                        dst = row['Category'].split(",")[1].replace("To:", "")
                        total_budget -= row['Amount']
                        html_rows += f"<tr class='trans-row bg-yellow'><td class='trans-cell'>โอนไปยัง {dst}</td><td class='trans-cell trans-amount'>-{row['Amount']:,.2f}</td></tr>"

                # 3. รายจ่าย (สีแดง)
                expenses = st.session_state.df[(st.session_state.df['Type'] == "รายจ่าย") & (st.session_state.df['Category'] == cat_name)]
                for _, row in expenses.iterrows():
                    total_spent += row['Amount']
                    html_rows += f"<tr class='trans-row bg-red'><td class='trans-cell'>จ่ายค่า {row['Category']}</td><td class='trans-cell trans-amount'>-{row['Amount']:,.2f}</td></tr>"
                
                if html_rows == "":
                    html_rows = "<tr><td colspan='2' style='padding:10px; text-align:center; color:#999;'>ยังไม่มีรายการ</td></tr>"

                # แสดงตาราง (ชิดซ้ายไม่มีย่อหน้า)
                st.markdown(f"""<table class='trans-table'>{html_rows}</table>""", unsafe_allow_html=True)
                
                # สรุปยอด
                remaining = total_budget - total_spent
                if remaining >= 0:
                    st.success(f"คงเหลือ: {remaining:,.2f}")
                else:
                    st.error(f"เกินงบ: {remaining:,.2f}")
                
                st.markdown("---")

# ==========================================
# หน้า 3: ประวัติ
# ==========================================
elif page == "3. ประวัติและแก้ไขข้อมูล":
    st.header("ประวัติรายการ")
    if not st.session_state.df.empty:
        df_show = st.session_state.df.sort_values(by="Date", ascending=False)
        for _, row in df_show.iterrows():
            with st.expander(f"{row['Date']} | {row['Category']} | {row['Amount']:,.2f}"):
                if st.button("ลบรายการ", key=f"del_{row['ID']}"):
                    if send_data_to_sheet({"action": "delete", "id": row['ID']}):
                        st.success("ลบแล้ว")
                        st.session_state.df = load_data()
                        st.rerun()
