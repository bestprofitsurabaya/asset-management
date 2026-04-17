import streamlit as st
import database_engine as db
import pandas as pd
import numpy as np
import os
import hashlib
import secrets
from datetime import datetime, timedelta
from sklearn.linear_model import LinearRegression
import json
import logging
from pathlib import Path
import base64
from io import BytesIO
from fpdf import FPDF

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Session state initialization
if 'db_mode' not in st.session_state:
    st.session_state.db_mode = 'real'
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'user_role' not in st.session_state:
    st.session_state.user_role = None
if 'username' not in st.session_state:
    st.session_state.username = None

def load_users():
    """Load users from environment variable or config file"""
    users_json = os.environ.get('BPF_USERS')
    if users_json:
        try:
            return json.loads(users_json)
        except:
            pass
    
    # Default users dengan hash SHA-256
    return {
        "admin": {
            "password": hashlib.sha256("admin123".encode('utf-8')).hexdigest(),
            "role": "admin"
        },
        "teknisi": {
            "password": hashlib.sha256("teknisi123".encode('utf-8')).hexdigest(),
            "role": "teknisi"
        },
        "manager": {
            "password": hashlib.sha256("manager123".encode('utf-8')).hexdigest(),
            "role": "manager"
        },
        "demo": {
            "password": hashlib.sha256("demo123".encode('utf-8')).hexdigest(),
            "role": "viewer"
        }
    }

def verify_password(username, password):
    """Verify username and password"""
    users = load_users()
    
    if not username or not password:
        return False, "Mohon isi username dan password"
    
    if username not in users:
        return False, "Username tidak ditemukan"
    
    hashed_input = hashlib.sha256(password.encode('utf-8')).hexdigest()
    
    if hashed_input == users[username]["password"]:
        return True, "Login berhasil"
    else:
        return False, "Password salah"

def logout():
    """Logout user"""
    st.session_state.authenticated = False
    st.session_state.user_role = None
    st.session_state.username = None
    if "password" in st.session_state:
        del st.session_state["password"]

def initialize_database(mode='real'):
    """Initialize database based on mode"""
    try:
        db.create_db(mode=mode)
        if mode == 'real':
            db.init_bpf_assets(mode=mode)
            db.init_vehicle_components(mode=mode)
            db.init_sample_vehicles(mode=mode)
        else:
            db.init_bpf_assets(mode=mode)
            db.init_vehicle_components(mode=mode)
            db.init_sample_vehicles(mode=mode)
            db.generate_dummy_ac_logs(logs_per_asset=100, mode=mode)
            db.generate_dummy_vehicle_services(services_per_vehicle=50, mode=mode)
            db.generate_dummy_vehicles(count=15, mode=mode)
        return True
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        st.error(f"Gagal menginisialisasi database: {e}")
        return False

# Initialize database on startup
if not initialize_database(st.session_state.db_mode):
    st.stop()

