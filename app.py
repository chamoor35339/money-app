import streamlit as st
import pandas as pd
import plotly.express as px
import requests
import json
from datetime import datetime

# ==========================================
# 🔧 ส่วนตั้งค่า (เอาลิงก์ของคุณมาแปะตรงนี้)
# ==========================================

# 1. ลิงก์สำหรับ "อ่าน" (จากขั้นตอน Publish to web เป็น CSV)
CSV_URL = "วางลิงก์_CSV_ยาวๆ_ตรงนี้"

# 2. ลิงก์สำหรับ "บันทึก" (จากขั้นตอน Apps Script /exec)
WEB_APP_URL = "วางลิงก์_Web_App_URL_ยาวๆ_ตรงนี้"

# ==========================================

st.set_page_config(page_title="Chanon Money", layout="wide", page_icon="💰")
st.title("💰 ระบบบริหารจัดการเงิน - คุณชานนท์ รักปรางค์")

# ฟังก์ชันโหลดข้อมูล
def load_data():
    try:
        # อ่าน CSV จากเว็บ
        df = pd.read_csv(CSV_URL)
        # เปลี่ยนชื่อคอลัมน์ให้ชัวร์ (เผื่อ Google Sheet มีชื่ออื่น)
        # สมมติลำดับคือ Date, Type, Category, Amount, Note
        if len(df.columns) >= 5:
            df.columns = ["Date", "Type", "Category", "Amount", "Note"]
        
        df['Date'] = pd.to_datetime(df['Date'])
        return df
    except:
        return pd.DataFrame(columns=["Date", "Type", "Category", "Amount", "Note"])

# โหลดข้อมูลครั้งแรก
if 'df' not in st.session_state:
    st.session_state.df = load_data()

# ตั้งค่า Budget Rules
budget_rules = {
    "ค่าผ่อนคอนโด": 20, "หนี้สหกรณ์": 21, "หนี้บัตรเครดิต": 19,
    "ค่าน้ำมัน": 6, "ค่าน้ำ": 1, "ค่าไฟ": 3, "ค่าโทรศัพท์": 3,
    "ค่าใช้จ่ายในครอบครัว": 5, "ค่าใช้จ่ายของตนเอง": 6
}
income_cats = ["เงินเดือน", "เงินค่าจ้าง", "เงินค่าเช่า", "เงินปันผล", "อื่น ๆ"]
expense_cats = list(budget_rules.keys()) + ["อื่น ๆ"]

# --- เมนู Sidebar ---
st.sidebar.header("เมนูหลัก")
page = st.sidebar.radio("เลือกหน้า", ["1. บันทึกและภาพรวม", "2. จัดสรรงบประมาณ (Budget)", "3. ข้อมูลทั้งหมด"])

# ปุ่มรีเฟรชข้อมูลจริงจาก Google Sheet
if st.sidebar.button("🔄 ดึงข้อมูลล่าสุดจาก Server"):
    st.cache_data.clear()
    st.session_state.df = load_data()
    st.rerun()

