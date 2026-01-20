import streamlit as st
import pandas as pd
import requests
import uuid
from datetime import datetime

# ==========================================
# 🔧 ส่วนตั้งค่า (วางลิงก์ของคุณที่นี่)
# ==========================================
CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSdAkGWiQR4ybP0nlzrzddrGUHGAEOqn1mMlM6cFGDtbJAySnGvC7pLvxy7Bsszpog1_sunb19l3GfA/pub?output=csv"
WEB_APP_URL = "https://script.google.com/macros/s/AKfycbzbEluMkn-mnr74QYavb5K7AbnvOAy-YkvYrsytsFNfq8bft8ACQnAPWv9akUdkycU/exec"
# ==========================================

st.set_page_config(page_title="Chanon Budget Pro", layout="wide", page_icon="💰")

# --- CSS: ซ่อนปุ่ม +/- และปรับแต่งตาราง ---
st.markdown("""
<style>
    /* ซ่อนปุ่ม +/- ของ Number Input ทุกรูปแบบ */
    button[data-testid="stNumberInputStepDown"],
    button[data-testid="stNumberInputStepUp"] {
        display: none !important;
    }
    div[data-testid="stNumberInput"] input {
        -moz-appearance: textfield;
    }
    div[data-testid="stNumberInput"] input::-webkit-outer-spin-button,
    div[data-testid="stNumberInput"] input::-webkit-inner-spin-button {
        -webkit-appearance: none;
        margin: 0;
    }
    
    /* ปรับแต่งหัวข้อ */
    h3 { color: #2c3e50; }
</style>
""", unsafe_allow_html=True)

# --- ฟังก์ชันจัดการข้อมูล ---
@st.cache_data(ttl=10) # โหลดข้อมูลใหม่ทุก 10 วินาที
def load_data():
    try:
        df = pd.read_csv(CSV_URL)
        expected_cols = ["ID", "Date", "Type", "Category", "Amount", "Note"]
        # ป้องกันกรณี CSV ยังไม่มีข้อมูลหรือหัวตารางผิด
        if df.shape[1] >= 6:
            df.columns = expected_cols
        else:
            return pd.DataFrame(columns=expected_cols)
        
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
        return df
    except:
        return pd.DataFrame(columns=["ID", "Date", "Type", "Category", "Amount", "Note"])

def send_data_to_sheet(payload):
    try:
        response = requests.post(WEB_APP_URL, json=payload)
        return response.status_code == 200
    except:
        return False

# โหลดข้อมูลเข้า Session
if 'df' not in st.session_state or st.sidebar.button("🔄 รีโหลดข้อมูล (แก้ข้อมูลหาย)"):
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
        st.info("กรอกข้อมูลรายการด้านล่าง")
        # เรียงลำดับตามที่ขอ: วันที่ -> ประเภท -> รายการ -> จำนวนเงิน
        entry_date = st.date_input("1. วันที่", datetime.now())
        entry_type = st.radio("2. ประเภท", ["รายรับ", "รายจ่าย"], horizontal=True)
        
        # Dropdown เปลี่ยนตามประเภท
        if entry_type == "รายรับ":
            entry_cat = st.selectbox("3. รายการ", income_cats)
        else:
            entry_cat = st.selectbox("3. รายการ", expense_cats)
        
        # ช่องเงิน (ไม่มีปุ่ม +/- แล้ว)
        entry_amount = st.number_input("4. จำนวนเงิน (บาท)", min_value=0.0, step=None, format="%.2f")
        entry_note = st.text_input("หมายเหตุ (ถ้ามี)")
        
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
                        st.success("บันทึกสำเร็จ!")
                        st.cache_data.clear() # ล้าง Cache เพื่อให้โหลดใหม่
                        st.session_state.df = load_data() # โหลดใหม่ทันที
                        st.rerun()
                    else:
                        st.error("บันทึกไม่สำเร็จ! กรุณาเช็คสิทธิ์ Apps Script (ต้องเป็น Anyone)")
            else:
                st.warning("จำนวนเงินต้องมากกว่า 0")

    st.markdown("---")
    # Dashboard
    if not st.session_state.df.empty:
        valid = st.session_state.df[st.session_state.df['Type'].isin(['รายรับ', 'รายจ่าย'])]
        inc = valid[valid['Type']=="รายรับ"]['Amount'].sum()
        exp = valid[valid['Type']=="รายจ่าย"]['Amount'].sum()
        
        c1, c2, c3 = st.columns(3)
        c1.metric("รายรับ", f"{inc:,.2f}")
        c2.metric("รายจ่าย", f"{exp:,.2f}")
        c3.metric("คงเหลือ", f"{inc-exp:,.2f}")

