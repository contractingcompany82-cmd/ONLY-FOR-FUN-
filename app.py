import streamlit as st
from datetime import datetime, timezone, timedelta
import os
import requests
from io import BytesIO
import qrcode
from PIL import Image
import base64
import json
import uuid
import cv2
import numpy as np

# --- PAGE CONFIG ---
st.set_page_config(
    page_title="Azaz Pay | ازاز باي",
    page_icon="💳",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# --- CUSTOM CSS ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Tajawal:wght@400;700&display=swap');
    
    .main { direction: rtl; text-align: right; }
    .arabic-text { font-family: 'Tajawal', sans-serif; direction: rtl; text-align: right; }
    
    .payment-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 30px;
        border-radius: 20px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.3);
        margin: 20px 0;
    }
    
    .bank-card {
        background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
        color: white;
        padding: 25px;
        border-radius: 15px;
        margin: 15px 0;
        box-shadow: 0 5px 15px rgba(0,0,0,0.2);
        border-left: 5px solid #ffd700;
    }
    
    .scanner-box {
        border: 3px dashed #667eea;
        border-radius: 15px;
        padding: 40px;
        text-align: center;
        background: #f8f9fa;
        margin: 20px 0;
    }
    
    .success-animation {
        background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
        color: white;
        padding: 30px;
        border-radius: 20px;
        text-align: center;
        animation: pulse 2s infinite;
    }
    
    @keyframes pulse {
        0% { transform: scale(1); }
        50% { transform: scale(1.05); }
        100% { transform: scale(1); }
    }
    
    .stButton>button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        font-weight: bold;
        border-radius: 10px;
        padding: 15px;
        width: 100%;
        border: none;
    }
    </style>
""", unsafe_allow_html=True)

# --- SESSION STATE INIT ---
if 'accounts' not in st.session_state:
    st.session_state.accounts = []
if 'transactions' not in st.session_state:
    st.session_state.transactions = []
if 'page' not in st.session_state:
    st.session_state.page = 'home'

# --- BANK FUNCTIONS ---
def add_account(name, bank_name, account_number, ifsc_code, branch, country):
    account = {
        'id': str(uuid.uuid4())[:8],
        'holder_name': name,
        'bank_name': bank_name,
        'account_number': account_number,
        'ifsc_code': ifsc_code,
        'branch': branch,
        'country': country,
        'added_on': datetime.now().strftime("%Y-%m-%d %H:%M")
    }
    st.session_state.accounts.append(account)
    return True

def delete_account(account_id):
    st.session_state.accounts = [acc for acc in st.session_state.accounts if acc['id'] != account_id]

def generate_payment_qr(amount, order_id, account_details, note=""):
    qr_data = f"AZAZPAY|{amount}|{account_details['account_number']}|{order_id}|{note}"
    qr = qrcode.QRCode(version=3, box_size=10, border=5)
    qr.add_data(qr_data)
    qr.make(fit=True)
    return qr.make_image(fill_color="black", back_color="white")

def scan_qr_code(image):
    """Scan QR code from uploaded image"""
    try:
        # Convert to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Initialize QR detector
        detector = cv2.QRCodeDetector()
        
        # Detect and decode
        data, bbox, _ = detector.detectAndDecode(gray)
        
        if data:
            return data
        return None
    except:
        return None

# --- UI COMPONENTS ---
def show_logo():
    try:
        for logo_file in ["logo azaz.jpg", "logo_azaz.jpg"]:
            if os.path.exists(logo_file):
                st.image(logo_file, width=150)
                return
    except:
        pass
    st.markdown("<h1 style='color: #c41e3a; text-align: center;'>🏗️ Azaz Pay</h1>", unsafe_allow_html=True)

# --- MAIN UI ---
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    show_logo()
    st.markdown("<h3 style='text-align: center; color: #667eea;'>ازاز باي - نظام الدفع</h3>", unsafe_allow_html=True)

st.markdown("---")

# DEMO WARNING
st.markdown("""
    <div style='text-align: center; margin-bottom: 20px; padding: 15px; background: #fff3cd; border-radius: 10px; border: 2px solid #ffc107;'>
        <h4>⚠️ DEMO MODE | وضع تجريبي</h4>
        <p style='color: red; font-weight: bold; margin: 0;'>For fun/testing only - No real money!</p>
    </div>