st.set_page_config(
    page_title="BPF Asset Management System",
    page_icon="A",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- UI THEME ---
st.markdown("""
    <style>
    .main { background-color: #f0f2f6; }
    
    [data-testid="stSidebar"] { 
        background: linear-gradient(135deg, #003366 0%, #002244 100%);
    }
    
    [data-testid="stSidebar"] .stSelectbox label,
    [data-testid="stSidebar"] .stSelectbox div,
    [data-testid="stSidebar"] .stMarkdown,
    [data-testid="stSidebar"] .stText,
    [data-testid="stSidebar"] p {
        color: white !important;
    }
    
    [data-testid="stSidebar"] .stSelectbox > div > div {
        background-color: rgba(255, 255, 255, 0.1);
        color: white;
        border-color: rgba(255, 255, 255, 0.2);
    }
    
    .stButton>button { 
        background: linear-gradient(135deg, #CC0000 0%, #990000 100%);
        color: white; 
        border-radius: 8px; 
        width: 100%; 
        height: 50px; 
        font-weight: bold; 
        border: none;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        transition: all 0.3s ease;
    }
    
    .stButton>button:hover { 
        background: linear-gradient(135deg, #990000 0%, #660000 100%);
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
    }
    
    .vehicle-card {
        background: white;
        padding: 20px;
        border-radius: 12px;
        border-left: 5px solid #CC0000;
        margin-bottom: 15px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        transition: all 0.3s ease;
    }
    
    .vehicle-card:hover {
        box-shadow: 0 4px 16px rgba(0,0,0,0.15);
        transform: translateX(5px);
    }
    
    .metric-card {
        background: white;
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        text-align: center;
        border-bottom: 3px solid #003366;
    }
    
    .status-badge {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.9em;
        font-weight: bold;
    }
    
    .status-good { background-color: #28a745; color: white; }
    .status-warning { background-color: #ffc107; color: black; }
    .status-critical { background-color: #dc3545; color: white; }
    .status-info { background-color: #17a2b8; color: white; }
    
    .db-mode-indicator {
        position: fixed;
        top: 10px;
        right: 10px;
        padding: 5px 15px;
        border-radius: 20px;
        font-weight: bold;
        z-index: 1000;
        background: rgba(255, 255, 255, 0.9);
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }
    
    .db-mode-demo { color: #ff6b6b; border: 2px solid #ff6b6b; }
    .db-mode-real { color: #51cf66; border: 2px solid #51cf66; }
    
    @media print {
        header, [data-testid="stSidebar"], .stButton, .no-print, .stTabs, .db-mode-indicator { 
            display: none !important; 
        }
        .main { width: 100% !important; padding: 0 !important; }
        .report-header { border-bottom: 3px solid #CC0000; margin-bottom: 20px; }
    }
    </style>
    """, unsafe_allow_html=True)

# --- PDF Generation Functions ---
class PDFReport(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 14)
        self.set_text_color(0, 51, 102)
        self.cell(0, 10, 'PT BESTPROFIT FUTURES SURABAYA', 0, 1, 'C')
        self.set_font('Arial', 'B', 12)
        self.set_text_color(204, 0, 0)
        self.cell(0, 8, 'LAPORAN ASSET MANAGEMENT', 0, 1, 'C')
        self.set_draw_color(204, 0, 0)
        self.line(10, 28, 200, 28)
        self.ln(10)
    
    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.set_text_color(128, 128, 128)
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')
        self.cell(0, 10, f'Dicetak: {datetime.now().strftime("%d/%m/%Y %H:%M")}', 0, 0, 'R')

def generate_ac_report_pdf(logs, asset_filter="Semua", date_range="Semua"):
    """Generate PDF report for AC maintenance"""
    pdf = PDFReport()
    pdf.add_page()
    
    # Report info
    pdf.set_font('Arial', 'B', 11)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(0, 8, f'Periode: {date_range} | Asset: {asset_filter}', 0, 1, 'L')
    pdf.ln(5)
    
    # Summary
    pdf.set_font('Arial', 'B', 10)
    pdf.set_fill_color(0, 51, 102)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(0, 8, 'RINGKASAN', 1, 1, 'L', True)
    
    pdf.set_font('Arial', '', 10)
    pdf.set_text_color(0, 0, 0)
    
    avg_health = logs['health_score'].mean() if 'health_score' in logs.columns else 0
    avg_delta = logs['delta_t'].mean() if 'delta_t' in logs.columns else 0
    total_cost = logs['sparepart_cost'].sum() if 'sparepart_cost' in logs.columns else 0
    
    pdf.cell(60, 7, f'Total Maintenance: {len(logs)} log', 0, 0)
    pdf.cell(60, 7, f'Rata-rata Health Score: {avg_health:.1f}%', 0, 1)
    pdf.cell(60, 7, f'Total Biaya Sparepart: Rp {total_cost:,.0f}', 0, 0)
    pdf.cell(60, 7, f'Rata-rata Delta T: {avg_delta:.1f} C', 0, 1)
    pdf.ln(5)
    
    # Table header
    pdf.set_font('Arial', 'B', 9)
    pdf.set_fill_color(0, 51, 102)
    pdf.set_text_color(255, 255, 255)
    
    headers = ['Tanggal', 'Asset ID', 'Teknisi', 'Delta T', 'Health', 'Status']
    widths = [30, 50, 45, 25, 20, 25]
    
    for i, header in enumerate(headers):
        pdf.cell(widths[i], 8, header, 1, 0, 'C', True)
    pdf.ln()
    
    # Table data
    pdf.set_font('Arial', '', 9)
    pdf.set_text_color(0, 0, 0)
    
    # Batasi jumlah data untuk PDF (max 50 baris)
    logs_to_show = logs.head(50)
    
    for _, row in logs_to_show.iterrows():
        # Konversi Timestamp ke string
        if 'tanggal' in row:
            tanggal_val = row['tanggal']
            if hasattr(tanggal_val, 'strftime'):
                tanggal_str = tanggal_val.strftime('%Y-%m-%d')
            else:
                tanggal_str = str(tanggal_val)[:10]
        else:
            tanggal_str = ''
        
        pdf.cell(widths[0], 7, tanggal_str, 1, 0, 'C')
        
        asset_id_str = str(row['asset_id'])[:20] if 'asset_id' in row else ''
        pdf.cell(widths[1], 7, asset_id_str, 1, 0, 'L')
        
        teknisi_str = str(row['teknisi'])[:15] if 'teknisi' in row else ''
        pdf.cell(widths[2], 7, teknisi_str, 1, 0, 'L')
        
        delta_val = row['delta_t'] if 'delta_t' in row else 0
        pdf.cell(widths[3], 7, f"{delta_val:.1f}", 1, 0, 'C')
        
        health = row['health_score'] if 'health_score' in row else 0
        if health >= 70:
            pdf.set_text_color(40, 167, 69)
        elif health >= 50:
            pdf.set_text_color(255, 193, 7)
        else:
            pdf.set_text_color(220, 53, 69)
        pdf.cell(widths[4], 7, f"{health}%", 1, 0, 'C')
        pdf.set_text_color(0, 0, 0)
        
        test_val = row['test_run'] if 'test_run' in row else ''
        pdf.cell(widths[5], 7, str(test_val)[:10], 1, 0, 'C')
        pdf.ln()
    
    if len(logs) > 50:
        pdf.set_font('Arial', 'I', 9)
        pdf.cell(0, 7, f'... dan {len(logs) - 50} data lainnya', 0, 1, 'C')
    
    # Footer signature
    pdf.ln(15)
    pdf.set_font('Arial', '', 10)
    pdf.cell(90, 7, 'Mengetahui,', 0, 0, 'C')
    pdf.cell(90, 7, 'Dibuat oleh,', 0, 1, 'C')
    pdf.ln(10)
    pdf.cell(90, 7, '_________________', 0, 0, 'C')
    pdf.cell(90, 7, '_________________', 0, 1, 'C')
    pdf.cell(90, 7, 'Manager Operasional', 0, 0, 'C')
    pdf.cell(90, 7, 'Teknisi', 0, 1, 'C')
    
    return pdf

def generate_vehicle_report_pdf(vehicles, health_data):
    """Generate PDF report for vehicles"""
    pdf = PDFReport()
    pdf.add_page()
    
    pdf.set_font('Arial', 'B', 11)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(0, 8, f'Tanggal Cetak: {datetime.now().strftime("%d %B %Y")}', 0, 1, 'L')
    pdf.ln(5)
    
    # Summary
    pdf.set_font('Arial', 'B', 10)
    pdf.set_fill_color(0, 51, 102)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(0, 8, 'RINGKASAN KENDARAAN', 1, 1, 'L', True)
    
    pdf.set_font('Arial', '', 10)
    pdf.set_text_color(0, 0, 0)
    
    total_vehicles = len(vehicles)
    aktif_count = len(vehicles[vehicles['status'] == 'Aktif']) if 'status' in vehicles.columns else 0
    service_count = len(vehicles[vehicles['status'] == 'Service']) if 'status' in vehicles.columns else 0
    total_odometer = vehicles['last_odometer'].sum() if 'last_odometer' in vehicles.columns else 0
    
    pdf.cell(50, 7, f'Total Kendaraan: {total_vehicles}', 0, 0)
    pdf.cell(50, 7, f'Aktif: {aktif_count}', 0, 1)
    pdf.cell(50, 7, f'Service: {service_count}', 0, 0)
    pdf.cell(50, 7, f'Total Odometer: {total_odometer:,.0f} km', 0, 1)
    pdf.ln(5)
    
    # Vehicle details (batasi 5 kendaraan per halaman)
    for idx, (_, row) in enumerate(vehicles.iterrows()):
        if idx > 0 and idx % 5 == 0:
            pdf.add_page()
        
        health = health_data.get(row['vehicle_id'], {})
        
        pdf.set_font('Arial', 'B', 11)
        pdf.set_text_color(0, 51, 102)
        pdf.cell(0, 8, f"{row['vehicle_id']} - {row['brand']} {row['model']} ({row['year']})", 0, 1, 'L')
        
        pdf.set_font('Arial', '', 10)
        pdf.set_text_color(0, 0, 0)
        pdf.cell(60, 6, f"Plat: {row['plate_number']}", 0, 0)
        pdf.cell(60, 6, f"Odometer: {row['last_odometer']:,.0f} km", 0, 1)
        pdf.cell(60, 6, f"Status: {row['status']}", 0, 0)
        
        if health:
            health_score = health.get('health_score', 0)
            if health_score >= 80:
                pdf.set_text_color(40, 167, 69)
            elif health_score >= 60:
                pdf.set_text_color(255, 193, 7)
            else:
                pdf.set_text_color(220, 53, 69)
            pdf.cell(60, 6, f"Health Score: {health_score:.0f}% - {health.get('status', '')}", 0, 1)
            pdf.set_text_color(0, 0, 0)
        
        pdf.ln(3)
        
        # Component table
        if health and health.get('next_services'):
            pdf.set_font('Arial', 'B', 9)
            pdf.set_fill_color(200, 200, 200)
            pdf.cell(70, 6, 'Komponen', 1, 0, 'L', True)
            pdf.cell(50, 6, 'Pemakaian', 1, 0, 'C', True)
            pdf.cell(60, 6, 'Status', 1, 1, 'C', True)
            
            pdf.set_font('Arial', '', 9)
            for comp in health['next_services'][:5]:
                comp_name = str(comp['component'])[:25]
                pdf.cell(70, 6, comp_name, 1, 0, 'L')
                pdf.cell(50, 6, f"{comp['usage_percent']:.0f}%", 1, 0, 'C')
                status_str = str(comp['status'])[:20]
                pdf.cell(60, 6, status_str, 1, 1, 'L')
        
        pdf.ln(5)
    
    return pdf

def get_pdf_download_link(pdf, filename):
    """Generate download link for PDF"""
    pdf_output = BytesIO()
    pdf.output(pdf_output)
    pdf_data = pdf_output.getvalue()
    pdf_output.close()
    
    b64 = base64.b64encode(pdf_data).decode()
    href = f'<a href="data:application/pdf;base64,{b64}" download="{filename}" style="text-decoration:none;padding:10px 20px;background:#CC0000;color:white;border-radius:8px;">Download PDF: {filename}</a>'
    return href

# --- FUNGSI AI: PREDICTIVE HEALTH untuk AC ---
def analyze_predictive_maintenance(asset_id, mode='real'):
    """Enhanced predictive maintenance analysis"""
    try:
        logs = db.get_all_logs(mode=mode)
        if logs.empty:
            return "Belum ada data", "Normal", 0
            
        unit_logs = logs[logs['asset_id'] == asset_id].copy()
        
        if len(unit_logs) < 5:
            return "Data Belum Cukup (Min. 5 log)", "Normal", 0
        
        unit_logs['tgl_dt'] = pd.to_datetime(unit_logs['tanggal'])
        base_date = unit_logs['tgl_dt'].min()
        unit_logs['days'] = (unit_logs['tgl_dt'] - base_date).dt.days
        
        X = unit_logs[['days']].values
        y = unit_logs['health_score'].values
        
        if len(set(y)) < 2:
            return "Data tidak cukup bervariasi", "Normal", 0
        
        weights = np.linspace(0.5, 1.0, len(y))
        model = LinearRegression()
        model.fit(X, y, sample_weight=weights)
        
        confidence = min(95, max(0, model.score(X, y) * 100))
        
        m = model.coef_[0]
        c = model.intercept_
        
        if m >= 0:
            pred_msg = "Kondisi Stabil/Membaik"
        else:
            days_to_fail = (65 - c) / m
            if days_to_fail > 0:
                fail_date = base_date + timedelta(days=int(days_to_fail))
                pred_msg = fail_date.strftime('%d %b %Y')
            else:
                pred_msg = "SEGERA - Sudah Kritis!"
        
        status = "Normal"
        
        if 'amp_kompresor' in unit_logs.columns:
            avg_amp = unit_logs['amp_kompresor'].mean()
            std_amp = unit_logs['amp_kompresor'].std()
            last_amp = unit_logs['amp_kompresor'].iloc[-1]
            if std_amp > 0 and last_amp > (avg_amp + 2 * std_amp):
                status = "Anomali Arus Tinggi"
        
        if 'delta_t' in unit_logs.columns and len(unit_logs) >= 3:
            recent_delta_t = unit_logs['delta_t'].iloc[-3:].mean()
            historical_delta_t = unit_logs['delta_t'].iloc[:-3].mean()
            if historical_delta_t > 0 and recent_delta_t < historical_delta_t * 0.8:
                status = "Anomali Efisiensi" if status == "Normal" else "Multi Anomali"
        
        return pred_msg, status, confidence
        
    except Exception as e:
        logger.error(f"Error in predictive maintenance analysis: {e}")
        return "Error Analisis", "Error", 0

# --- FUNGSI PREDICTIVE UNTUK KENDARAAN ---
def analyze_vehicle_health(vehicle_id, mode='real'):
    """Enhanced vehicle health analysis"""
    try:
        services = db.get_vehicle_services(vehicle_id, mode=mode)
        vehicle = db.get_vehicles(mode=mode)
        
        if vehicle.empty:
            return {
                "status": "Data Kendaraan Tidak Ditemukan",
                "health_score": 0,
                "next_services": [],
                "current_odometer": 0,
                "months_used": 0,
                "error": True,
                "maintenance_cost": 0,
                "cost_per_km": 0
            }
        
        vehicle_data = vehicle[vehicle['vehicle_id'] == vehicle_id]
        if vehicle_data.empty:
            return {
                "status": "Data Kendaraan Tidak Ditemukan",
                "health_score": 0,
                "next_services": [],
                "current_odometer": 0,
                "months_used": 0,
                "error": True,
                "maintenance_cost": 0,
                "cost_per_km": 0
            }
        
        vehicle_data = vehicle_data.iloc[0]
        current_odometer = vehicle_data['last_odometer']
        purchase_date = pd.to_datetime(vehicle_data['purchase_date'])
        current_date = datetime.now()
        months_used = (current_date.year - purchase_date.year) * 12 + (current_date.month - purchase_date.month)
        
        total_cost = services['cost'].sum() if not services.empty else 0
        cost_per_km = total_cost / current_odometer if current_odometer > 0 else 0
        
        components = db.get_vehicle_components(mode=mode)
        next_services = []
        
        for _, comp in components.iterrows():
            last_service = services[services['component_name'] == comp['component_name']]
            
            if not last_service.empty:
                last_service_date = pd.to_datetime(last_service.iloc[0]['service_date'])
                last_odometer = last_service.iloc[0]['odometer']
                months_since = (current_date.year - last_service_date.year) * 12 + (current_date.month - last_service_date.month)
                km_since = current_odometer - last_odometer
            else:
                months_since = months_used
                km_since = current_odometer
            
            km_percent = 0
            month_percent = 0
            
            if comp['standard_life_km'] > 0:
                safe_life_km = comp['standard_life_km'] * 0.9
                km_percent = min(100, (km_since / safe_life_km * 100))
            
            if comp['standard_life_months'] > 0:
                safe_life_months = comp['standard_life_months'] * 0.9
                month_percent = min(100, (months_since / safe_life_months * 100))
            
            max_percent = max(km_percent, month_percent)
            
            if max_percent >= 95:
                status = "CRITICAL - SEGERA GANTI"
                color = "red"
            elif max_percent >= 85:
                status = "Warning - Segera Ganti"
                color = "orange"
            elif max_percent >= 70:
                status = "Perhatian - Siapkan Penggantian"
                color = "yellow"
            else:
                status = "Good"
                color = "green"
            
            km_remaining = max(0, (comp['standard_life_km'] - km_since)) if comp['standard_life_km'] > 0 else 0
            months_remaining = max(0, (comp['standard_life_months'] - months_since)) if comp['standard_life_months'] > 0 else 0
            
            next_services.append({
                'component': comp['component_name'],
                'km_used': km_since,
                'km_limit': comp['standard_life_km'],
                'months_used': months_since,
                'months_limit': comp['standard_life_months'],
                'usage_percent': max_percent,
                'status': status,
                'color': color,
                'km_remaining': km_remaining,
                'months_remaining': months_remaining
            })
        
        if len(next_services) > 0:
            health_score = max(0, 100 - sum(s['usage_percent'] for s in next_services) / len(next_services))
        else:
            health_score = 100
        
        if health_score >= 80:
            overall_status = "Sangat Baik"
        elif health_score >= 70:
            overall_status = "Baik"
        elif health_score >= 60:
            overall_status = "Cukup"
        elif health_score >= 50:
            overall_status = "Perlu Perhatian"
        elif health_score >= 40:
            overall_status = "Kritis - Segera Tindak Lanjut"
        else:
            overall_status = "SANGAT KRITIS - STOP OPERASI"
        
        if services.empty:
            overall_status = "Baru - Belum Ada Servis"
            health_score = 100
        
        return {
            "status": overall_status,
            "health_score": health_score,
            "next_services": next_services,
            "current_odometer": current_odometer,
            "months_used": months_used,
            "error": False,
            "maintenance_cost": total_cost,
            "cost_per_km": cost_per_km,
            "service_count": len(services)
        }
        
    except Exception as e:
        logger.error(f"Error in vehicle health analysis: {e}")
        return {
            "status": "Error Analisis",
            "health_score": 0,
            "next_services": [],
            "current_odometer": 0,
            "months_used": 0,
            "error": True,
            "maintenance_cost": 0,
            "cost_per_km": 0
        }

# --- LOGIN PAGE ---
if not st.session_state.authenticated:
    st.title("BPF Asset Management System")
    st.markdown("---")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("### Silakan Login")
        
        with st.form("login_form"):
            username_input = st.text_input("Username", placeholder="Masukkan username")
            password_input = st.text_input("Password", type="password", placeholder="Masukkan password")
            
            col_btn1, col_btn2 = st.columns(2)
            with col_btn1:
                login_submitted = st.form_submit_button("Login", use_container_width=True)
            with col_btn2:
                demo_submitted = st.form_submit_button("Demo Mode", use_container_width=True)
            
            if login_submitted:
                success, message = verify_password(username_input, password_input)
                if success:
                    users = load_users()
                    st.session_state.authenticated = True
                    st.session_state.user_role = users[username_input]["role"]
                    st.session_state.username = username_input
                    st.session_state.db_mode = 'real'
                    initialize_database('real')
                    st.rerun()
                else:
                    st.error(message)
            
            if demo_submitted:
                st.session_state.authenticated = True
                st.session_state.user_role = "viewer"
                st.session_state.username = "demo"
                st.session_state.db_mode = 'demo'
                initialize_database('demo')
                st.rerun()
    
    st.markdown("---")
    with st.expander("Default Credentials (Klik untuk lihat)"):
        st.markdown("""
        **Gunakan kredensial berikut untuk login:**
        
        | Username | Password | Role |
        |----------|----------|------|
        | admin | admin123 | Administrator |
        | teknisi | teknisi123 | Teknisi |
        | manager | manager123 | Manager |
        | demo | demo123 | Viewer |
        """)
    
    st.stop()

# --- MAIN APPLICATION ---

# Database mode indicator
mode_color = "demo" if st.session_state.db_mode == 'demo' else "real"
st.markdown(f"""
    <div class="db-mode-indicator db-mode-{mode_color}">
        Database: {st.session_state.db_mode.upper()}
    </div>
""", unsafe_allow_html=True)

# --- SIDEBAR NAVIGATION ---
with st.sidebar:
    st.markdown("""
    <div style="text-align:center; padding:20px 0;">
        <h2 style="color:white; margin:0;">BPF</h2>
        <p style="color:#CC0000; margin:0;">Asset Management</p>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("---")
    
    st.markdown(f"""
    <div style="background: rgba(255,255,255,0.1); padding: 10px; border-radius: 8px; margin-bottom: 20px;">
        <p style="margin: 0; color: white;">User: {st.session_state.username}</p>
        <p style="margin: 0; color: #aaa; font-size: 0.9em;">Role: {st.session_state.user_role}</p>
    </div>
    """, unsafe_allow_html=True)
    
    if st.session_state.user_role == 'admin':
        st.markdown("### System Settings")
        new_mode = st.selectbox(
            "Database Mode",
            ['real', 'demo'],
            index=0 if st.session_state.db_mode == 'real' else 1,
            help="Real: Production database | Demo: Dummy data for testing"
        )
        if new_mode != st.session_state.db_mode:
            st.session_state.db_mode = new_mode
            initialize_database(new_mode)
            st.rerun()
        st.markdown("---")
    
    menu = st.selectbox("PILIH MODUL", [
        "AI Dashboard", 
        "Manage Master Aset AC", 
        "Input Log SOW AC", 
        "Manage Kendaraan", 
        "Input Servis Kendaraan",
        "Dashboard Kendaraan",
        "Analytics & Reports",
        "Edit/Hapus Data", 
        "Cetak Laporan"
    ])
    
    st.markdown("---")
    
    if st.session_state.db_mode == 'demo':
        st.warning("DEMO MODE - Data yang ditampilkan adalah data dummy untuk demonstrasi.")
    else:
        st.success("PRODUCTION MODE - Menggunakan database real.")
    
    st.markdown("---")
    if st.button("Logout", use_container_width=True):
        logout()
        st.rerun()

# --- MODUL 1: AI DASHBOARD AC ---
if menu == "AI Dashboard":
    st.title("BPF Smart Maintenance Analytics - AC")
    
    assets = db.get_assets(mode=st.session_state.db_mode)
    logs = db.get_all_logs(mode=st.session_state.db_mode)
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Unit AC", len(assets))
    with col2:
        total_logs = len(logs)
        st.metric("Total Log Maintenance", total_logs)
    with col3:
        if not logs.empty:
            avg_health = logs['health_score'].mean()
            st.metric("Rata-rata Health Score", f"{avg_health:.1f}%")
        else:
            st.metric("Rata-rata Health Score", "N/A")
    with col4:
        if not logs.empty:
            logs['tanggal'] = pd.to_datetime(logs['tanggal'])
            recent_logs = logs[logs['tanggal'] > (datetime.now() - timedelta(days=30))]
            st.metric("Log 30 Hari Terakhir", len(recent_logs))
        else:
            st.metric("Log 30 Hari Terakhir", 0)
    
    st.markdown("---")
    
    tab_ai, tab_analytics = st.tabs(["AI Prediksi", "Statistik Lanjutan"])
    
    with tab_ai:
        st.subheader("Estimasi Kerusakan & Kesiapan Unit AC (AI)")
        
        show_anomaly_only = st.checkbox("Tampilkan Hanya Unit dengan Anomali")
        
        assets_list = []
        for _, asset in assets.iterrows():
            as_id = asset['asset_id']
            pred, anomaly, confidence = analyze_predictive_maintenance(as_id, mode=st.session_state.db_mode)
            
            asset_logs = logs[logs['asset_id'] == as_id] if not logs.empty else pd.DataFrame()
            latest_health = asset_logs['health_score'].iloc[-1] if not asset_logs.empty else 100
            
            assets_list.append({
                'asset_id': as_id,
                'prediction': pred,
                'anomaly': anomaly,
                'confidence': confidence,
                'health_score': latest_health,
                'location': asset['lokasi']
            })
        
        if show_anomaly_only:
            assets_list = [a for a in assets_list if 'Anomali' in a['anomaly']]
        
        for i in range(0, len(assets_list), 3):
            cols = st.columns(3)
            for j in range(3):
                if i+j < len(assets_list):
                    asset = assets_list[i+j]
                    with cols[j]:
                        if 'Anomali' in asset['anomaly']:
                            border_color = "#FF6B6B"
                            bg_color = "#FFF5F5"
                        elif asset['health_score'] < 70:
                            border_color = "#FFD93D"
                            bg_color = "#FFFBF0"
                        else:
                            border_color = "#51CF66"
                            bg_color = "#F0FFF4"
                        
                        confidence_stars = "***" if asset['confidence'] > 70 else "**" if asset['confidence'] > 50 else "*"
                        
                        st.markdown(f"""
                        <div style="background:{bg_color}; padding:20px; border-left: 5px solid {border_color}; border-radius:8px; margin-bottom:10px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
                            <div style="display: flex; justify-content: space-between; align-items: center;">
                                <b style="color:#003366; font-size:1.1em;">{asset['asset_id']}</b>
                                <span title="Confidence: {asset['confidence']:.1f}%">{confidence_stars}</span>
                            </div>
                            <p style="margin:5px 0; color:#666; font-size:0.9em;">Lokasi: {asset['location']}</p>
                            <p style="margin:10px 0 5px 0;"><small>Estimasi Servis Besar:</small><br>
                            <b style="color:#CC0000; font-size:1.2em;">{asset['prediction']}</b></p>
                            <p style="margin:5px 0;"><small>Health Score: <b>{asset['health_score']:.0f}%</b></small></p>
                            <p style="margin:5px 0; color:{'#FF6B6B' if 'Anomali' in asset['anomaly'] else '#666'};">
                                <small>Status: {asset['anomaly']}</small>
                            </p>
                        </div>
                        """, unsafe_allow_html=True)
    
    with tab_analytics:
        st.subheader("Analisis Tren & Statistik")
        
        if not logs.empty:
            logs['tanggal'] = pd.to_datetime(logs['tanggal'])
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("### Distribusi Health Score")
                health_bins = [0, 50, 70, 85, 100]
                health_labels = ['Kritis (<50%)', 'Perhatian (50-70%)', 'Baik (70-85%)', 'Sangat Baik (>85%)']
                logs['health_category'] = pd.cut(logs['health_score'], bins=health_bins, labels=health_labels)
                health_dist = logs['health_category'].value_counts()
                st.bar_chart(health_dist)
            
            with col2:
                st.markdown("### Efisiensi (Delta T) per Unit")
                avg_delta_t = logs.groupby('asset_id')['delta_t'].mean().sort_values()
                st.bar_chart(avg_delta_t)

# --- MODUL 2: MANAGE MASTER ASET AC ---
elif menu == "Manage Master Aset AC":
    st.title("Manajemen Spesifikasi Aset AC")
    
    if st.session_state.user_role not in ['admin', 'manager']:
        st.error("Anda tidak memiliki akses untuk mengelola data master.")
        st.stop()
    
    tab_view, tab_add, tab_edit = st.tabs(["View Assets", "Add New Asset", "Edit/Delete Asset"])
    
    with tab_view:
        as_df = db.get_assets(mode=st.session_state.db_mode)
        if not as_df.empty:
            st.dataframe(
                as_df,
                column_config={
                    "asset_id": "Asset ID",
                    "merk": "Merk",
                    "tipe": "Tipe",
                    "kapasitas": "Kapasitas",
                    "lokasi": "Lokasi",
                    "refrigerant": "Refrigerant",
                    "status": "Status"
                },
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info("Belum ada data aset AC")
    
    with tab_add:
        with st.form("add_asset_form"):
            st.markdown("### Tambah Aset AC Baru")
            
            col1, col2 = st.columns(2)
            new_id = col1.text_input("Asset ID*", placeholder="Contoh: AC-16-NEW")
            new_merk = col1.text_input("Merk*", value="Daikin")
            new_tipe = col2.text_input("Tipe*", placeholder="Split Duct / Split Wall")
            new_kap = col2.text_input("Kapasitas*", placeholder="Contoh: 60.000 Btu/h")
            
            col3, col4 = st.columns(2)
            new_lok = col3.text_input("Lokasi*", placeholder="Detail ruangan")
            new_ref = col4.text_input("Refrigerant*", value="R32")
            
            if st.form_submit_button("TAMBAH ASET"):
                if all([new_id, new_merk, new_tipe, new_kap, new_lok, new_ref]):
                    try:
                        db.add_asset((new_id, new_merk, new_tipe, new_kap, new_lok, new_ref), mode=st.session_state.db_mode)
                        st.success(f"Aset {new_id} berhasil ditambahkan!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Gagal menambah aset: {e}")
                else:
                    st.error("Mohon isi semua field yang bertanda *")
    
    with tab_edit:
        as_df = db.get_assets(mode=st.session_state.db_mode)
        if not as_df.empty:
            sel_as = st.selectbox("Pilih Aset AC untuk Edit", as_df['asset_id'].tolist())
            curr = as_df[as_df['asset_id'] == sel_as].iloc[0]
            
            with st.form("edit_as_form"):
                col1, col2 = st.columns(2)
                m_merk = col1.text_input("Merk", value=curr['merk'])
                m_tipe = col1.text_input("Tipe", value=curr['tipe'])
                m_kap = col2.text_input("Kapasitas", value=curr['kapasitas'])
                m_lok = col2.text_input("Detail Lokasi", value=curr['lokasi'])
                m_ref = st.text_input("Refrigerant", value=curr['refrigerant'])
                
                col_btn1, col_btn2 = st.columns(2)
                
                if col_btn1.form_submit_button("UPDATE SPESIFIKASI"):
                    db.update_asset(sel_as, (m_merk, m_tipe, m_kap, m_lok, m_ref), mode=st.session_state.db_mode)
                    st.success("Spesifikasi Berhasil Diperbarui!")
                    st.rerun()
                
                if col_btn2.form_submit_button("HAPUS ASET", type="secondary"):
                    if st.session_state.db_mode == 'real':
                        st.warning("Hapus aset hanya tersedia di production mode dengan konfirmasi")
                        confirm = st.text_input("Ketik 'HAPUS' untuk konfirmasi")
                        if confirm == "HAPUS":
                            db.delete_asset(sel_as, mode=st.session_state.db_mode)
                            st.success("Aset berhasil dihapus!")
                            st.rerun()
                    else:
                        db.delete_asset(sel_as, mode=st.session_state.db_mode)
                        st.success("Aset berhasil dihapus!")
                        st.rerun()

# --- MODUL 3: INPUT LOG SOW AC ---
elif menu == "Input Log SOW AC":
    st.title("Form Servis Berkala AC (SOW BPF)")
    
    if st.session_state.user_role not in ['admin', 'teknisi']:
        st.error("Anda tidak memiliki akses untuk input data maintenance.")
        st.stop()
    
    assets = db.get_assets(mode=st.session_state.db_mode)
    
    if assets.empty:
        st.warning("Belum ada data aset AC. Silakan tambahkan terlebih dahulu.")
    else:
        with st.form("input_log_form", clear_on_submit=True):
            st.markdown("### Informasi Dasar")
            col1, col2 = st.columns(2)
            a_id = col1.selectbox("ID Aset AC*", assets['asset_id'].tolist())
            tek = col1.text_input("Nama Teknisi*", value=st.session_state.username)
            tgl = col2.date_input("Tanggal Pelaksanaan*", datetime.now())
            
            asset_info = assets[assets['asset_id'] == a_id].iloc[0]
            st.info(f"Lokasi: {asset_info['lokasi']} | Kapasitas: {asset_info['kapasitas']}")
            
            st.markdown("---")
            st.markdown("### Parameter Pengukuran")
            
            col3, col4, col5, col6 = st.columns(4)
            v_supply = col3.number_input("Voltase (V)", value=380.0, min_value=0.0, step=1.0)
            amp = col4.number_input("Arus Listrik (A)", min_value=0.0, step=0.1)
            low_p = col5.number_input("Pressure Low (Psi)", value=140.0, min_value=0.0, step=1.0)
            high_p = col6.number_input("Pressure High (Psi)", value=350.0, min_value=0.0, step=1.0)
            
            col7, col8, col9 = st.columns(3)
            t_ret = col7.number_input("Suhu Return (C)*", min_value=0.0, max_value=50.0, step=0.1)
            t_sup = col8.number_input("Suhu Supply (C)*", min_value=0.0, max_value=50.0, step=0.1)
            t_out = col9.number_input("Suhu Outdoor (C)", min_value=0.0, max_value=50.0, step=0.1, value=32.0)
            
            col10, col11 = st.columns(2)
            drain = col10.selectbox("Drainase*", ["Lancar", "Tersumbat", "Perlu Pembersihan"])
            test = col11.selectbox("Status Run*", ["Normal", "Abnormal"])
            
            st.markdown("---")
            st.markdown("### Catatan & Biaya")
            
            col12, col13 = st.columns(2)
            sparepart_cost = col12.number_input("Biaya Sparepart (Rp)", min_value=0, step=50000, value=0)
            catatan = col13.text_area("Catatan LHO / Tindakan yang dilakukan", height=100)
            
            delta_t = t_ret - t_sup if t_ret > t_sup else 0
            
            health_score = 100
            
            if delta_t >= 12:
                health_score -= 0
            elif delta_t >= 10:
                health_score -= 10
            elif delta_t >= 8:
                health_score -= 20
            elif delta_t >= 6:
                health_score -= 35
            else:
                health_score -= 50
            
            if amp > 25:
                health_score -= 20
            elif amp > 20:
                health_score -= 10
            elif amp > 15:
                health_score -= 5
            
            if drain != "Lancar":
                health_score -= 15
            
            if low_p < 130 or low_p > 150:
                health_score -= 10
            
            health_score = max(0, min(100, health_score))
            
            st.markdown("---")
            st.markdown("### Preview Health Score")
            
            col_preview1, col_preview2, col_preview3 = st.columns(3)
            col_preview1.metric("Delta T", f"{delta_t:.1f}C")
            col_preview2.metric("Health Score", f"{health_score}/100")
            
            health_color = "green" if health_score >= 70 else "orange" if health_score >= 50 else "red"
            status_text = "NORMAL" if health_score >= 70 else "PERHATIAN" if health_score >= 50 else "KRITIS"
            col_preview3.markdown(f"**Status:** <span style='color:{health_color};font-weight:bold;'>{status_text}</span>", unsafe_allow_html=True)
            
            st.markdown("---")
            
            if st.form_submit_button("SIMPAN DATA MAINTENANCE", use_container_width=True):
                if all([a_id, tek, t_ret, t_sup]):
                    try:
                        db.add_log((
                            a_id, str(tgl), tek, v_supply, amp, low_p, 
                            t_ret, t_sup, delta_t, drain, test, health_score, 
                            sparepart_cost, catatan
                        ), mode=st.session_state.db_mode)
                        st.success("Laporan Maintenance Berhasil Disimpan!")
                        st.balloons()
                        st.rerun()
                    except Exception as e:
                        st.error(f"Gagal menyimpan data: {e}")
                else:
                    st.error("Mohon isi semua field yang bertanda *")

# --- MODUL 4: MANAGE KENDARAAN ---
elif menu == "Manage Kendaraan":
    st.title("Manajemen Aset Kendaraan Kantor")
    
    if st.session_state.user_role not in ['admin', 'manager']:
        st.error("Anda tidak memiliki akses untuk mengelola data kendaraan.")
        st.stop()
    
    tab_list, tab_add, tab_edit, tab_components = st.tabs(["Daftar Kendaraan", "Tambah Kendaraan", "Edit Kendaraan", "Master Komponen"])
    
    with tab_list:
        vehicles = db.get_vehicles(mode=st.session_state.db_mode)
        if not vehicles.empty:
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Total Kendaraan", len(vehicles))
            col2.metric("Aktif", len(vehicles[vehicles['status'] == 'Aktif']))
            col3.metric("Service", len(vehicles[vehicles['status'] == 'Service']))
            col4.metric("Total Odometer", f"{vehicles['last_odometer'].sum():,} km")
            
            st.markdown("---")
            
            for _, v in vehicles.iterrows():
                health = analyze_vehicle_health(v['vehicle_id'], mode=st.session_state.db_mode)
                
                if health.get('error', False):
                    status_color = "#6c757d"
                    health_score_display = "N/A"
                    status_text = health.get('status', 'Error')
                    bg_color = "#f8f9fa"
                else:
                    health_score = health.get('health_score', 0)
                    if health_score >= 80:
                        status_color = "#28a745"
                        bg_color = "#f0fff4"
                    elif health_score >= 60:
                        status_color = "#ffc107"
                        bg_color = "#fffbf0"
                    else:
                        status_color = "#dc3545"
                        bg_color = "#fff5f5"
                    
                    health_score_display = f"{health_score:.0f}%"
                    status_text = health.get('status', 'Unknown')
                
                status_badge_class = {
                    'Aktif': 'status-good',
                    'Service': 'status-warning',
                    'Nonaktif': 'status-critical'
                }.get(v['status'], 'status-info')
                
                st.markdown(f"""
                <div class="vehicle-card" style="background:{bg_color};">
                    <table style="width:100%;">
                        <tr>
                            <td style="width:50%;">
                                <b style="font-size:1.3em;">{v['vehicle_id']}</b><br>
                                <span style="font-size:1.1em;">{v['brand']} {v['model']} ({v['year']})</span><br>
                                <span style="color:#666;">Plat: {v['plate_number']} | {v['color']} | {v['fuel_type']}</span>
                            </td>
                            <td style="width:25%; text-align:center;">
                                <span style="font-size:0.9em; color:#666;">Odometer</span><br>
                                <b style="font-size:1.2em;">{v['last_odometer']:,} km</b><br>
                                <span class="status-badge {status_badge_class}">{v['status']}</span>
                            </td>
                            <td style="width:25%; text-align:center;">
                                <div style="background:rgba(0,0,0,0.05); border-radius:10px; padding:10px;">
                                    <span style="font-size:0.9em; color:#666;">Health Score</span><br>
                                    <span style="font-size:1.8em; color:{status_color}; font-weight:bold;">{health_score_display}</span><br>
                                    <small style="color:#666;">{status_text}</small>
                                </div>
                            </td>
                        </tr>
                    </table>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("Belum ada data kendaraan. Silakan tambah kendaraan baru.")
    
    with tab_add:
        with st.form("add_vehicle_form"):
            st.markdown("### Informasi Kendaraan")
            
            col1, col2 = st.columns(2)
            vid = col1.text_input("ID Kendaraan*", placeholder="Contoh: VH-006")
            brand = col1.text_input("Merek*", placeholder="Toyota, Honda, dll")
            model = col2.text_input("Model*", placeholder="Innova, CRV, dll")
            year = col2.number_input("Tahun*", min_value=2000, max_value=datetime.now().year + 1, step=1, value=datetime.now().year)
            
            col3, col4 = st.columns(2)
            plate = col3.text_input("Plat Nomor*", placeholder="B 1234 ABC")
            color = col4.text_input("Warna", placeholder="Hitam, Putih, dll")
            
            col5, col6 = st.columns(2)
            fuel = col5.selectbox("Jenis BBM*", ["Bensin", "Solar", "Listrik", "Hybrid"])
            status = col6.selectbox("Status*", ["Aktif", "Nonaktif", "Service"])
            
            col7, col8 = st.columns(2)
            purchase_date = col7.date_input("Tanggal Beli*", datetime.now())
            last_odometer = col8.number_input("Odometer Awal (km)*", min_value=0, step=1000, value=0)
            
            notes = st.text_area("Catatan", placeholder="Informasi tambahan...")
            
            if st.form_submit_button("SIMPAN KENDARAAN", use_container_width=True):
                if all([vid, brand, model, plate, fuel, status]):
                    try:
                        db.add_vehicle((
                            vid, brand, model, year, plate, color, 
                            fuel, status, str(purchase_date), last_odometer, notes
                        ), mode=st.session_state.db_mode)
                        st.success(f"Kendaraan {vid} berhasil ditambahkan!")
                        st.balloons()
                        st.rerun()
                    except Exception as e:
                        st.error(f"Gagal menambah kendaraan: {e}")
                else:
                    st.error("Mohon isi semua field yang bertanda *")
    
    with tab_edit:
        vehicles = db.get_vehicles(mode=st.session_state.db_mode)
        if not vehicles.empty:
            sel_vehicle = st.selectbox("Pilih Kendaraan", vehicles['vehicle_id'].tolist())
            v_data = vehicles[vehicles['vehicle_id'] == sel_vehicle].iloc[0]
            
            with st.form("edit_vehicle_form"):
                st.markdown(f"### Edit Kendaraan: {sel_vehicle}")
                
                col1, col2 = st.columns(2)
                e_brand = col1.text_input("Merek*", value=v_data['brand'])
                e_model = col1.text_input("Model*", value=v_data['model'])
                e_year = col2.number_input("Tahun*", value=int(v_data['year']), min_value=2000)
                e_plate = col2.text_input("Plat Nomor*", value=v_data['plate_number'])
                
                col3, col4 = st.columns(2)
                e_color = col3.text_input("Warna", value=v_data['color'] if v_data['color'] else "")
                
                fuel_options = ["Bensin", "Solar", "Listrik", "Hybrid"]
                e_fuel = col3.selectbox("Jenis BBM*", fuel_options, 
                                       index=fuel_options.index(v_data['fuel_type']) if v_data['fuel_type'] in fuel_options else 0)
                
                status_options = ["Aktif", "Nonaktif", "Service"]
                e_status = col4.selectbox("Status*", status_options,
                                         index=status_options.index(v_data['status']) if v_data['status'] in status_options else 0)
                
                col5, col6 = st.columns(2)
                e_purchase = col5.date_input("Tanggal Beli*", pd.to_datetime(v_data['purchase_date']))
                e_odometer = col6.number_input("Odometer (km)*", value=int(v_data['last_odometer']), min_value=0)
                
                e_notes = st.text_area("Catatan", value=v_data['notes'] if v_data['notes'] else "")
                
                col_btn1, col_btn2 = st.columns(2)
                
                if col_btn1.form_submit_button("UPDATE KENDARAAN"):
                    try:
                        db.update_vehicle(sel_vehicle, (
                            e_brand, e_model, e_year, e_plate, e_color, 
                            e_fuel, e_status, str(e_purchase), e_odometer, e_notes
                        ), mode=st.session_state.db_mode)
                        st.success("Data kendaraan berhasil diupdate!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Gagal update kendaraan: {e}")
                
                if col_btn2.form_submit_button("HAPUS KENDARAAN", type="secondary"):
                    if st.session_state.db_mode == 'real':
                        confirm = st.text_input("Ketik 'HAPUS' untuk konfirmasi")
                        if confirm == "HAPUS":
                            db.delete_vehicle(sel_vehicle, mode=st.session_state.db_mode)
                            st.success("Kendaraan berhasil dihapus!")
                            st.rerun()
                    else:
                        db.delete_vehicle(sel_vehicle, mode=st.session_state.db_mode)
                        st.success("Kendaraan berhasil dihapus!")
                        st.rerun()
    
    with tab_components:
        st.subheader("Master Komponen Kendaraan")
        
        components = db.get_vehicle_components(mode=st.session_state.db_mode)
        
        if not components.empty:
            st.dataframe(
                components[['component_name', 'standard_life_km', 'standard_life_months', 'is_active']],
                column_config={
                    "component_name": "Nama Komponen",
                    "standard_life_km": "Life Time (km)",
                    "standard_life_months": "Life Time (bulan)",
                    "is_active": "Status"
                },
                use_container_width=True,
                hide_index=True
            )
        
        st.markdown("---")
        st.markdown("### Tambah Komponen")
        
        with st.form("component_form"):
            comp_name = st.text_input("Nama Komponen*")
            col1, col2 = st.columns(2)
            life_km = col1.number_input("Standard Life (km)", min_value=0, step=1000, value=0)
            life_months = col2.number_input("Standard Life (bulan)", min_value=0, step=1, value=0)
            is_active = st.checkbox("Aktif", value=True)
            
            if st.form_submit_button("SIMPAN KOMPONEN"):
                if comp_name:
                    try:
                        db.add_vehicle_component((comp_name, life_km, life_months, 1 if is_active else 0), mode=st.session_state.db_mode)
                        st.success(f"Komponen {comp_name} berhasil disimpan!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Gagal menyimpan komponen: {e}")
                else:
                    st.error("Nama komponen harus diisi")

# --- MODUL 5: INPUT SERVIS KENDARAAN ---
elif menu == "Input Servis Kendaraan":
    st.title("Input Servis / Penggantian Komponen Kendaraan")
    
    if st.session_state.user_role not in ['admin', 'teknisi']:
        st.error("Anda tidak memiliki akses untuk input data servis.")
        st.stop()
    
    vehicles = db.get_vehicles(mode=st.session_state.db_mode)
    
    if vehicles.empty:
        st.warning("Belum ada data kendaraan. Silakan tambah kendaraan terlebih dahulu.")
    else:
        active_vehicles = vehicles[vehicles['status'] == 'Aktif']
        if active_vehicles.empty:
            st.warning("Tidak ada kendaraan dengan status Aktif.")
            vehicle_id = st.selectbox("Pilih Kendaraan", vehicles['vehicle_id'].tolist())
        else:
            vehicle_id = st.selectbox("Pilih Kendaraan", active_vehicles['vehicle_id'].tolist())
        
        vehicle_data = vehicles[vehicles['vehicle_id'] == vehicle_id].iloc[0]
        
        col1, col2, col3 = st.columns(3)
        col1.metric("Odometer Saat Ini", f"{vehicle_data['last_odometer']:,} km")
        col2.metric("Merek/Model", f"{vehicle_data['brand']} {vehicle_data['model']}")
        col3.metric("Plat Nomor", vehicle_data['plate_number'])
        
        st.markdown("---")
        
        with st.form("service_form", clear_on_submit=True):
            st.markdown("### Detail Servis")
            
            col1, col2 = st.columns(2)
            service_date = col1.date_input("Tanggal Servis*", datetime.now())
            odometer = col2.number_input("Odometer saat servis (km)*", min_value=0, step=1000, value=int(vehicle_data['last_odometer']))
            
            components = db.get_vehicle_components(mode=st.session_state.db_mode)
            component_list = components['component_name'].tolist()
            component_name = st.selectbox("Komponen yang Diganti*", component_list + ["Lainnya (isi di catatan)"])
            
            col3, col4 = st.columns(2)
            service_type = col3.selectbox("Jenis Servis*", ["Servis Rutin", "Perbaikan", "Penggantian Komponen", "Turun Mesin", "Body Repair", "Lainnya"])
            mechanic = col4.text_input("Nama Montir/Bengkel*", value="Bengkel Resmi")
            
            col5, col6 = st.columns(2)
            cost = col5.number_input("Biaya (Rp)*", min_value=0, step=50000, value=0)
            
            notes = st.text_area("Catatan Servis / Komponen Lainnya", height=100)
            
            if component_name in component_list:
                comp_standard = components[components['component_name'] == component_name].iloc[0]
                life_km = comp_standard['standard_life_km']
                life_months = comp_standard['standard_life_months']
                next_km = odometer + life_km if life_km > 0 else 0
                next_date = service_date + timedelta(days=life_months * 30) if life_months > 0 else None
                
                st.info(f"""
                **Standar Komponen {component_name}:**
                - Penggantian setiap: {life_km:,} km atau {life_months} bulan
                - Servis berikutnya pada odometer: {next_km:,} km
                - Estimasi tanggal servis berikutnya: {next_date.strftime('%d %b %Y') if next_date else 'N/A'}
                """)
            else:
                life_km = 0
                life_months = 0
            
            st.markdown("---")
            
            if st.form_submit_button("SIMPAN SERVIS", use_container_width=True):
                if all([vehicle_id, component_name, service_type, mechanic]):
                    try:
                        db.add_vehicle_service((
                            vehicle_id, str(service_date), odometer, service_type, component_name,
                            life_km, life_months, 0, 0,
                            odometer + life_km if life_km > 0 else 0,
                            life_months, cost, mechanic, notes
                        ), mode=st.session_state.db_mode)
                        
                        if odometer > vehicle_data['last_odometer']:
                            db.update_vehicle_odometer(vehicle_id, odometer, mode=st.session_state.db_mode)
                        
                        st.success("Data servis berhasil disimpan!")
                        st.balloons()
                        st.rerun()
                    except Exception as e:
                        st.error(f"Gagal menyimpan servis: {e}")
                else:
                    st.error("Mohon isi semua field yang bertanda *")

# --- MODUL 6: DASHBOARD KENDARAAN ---
elif menu == "Dashboard Kendaraan":
    st.title("Dashboard Pemeliharaan Kendaraan")
    
    vehicles = db.get_vehicles(mode=st.session_state.db_mode)
    
    if vehicles.empty:
        st.warning("Belum ada data kendaraan.")
    else:
        total_vehicles = len(vehicles)
        active_vehicles = len(vehicles[vehicles['status'] == 'Aktif'])
        total_odometer = vehicles['last_odometer'].sum()
        
        all_services = db.get_vehicle_services(mode=st.session_state.db_mode)
        total_cost = all_services['cost'].sum() if not all_services.empty else 0
        
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Kendaraan", total_vehicles)
        col2.metric("Kendaraan Aktif", active_vehicles)
        col3.metric("Total Odometer", f"{total_odometer:,} km")
        col4.metric("Total Biaya Servis", f"Rp {total_cost:,.0f}")
        
        st.markdown("---")
        
        st.subheader("Status Kesehatan Kendaraan")
        
        health_data = []
        for _, v in vehicles.iterrows():
            health = analyze_vehicle_health(v['vehicle_id'], mode=st.session_state.db_mode)
            if not health.get('error', False):
                health_data.append({
                    'Kendaraan': f"{v['vehicle_id']} - {v['brand']} {v['model']}",
                    'Health Score': health['health_score'],
                    'Status': health['status'],
                    'Odometer': health['current_odometer'],
                    'Usia (bulan)': health['months_used'],
                    'Jumlah Servis': health.get('service_count', 0),
                    'Total Biaya': health.get('maintenance_cost', 0)
                })
        
        if health_data:
            health_df = pd.DataFrame(health_data)
            
            st.dataframe(
                health_df,
                column_config={
                    'Kendaraan': st.column_config.TextColumn('Kendaraan'),
                    'Health Score': st.column_config.ProgressColumn(
                        'Health Score',
                        format="%.0f%%",
                        min_value=0,
                        max_value=100
                    ),
                    'Status': st.column_config.TextColumn('Status'),
                    'Odometer': st.column_config.NumberColumn('Odometer', format="%d km"),
                    'Usia (bulan)': st.column_config.NumberColumn('Usia', format="%d bulan"),
                    'Jumlah Servis': st.column_config.NumberColumn('Servis', format="%d kali"),
                    'Total Biaya': st.column_config.NumberColumn('Total Biaya', format="Rp %.0f")
                },
                use_container_width=True,
                hide_index=True
            )
        
        st.markdown("---")
        
        st.subheader("Analisis Detail per Kendaraan")
        
        selected_vehicle = st.selectbox("Pilih Kendaraan untuk Analisis Detail", vehicles['vehicle_id'].tolist())
        
        if selected_vehicle:
            v_data = vehicles[vehicles['vehicle_id'] == selected_vehicle].iloc[0]
            health = analyze_vehicle_health(selected_vehicle, mode=st.session_state.db_mode)
            
            if not health.get('error', False):
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    health_score = health['health_score']
                    health_color = "green" if health_score >= 80 else "orange" if health_score >= 60 else "red"
                    st.markdown(f"""
                    <div class="metric-card">
                        <h3 style="color:#003366;">Health Score</h3>
                        <p style="font-size:3em; color:{health_color}; margin:10px 0;">{health_score:.0f}%</p>
                        <p>{health['status']}</p>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col2:
                    st.markdown(f"""
                    <div class="metric-card">
                        <h3 style="color:#003366;">Informasi Kendaraan</h3>
                        <p style="font-size:1.2em; margin:10px 0;">{v_data['brand']} {v_data['model']}</p>
                        <p>Odometer: {health['current_odometer']:,} km</p>
                        <p>Usia: {health['months_used']} bulan</p>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col3:
                    cost_per_km = health['cost_per_km']
                    st.markdown(f"""
                    <div class="metric-card">
                        <h3 style="color:#003366;">Biaya Pemeliharaan</h3>
                        <p style="font-size:1.5em; margin:10px 0;">Rp {health['maintenance_cost']:,.0f}</p>
                        <p>Biaya per km: Rp {cost_per_km:,.0f}</p>
                        <p>Jumlah Servis: {health['service_count']} kali</p>
                    </div>
                    """, unsafe_allow_html=True)
                
                st.markdown("---")
                
                st.markdown("### Status Komponen")
                
                component_data = []
                for comp in health['next_services']:
                    status_emoji = "OK" if comp['usage_percent'] < 70 else "WARN" if comp['usage_percent'] < 85 else "CRIT" if comp['usage_percent'] < 95 else "STOP"
                    component_data.append({
                        'Komponen': comp['component'],
                        'Pemakaian': f"{comp['usage_percent']:.0f}%",
                        'Status': f"{status_emoji} {comp['status']}",
                        'KM Tersisa': f"{comp['km_remaining']:,}" if comp['km_limit'] > 0 else "N/A",
                        'Bulan Tersisa': f"{comp['months_remaining']}" if comp['months_limit'] > 0 else "N/A"
                    })
                
                if component_data:
                    comp_df = pd.DataFrame(component_data)
                    st.dataframe(comp_df, use_container_width=True, hide_index=True)
                
                st.markdown("---")
                
                st.markdown("### Riwayat Servis")
                
                services = db.get_vehicle_services(selected_vehicle, mode=st.session_state.db_mode)
                if not services.empty:
                    services['service_date'] = pd.to_datetime(services['service_date'])
                    services = services.sort_values('service_date', ascending=False)
                    
                    st.dataframe(
                        services[['service_date', 'odometer', 'component_name', 'service_type', 'cost', 'mechanic_name']].head(10),
                        column_config={
                            'service_date': 'Tanggal',
                            'odometer': st.column_config.NumberColumn('Odometer', format="%d km"),
                            'component_name': 'Komponen',
                            'service_type': 'Jenis Servis',
                            'cost': st.column_config.NumberColumn('Biaya', format="Rp %.0f"),
                            'mechanic_name': 'Montir/Bengkel'
                        },
                        use_container_width=True,
                        hide_index=True
                    )

# --- MODUL 7: ANALYTICS & REPORTS ---
elif menu == "Analytics & Reports":
    st.title("Analytics & Reports")
    
    tab_ac, tab_vehicle, tab_combined = st.tabs(["AC Analytics", "Vehicle Analytics", "Combined Report"])
    
    with tab_ac:
        st.subheader("Analisis Performa AC")
        
        logs = db.get_all_logs(mode=st.session_state.db_mode)
        
        if not logs.empty:
            logs['tanggal'] = pd.to_datetime(logs['tanggal'])
            min_date = logs['tanggal'].min()
            max_date = logs['tanggal'].max()
            
            col1, col2 = st.columns(2)
            start_date = col1.date_input("Tanggal Mulai", min_date, key="ac_start")
            end_date = col2.date_input("Tanggal Akhir", max_date, key="ac_end")
            
            filtered_logs = logs[(logs['tanggal'] >= pd.Timestamp(start_date)) & 
                                (logs['tanggal'] <= pd.Timestamp(end_date))]
            
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Total Maintenance", len(filtered_logs))
            col2.metric("Rata-rata Health Score", f"{filtered_logs['health_score'].mean():.1f}%")
            col3.metric("Rata-rata Delta T", f"{filtered_logs['delta_t'].mean():.1f} C")
            col4.metric("Total Biaya Sparepart", f"Rp {filtered_logs['sparepart_cost'].sum():,.0f}")
            
            st.markdown("---")
            
            st.markdown("### Tren Performa")
            metric = st.selectbox("Pilih Metrik", ["Health Score", "Delta T", "Arus Listrik"])
            
            if metric == "Health Score":
                data = filtered_logs.pivot_table(index='tanggal', columns='asset_id', values='health_score', aggfunc='mean')
            elif metric == "Delta T":
                data = filtered_logs.pivot_table(index='tanggal', columns='asset_id', values='delta_t', aggfunc='mean')
            else:
                data = filtered_logs.pivot_table(index='tanggal', columns='asset_id', values='amp_kompresor', aggfunc='mean')
            
            st.line_chart(data)
            
            if st.button("Export to CSV (AC)"):
                csv = filtered_logs.to_csv(index=False)
                st.download_button(
                    label="Download CSV",
                    data=csv,
                    file_name=f"ac_report_{start_date}_{end_date}.csv",
                    mime="text/csv"
                )
    
    with tab_vehicle:
        st.subheader("Analisis Performa Kendaraan")
        
        vehicles = db.get_vehicles(mode=st.session_state.db_mode)
        services = db.get_vehicle_services(mode=st.session_state.db_mode)
        
        if not vehicles.empty:
            total_cost = services['cost'].sum() if not services.empty else 0
            
            col1, col2, col3 = st.columns(3)
            col1.metric("Total Biaya Servis", f"Rp {total_cost:,.0f}")
            col2.metric("Total Servis", len(services))
            col3.metric("Rata-rata per Servis", f"Rp {total_cost/len(services):,.0f}" if len(services) > 0 else "Rp 0")
            
            st.markdown("---")
            
            st.markdown("### Analisis Biaya per Kendaraan")
            
            vehicle_costs = []
            for _, v in vehicles.iterrows():
                vehicle_services = services[services['vehicle_id'] == v['vehicle_id']] if not services.empty else pd.DataFrame()
                vehicle_costs.append({
                    'Kendaraan': f"{v['vehicle_id']} - {v['brand']} {v['model']}",
                    'Total Biaya': vehicle_services['cost'].sum() if not vehicle_services.empty else 0,
                    'Jumlah Servis': len(vehicle_services),
                    'Odometer': v['last_odometer']
                })
            
            cost_df = pd.DataFrame(vehicle_costs)
            st.bar_chart(cost_df.set_index('Kendaraan')['Total Biaya'])
            st.dataframe(cost_df, use_container_width=True, hide_index=True)
    
    with tab_combined:
        st.subheader("Laporan Gabungan")
        
        ac_logs = db.get_all_logs(mode=st.session_state.db_mode)
        vehicles = db.get_vehicles(mode=st.session_state.db_mode)
        vehicle_services = db.get_vehicle_services(mode=st.session_state.db_mode)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### Aset AC")
            st.metric("Total Unit", len(db.get_assets(mode=st.session_state.db_mode)))
            st.metric("Total Maintenance", len(ac_logs))
            if not ac_logs.empty:
                st.metric("Rata-rata Health Score", f"{ac_logs['health_score'].mean():.1f}%")
        
        with col2:
            st.markdown("### Aset Kendaraan")
            st.metric("Total Unit", len(vehicles))
            st.metric("Total Servis", len(vehicle_services))
            total_vehicle_cost = vehicle_services['cost'].sum() if not vehicle_services.empty else 0
            st.metric("Total Biaya", f"Rp {total_vehicle_cost:,.0f}")

# --- MODUL 8: EDIT/HAPUS DATA ---
elif menu == "Edit/Hapus Data":
    st.title("Koreksi Data")
    
    if st.session_state.user_role not in ['admin']:
        st.error("Hanya admin yang dapat mengedit/menghapus data.")
        st.stop()
    
    tab_ac, tab_vehicle, tab_bulk = st.tabs(["Hapus Log AC", "Hapus Servis Kendaraan", "Bulk Operations"])
    
    with tab_ac:
        logs = db.get_all_logs(mode=st.session_state.db_mode)
        if not logs.empty:
            st.warning("Hati-hati! Data yang dihapus tidak dapat dikembalikan.")
            
            asset_filter = st.selectbox("Filter by Asset", ["All"] + logs['asset_id'].unique().tolist(), key="ac_filter")
            
            filtered_logs = logs if asset_filter == "All" else logs[logs['asset_id'] == asset_filter]
            
            sel = st.selectbox("Pilih Log AC", 
                              filtered_logs.apply(lambda x: f"ID: {x['id']} - {x['asset_id']} - {x['tanggal']} - Teknisi: {x['teknisi']}", axis=1))
            l_id = int(sel.split(" - ")[0].replace("ID: ", ""))
            
            log_detail = filtered_logs[filtered_logs['id'] == l_id].iloc[0]
            st.json(log_detail.to_dict())
            
            if st.button("HAPUS LOG AC PERMANEN", type="primary"):
                if st.session_state.db_mode == 'real':
                    confirm = st.text_input("Ketik 'HAPUS' untuk konfirmasi", key="ac_confirm")
                    if confirm == "HAPUS":
                        db.delete_log(l_id, mode=st.session_state.db_mode)
                        st.success("Log Terhapus!")
                        st.rerun()
                else:
                    db.delete_log(l_id, mode=st.session_state.db_mode)
                    st.success("Log Terhapus!")
                    st.rerun()
        else:
            st.info("Tidak ada log AC")
    
    with tab_vehicle:
        services = db.get_vehicle_services(mode=st.session_state.db_mode)
        if not services.empty:
            st.warning("Hati-hati! Data yang dihapus tidak dapat dikembalikan.")
            
            vehicle_filter = st.selectbox("Filter by Vehicle", ["All"] + services['vehicle_id'].unique().tolist(), key="vh_filter")
            
            filtered_services = services if vehicle_filter == "All" else services[services['vehicle_id'] == vehicle_filter]
            
            sel = st.selectbox("Pilih Servis Kendaraan", 
                              filtered_services.apply(lambda x: f"ID: {x['id']} - {x['vehicle_id']} - {x['component_name']} - {x['service_date']} - Rp {x['cost']:,.0f}", axis=1))
            s_id = int(sel.split(" - ")[0].replace("ID: ", ""))
            
            service_detail = filtered_services[filtered_services['id'] == s_id].iloc[0]
            st.json(service_detail.to_dict())
            
            if st.button("HAPUS SERVIS KENDARAAN", type="primary"):
                if st.session_state.db_mode == 'real':
                    confirm = st.text_input("Ketik 'HAPUS' untuk konfirmasi", key="vh_confirm")
                    if confirm == "HAPUS":
                        db.delete_vehicle_service(s_id, mode=st.session_state.db_mode)
                        st.success("Servis kendaraan terhapus!")
                        st.rerun()
                else:
                    db.delete_vehicle_service(s_id, mode=st.session_state.db_mode)
                    st.success("Servis kendaraan terhapus!")
                    st.rerun()
        else:
            st.info("Tidak ada data servis kendaraan")
    
    with tab_bulk:
        st.subheader("Bulk Operations")
        st.warning("Operasi bulk akan mempengaruhi banyak data sekaligus. Gunakan dengan hati-hati!")
        
        if st.button("Backup Database"):
            backup_path = db.backup_database(st.session_state.db_mode)
            if backup_path:
                st.success(f"Database dibackup ke: {backup_path}")
            else:
                st.error("Backup gagal")
        
        st.markdown("---")
        st.markdown("### Hapus Log Lama")
        
        days_to_keep = st.number_input("Hapus log lebih lama dari (hari)", min_value=30, value=365)
        
        if st.button("Hapus Log Lama"):
            if st.session_state.db_mode == 'real':
                confirm = st.text_input("Ketik 'HAPUS SEMUA LOG LAMA' untuk konfirmasi", key="bulk_confirm")
                if confirm == "HAPUS SEMUA LOG LAMA":
                    deleted = db.delete_old_logs(days_to_keep, mode=st.session_state.db_mode)
                    st.success(f"{deleted} log berhasil dihapus!")
            else:
                deleted = db.delete_old_logs(days_to_keep, mode=st.session_state.db_mode)
                st.success(f"{deleted} log berhasil dihapus!")

# --- MODUL 9: CETAK LAPORAN ---
elif menu == "Cetak Laporan":
    st.title("Cetak Laporan")
    
    report_type = st.selectbox("Pilih Jenis Laporan", [
        "Laporan Maintenance AC",
        "Laporan Status Kendaraan",
        "Laporan Biaya Servis"
    ])
    
    if report_type == "Laporan Maintenance AC":
        logs = db.get_all_logs(mode=st.session_state.db_mode)
        if not logs.empty:
            logs['tanggal'] = pd.to_datetime(logs['tanggal'])
            
            col1, col2 = st.columns(2)
            asset_filter = col1.selectbox("Pilih Asset", ["Semua"] + logs['asset_id'].unique().tolist(), key="report_ac_asset")
            
            if asset_filter != "Semua":
                logs = logs[logs['asset_id'] == asset_filter]
            
            date_range = col2.selectbox("Periode", ["Semua", "30 Hari Terakhir", "90 Hari Terakhir", "1 Tahun Terakhir"], key="report_ac_date")
            
            if date_range == "30 Hari Terakhir":
                logs = logs[logs['tanggal'] > (datetime.now() - timedelta(days=30))]
            elif date_range == "90 Hari Terakhir":
                logs = logs[logs['tanggal'] > (datetime.now() - timedelta(days=90))]
            elif date_range == "1 Tahun Terakhir":
                logs = logs[logs['tanggal'] > (datetime.now() - timedelta(days=365))]
            
            st.markdown("---")
            st.markdown("### Preview Laporan")
            st.dataframe(
                logs[['tanggal', 'asset_id', 'teknisi', 'delta_t', 'health_score', 'test_run', 'sparepart_cost']].head(20),
                use_container_width=True
            )
            
            st.markdown("---")
            
            if st.button("Generate PDF Report (AC)", type="primary"):
                if not logs.empty:
                    pdf = generate_ac_report_pdf(logs, asset_filter, date_range)
                    filename = f"Laporan_AC_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
                    st.markdown(get_pdf_download_link(pdf, filename), unsafe_allow_html=True)
                    st.success("PDF berhasil dibuat! Klik link di atas untuk download.")
                else:
                    st.warning("Tidak ada data untuk periode yang dipilih.")
        else:
            st.info("Belum ada data maintenance AC")
    
    elif report_type == "Laporan Status Kendaraan":
        vehicles = db.get_vehicles(mode=st.session_state.db_mode)
        if not vehicles.empty:
            sel_v = st.selectbox("Pilih Kendaraan", ["Semua"] + vehicles['vehicle_id'].tolist(), key="report_vh_select")
            
            if sel_v == "Semua":
                vehicles_to_report = vehicles
            else:
                vehicles_to_report = vehicles[vehicles['vehicle_id'] == sel_v]
            
            st.markdown("---")
            st.markdown("### Preview Status Kendaraan")
            
            health_data = {}
            for _, v in vehicles_to_report.iterrows():
                health = analyze_vehicle_health(v['vehicle_id'], mode=st.session_state.db_mode)
                health_data[v['vehicle_id']] = health
            
            preview_data = []
            for _, v in vehicles_to_report.iterrows():
                health = health_data.get(v['vehicle_id'], {})
                preview_data.append({
                    'ID': v['vehicle_id'],
                    'Kendaraan': f"{v['brand']} {v['model']}",
                    'Plat': v['plate_number'],
                    'Odometer': v['last_odometer'],
                    'Status': v['status'],
                    'Health': f"{health.get('health_score', 0):.0f}%" if health else "N/A"
                })
            
            st.dataframe(pd.DataFrame(preview_data), use_container_width=True)
            
            st.markdown("---")
            
            if st.button("Generate PDF Report (Kendaraan)", type="primary"):
                pdf = generate_vehicle_report_pdf(vehicles_to_report, health_data)
                filename = f"Laporan_Kendaraan_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
                st.markdown(get_pdf_download_link(pdf, filename), unsafe_allow_html=True)
                st.success("PDF berhasil dibuat! Klik link di atas untuk download.")
        else:
            st.info("Belum ada data kendaraan")
    
    elif report_type == "Laporan Biaya Servis":
        services = db.get_vehicle_services(mode=st.session_state.db_mode)
        
        if not services.empty:
            services['service_date'] = pd.to_datetime(services['service_date'])
            min_date = services['service_date'].min()
            max_date = services['service_date'].max()
            
            col1, col2 = st.columns(2)
            start_date = col1.date_input("Tanggal Mulai", min_date, key="cost_start")
            end_date = col2.date_input("Tanggal Akhir", max_date, key="cost_end")
            
            filtered_services = services[(services['service_date'] >= pd.Timestamp(start_date)) & 
                                        (services['service_date'] <= pd.Timestamp(end_date))]
            
            total_cost = filtered_services['cost'].sum()
            
            st.markdown("---")
            st.markdown(f"### Total Biaya: Rp {total_cost:,.0f}")
            st.dataframe(
                filtered_services[['service_date', 'vehicle_id', 'component_name', 'service_type', 'cost']].head(20),
                use_container_width=True
            )
            
            st.markdown("---")
            
            if st.button("Export to CSV (Biaya)"):
                csv = filtered_services.to_csv(index=False)
                st.download_button(
                    label="Download CSV",
                    data=csv,
                    file_name=f"biaya_servis_{start_date}_{end_date}.csv",
                    mime="text/csv"
                )

# Footer
st.sidebar.markdown("---")
st.sidebar.markdown(f"""
<div style="text-align:center; color:white; font-size:0.8em;">
    <p>BPF Asset Management System v2.0</p>
    <p>(C) 2024 PT BESTPROFIT FUTURES</p>
    <p>Mode: {st.session_state.db_mode.upper()}</p>
</div>
""", unsafe_allow_html=True)