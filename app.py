import streamlit as st
import pandas as pd
import plotly.express as px
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

# --- CSS ปรับแต่งความสวยงาม ---
st.markdown("""
<style>
    .stMetric {background-color: #f0f2f6; padding: 10px; border-radius: 10px;}
    div[data-testid="stExpander"] {border: 1px solid #e0e0e0; border-radius: 5px;}
</style>
""", unsafe_allow_html=True)

# --- ฟังก์ชันจัดการข้อมูล ---
def load_data():
    try:
        df = pd.read_csv(CSV_URL)
        # ตั้งชื่อคอลัมน์ให้ชัวร์
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

# โหลดข้อมูล
if 'df' not in st.session_state:
    st.session_state.df = load_data()

# --- กฎงบประมาณใหม่ (ตามข้อ 2) ---
budget_rules = {
    "ค่าผ่อนคอนโด": 17.0,
    "หนี้สหกรณ์": 18.0,
    "หนี้บัตรเครดิต": 29.0,
    "ค่าน้ำมัน": 7.5,
    "ค่าไฟ": 5.7,
    "ค่าโทรศัพท์": 5.0,
    "ค่าใช้จ่ายในครอบครัว": 7.6,
    "ค่าใช้จ่ายของตนเอง": 9.4,
    "ค่าน้ำ": 0.38
    # ส่วนที่เหลือ -> อื่น ๆ
}

# รายการ Dropdown
income_cats = ["เงินเดือน", "เงินค่าจ้าง", "เงินค่าเช่า", "เงินปันผล", "อื่น ๆ"]
# สร้างรายการรายจ่ายจากกฎ + อื่นๆ
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
    st.header("📝 บันทึกรายการประจำวัน")
    
    with st.form("entry_form", clear_on_submit=True):
        c1, c2, c3 = st.columns(3)
        with c1: d = st.date_input("วันที่", datetime.now())
        with c2: t = st.selectbox("ประเภท", ["รายรับ", "รายจ่าย"])
        with c3: a = st.number_input("จำนวนเงิน", min_value=0.0, step=0.1)
        
        # แก้ไขข้อ 1: แสดงรายการรายจ่ายให้ถูกต้อง
        if t == "รายรับ":
            cat = st.selectbox("รายการ", income_cats)
        else:
            cat = st.selectbox("รายการ", expense_cats)
            
        n = st.text_input("หมายเหตุ")
        
        if st.form_submit_button("บันทึกข้อมูล"):
            new_id = str(uuid.uuid4()) # สร้าง ID ไม่ซ้ำ
            payload = {
                "action": "add",
                "id": new_id,
                "date": d.strftime("%Y-%m-%d"),
                "type": t,
                "category": cat,
                "amount": a,
                "note": n
            }
            if send_data_to_sheet(payload):
                st.success("บันทึกสำเร็จ!")
                # อัปเดตข้อมูล Local ทันที
                new_row = pd.DataFrame([[new_id, pd.to_datetime(d), t, cat, a, n]], 
                                     columns=["ID", "Date", "Type", "Category", "Amount", "Note"])
                st.session_state.df = pd.concat([st.session_state.df, new_row], ignore_index=True)
                st.rerun()
            else:
                st.error("บันทึกไม่สำเร็จ กรุณาตรวจสอบอินเทอร์เน็ต")

    # Dashboard
    st.markdown("---")
    st.subheader("📊 สรุปภาพรวม")
    if not st.session_state.df.empty:
        # กรองเอาเฉพาะ รายรับ และ รายจ่าย (ไม่เอาโอนงบ)
        valid_df = st.session_state.df[st.session_state.df['Type'].isin(['รายรับ', 'รายจ่าย'])]
        
        inc = valid_df[valid_df['Type'] == "รายรับ"]['Amount'].sum()
        exp = valid_df[valid_df['Type'] == "รายจ่าย"]['Amount'].sum()
        bal = inc - exp
        
        m1, m2, m3 = st.columns(3)
        m1.metric("รายรับรวม", f"{inc:,.2f}")
        m2.metric("รายจ่ายรวม", f"{exp:,.2f}")
        m3.metric("คงเหลือสุทธิ", f"{bal:,.2f}")