# ==========================================
# หน้า 1: บันทึกและภาพรวม (รวมไว้หน้าเดียวตามคำขอ)
# ==========================================
if page == "1. บันทึกและภาพรวม":
    
    # --- ส่วนกรอกข้อมูล ---
    st.subheader("📝 บันทึกรายการใหม่")
    with st.form("entry_form", clear_on_submit=True):
        c1, c2, c3 = st.columns(3)
        with c1: d = st.date_input("วันที่", datetime.now())
        with c2: t = st.selectbox("ประเภท", ["รายรับ", "รายจ่าย"])
        with c3: a = st.number_input("จำนวนเงิน", min_value=0.0, step=1.0)
        
        if t == "รายรับ": cat = st.selectbox("รายการ", income_cats)
        else: cat = st.selectbox("รายการ", expense_cats)
        
        n = st.text_input("หมายเหตุ")
        
        submitted = st.form_submit_button("บันทึกข้อมูล")
        
        if submitted:
            # 1. เตรียมข้อมูลส่งไป Google Sheet (Background)
            payload = {
                "date": d.strftime("%Y-%m-%d"),
                "type": t,
                "category": cat,
                "amount": a,
                "note": n
            }
            
            try:
                # ส่งข้อมูลไปที่ Apps Script
                response = requests.post(WEB_APP_URL, json=payload)
                
                if response.status_code == 200:
                    st.success("บันทึกสำเร็จ!")
                    
                    # 2. อัปเดตหน้าจอทันที (ไม่ต้องรอ Server)
                    new_row = pd.DataFrame({
                        "Date": [pd.to_datetime(d)],
                        "Type": [t],
                        "Category": [cat],
                        "Amount": [a],
                        "Note": [n]
                    })
                    st.session_state.df = pd.concat([st.session_state.df, new_row], ignore_index=True)
                    st.rerun()
                else:
                    st.error("เกิดข้อผิดพลาดในการเชื่อมต่อกับ Google Sheet")
            except Exception as e:
                st.error(f"Error: {e}")

    st.markdown("---")

    # --- ส่วนแสดงผล (Dashboard) ---
    st.subheader("📊 สรุปสถานะการเงิน")
    
    if not st.session_state.df.empty:
        inc = st.session_state.df[st.session_state.df['Type'] == "รายรับ"]['Amount'].sum()
        exp = st.session_state.df[st.session_state.df['Type'] == "รายจ่าย"]['Amount'].sum()
        bal = inc - exp
        
        m1, m2, m3 = st.columns(3)
        m1.metric("รายรับ", f"{inc:,.0f}")
        m2.metric("รายจ่าย", f"{exp:,.0f}")
        m3.metric("คงเหลือ", f"{bal:,.0f}", delta_color="normal")
        
        # กราฟ
        g1, g2 = st.columns(2)
        with g1:
            exp_df = st.session_state.df[st.session_state.df['Type'] == "รายจ่าย"]
            if not exp_df.empty:
                st.plotly_chart(px.pie(exp_df, values='Amount', names='Category', hole=0.4, title="สัดส่วนรายจ่าย"), use_container_width=True)
        with g2:
            # กราฟแท่งรายเดือน
            df_chart = st.session_state.df.copy()
            df_chart['Month'] = df_chart['Date'].dt.strftime('%Y-%m')
            monthly = df_chart.groupby(['Month', 'Type'])['Amount'].sum().reset_index()
            if not monthly.empty:
                st.plotly_chart(px.bar(monthly, x='Month', y='Amount', color='Type', barmode='group', title="รายรับ-จ่าย รายเดือน"), use_container_width=True)

# ==========================================
# หน้า 2: จัดสรรงบประมาณ
# ==========================================
elif page == "2. จัดสรรงบประมาณ (Budget)":
    st.header("🧱 ติดตามงบประมาณ")
    inc = st.session_state.df[st.session_state.df['Type'] == "รายรับ"]['Amount'].sum()
    
    cols = st.columns(3)
    all_rules = budget_rules.copy()
    all_rules["อื่น ๆ"] = 100 - sum(budget_rules.values())
    
    for i, (c, pct) in enumerate(all_rules.items()):
        allocated = inc * (pct/100)
        spent = st.session_state.df[(st.session_state.df['Type']=="รายจ่าย") & (st.session_state.df['Category']==c)]['Amount'].sum()
        remain = allocated - spent
        
        with cols[i%3]:
            st.markdown(f"**{c}** ({pct}%)")
            if allocated > 0:
                st.progress(min(1.0, max(0.0, spent/allocated)))
            st.caption(f"งบ: {allocated:,.0f} | ใช้: {spent:,.0f}")
            if remain >= 0: st.success(f"เหลือ: {remain:,.0f}")
            else: st.error(f"เกิน: {abs(remain):,.0f}")
            st.markdown("---")

# ==========================================
# หน้า 3: ข้อมูลดิบ
# ==========================================
else:
    st.header("📋 ประวัติรายการทั้งหมด")
    st.dataframe(st.session_state.df.sort_values(by="Date", ascending=False), use_container_width=True)
