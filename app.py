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

# --- CSS ปรับแต่ง (ซ่อนปุ่ม +/- และปรับสี) ---
st.markdown("""
<style>
    /* ซ่อนปุ่ม +/- ในช่องกรอกตัวเลข */
    button[title="Increment"] {display: none;}
    button[title="Decrement"] {display: none;}
    input[type=number] {-moz-appearance: textfield;}
    
    /* ปรับแต่งการ์ดแสดงผล */
    .stMetric {
        background-color: #f8f9fa;
        border: 1px solid #e9ecef;
        padding: 10px;
        border-radius: 8px;
        color: #333;
    }
    
    /* ปรับสีปุ่มบันทึก */
    div.stButton > button:first-child {
        background-color: #4CAF50;
        color: white;
        border-radius: 8px;
        height: 50px;
        width: 100%;
        font-size: 18px;
    }
</style>
""", unsafe_allow_html=True)

# --- ฟังก์ชันจัดการข้อมูล ---
def load_data():
    try:
        df = pd.read_csv(CSV_URL)
        expected_cols = ["ID", "Date", "Type", "Category", "Amount", "Note"]
        if len(df.columns) >= 6:
            df.columns = expected_cols
        df['Date'] = pd.to_datetime(df['Date'])
        return df
    except:
        return pd.DataFrame(columns=["ID", "Date", "Type", "Category", "Amount", "Note"])

def send_data_to_sheet(payload):
    try:
        response = requests.post(WEB_APP_URL, json=payload)
        return response.status_code == 200
    except:
        return False

# โหลดข้อมูล (ใช้ session state เพื่อให้ข้อมูลไม่หายเวลากดปุ่ม)
if 'df' not in st.session_state:
    st.session_state.df = load_data()

# --- กฎงบประมาณ ---
budget_rules = {
    "ค่าผ่อนคอนโด": 17.0, "หนี้สหกรณ์": 18.0, "หนี้บัตรเครดิต": 29.0,
    "ค่าน้ำมัน": 7.5, "ค่าไฟ": 5.7, "ค่าโทรศัพท์": 5.0,
    "ค่าใช้จ่ายในครอบครัว": 7.6, "ค่าใช้จ่ายของตนเอง": 9.4, "ค่าน้ำ": 0.38
}

# รายการ Dropdown
income_cats = ["เงินเดือน", "เงินค่าจ้าง", "เงินค่าเช่า", "เงินปันผล", "อื่น ๆ"]
expense_cats = list(budget_rules.keys()) + ["อื่น ๆ"]

# --- Sidebar ---
st.sidebar.title("💰 เมนูหลัก")
page = st.sidebar.radio("เลือกหน้า", ["1. บันทึกและภาพรวม", "2. จัดสรรและโอนงบ", "3. ประวัติและแก้ไขข้อมูล"])

if st.sidebar.button("🔄 รีโหลดข้อมูลล่าสุด"):
    st.cache_data.clear()
    st.session_state.df = load_data()
    st.rerun()