# ==========================================
# หน้า 2: จัดสรรและโอนงบ (แก้ไขข้อ 2, 3, 4)
# ==========================================
elif page == "2. จัดสรรและโอนงบ":
    st.header("🧱 บริหารจัดการงบประมาณ")
    
    # 1. ส่วนโอนงบ (ข้อ 3)
    with st.expander("💸 **เมนูโอนย้ายงบประมาณ (Transfer Budget)**"):
        with st.form("transfer_form"):
            st.write("เลือกรายการที่จะโอนงบหากัน")
            tc1, tc2, tc3 = st.columns(3)
            with tc1: from_cat = st.selectbox("ต้นทาง (ลด)", expense_cats)
            with tc2: to_cat = st.selectbox("ปลายทาง (เพิ่ม)", expense_cats)
            with tc3: trans_amount = st.number_input("จำนวนเงินที่โอน", min_value=0.0)
            
            if st.form_submit_button("ยืนยันการโอน"):
                if from_cat == to_cat:
                    st.error("ต้นทางและปลายทางต้องไม่เหมือนกัน")
                else:
                    new_id = str(uuid.uuid4())
                    # บันทึกเป็น Type พิเศษชื่อ "โอนงบ"
                    # Category format: "From:AAA,To:BBB"
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
                        st.success(f"โอนงบ {trans_amount} จาก {from_cat} ไป {to_cat} สำเร็จ!")
                        st.cache_data.clear() # บังคับโหลดใหม่เพื่อให้ตารางอัปเดต
                        st.rerun()

    st.markdown("---")

    # 2. ตารางและกราฟ (ข้อ 4)
    if not st.session_state.df.empty:
        total_income = st.session_state.df[st.session_state.df['Type'] == "รายรับ"]['Amount'].sum()
        
        # เตรียมข้อมูลสรุป
        budget_data = []
        sum_pct = sum(budget_rules.values())
        all_rules = budget_rules.copy()
        all_rules["อื่น ๆ"] = 100 - sum_pct # ส่วนที่เหลือ

        # ดึงข้อมูลการโอน
        transfers = st.session_state.df[st.session_state.df['Type'] == "โอนงบ"]

        for cat, pct in all_rules.items():
            # 1. งบตั้งต้น (Initial Budget)
            initial = total_income * (pct / 100)
            
            # 2. คำนวณยอดโอน (Transfer Effect)
            # โอนเข้า (To: cat)
            in_amt = 0
            # โอนออก (From: cat)
            out_amt = 0
            
            if not transfers.empty:
                # Loop หาแบบบ้านๆ แต่มั่นใจ
                for index, row in transfers.iterrows():
                    if f"To:{cat}" in row['Category']:
                        in_amt += row['Amount']
                    if f"From:{cat}" in row['Category']:
                        out_amt += row['Amount']
            
            net_transfer = in_amt - out_amt
            final_budget = initial + net_transfer
            
            # 3. ใช้ไปจริง (Spent)
            spent = st.session_state.df[
                (st.session_state.df['Type'] == "รายจ่าย") & 
                (st.session_state.df['Category'] == cat)
            ]['Amount'].sum()
            
            remaining = final_budget - spent
            status = "ปกติ" if remaining >= 0 else "เกินงบ"
            
            budget_data.append({
                "รายการ": cat,
                "สัดส่วน (%)": pct,
                "งบตั้งต้น": initial,
                "รับโอน (+)/โอนออก (-)": net_transfer,
                "งบสุทธิ": final_budget,
                "ใช้ไปจริง": spent,
                "คงเหลือ": remaining,
                "สถานะ": status
            })
            
        # แสดงตารางสรุป (ข้อ 4)
        st.subheader("📋 ตารางรายละเอียดงบประมาณ")
        budget_df = pd.DataFrame(budget_data)
        # จัดรูปแบบตัวเลขให้สวยงาม
        st.dataframe(budget_df.style.format({
            "งบตั้งต้น": "{:,.2f}", 
            "รับโอน (+)/โอนออก (-)": "{:,.2f}",
            "งบสุทธิ": "{:,.2f}",
            "ใช้ไปจริง": "{:,.2f}",
            "คงเหลือ": "{:,.2f}"
        }), use_container_width=True)

        # แสดงกราฟแท่งแบบ Progress
        st.subheader("กราฟติดตามสถานะ")
        cols = st.columns(3)
        for i, row in budget_df.iterrows():
            with cols[i % 3]:
                st.markdown(f"**{row['รายการ']}**")
                
                # Progress Bar calculation
                if row['งบสุทธิ'] > 0:
                    prog = min(1.0, max(0.0, row['ใช้ไปจริง'] / row['งบสุทธิ']))
                else:
                    prog = 1.0 if row['ใช้ไปจริง'] > 0 else 0.0
                
                st.progress(prog)
                if row['คงเหลือ'] >= 0:
                    st.caption(f"เหลือ: {row['คงเหลือ']:,.2f} บาท")
                else:
                    st.error(f"เกินงบ: {abs(row['คงเหลือ']):,.2f} บาท")
                st.markdown("---")