""", unsafe_allow_html=True)

# --- NAVIGATION ---
col1, col2, col3, col4 = st.columns(4)
with col1:
    if st.button("🏠 Home", use_container_width=True):
        st.session_state.page = 'home'
        st.rerun()
with col2:
    if st.button("💳 Pay", use_container_width=True):
        st.session_state.page = 'pay'
        st.rerun()
with col3:
    if st.button("📷 Scan QR", use_container_width=True):
        st.session_state.page = 'scan'
        st.rerun()
with col4:
    if st.button("🏦 Accounts", use_container_width=True):
        st.session_state.page = 'accounts'
        st.rerun()

# --- HOME PAGE ---
if st.session_state.page == 'home':
    st.markdown("### Welcome to Azaz Pay | مرحباً بكم في ازاز باي")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
            <div class="payment-card" style="text-align: center;">
                <h3>💳 Generate QR</h3>
                <p>Create payment QR code</p>
            </div>
        """, unsafe_allow_html=True)
        if st.button("Create Payment", key="home_pay"):
            st.session_state.page = 'pay'
            st.rerun()
    
    with col2:
        st.markdown("""
            <div class="payment-card" style="text-align: center; background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%) !important;">
                <h3>📷 Scan QR</h3>
                <p>Scan & pay instantly</p>
            </div>
        """, unsafe_allow_html=True)
        if st.button("Scan Now", key="home_scan"):
            st.session_state.page = 'scan'
            st.rerun()
    
    # Quick Stats
    if st.session_state.transactions:
        total = sum(float(t['amount']) for t in st.session_state.transactions)
        st.markdown(f"""
            <div style='background: #f8f9fa; padding: 20px; border-radius: 15px; margin-top: 20px; text-align: center;'>
                <h4>Total Transactions: {len(st.session_state.transactions)} | المبلغ: {total} SAR</h4>
            </div>
        """, unsafe_allow_html=True)

# --- PAY PAGE (Generate QR) ---
elif st.session_state.page == 'pay':
    st.markdown("### 💳 Generate Payment QR | إنشاء رمز الدفع")
    
    if not st.session_state.accounts:
        st.warning("Add a bank account first! | أضف حساب بنكي أولاً!")
        if st.button("Go to Accounts"):
            st.session_state.page = 'accounts'
            st.rerun()
    else:
        # Select Account
        account_options = {f"{acc['bank_name']} - {acc['holder_name']}": acc['id'] 
                          for acc in st.session_state.accounts}
        selected = st.selectbox("Select Account | اختر الحساب", list(account_options.keys()))
        selected_acc = next(acc for acc in st.session_state.accounts if acc['id'] == account_options[selected])
        
        # Amount
        amount = st.number_input("Amount (SAR)", min_value=1, value=100)
        note = st.text_input("Note (Optional)", placeholder="Invoice #123")
        
        if st.button("Generate QR | إنشاء الرمز", type="primary"):
            order_id = f"AZZ{datetime.now().strftime('%Y%m%d%H%M%S')}"
            
            # Generate QR
            qr_img = generate_payment_qr(amount, order_id, selected_acc, note)
            
            buf = BytesIO()
            qr_img.save(buf, format='PNG')
            b64 = base64.b64encode(buf.getvalue()).decode()
            
            st.session_state.generated_qr = {
                'b64': b64,
                'amount': amount,
                'order_id': order_id,
                'account': selected_acc,
                'note': note
            }
        
        # Show QR if generated
        if 'generated_qr' in st.session_state:
            qr = st.session_state.generated_qr
            
            st.markdown(f"""
                <div class="payment-card">
                    <h2 style='text-align: center;'>{qr['amount']} SAR</h2>
                    <p>To: {qr['account']['holder_name']}</p>
                    <p>Bank: {qr['account']['bank_name']}</p>
                </div>
                <div class="scanner-box">
                    <img src="data:image/png;base64,{qr['b64']}" style="max-width: 300px;">
                    <p>Scan this QR to pay | امسح للدفع</p>
                </div>
            """, unsafe_allow_html=True)
            
            # Simulate receiving payment
            if st.button("✅ Mark as Paid (Demo)"):
                txn = {
                    'id': f"TXN{datetime.now().strftime('%Y%m%d%H%M%S')}",
                    'amount': qr['amount'],
                    'to': qr['account']['holder_name'],
                    'bank': qr['account']['bank_name'],
                    'time': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    'order_id': qr['order_id']
                }
                st.session_state.transactions.append(txn)
                del st.session_state.generated_qr
                st.balloons()
                st.success("Payment Successful! | تم الدفع بنجاح!")
                st.rerun()