# ==========================================
# หน้า 1: บันทึกและภาพรวม
# ==========================================
if page == "1. บันทึกและภาพรวม":
    st.header("📝 บันทึกรายการ (กรอกง่าย)")
    
    # ส่วนกรอกข้อมูล (เอา st.form ออก เพื่อให้ Dropdown เปลี่ยนตาม Type ทันที)
    # ใช้ Container เพื่อจัดกลุ่ม
    with st.container():
        st.info("กรุณากรอกข้อมูลตามลำดับ")
        
        # 1. วันที่
        entry_date = st.date_input("1. วันที่", datetime.now())
        
        # 2. ประเภท
        entry_type = st.radio("2. ประเภท", ["รายรับ", "รายจ่าย"], horizontal=True)
        
        # 3. รายการ (เปลี่ยนตามประเภทอัตโนมัติ)
        if entry_type == "รายรับ":
            entry_cat = st.selectbox("3. รายการ", income_cats)
        else:
            entry_cat = st.selectbox("3. รายการ", expense_cats)
        
        # 4. จำนวนเงิน (step=0 ทำให้ไม่มีปุ่ม +/-)
        entry_amount = st.number_input("4. จำนวนเงิน (บาท)", min_value=0.0, step=0.0, format="%.2f")
        
        entry_note = st.text_input("หมายเหตุ (ถ้ามี)")
        
        # ปุ่มบันทึกขนาดใหญ่
        if st.button("✅ ยืนยันการบันทึก"):
            if entry_amount > 0:
                new_id = str(uuid.uuid4())
                payload = {
                    "action": "add",
                    "id": new_id,
                    "date": entry_date.strftime("%Y-%m-%d"),
                    "type": entry_type,
                    "category": entry_cat,
                    "amount": entry_amount,
                    "note": entry_note
                }
                
                # แสดงสถานะกำลังบันทึก
                with st.spinner('กำลังส่งข้อมูลไป Google Sheets...'):
                    if send_data_to_sheet(payload):
                        st.success("บันทึกสำเร็จ!")
                        # อัปเดตข้อมูลในแอปทันที
                        new_row = pd.DataFrame([[new_id, pd.to_datetime(entry_date), entry_type, entry_cat, entry_amount, entry_note]], 
                                             columns=["ID", "Date", "Type", "Category", "Amount", "Note"])
                        st.session_state.df = pd.concat([st.session_state.df, new_row], ignore_index=True)
                        st.rerun()
                    else:
                        st.error("เกิดข้อผิดพลาด! กรุณาตรวจสอบลิงก์ Web App URL หรือสิทธิ์การเข้าถึง (Anyone)")
            else:
                st.warning("กรุณากรอกจำนวนเงินมากกว่า 0")

    st.markdown("---")
    
    # Dashboard (ปรับสีให้ชัดเจน)
    st.subheader("📊 สรุปภาพรวม")
    if not st.session_state.df.empty:
        valid_df = st.session_state.df[st.session_state.df['Type'].isin(['รายรับ', 'รายจ่าย'])]
        inc = valid_df[valid_df['Type'] == "รายรับ"]['Amount'].sum()
        exp = valid_df[valid_df['Type'] == "รายจ่าย"]['Amount'].sum()
        bal = inc - exp
        
        c1, c2, c3 = st.columns(3)
        with c1:
            st.info(f"💰 รายรับรวม\n# {inc:,.2f} บาท")
        with c2:
            st.warning(f"💸 รายจ่ายรวม\n# {exp:,.2f} บาท")
        with c3:
            if bal >= 0:
                st.success(f"✅ คงเหลือสุทธิ\n# {bal:,.2f} บาท")
            else:
                st.error(f"⚠️ ติดลบ\n# {bal:,.2f} บาท")