# ==========================================
# หน้า 3: ประวัติและแก้ไขข้อมูล (ข้อ 5, 6)
# ==========================================
elif page == "3. ประวัติและแก้ไขข้อมูล":
    st.header("🕰️ ประวัติรายการ (แก้ไข/ลบ)")
    
    # ตัวกรอง (Filter)
    if not st.session_state.df.empty:
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            # สร้างรายการเดือนที่มีข้อมูล
            st.session_state.df['Month'] = st.session_state.df['Date'].dt.strftime('%Y-%m')
            available_months = ["ทั้งหมด"] + sorted(st.session_state.df['Month'].unique().tolist(), reverse=True)
            selected_month = st.selectbox("เลือกเดือน", available_months)
        
        with col_f2:
            sort_order = st.radio("เรียงลำดับ", ["ใหม่สุดไปเก่าสุด", "เก่าสุดไปใหม่สุด"], horizontal=True)
        
        # กรองข้อมูล
        filtered_df = st.session_state.df.copy()
        if selected_month != "ทั้งหมด":
            filtered_df = filtered_df[filtered_df['Month'] == selected_month]
            
        if sort_order == "ใหม่สุดไปเก่าสุด":
            filtered_df = filtered_df.sort_values(by="Date", ascending=False)
        else:
            filtered_df = filtered_df.sort_values(by="Date", ascending=True)

        st.write(f"พบรายการทั้งสิ้น: {len(filtered_df)} รายการ")
        
        # แสดงรายการพร้อมปุ่ม Edit/Delete
        # เนื่องจาก Streamlit แสดงปุ่มในตารางยาก เราจะใช้ Expander
        for index, row in filtered_df.iterrows():
            # สีขอบซ้ายบอกประเภท
            border_color = "green" if row['Type'] == "รายรับ" else "red"
            if row['Type'] == "โอนงบ": border_color = "blue"
            
            with st.expander(f"{border_color} | {row['Date'].strftime('%d/%m/%Y')} | {row['Category']} | {row['Amount']:,.2f} บาท"):
                
                e_col1, e_col2 = st.columns(2)
                
                # --- ส่วนแก้ไข (Edit) ---
                with e_col1:
                    st.write("✏️ **แก้ไขรายการ**")
                    with st.form(key=f"edit_{row['ID']}"):
                        ed_date = st.date_input("วันที่", row['Date'])
                        ed_type = st.selectbox("ประเภท", ["รายรับ", "รายจ่าย", "โอนงบ"], index=["รายรับ", "รายจ่าย", "โอนงบ"].index(row['Type']))
                        ed_cat = st.text_input("รายการ", row['Category']) # ใช้ Text input เพื่อรองรับรายการโอนด้วย
                        ed_amt = st.number_input("จำนวนเงิน", value=float(row['Amount']), min_value=0.0)
                        ed_note = st.text_input("หมายเหตุ", row['Note'])
                        
                        if st.form_submit_button("บันทึกการแก้ไข"):
                            payload = {
                                "action": "edit",
                                "id": row['ID'],
                                "date": ed_date.strftime("%Y-%m-%d"),
                                "type": ed_type,
                                "category": ed_cat,
                                "amount": ed_amt,
                                "note": ed_note
                            }
                            if send_data_to_sheet(payload):
                                st.success("แก้ไขเรียบร้อย!")
                                st.cache_data.clear()
                                st.rerun()
                
                # --- ส่วนลบ (Delete) ---
                with e_col2:
                    st.write("🗑️ **ลบรายการ**")
                    st.warning("กดแล้วลบทันที")
                    if st.button("ลบรายการนี้", key=f"del_{row['ID']}"):
                        payload = {"action": "delete", "id": row['ID']}
                        if send_data_to_sheet(payload):
                            st.success("ลบข้อมูลแล้ว")
                            st.cache_data.clear()
                            st.rerun()
                            
    else:
        st.info("ยังไม่มีข้อมูลในระบบ")