# ==========================================
# หน้า 2: จัดสรรและโอนงบ (แก้ไขตารางสี)
# ==========================================
elif page == "2. จัดสรรและโอนงบ":
    st.header("🧱 รายละเอียดงบประมาณ (แยกสี)")

    # ส่วนโอนงบ
    with st.expander("💸 เมนูโอนเงิน (Transfer)"):
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
                    st.cache_data.clear()
                    st.session_state.df = load_data()
                    st.rerun()

    st.markdown("---")

    # ส่วนแสดงตารางแยกสี (Logic ใหม่)
    if not st.session_state.df.empty:
        # เตรียมข้อมูล
        sum_pct = sum(budget_rules.values())
        all_rules = budget_rules.copy()
        all_rules["อื่น ๆ"] = 100 - sum_pct
        
        # วนลูปสร้างการ์ดทีละ 2 ใบ เพื่อความสวยงาม
        cols = st.columns(2)
        
        for i, (cat_name, pct) in enumerate(all_rules.items()):
            with cols[i % 2]:
                st.subheader(f"📌 {cat_name} ({pct}%)")
                
                # --- สร้างข้อมูลสำหรับตาราง ---
                table_rows = []
                total_budget_amount = 0
                total_spent_amount = 0
                
                # 1. รายรับ (สีเขียว): วนลูปดูรายรับทุกรายการ แล้วคำนวณ % เข้ากระเป๋านี้
                incomes = st.session_state.df[st.session_state.df['Type'] == "รายรับ"]
                for _, row in incomes.iterrows():
                    allocated = row['Amount'] * (pct / 100)
                    if allocated > 0:
                        table_rows.append({
                            "รายการ": f"จัดสรรจาก {row['Category']}",
                            "จำนวนเงิน": f"+{allocated:,.2f}",
                            "Color": "#d4edda" # สีเขียวอ่อน
                        })
                        total_budget_amount += allocated

                # 2. รายจ่าย (สีแดง): จ่ายออกจากกระเป๋านี้
                expenses = st.session_state.df[
                    (st.session_state.df['Type'] == "รายจ่าย") & 
                    (st.session_state.df['Category'] == cat_name)
                ]
                for _, row in expenses.iterrows():
                    table_rows.append({
                        "รายการ": f"จ่ายค่า {row['Category']}",
                        "จำนวนเงิน": f"-{row['Amount']:,.2f}",
                        "Color": "#f8d7da" # สีแดงอ่อน
                    })
                    total_spent_amount += row['Amount']

                # 3. โอน (ฟ้า/เหลือง)
                transfers = st.session_state.df[st.session_state.df['Type'] == "โอนงบ"]
                for _, row in transfers.iterrows():
                    # โอนเข้า (ฟ้า)
                    if f"To:{cat_name}" in row['Category']:
                        # ดึงชื่อต้นทาง
                        src = row['Category'].split(",")[0].replace("From:", "")
                        table_rows.append({
                            "รายการ": f"รับโอนมาจาก {src}",
                            "จำนวนเงิน": f"+{row['Amount']:,.2f}",
                            "Color": "#cce5ff" # สีฟ้าอ่อน
                        })
                        total_budget_amount += row['Amount']
                    
                    # โอนออก (เหลือง)
                    if f"From:{cat_name}" in row['Category']:
                        # ดึงชื่อปลายทาง
                        dst = row['Category'].split(",")[1].replace("To:", "")
                        table_rows.append({
                            "รายการ": f"โอนไปยัง {dst}",
                            "จำนวนเงิน": f"-{row['Amount']:,.2f}",
                            "Color": "#fff3cd" # สีเหลืองอ่อน
                        })
                        total_budget_amount -= row['Amount']

                # สร้าง DataFrame เพื่อแสดงผล
                if table_rows:
                    df_table = pd.DataFrame(table_rows)
                    
                    # ใช้ Pandas Styler ใส่สีพื้นหลังตามเงื่อนไข
                    def highlight_rows(row):
                        return [f'background-color: {row["Color"]}']*len(row)
                    
                    # ซ่อนคอลัมน์ Color ไม่ให้เห็น แต่เอาไว้ใช้กำหนดสี
                    st.dataframe(
                        df_table.style.apply(highlight_rows, axis=1),
                        column_config={
                            "Color": None # ซ่อนคอลัมน์นี้
                        },
                        hide_index=True,
                        use_container_width=True
                    )
                else:
                    st.caption("ยังไม่มีรายการเคลื่อนไหว")

                # สรุปยอดคงเหลือใต้ตาราง
                remaining = total_budget_amount - total_spent_amount
                if remaining >= 0:
                    st.success(f"💰 คงเหลือ: {remaining:,.2f} บาท")
                else:
                    st.error(f"⚠️ เกินงบ: {remaining:,.2f} บาท")
                
                st.markdown("---")

# ==========================================
# หน้า 3: ประวัติ (คงเดิม)
# ==========================================
elif page == "3. ประวัติและแก้ไขข้อมูล":
    st.header("ประวัติรายการ")
    if not st.session_state.df.empty:
        df_show = st.session_state.df.sort_values(by="Date", ascending=False)
        for _, row in df_show.iterrows():
            with st.expander(f"{row['Date'].strftime('%d/%m')} | {row['Category']} | {row['Amount']:,.2f}"):
                if st.button("ลบรายการ", key=f"del_{row['ID']}"):
                    if send_data_to_sheet({"action": "delete", "id": row['ID']}):
                        st.success("ลบแล้ว")
                        st.cache_data.clear()
                        st.session_state.df = load_data()
                        st.rerun()