# ==========================================
# หน้า 2: จัดสรรและโอนงบ
# ==========================================
elif page == "2. จัดสรรและโอนงบ":
    st.header("🧱 กระเป๋าเงินและการจัดสรร")
    
    # ส่วนโอนงบ (ปรับ Input ให้กรอกง่าย)
    with st.expander("💸 **เมนูโอนย้ายงบประมาณ (Transfer)**", expanded=True):
        col_t1, col_t2 = st.columns(2)
        with col_t1: from_cat = st.selectbox("ต้นทาง (ดึงเงินออก)", expense_cats)
        with col_t2: to_cat = st.selectbox("ปลายทาง (ใส่เงินเข้า)", expense_cats)
        
        # Input แบบไม่มีปุ่ม +/-
        trans_amount = st.number_input("จำนวนเงินที่ต้องการโอน", min_value=0.0, step=0.0, format="%.2f")
        
        if st.button("ยืนยันการโอนย้าย"):
            if trans_amount > 0 and from_cat != to_cat:
                new_id = str(uuid.uuid4())
                cat_str = f"From:{from_cat},To:{to_cat}"
                payload = {
                    "action": "add",
                    "id": new_id,
                    "date": datetime.now().strftime("%Y-%m-%d"),
                    "type": "โอนงบ",
                    "category": cat_str,
                    "amount": trans_amount,
                    "note": "โอนย้ายงบประมาณ"
                }
                if send_data_to_sheet(payload):
                    st.success("โอนเงินเรียบร้อย!")
                    st.rerun()
            else:
                st.error("กรุณาตรวจสอบจำนวนเงินและรายการต้นทาง/ปลายทาง")

    st.markdown("---")

    # ส่วนแสดงกราฟและตารางจิ๋ว (ตามข้อ 6)
    if not st.session_state.df.empty:
        total_income = st.session_state.df[st.session_state.df['Type'] == "รายรับ"]['Amount'].sum()
        
        sum_pct = sum(budget_rules.values())
        all_rules = budget_rules.copy()
        all_rules["อื่น ๆ"] = 100 - sum_pct

        transfers = st.session_state.df[st.session_state.df['Type'] == "โอนงบ"]

        st.subheader("สถานะงบประมาณแต่ละรายการ")
        cols = st.columns(3) # แสดงทีละ 3 การ์ด
        
        for i, (cat, pct) in enumerate(all_rules.items()):
            # 1. คำนวณตัวเลข
            initial_budget = total_income * (pct / 100) # สีเขียว (จัดสรรจากรายได้)
            
            # หาการโอนเข้า (สีฟ้า) และ ออก (สีเหลือง)
            transfer_in = 0
            transfer_out = 0
            if not transfers.empty:
                for idx, row in transfers.iterrows():
                    if f"To:{cat}" in row['Category']: transfer_in += row['Amount']
                    if f"From:{cat}" in row['Category']: transfer_out += row['Amount']
            
            # หาค่าใช้จ่ายจริง (สีแดง)
            spent = st.session_state.df[
                (st.session_state.df['Type'] == "รายจ่าย") & 
                (st.session_state.df['Category'] == cat)
            ]['Amount'].sum()
            
            net_budget = initial_budget + transfer_in - transfer_out
            remaining = net_budget - spent
            
            # 2. แสดงผล Card
            with cols[i % 3]:
                # ส่วนหัวการ์ด
                status_color = "green" if remaining >= 0 else "red"
                st.markdown(f"#### :{status_color}[{cat}]")
                
                # Progress Bar
                if net_budget > 0:
                    prog = min(1.0, max(0.0, spent / net_budget))
                else:
                    prog = 1.0 if spent > 0 else 0.0
                st.progress(prog)
                
                if remaining >= 0:
                    st.caption(f"คงเหลือ: {remaining:,.2f} บาท")
                else:
                    st.error(f"เกินงบ: {abs(remaining):,.2f} บาท")

                # 3. ตารางจิ๋ว (Mini Breakdown)
                # สร้าง DataFrame สำหรับตาราง
                breakdown_data = [
                    {"รายการ": "ได้รับจัดสรร (รายได้)", "จำนวน": initial_budget, "สี": "🟢 เขียว"},
                    {"รายการ": "รับโอนงบเข้า", "จำนวน": transfer_in, "สี": "🔵 ฟ้า"},
                    {"รายการ": "โอนงบออก", "จำนวน": transfer_out, "สี": "🟡 เหลือง"},
                    {"รายการ": "ใช้จ่ายจริง", "จำนวน": spent, "สี": "🔴 แดง"}
                ]
                bd_df = pd.DataFrame(breakdown_data)
                # กรองเอาเฉพาะอันที่ไม่เป็น 0 เพื่อความสะอาดตา (ยกเว้นใช้จ่ายให้โชว์ตลอด)
                bd_df = bd_df[(bd_df['จำนวน'] > 0) | (bd_df['รายการ'] == "ใช้จ่ายจริง")]
                
                st.dataframe(
                    bd_df, 
                    column_config={
                        "รายการ": st.column_config.TextColumn("รายการ"),
                        "จำนวน": st.column_config.NumberColumn("บาท", format="%.2f"),
                        "สี": st.column_config.TextColumn("กลุ่ม")
                    },
                    hide_index=True,
                    use_container_width=True
                )
                st.markdown("---")

# ==========================================
# หน้า 3: ประวัติและแก้ไขข้อมูล
# ==========================================
elif page == "3. ประวัติและแก้ไขข้อมูล":
    st.header("🕰️ ประวัติรายการ")
    
    if not st.session_state.df.empty:
        # Filter & Sort
        df_show = st.session_state.df.copy()
        df_show = df_show.sort_values(by="Date", ascending=False)
        
        for index, row in df_show.iterrows():
            if row['Type'] == 'รายรับ': icon = "💰"
            elif row['Type'] == 'รายจ่าย': icon = "💸"
            else: icon = "🔄"
            
            with st.expander(f"{icon} {row['Date'].strftime('%d/%m')} | {row['Category']} | {row['Amount']:,.2f} บาท"):
                c1, c2 = st.columns(2)
                if c2.button("ลบรายการ", key=f"del_{row['ID']}"):
                    if send_data_to_sheet({"action": "delete", "id": row['ID']}):
                        st.success("ลบแล้ว")
                        st.cache_data.clear()
                        st.rerun()
    else:
        st.info("ยังไม่มีข้อมูล")
