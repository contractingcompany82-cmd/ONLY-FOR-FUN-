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
    
    .bank-card h4 {
        margin: 0 0 15px 0;
        color: #ffd700;
    }
    
    .bank-detail {
        display: flex;
        justify-content: space-between;
        margin: 8px 0;
        padding: 8px;
        background: rgba(255,255,255,0.1);
        border-radius: 8px;
    }
    
    .qr-container {
        background: white;
        padding: 20px;
        border-radius: 15px;
        text-align: center;
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
    
    .delete-btn {
        background: #dc3545 !important;
        color: white !important;
    }
    
    .tabs {
        border-bottom: 2px solid #dee2e6;
        margin-bottom: 20px;
    }
    </style>
""", unsafe_allow_html=True)

# --- SESSION STATE INIT ---
if 'accounts' not in st.session_state:
    st.session_state.accounts = []
if 'transactions' not in st.session_state:
    st.session_state.transactions = []
if 'selected_account' not in st.session_state:
    st.session_state.selected_account = None

# --- BANK ACCOUNT MANAGEMENT ---
def add_account(name, bank_name, account_number, ifsc_code, branch, country):
    """Add new bank account"""
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
    return account['id']

def delete_account(account_id):
    """Delete bank account"""
    st.session_state.accounts = [acc for acc in st.session_state.accounts if acc['id'] != account_id]
    if st.session_state.selected_account == account_id:
        st.session_state.selected_account = None

def generate_payment_qr(amount, order_id, account_details):
    """Generate payment QR with bank details"""
    qr_data = f"""
AZAZ PAY - DEMO MODE
Amount: {amount} SAR
To: {account_details['holder_name']}
Bank: {account_details['bank_name']}
A/C: {account_details['account_number']}
{'IFSC: ' + account_details['ifsc_code'] if account_details['ifsc_code'] else 'IBAN: SA00XXXX'}
Order: {order_id}
Status: DEMO - NO REAL MONEY
"""
    qr = qrcode.QRCode(version=3, box_size=10, border=5)
    qr.add_data(qr_data)
    qr.make(fit=True)
    return qr.make_image(fill_color="black", back_color="white")

# --- LOGO DISPLAY ---
def display_logo():
    try:
        for logo_file in ["logo azaz.jpg", "logo_azaz.jpg"]:
            if os.path.exists(logo_file):
                st.image(logo_file, width=150)
                return True
    except:
        pass
    st.markdown("<h1 style='color: #c41e3a; text-align: center;'>🏗️ Azaz Pay</h1>", unsafe_allow_html=True)
    return True

# --- MAIN APP ---
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    display_logo()
    st.markdown("<h3 style='text-align: center; color: #667eea;'>ازاز باي - نظام الدفع</h3>", unsafe_allow_html=True)

st.markdown("---")

# DEMO WARNING
st.markdown("""
    <div style='text-align: center; margin-bottom: 20px; padding: 15px; background: #fff3cd; border-radius: 10px; border: 2px solid #ffc107;'>
        <h4>⚠️ DEMO MODE | وضع تجريبي</h4>
        <p style='color: red; font-weight: bold; margin: 0;'>This is for fun/testing only - No real money!</p>
        <p style='color: #666; margin: 5px 0 0 0;'>هذا للتجربة فقط - لا يوجد دفع حقيقي</p>
    </div>
""", unsafe_allow_html=True)

# --- TABS ---
tab1, tab2, tab3 = st.tabs(["💳 Pay | دفع", "🏦 Accounts | الحسابات", "📋 History | السجل"])

# --- TAB 1: PAYMENT ---
with tab1:
    if not st.session_state.accounts:
        st.warning("⚠️ Please add a bank account first | يرجى إضافة حساب بنكي أولاً")
        st.info("Go to 'Accounts' tab to add bank details | اذهب إلى تبويب 'الحسابات'")
    else:
        # Select Account
        st.markdown("### Select Bank Account | اختر الحساب البنكي")
        
        account_options = {f"{acc['bank_name']} - {acc['holder_name']} ({acc['account_number'][-4:]})": acc['id'] 
                          for acc in st.session_state.accounts}
        
        selected = st.selectbox("Choose Account | اختر الحساب", options=list(account_options.keys()))
        selected_id = account_options[selected]
        st.session_state.selected_account = selected_id
        
        account_details = next(acc for acc in st.session_state.accounts if acc['id'] == selected_id)
        
        # Show Selected Account Card
        st.markdown(f"""
            <div class="bank-card">
                <h4>🏦 {account_details['bank_name']}</h4>
                <div class="bank-detail">
                    <span>Account Holder | صاحب الحساب:</span>
                    <span style='font-weight: bold;'>{account_details['holder_name']}</span>
                </div>
                <div class="bank-detail">
                    <span>Account Number | رقم الحساب:</span>
                    <span style='font-family: monospace;'>****{account_details['account_number'][-4:]}</span>
                </div>
                <div class="bank-detail">
                    <span>{'IFSC Code' if account_details['country'] == 'India' else 'IBAN'} | رمز البنك:</span>
                    <span style='font-family: monospace;'>{account_details['ifsc_code'] or 'SA00XXXX'}</span>
                </div>
                <div class="bank-detail">
                    <span>Branch | الفرع:</span>
                    <span>{account_details['branch']}</span>
                </div>
            </div>
        """, unsafe_allow_html=True)
        
        # Amount Selection
        st.markdown("### Enter Amount | أدخل المبلغ")
        
        col1, col2, col3, col4 = st.columns(4)
        quick_amounts = [50, 100, 500, 1000]
        
        for col, amt in zip([col1, col2, col3, col4], quick_amounts):
            with col:
                if st.button(f"{amt} SAR"):
                    st.session_state.quick_amount = amt
        
        amount = st.number_input("Amount (SAR) | المبلغ", 
                                min_value=1, max_value=50000, 
                                value=st.session_state.get('quick_amount', 100))
        
        note = st.text_input("Payment Note | ملاحظة (اختياري)", placeholder="Invoice #123 | فاتورة رقم")
        
        # Generate QR
        if st.button("🔄 Generate Payment QR | إنشاء رمز الدفع", type="primary"):
            order_id = f"AZZ{datetime.now().strftime('%Y%m%d%H%M%S')}"
            st.session_state.current_payment = {
                'amount': amount,
                'order_id': order_id,
                'account': account_details,
                'note': note,
                'time': datetime.now()
            }
            st.session_state.qr_generated = True
        
        # Display QR
        if st.session_state.get('qr_generated', False):
            payment = st.session_state.current_payment
            
            st.markdown(f"""
                <div class="payment-card">
                    <h3 style='text-align: center;'>💳 Payment Request | طلب دفع</h3>
                    <h2 style='text-align: center; font-size: 36px; margin: 20px 0;'>{payment['amount']} SAR</h2>
                    <div style='background: rgba(255,255,255,0.2); padding: 15px; border-radius: 10px;'>
                        <p><strong>To | إلى:</strong> {payment['account']['holder_name']}</p>
                        <p><strong>Bank | البنك:</strong> {payment['account']['bank_name']}</p>
                        <p><strong>Order ID | رقم الطلب:</strong> {payment['order_id']}</p>
                        {f"<p><strong>Note | ملاحظة:</strong> {payment['note']}</p>" if payment['note'] else ""}
                    </div>
                </div>
            """, unsafe_allow_html=True)
            
            # Generate QR
            qr_img = generate_payment_qr(payment['amount'], payment['order_id'], payment['account'])
            
            import io
            buf = io.BytesIO()
            qr_img.save(buf, format='PNG')
            b64 = base64.b64encode(buf.getvalue()).decode()
            
            st.markdown(f"""
                <div class="qr-container">
                    <h4>📱 Scan to Pay | امسح للدفع</h4>
                    <img src="data:image/png;base64,{b64}" style="max-width: 250px; margin: 15px 0;">
                    <p style='color: #666; font-size: 0.8rem;'>Demo QR - No real transaction</p>
                </div>
            """, unsafe_allow_html=True)
            
            # Simulate Payment
            col1, col2 = st.columns(2)
            with col1:
                if st.button("✅ Payment Received | تم استلام الدفع", type="primary"):
                    # Save transaction
                    transaction = {
                        'id': f"TXN{datetime.now().strftime('%Y%m%d%H%M%S')}",
                        'amount': payment['amount'],
                        'to': payment['account']['holder_name'],
                        'bank': payment['account']['bank_name'],
                        'time': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        'status': 'Success',
                        'order_id': payment['order_id']
                    }
                    st.session_state.transactions.append(transaction)
                    st.session_state.payment_success = True
                    st.balloons()
            
            with col2:
                if st.button("❌ Cancel | إلغاء"):
                    st.session_state.qr_generated = False
                    st.experimental_rerun()
        
        # Success Message
        if st.session_state.get('payment_success', False):
            st.markdown("""
                <div class="success-animation">
                    <h2>🎉 Payment Successful!</h2>
                    <h3>تم الدفع بنجاح!</h3>
                    <p>Transaction saved in History | تم حفظ العملية في السجل</p>
                </div>
            """, unsafe_allow_html=True)
            if st.button("New Payment | دفع جديد"):
                st.session_state.qr_generated = False
                st.session_state.payment_success = False
                st.experimental_rerun()

# --- TAB 2: ACCOUNTS ---
with tab2:
    st.markdown("### 🏦 Manage Bank Accounts | إدارة الحسابات البنكية")
    
    # Add New Account Form
    with st.expander("➕ Add New Account | إضافة حساب جديد", expanded=len(st.session_state.accounts)==0):
        with st.form("add_account"):
            col1, col2 = st.columns(2)
            
            with col1:
                country = st.selectbox("Country | الدولة", ["Saudi Arabia", "India", "UAE", "Other"])
                bank_name = st.text_input("Bank Name | اسم البنك", placeholder="Saudi National Bank")
                holder_name = st.text_input("Account Holder Name | اسم صاحب الحساب", placeholder="Mohammed Ahmed")
            
            with col2:
                account_number = st.text_input("Account Number | رقم الحساب", placeholder="SA0380000000608010167519")
                if country == "India":
                    ifsc_code = st.text_input("IFSC Code | رمز IFSC", placeholder="SBIN0001234")
                else:
                    ifsc_code = st.text_input("IBAN / Swift Code | رمز IBAN", placeholder="SNB SA 38")
                branch = st.text_input("Branch | الفرع", placeholder="Riyadh Main Branch")
            
            submit = st.form_submit_button("💾 Save Account | حفظ الحساب")
            
            if submit:
                if bank_name and holder_name and account_number:
                    acc_id = add_account(holder_name, bank_name, account_number, ifsc_code, branch, country)
                    st.success(f"✅ Account added successfully! | تم إضافة الحساب بنجاح! (ID: {acc_id})")
                    st.experimental_rerun()
                else:
                    st.error("⚠️ Please fill required fields | يرجى ملء الحقول المطلوبة")
    
    # Show Existing Accounts
    st.markdown("### Your Accounts | حساباتك")
    
    if not st.session_state.accounts:
        st.info("No accounts added yet | لم تتم إضافة حسابات بعد")
    else:
        for acc in st.session_state.accounts:
            with st.container():
                st.markdown(f"""
                    <div class="bank-card">
                        <div style='display: flex; justify-content: space-between; align-items: center;'>
                            <h4>🏦 {acc['bank_name']} <small style='color: #ffd700;'>({acc['country']})</small></h4>
                            <small style='color: #aaa;'>ID: {acc['id']}</small>
                        </div>
                        <div class="bank-detail">
                            <span>Holder | الصاحب:</span>
                            <span>{acc['holder_name']}</span>
                        </div>
                        <div class="bank-detail">
                            <span>Account | الحساب:</span>
                            <span style='font-family: monospace;'>****{acc['account_number'][-4:]}</span>
                        </div>
                        <div class="bank-detail">
                            <span>Code | الرمز:</span>
                            <span style='font-family: monospace;'>{acc['ifsc_code'] or 'N/A'}</span>
                        </div>
                        <div class="bank-detail">
                            <span>Branch | الفرع:</span>
                            <span>{acc['branch']}</span>
                        </div>
                        <small style='color: #aaa;'>Added: {acc['added_on']}</small>
                    </div>
                """, unsafe_allow_html=True)
                
                if st.button("🗑️ Delete | حذف", key=f"del_{acc['id']}"):
                    delete_account(acc['id'])
                    st.experimental_rerun()

# --- TAB 3: HISTORY ---
with tab3:
    st.markdown("### 📋 Transaction History | سجل المعاملات")
    
    if not st.session_state.transactions:
        st.info("No transactions yet | لا توجد معاملات حتى الآن")
    else:
        total_amount = sum(float(t['amount']) for t in st.session_state.transactions)
        
        st.markdown(f"""
            <div style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                        color: white; padding: 20px; border-radius: 15px; margin-bottom: 20px;'>
                <h4 style='margin: 0;'>Total Transactions | إجمالي المعاملات</h4>
                <h2 style='margin: 10px 0 0 0;'>{len(st.session_state.transactions)}</h2>
                <p style='margin: 5px 0 0 0; opacity: 0.9;'>Total Amount | المبلغ الإجمالي: {total_amount} SAR</p>
            </div>
        """, unsafe_allow_html=True)
        
        for txn in reversed(st.session_state.transactions):
            st.markdown(f"""
                <div style='background: #f8f9fa; padding: 15px; border-radius: 10px; 
                            margin: 10px 0; border-right: 4px solid #28a745;'>
                    <div style='display: flex; justify-content: space-between; align-items: center;'>
                        <h4 style='margin: 0; color: #28a745;'>✅ {txn['amount']} SAR</h4>
                        <small style='color: #666;'>{txn['time']}</small>
                    </div>
                    <p style='margin: 5px 0; color: #555;'>
                        <strong>To:</strong> {txn['to']}<br>
                        <strong>Bank:</strong> {txn['bank']}<br>
                        <small style='color: #999;'>ID: {txn['id']} | Order: {txn['order_id']}</small>
                    </p>
                </div>
            """, unsafe_allow_html=True)

# --- FOOTER ---
st.markdown("---")
st.markdown("""
    <div style='text-align: center; color: #666; padding: 20px;'>
        <p style='color: #c41e3a; font-weight: bold; font-size: 1.2rem;'>🏗️ Azaz Pay | ازاز باي</div>
        <p>Demo Payment System with Bank Accounts | نظام دفع تجريبي مع حسابات بنكية</p>
        <small>⚠️ For Fun Only | للتسلية فقط © 2026</small>
    </div>
""", unsafe_allow_html=True)