# --- SCAN PAGE (QR Scanner) ---
elif st.session_state.page == 'scan':
    st.markdown("### 📷 Scan QR Code | مسح رمز الاستجابة")
    
    st.markdown("""
        <div class="scanner-box">
            <h3>📱 Upload QR Code Image</h3>
            <p>Take screenshot of QR and upload | التقط صورة للرمز وارفعها</p>
        </div>
    """, unsafe_allow_html=True)
    
    uploaded_file = st.file_uploader("Choose QR image | اختر صورة الرمز", type=['png', 'jpg', 'jpeg'])
    
    if uploaded_file is not None:
        # Display uploaded image
        file_bytes = np.asarray(bytearray(uploaded_file.read()), dtype=np.uint8)
        image = cv2.imdecode(file_bytes, 1)
        
        st.image(image, channels="BGR", caption="Uploaded QR", use_column_width=True)
        
        # Scan button
        if st.button("🔍 Scan Now | مسح", type="primary"):
            with st.spinner("Scanning..."):
                qr_data = scan_qr_code(image)
                
                if qr_data:
                    st.success("QR Code Detected! | تم العثور على الرمز!")
                    
                    # Parse QR data
                    try:
                        parts = qr_data.split('|')
                        if len(parts) >= 3:
                            amount = parts[1]
                            acc_num = parts[2]
                            order_id = parts[3] if len(parts) > 3 else "UNKNOWN"
                            
                            st.markdown(f"""
                                <div class="payment-card">
                                    <h3>Payment Details | تفاصيل الدفع</h3>
                                    <h2>{amount} SAR</h2>
                                    <p>Account: ****{acc_num[-4:]}</p>
                                    <p>Order: {order_id}</p>
                                </div>
                            """, unsafe_allow_html=True)
                            
                            if st.button("💳 Pay Now | ادفع الآن"):
                                st.session_state.scanned_payment = {
                                    'amount': amount,
                                    'order_id': order_id
                                }
                                st.balloons()
                                st.success("Demo Payment Successful! | تم الدفع بنجاح!")
                        else:
                            st.info(f"QR Data: {qr_data}")
                    except:
                        st.info(f"Raw QR Data: {qr_data}")
                else:
                    st.error("No QR code found. Try another image. | لم يتم العثور على رمز")

# --- ACCOUNTS PAGE ---
elif st.session_state.page == 'accounts':
    st.markdown("### 🏦 Bank Accounts | الحسابات البنكية")
    
    # Add Account Form
    with st.expander("➕ Add Account"):
        with st.form("add_acc"):
            col1, col2 = st.columns(2)
            with col1:
                country = st.selectbox("Country", ["Saudi Arabia", "India", "UAE", "Other"])
                bank = st.text_input("Bank Name")
                holder = st.text_input("Account Holder")
            with col2:
                acc_num = st.text_input("Account Number")
                ifsc = st.text_input("IFSC/IBAN Code")
                branch = st.text_input("Branch")
            
            if st.form_submit_button("Save"):
                if bank and holder and acc_num:
                    add_account(holder, bank, acc_num, ifsc, branch, country)
                    st.success("Account added!")
                    st.rerun()
                else:
                    st.error("Fill required fields!")
    
    # List Accounts
    if st.session_state.accounts:
        for acc in st.session_state.accounts:
            with st.container():
                st.markdown(f"""
                    <div class="bank-card">
                        <h4>{acc['bank_name']} ({acc['country']})</h4>
                        <p><strong>Holder:</strong> {acc['holder_name']}</p>
                        <p><strong>Account:</strong> ****{acc['account_number'][-4:]}</p>
                        <p><strong>Code:</strong> {acc['ifsc_code'] or 'N/A'}</p>
                        <small>ID: {acc['id']}</small>
                    </div>
                """, unsafe_allow_html=True)
                
                if st.button("🗑️ Delete", key=f"del_{acc['id']}"):
                    delete_account(acc['id'])
                    st.rerun()
    else:
        st.info("No accounts yet")

# --- FOOTER ---
st.markdown("---")
st.markdown("""
    <div style='text-align: center; color: #666; padding: 20px;'>
        <p style='color: #c41e3a; font-weight: bold;'>🏗️ Azaz Pay | ازاز باي</p>
        <small>Demo Only | للتسلية فقط © 2026</small>
    </div>
""", unsafe_allow_html=True)
