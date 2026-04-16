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

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Session state initialization
if 'db_mode' not in st.session_state:
    st.session_state.db_mode = 'real'  # Default to real database
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'user_role' not in st.session_state:
    st.session_state.user_role = None

# Inisialisasi database berdasarkan mode
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
            # Generate extensive dummy data for demo
            generate_extensive_dummy_data()
        return True
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        st.error(f"Gagal menginisialisasi database: {e}")
        return False

def generate_extensive_dummy_data():
    """Generate extensive dummy data for demo mode"""
    try:
        # Generate 100+ logs per AC unit (15 units = 1500+ logs)
        db.generate_dummy_ac_logs(logs_per_asset=100)
        # Generate 50+ service logs per vehicle (5 vehicles = 250+ logs)
        db.generate_dummy_vehicle_services(services_per_vehicle=50)
        # Generate additional vehicles for demo
        db.generate_dummy_vehicles(count=15)
        logger.info("Extensive dummy data generated successfully")
    except Exception as e:
        logger.error(f"Failed to generate dummy data: {e}")

# Initialize database on startup
if not initialize_database(st.session_state.db_mode):
    st.stop()

st.set_page_config(
    page_title="BPF Asset Management System",
    page_icon="??",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Authentication System ---
# --- Authentication System ---
def check_password():
    """Returns True if the user has entered correct credentials"""
    
    # Load user credentials from environment or config file
    users = load_users()
    
    # Get username and password from session state
    username = st.session_state.get("username", "")
    password = st.session_state.get("password", "")
    
    if username in users:
        # Hash the input password
        hashed_input = hashlib.sha256(password.encode()).hexdigest()
        if hashed_input == users[username]["password"]:
            st.session_state.authenticated = True
            st.session_state.user_role = users[username]["role"]
            st.session_state.username = username
            # Clear password from session state
            if "password" in st.session_state:
                del st.session_state["password"]
            return True
        else:
            st.error("í ½í¸ Password salah")
            return False
    else:
        if username:  # Only show error if username was entered
            st.error("í ½í¸ Username tidak ditemukan")
        return False

def load_users():
    """Load users from environment variable or config file"""
    users_json = os.environ.get('BPF_USERS')
    if users_json:
        try:
            return json.loads(users_json)
        except:
            pass
    
    # Default users (should be changed in production)
    # Password: admin123, teknisi123, manager123, demo123
    return {
        "admin": {
            "password": "8c6976e5b5410415bde908bd4dee15dfb167a9c873fc4bb8a81f6f2ab448a918",  # admin123
            "role": "admin"
        },
        "teknisi": {
            "password": "6ca13d52ca70c883e0f0bb101e425a89e8624de51db2d2392593af6a84118090",  # teknisi123
            "role": "teknisi"
        },
        "manager": {
            "password": "6b3a55e0261b0304143f805a24924d0c1c44524821305f31d9277843b8a0f49e",  # manager123
            "role": "manager"
        },
        "demo": {
            "password": "2a97516c354b68848cdbd8f54a226a0a55b21ed138e207ad6c5cbb9c00aa5aea",  # demo123
            "role": "viewer"
        }
    }

def logout():
    """Logout user"""
    st.session_state.authenticated = False
    st.session_state.user_role = None
    st.session_state.username = None
    # Clear any other session data
    keys_to_clear = ['password', 'db_mode']
    for key in keys_to_clear:
        if key in st.session_state:
            del st.session_state[key]

# Login form
if not st.session_state.get('authenticated', False):
    st.title("í ½í´ BPF Asset Management System")
    st.markdown("---")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("### Silakan Login")
        
        # Use a form to handle login
        with st.form("login_form"):
            username_input = st.text_input("Username", key="login_username")
            password_input = st.text_input("Password", type="password", key="login_password")
            
            col_login, col_demo = st.columns(2)
            with col_login:
                login_submitted = st.form_submit_button("Login", use_container_width=True)
            with col_demo:
                demo_submitted = st.form_submit_button("Demo Mode", use_container_width=True, type="secondary")
            
            if login_submitted:
                if username_input and password_input:
                    users = load_users()
                    if username_input in users:
                        hashed_input = hashlib.sha256(password_input.encode()).hexdigest()
                        if hashed_input == users[username_input]["password"]:
                            st.session_state.authenticated = True
                            st.session_state.user_role = users[username_input]["role"]
                            st.session_state.username = username_input
                            st.session_state.db_mode = 'real'
                            initialize_database('real')
                            st.rerun()
                        else:
                            st.error("í ½í¸ Password salah")
                    else:
                        st.error("í ½í¸ Username tidak ditemukan")
                else:
                    st.error("Mohon isi username dan password")
            
            if demo_submitted:
                st.session_state.username = "demo"
                st.session_state.authenticated = True
                st.session_state.user_role = "viewer"
                st.session_state.db_mode = 'demo'
                initialize_database('demo')
                st.rerun()
    
    st.markdown("---")
    with st.expander("â¹ï¸ Default Credentials"):
        st.markdown("""
        **Default Credentials:**
        - Admin: `admin` / `admin123`
        - Teknisi: `teknisi` / `teknisi123`
        - Manager: `manager` / `manager123`
        - Demo: `demo` / `demo123`
        """)
    st.stop()

def load_users():
    """Load users from environment variable or config file"""
    users_json = os.environ.get('BPF_USERS')
    if users_json:
        return json.loads(users_json)
    
    # Default users (should be changed in production)
    return {
        "admin": {
            "password": hashlib.sha256("admin123".encode()).hexdigest(),
            "role": "admin"
        },
        "teknisi": {
            "password": hashlib.sha256("teknisi123".encode()).hexdigest(),
            "role": "teknisi"
        },
        "manager": {
            "password": hashlib.sha256("manager123".encode()).hexdigest(),
            "role": "manager"
        },
        "demo": {
            "password": hashlib.sha256("demo123".encode()).hexdigest(),
            "role": "viewer"
        }
    }

def logout():
    """Logout user"""
    st.session_state.authenticated = False
    st.session_state.user_role = None
    st.session_state.username = None

# Login form
if not st.session_state.authenticated:
    st.title("?? BPF Asset Management System")
    st.markdown("---")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("### Silakan Login")
        st.text_input("Username", key="username")
        st.text_input("Password", type="password", key="password")
        
        col_login, col_demo = st.columns(2)
        with col_login:
            st.button("Login", on_click=password_entered, use_container_width=True)
        with col_demo:
            if st.button("Demo Mode", use_container_width=True, type="secondary"):
                st.session_state.username = "demo"
                st.session_state.authenticated = True
                st.session_state.user_role = "viewer"
                st.session_state.db_mode = 'demo'
                initialize_database('demo')
                st.rerun()
    
    st.markdown("---")
    st.markdown("""
    **Default Credentials:**
    - Admin: `admin` / `admin123`
    - Teknisi: `teknisi` / `teknisi123`
    - Manager: `manager` / `manager123`
    - Demo: `demo` / `demo123`
    """)
    st.stop()

# --- UI THEME: RED & BLUE BPF ---
st.markdown("""
    <style>
    .main { background-color: #f0f2f6; }
    
    /* Sidebar styling */
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
    
    /* Button styling */
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
    
    /* Cards for vehicles */
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
    
    /* Metric cards */
    .metric-card {
        background: white;
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        text-align: center;
        border-bottom: 3px solid #003366;
    }
    
    /* Status badges */
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
    
    /* Database mode indicator */
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
    
    /* Formatting untuk PDF Print */
    @media print {
        header, [data-testid="stSidebar"], .stButton, .no-print, .stTabs, .db-mode-indicator { 
            display: none !important; 
        }
        .main { width: 100% !important; padding: 0 !important; }
        .report-header { border-bottom: 3px solid #CC0000; margin-bottom: 20px; }
    }
    
    /* Data table styling */
    .dataframe {
        width: 100%;
        border-collapse: collapse;
    }
    
    .dataframe th {
        background: linear-gradient(135deg, #003366 0%, #002244 100%);
        color: white;
        padding: 12px;
        text-align: left;
    }
    
    .dataframe td {
        padding: 10px;
        border-bottom: 1px solid #e0e0e0;
    }
    
    .dataframe tr:hover {
        background-color: #f5f5f5;
    }
    
    /* Form styling */
    .stTextInput>div>div>input,
    .stSelectbox>div>div>select,
    .stNumberInput>div>div>input {
        border-radius: 8px;
        border: 1px solid #ddd;
    }
    
    /* Tab styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px 8px 0 0;
        padding: 12px 24px;
        background: white;
        border: 1px solid #ddd;
        border-bottom: none;
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #003366 0%, #002244 100%);
        color: white;
    }
    </style>
    """, unsafe_allow_html=True)

# Database mode indicator
mode_color = "demo" if st.session_state.db_mode == 'demo' else "real"
st.markdown(f"""
    <div class="db-mode-indicator db-mode-{mode_color}">
        ??? Database: {st.session_state.db_mode.upper()}
    </div>
""", unsafe_allow_html=True)

# --- FUNGSI AI: PREDICTIVE HEALTH untuk AC ---
def analyze_predictive_maintenance(asset_id, mode='real'):
    """Enhanced predictive maintenance analysis"""
    try:
        logs = db.get_all_logs(mode=mode)
        unit_logs = logs[logs['asset_id'] == asset_id].copy()
        
        if len(unit_logs) < 5:
            return "Data Belum Cukup (Min. 5 log)", "Normal", 0
        
        # Konversi tanggal ke angka (hari sejak awal)
        unit_logs['tgl_dt'] = pd.to_datetime(unit_logs['tanggal'])
        base_date = unit_logs['tgl_dt'].min()
        unit_logs['days'] = (unit_logs['tgl_dt'] - base_date).dt.days
        
        # ML: Regresi Linear Health Score dengan weighted samples
        X = unit_logs[['days']].values
        y = unit_logs['health_score'].values
        
        # Weight recent samples more
        weights = np.linspace(0.5, 1.0, len(y))
        model = LinearRegression()
        model.fit(X, y, sample_weight=weights)
        
        # Confidence score based on RÃÂ²
        confidence = model.score(X, y) * 100
        
        # Prediksi kapan Health Score < 65% (Batas Kritis)
        m = model.coef_[0]
        c = model.intercept_
        
        if m >= 0:
            pred_msg = "Kondisi Stabil/Membaik"
            days_to_fail = None
        else:
            days_to_fail = (65 - c) / m
            if days_to_fail > 0:
                fail_date = base_date + timedelta(days=int(days_to_fail))
                pred_msg = fail_date.strftime('%d %b %Y')
            else:
                pred_msg = "SEGERA - Sudah Kritis!"
        
        # Enhanced Anomaly Detection
        avg_amp = unit_logs['amp_kompresor'].mean()
        std_amp = unit_logs['amp_kompresor'].std()
        last_amp = unit_logs['amp_kompresor'].iloc[-1]
        
        # Multi-factor anomaly detection
        status = "Normal"
        anomaly_score = 0
        
        # Check amperage anomaly
        if std_amp > 0 and last_amp > (avg_amp + 2 * std_amp):
            anomaly_score += 1
            status = "?? Anomali Arus Tinggi"
        
        # Check delta_t degradation
        if len(unit_logs) >= 3:
            recent_delta_t = unit_logs['delta_t'].iloc[-3:].mean()
            historical_delta_t = unit_logs['delta_t'].iloc[:-3].mean()
            if recent_delta_t < historical_delta_t * 0.8:
                anomaly_score += 1
                status = "?? Anomali Efisiensi" if status == "Normal" else "?? Multi Anomali"
        
        # Check pressure anomaly
        avg_pressure = unit_logs['low_p'].mean()
        std_pressure = unit_logs['low_p'].std()
        last_pressure = unit_logs['low_p'].iloc[-1]
        if std_pressure > 0 and abs(last_pressure - avg_pressure) > 2 * std_pressure:
            anomaly_score += 1
            status = "?? Anomali Tekanan" if status == "Normal" else "?? Multi Anomali"
        
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
        
        # Calculate total maintenance cost
        total_cost = services['cost'].sum() if not services.empty else 0
        cost_per_km = total_cost / current_odometer if current_odometer > 0 else 0
        
        # Dapatkan komponen yang perlu diganti
        components = db.get_vehicle_components(mode=mode)
        next_services = []
        
        for _, comp in components.iterrows():
            # Cari servis terakhir untuk komponen ini
            last_service = services[services['component_name'] == comp['component_name']]
            
            if not last_service.empty:
                last_service_date = pd.to_datetime(last_service.iloc[0]['service_date'])
                last_odometer = last_service.iloc[0]['odometer']
                months_since = (current_date.year - last_service_date.year) * 12 + (current_date.month - last_service_date.month)
                km_since = current_odometer - last_odometer
            else:
                months_since = months_used
                km_since = current_odometer
            
            # Hitung persentase usage dengan safety margin
            km_percent = 0
            month_percent = 0
            
            if comp['standard_life_km'] > 0:
                # Add 10% safety margin
                safe_life_km = comp['standard_life_km'] * 0.9
                km_percent = (km_since / safe_life_km * 100)
                km_percent = min(100, km_percent)
            
            if comp['standard_life_months'] > 0:
                # Add 10% safety margin
                safe_life_months = comp['standard_life_months'] * 0.9
                month_percent = (months_since / safe_life_months * 100)
                month_percent = min(100, month_percent)
            
            max_percent = max(km_percent, month_percent)
            
            # Enhanced status with urgency level
            status = "Good"
            color = "green"
            urgency = 0
            
            if max_percent >= 95:
                status = "CRITICAL - SEGERA GANTI"
                color = "red"
                urgency = 3
            elif max_percent >= 85:
                status = "Warning - Segera Ganti"
                color = "orange"
                urgency = 2
            elif max_percent >= 70:
                status = "Perhatian - Siapkan Penggantian"
                color = "yellow"
                urgency = 1
            
            # Calculate remaining life
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
                'urgency': urgency,
                'km_remaining': km_remaining,
                'months_remaining': months_remaining
            })
        
        # Calculate weighted health score
        if len(next_services) > 0:
            # Weight critical components more
            weights = []
            for service in next_services:
                if service['urgency'] == 3:
                    weights.append(0.4)
                elif service['urgency'] == 2:
                    weights.append(0.3)
                elif service['urgency'] == 1:
                    weights.append(0.2)
                else:
                    weights.append(0.1)
            
            weight_sum = sum(weights)
            if weight_sum > 0:
                weighted_usage = sum(s['usage_percent'] * w for s, w in zip(next_services, weights)) / weight_sum
            else:
                weighted_usage = sum(s['usage_percent'] for s in next_services) / len(next_services)
            
            health_score = max(0, 100 - weighted_usage)
        else:
            health_score = 100
        
        # Enhanced overall status
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
        
        # Check if vehicle is new (no service history)
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

# --- SIDEBAR NAVIGATION ---
with st.sidebar:
    st.image("https://via.placeholder.com/200x80/003366/ffffff?text=BPF", width=200)
    st.markdown("---")
    
    # User info
    st.markdown(f"""
    <div style="background: rgba(255,255,255,0.1); padding: 10px; border-radius: 8px; margin-bottom: 20px;">
        <p style="margin: 0; color: white;">?? {st.session_state.username}</p>
        <p style="margin: 0; color: #aaa; font-size: 0.9em;">Role: {st.session_state.user_role}</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Database mode selector (admin only)
    if st.session_state.user_role == 'admin':
        st.markdown("### ?? System Settings")
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
        "?? AI Dashboard", 
        "?? Manage Master Aset AC", 
        "?? Input Log SOW AC", 
        "?? Manage Kendaraan", 
        "?? Input Servis Kendaraan",
        "?? Dashboard Kendaraan",
        "?? Analytics & Reports",
        "??? Edit/Hapus Data", 
        "??? Cetak Laporan"
    ])
    
    st.markdown("---")
    
    # System status
    if st.session_state.db_mode == 'demo':
        st.warning("?? **DEMO MODE**\n\nData yang ditampilkan adalah data dummy untuk demonstrasi.")
    else:
        st.success("? **PRODUCTION MODE**\n\nMenggunakan database real.")
    
    st.markdown("---")
    if st.button("?? Logout", use_container_width=True):
        logout()
        st.rerun()

# --- MODUL 1: AI DASHBOARD AC ---
if menu == "?? AI Dashboard":
    st.title("?? BPF Smart Maintenance Analytics - AC")
    
    # Summary metrics
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
    with col4:
        if not logs.empty:
            recent_logs = logs[pd.to_datetime(logs['tanggal']) > (datetime.now() - timedelta(days=30))]
            st.metric("Log 30 Hari Terakhir", len(recent_logs))
    
    st.markdown("---")
    
    tab_ai, tab_analytics, tab_layout = st.tabs(["?? AI Prediksi", "?? Statistik Lanjutan", "??? Layout Graha Bukopin"])
    
    with tab_ai:
        st.subheader("Estimasi Kerusakan & Kesiapan Unit AC (AI)")
        
        # Filter options
        col_filter1, col_filter2 = st.columns(2)
        with col_filter1:
            show_anomaly_only = st.checkbox("Tampilkan Hanya Unit dengan Anomali")
        with col_filter2:
            sort_by = st.selectbox("Urutkan Berdasarkan", ["Health Score", "Estimasi Servis", "Confidence Score"])
        
        assets_list = []
        for _, asset in assets.iterrows():
            as_id = asset['asset_id']
            pred, anomaly, confidence = analyze_predictive_maintenance(as_id, mode=st.session_state.db_mode)
            
            # Get latest health score
            asset_logs = logs[logs['asset_id'] == as_id]
            latest_health = asset_logs['health_score'].iloc[-1] if not asset_logs.empty else 100
            
            assets_list.append({
                'asset_id': as_id,
                'prediction': pred,
                'anomaly': anomaly,
                'confidence': confidence,
                'health_score': latest_health,
                'location': asset['lokasi']
            })
        
        # Filter and sort
        if show_anomaly_only:
            assets_list = [a for a in assets_list if 'Anomali' in a['anomaly']]
        
        if sort_by == "Health Score":
            assets_list.sort(key=lambda x: x['health_score'])
        elif sort_by == "Confidence Score":
            assets_list.sort(key=lambda x: x['confidence'], reverse=True)
        
        # Display in grid
        for i in range(0, len(assets_list), 3):
            cols = st.columns(3)
            for j in range(3):
                if i+j < len(assets_list):
                    asset = assets_list[i+j]
                    with cols[j]:
                        # Determine color based on health score and anomaly
                        if 'Anomali' in asset['anomaly']:
                            border_color = "#FF6B6B"
                            bg_color = "#FFF5F5"
                        elif asset['health_score'] < 70:
                            border_color = "#FFD93D"
                            bg_color = "#FFFBF0"
                        else:
                            border_color = "#51CF66"
                            bg_color = "#F0FFF4"
                        
                        confidence_indicator = "??" if asset['confidence'] > 70 else "??" if asset['confidence'] > 50 else "??"
                        
                        st.markdown(f"""
                        <div style="background:{bg_color}; padding:20px; border-left: 5px solid {border_color}; border-radius:8px; margin-bottom:10px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
                            <div style="display: flex; justify-content: space-between; align-items: center;">
                                <b style="color:#003366; font-size:1.1em;">{asset['asset_id']}</b>
                                <span title="Confidence: {asset['confidence']:.1f}%">{confidence_indicator}</span>
                            </div>
                            <p style="margin:5px 0; color:#666; font-size:0.9em;">?? {asset['location']}</p>
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
            # Time series analysis
            st.markdown("### Tren Health Score Semua Unit")
            
            # Prepare time series data
            logs['tanggal'] = pd.to_datetime(logs['tanggal'])
            time_series = logs.groupby([pd.Grouper(key='tanggal', freq='W'), 'asset_id'])['health_score'].mean().unstack()
            
            # Add moving average
            for col in time_series.columns:
                time_series[f'{col}_MA'] = time_series[col].rolling(window=3, min_periods=1).mean()
            
            st.line_chart(time_series)
            
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
            
            # Anomaly statistics
            st.markdown("### Statistik Anomali")
            anomaly_stats = logs[logs['test_run'] == 'Abnormal'].groupby('asset_id').size()
            if not anomaly_stats.empty:
                st.bar_chart(anomaly_stats)
            else:
                st.info("Tidak ada data anomali yang tercatat")
        
        else:
            st.info("Belum ada data maintenance untuk analisis")

    with tab_layout:
        st.subheader("Peta Penempatan Unit (Graha Bukopin Lt. 11)")
        c1, c2 = st.columns(2)
        
        # Check for layout images
        layout_indoor = Path("layout_indoor.jpg")
        layout_outdoor = Path("layout_outdoor.jpg")
        
        if layout_indoor.exists(): 
            c1.image("layout_indoor.jpg", caption="Layout Indoor", use_column_width=True)
        else:
            c1.info("Upload gambar layout_indoor.jpg untuk tampilan layout")
            # Show placeholder layout
            c1.markdown("""
            <div style="background:#f0f0f0; padding:50px; text-align:center; border-radius:8px;">
                <p>?? Layout Indoor</p>
                <p style="color:#999;">Gambar tidak tersedia</p>
            </div>
            """, unsafe_allow_html=True)
        
        if layout_outdoor.exists(): 
            c2.image("layout_outdoor.jpg", caption="Layout Outdoor", use_column_width=True)
        else:
            c2.info("Upload gambar layout_outdoor.jpg untuk tampilan layout")
            c2.markdown("""
            <div style="background:#f0f0f0; padding:50px; text-align:center; border-radius:8px;">
                <p>?? Layout Outdoor</p>
                <p style="color:#999;">Gambar tidak tersedia</p>
            </div>
            """, unsafe_allow_html=True)

# --- MODUL 2: MANAGE MASTER ASET AC ---
elif menu == "?? Manage Master Aset AC":
    st.title("?? Manajemen Spesifikasi Aset AC")
    
    # Check permissions
    if st.session_state.user_role not in ['admin', 'manager']:
        st.error("? Anda tidak memiliki akses untuk mengelola data master.")
        st.stop()
    
    tab_view, tab_edit, tab_add = st.tabs(["?? View Assets", "?? Edit Asset", "? Add New Asset"])
    
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
                    "refrigerant": "Refrigerant"
                },
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info("Belum ada data aset AC")
    
    with tab_edit:
        as_df = db.get_assets(mode=st.session_state.db_mode)
        if not as_df.empty:
            sel_as = st.selectbox("Pilih Aset AC untuk Edit Spek", as_df['asset_id'].tolist())
            curr = as_df[as_df['asset_id'] == sel_as].iloc[0]
            
            with st.form("edit_as_form"):
                col1, col2 = st.columns(2)
                m_merk = col1.text_input("Merk", value=curr['merk'])
                m_tipe = col1.text_input("Tipe", value=curr['tipe'])
                m_kap = col2.text_input("Kapasitas", value=curr['kapasitas'])
                m_lok = col2.text_input("Detail Lokasi", value=curr['lokasi'])
                m_ref = st.text_input("Refrigerant", value=curr['refrigerant'])
                
                col_btn1, col_btn2 = st.columns(2)
                
                if col_btn1.form_submit_button("?? UPDATE SPESIFIKASI"):
                    db.update_asset(sel_as, (m_merk, m_tipe, m_kap, m_lok, m_ref), mode=st.session_state.db_mode)
                    st.success("Spesifikasi Berhasil Diperbarui!")
                    st.rerun()
                
                if col_btn2.form_submit_button("??? HAPUS ASET", type="secondary"):
                    if st.session_state.db_mode == 'real':
                        confirm = st.warning("?? Ini akan menghapus semua data maintenance untuk aset ini. Lanjutkan?")
                        if confirm:
                            db.delete_asset(sel_as, mode=st.session_state.db_mode)
                            st.success("Aset berhasil dihapus!")
                            st.rerun()
                    else:
                        st.error("Hapus aset hanya tersedia di production mode")
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
            
            if st.form_submit_button("? TAMBAH ASET"):
                if all([new_id, new_merk, new_tipe, new_kap, new_lok, new_ref]):
                    try:
                        db.add_asset((new_id, new_merk, new_tipe, new_kap, new_lok, new_ref), mode=st.session_state.db_mode)
                        st.success(f"Aset {new_id} berhasil ditambahkan!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Gagal menambah aset: {e}")
                else:
                    st.error("Mohon isi semua field yang bertanda *")

# --- MODUL 3: INPUT LOG SOW AC ---
elif menu == "?? Input Log SOW AC":
    st.title("?? Form Servis Berkala AC (SOW BPF)")
    
    # Check permissions
    if st.session_state.user_role not in ['admin', 'teknisi']:
        st.error("? Anda tidak memiliki akses untuk input data maintenance.")
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
            
            # Show asset info
            asset_info = assets[assets['asset_id'] == a_id].iloc[0]
            st.info(f"?? Lokasi: {asset_info['lokasi']} | Kapasitas: {asset_info['kapasitas']}")
            
            st.markdown("---")
            st.markdown("### ? Parameter Pengukuran")
            
            col3, col4, col5, col6 = st.columns(4)
            v_supply = col3.number_input("Voltase (V)", value=380.0, min_value=0.0, step=1.0)
            amp = col4.number_input("Arus Listrik (A)", min_value=0.0, step=0.1)
            low_p = col5.number_input("Pressure Low (Psi)", value=140.0, min_value=0.0, step=1.0)
            high_p = col6.number_input("Pressure High (Psi)", value=350.0, min_value=0.0, step=1.0)
            
            col7, col8, col9 = st.columns(3)
            t_ret = col7.number_input("Suhu Return (ÃÂ°C)*", min_value=0.0, max_value=50.0, step=0.1)
            t_sup = col8.number_input("Suhu Supply (ÃÂ°C)*", min_value=0.0, max_value=50.0, step=0.1)
            t_out = col9.number_input("Suhu Outdoor (ÃÂ°C)", min_value=0.0, max_value=50.0, step=0.1, value=32.0)
            
            col10, col11 = st.columns(2)
            drain = col10.selectbox("Drainase*", ["Lancar", "Tersumbat", "Perlu Pembersihan"])
            test = col11.selectbox("Status Run*", ["Normal", "Abnormal"])
            
            st.markdown("---")
            st.markdown("### ?? Catatan & Biaya")
            
            col12, col13 = st.columns(2)
            sparepart_cost = col12.number_input("Biaya Sparepart (Rp)", min_value=0, step=50000, value=0)
            catatan = col13.text_area("Catatan LHO / Tindakan yang dilakukan", height=100)
            
            # Calculate delta T
            delta_t = t_ret - t_sup if t_ret > t_sup else 0
            
            # Auto-calculate health score based on multiple parameters
            health_score = 100
            
            # Delta T scoring (most important)
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
            
            # Amperage scoring
            if amp > 25:
                health_score -= 20
            elif amp > 20:
                health_score -= 10
            elif amp > 15:
                health_score -= 5
            
            # Drainage scoring
            if drain != "Lancar":
                health_score -= 15
            
            # Pressure scoring
            if low_p < 130 or low_p > 150:
                health_score -= 10
            
            health_score = max(0, min(100, health_score))
            
            st.markdown("---")
            st.markdown("### ?? Preview Health Score")
            
            col_preview1, col_preview2, col_preview3 = st.columns(3)
            col_preview1.metric("Delta T", f"{delta_t:.1f}ÃÂ°C", delta=f"{'Baik' if delta_t >= 10 else 'Perlu Perhatian'}")
            col_preview2.metric("Health Score", f"{health_score}/100")
            
            health_color = "green" if health_score >= 70 else "orange" if health_score >= 50 else "red"
            col_preview3.markdown(f"**Status:** <span style='color:{health_color};font-weight:bold;'>{'NORMAL' if health_score >= 70 else 'PERHATIAN' if health_score >= 50 else 'KRITIS'}</span>", unsafe_allow_html=True)
            
            st.markdown("---")
            
            if st.form_submit_button("?? SIMPAN DATA MAINTENANCE", use_container_width=True):
                if all([a_id, tek, t_ret, t_sup]):
                    try:
                        db.add_log((
                            a_id, str(tgl), tek, v_supply, amp, low_p, 
                            t_ret, t_sup, delta_t, drain, test, health_score, 
                            sparepart_cost, catatan
                        ), mode=st.session_state.db_mode)
                        st.success("? Laporan Maintenance Berhasil Disimpan!")
                        st.balloons()
                        st.rerun()
                    except Exception as e:
                        st.error(f"Gagal menyimpan data: {e}")
                else:
                    st.error("Mohon isi semua field yang bertanda *")

# --- MODUL 4: MANAGE KENDARAAN ---
elif menu == "?? Manage Kendaraan":
    st.title("?? Manajemen Aset Kendaraan Kantor")
    
    # Check permissions
    if st.session_state.user_role not in ['admin', 'manager']:
        st.error("? Anda tidak memiliki akses untuk mengelola data kendaraan.")
        st.stop()
    
    tab_list, tab_add, tab_edit, tab_components = st.tabs([
        "?? Daftar Kendaraan", 
        "? Tambah Kendaraan", 
        "?? Edit/Hapus Kendaraan",
        "?? Master Komponen"
    ])
    
    with tab_list:
        vehicles = db.get_vehicles(mode=st.session_state.db_mode)
        if not vehicles.empty:
            # Summary metrics
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Total Kendaraan", len(vehicles))
            col2.metric("Aktif", len(vehicles[vehicles['status'] == 'Aktif']))
            col3.metric("Service", len(vehicles[vehicles['status'] == 'Service']))
            col4.metric("Total Odometer", f"{vehicles['last_odometer'].sum():,} km")
            
            st.markdown("---")
            
            # Filter
            status_filter = st.multiselect(
                "Filter Status",
                vehicles['status'].unique().tolist(),
                default=['Aktif']
            )
            
            if status_filter:
                vehicles = vehicles[vehicles['status'].isin(status_filter)]
            
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
                
                # Status badge
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
                                <div style="display: flex; align-items: center; gap: 10px;">
                                    <div>
                                        <b style="font-size:1.3em;">{v['vehicle_id']}</b><br>
                                        <span style="font-size:1.1em;">{v['brand']} {v['model']} ({v['year']})</span><br>
                                        <span style="color:#666;">?? Plat: {v['plate_number']} | ?? {v['color']} | ? {v['fuel_type']}</span>
                                    </div>
                                </div>
                            </td>
                            <td style="width:25%;">
                                <div style="text-align:center;">
                                    <span style="font-size:0.9em; color:#666;">Odometer</span><br>
                                    <b style="font-size:1.2em;">{v['last_odometer']:,} km</b><br>
                                    <span class="status-badge {status_badge_class}">{v['status']}</span>
                                </div>
                            </td>
                            <td style="width:25%;">
                                <div style="background:rgba(0,0,0,0.05); border-radius:10px; padding:10px; text-align:center;">
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
            
            st.markdown("---")
            
            if st.form_submit_button("?? SIMPAN KENDARAAN", use_container_width=True):
                if all([vid, brand, model, plate, fuel, status]):
                    try:
                        db.add_vehicle((
                            vid, brand, model, year, plate, color, 
                            fuel, status, str(purchase_date), last_odometer, notes
                        ), mode=st.session_state.db_mode)
                        st.success(f"? Kendaraan {vid} berhasil ditambahkan!")
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
                e_year = col2.number_input("Tahun*", value=int(v_data['year']), min_value=2000, max_value=datetime.now().year + 1)
                e_plate = col2.text_input("Plat Nomor*", value=v_data['plate_number'])
                
                col3, col4 = st.columns(2)
                e_color = col3.text_input("Warna", value=v_data['color'] if v_data['color'] else "")
                e_fuel = col3.selectbox("Jenis BBM*", ["Bensin", "Solar", "Listrik", "Hybrid"], 
                                       index=["Bensin", "Solar", "Listrik", "Hybrid"].index(v_data['fuel_type']) if v_data['fuel_type'] in ["Bensin", "Solar", "Listrik", "Hybrid"] else 0)
                e_status = col4.selectbox("Status*", ["Aktif", "Nonaktif", "Service"],
                                         index=["Aktif", "Nonaktif", "Service"].index(v_data['status']) if v_data['status'] in ["Aktif", "Nonaktif", "Service"] else 0)
                
                col5, col6 = st.columns(2)
                e_purchase = col5.date_input("Tanggal Beli*", pd.to_datetime(v_data['purchase_date']))
                e_odometer = col6.number_input("Odometer (km)*", value=int(v_data['last_odometer']), min_value=0)
                
                e_notes = st.text_area("Catatan", value=v_data['notes'] if v_data['notes'] else "")
                
                col_btn1, col_btn2 = st.columns(2)
                
                if col_btn1.form_submit_button("?? UPDATE KENDARAAN", use_container_width=True):
                    try:
                        db.update_vehicle(sel_vehicle, (
                            e_brand, e_model, e_year, e_plate, e_color, 
                            e_fuel, e_status, str(e_purchase), e_odometer, e_notes
                        ), mode=st.session_state.db_mode)
                        st.success("? Data kendaraan berhasil diupdate!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Gagal update kendaraan: {e}")
                
                if col_btn2.form_submit_button("??? HAPUS KENDARAAN", type="secondary", use_container_width=True):
                    if st.session_state.db_mode == 'real':
                        st.error("?? Hapus kendaraan akan menghapus semua data servis. Konfirmasi diperlukan.")
                        confirm = st.checkbox("Saya yakin ingin menghapus kendaraan ini")
                        if confirm:
                            db.delete_vehicle(sel_vehicle, mode=st.session_state.db_mode)
                            st.success("? Kendaraan berhasil dihapus!")
                            st.rerun()
                    else:
                        db.delete_vehicle(sel_vehicle, mode=st.session_state.db_mode)
                        st.success("? Kendaraan berhasil dihapus!")
                        st.rerun()
        else:
            st.info("Belum ada data kendaraan untuk diedit.")
    
    with tab_components:
        st.subheader("?? Master Komponen Kendaraan")
        
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
        st.markdown("### Tambah/Edit Komponen")
        
        with st.form("component_form"):
            comp_name = st.text_input("Nama Komponen*")
            col1, col2 = st.columns(2)
            life_km = col1.number_input("Standard Life (km)", min_value=0, step=1000, value=0, help="0 jika tidak berdasarkan jarak")
            life_months = col2.number_input("Standard Life (bulan)", min_value=0, step=1, value=0, help="0 jika tidak berdasarkan waktu")
            is_active = st.checkbox("Aktif", value=True)
            
            if st.form_submit_button("?? SIMPAN KOMPONEN"):
                if comp_name:
                    try:
                        db.add_vehicle_component((comp_name, life_km, life_months, 1 if is_active else 0), mode=st.session_state.db_mode)
                        st.success(f"? Komponen {comp_name} berhasil disimpan!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Gagal menyimpan komponen: {e}")
                else:
                    st.error("Nama komponen harus diisi")

# --- MODUL 5: INPUT SERVIS KENDARAAN ---
elif menu == "?? Input Servis Kendaraan":
    st.title("?? Input Servis / Penggantian Komponen Kendaraan")
    
    # Check permissions
    if st.session_state.user_role not in ['admin', 'teknisi']:
        st.error("? Anda tidak memiliki akses untuk input data servis.")
        st.stop()
    
    vehicles = db.get_vehicles(mode=st.session_state.db_mode)
    
    if vehicles.empty:
        st.warning("Belum ada data kendaraan. Silakan tambah kendaraan terlebih dahulu.")
    else:
        # Filter hanya kendaraan aktif
        active_vehicles = vehicles[vehicles['status'] == 'Aktif']
        if active_vehicles.empty:
            st.warning("Tidak ada kendaraan dengan status Aktif.")
            vehicle_id = st.selectbox("Pilih Kendaraan", vehicles['vehicle_id'].tolist())
        else:
            vehicle_id = st.selectbox("Pilih Kendaraan", active_vehicles['vehicle_id'].tolist())
        
        vehicle_data = vehicles[vehicles['vehicle_id'] == vehicle_id].iloc[0]
        
        # Show vehicle summary
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
            next_service_reminder = col6.checkbox("Set reminder servis berikutnya", value=True)
            
            notes = st.text_area("Catatan Servis / Komponen Lainnya", height=100)
            
            # Auto-calculate next service based on component standard
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
            
            if st.form_submit_button("?? SIMPAN SERVIS", use_container_width=True):
                if all([vehicle_id, component_name, service_type, mechanic]):
                    try:
                        db.add_vehicle_service((
                            vehicle_id, str(service_date), odometer, service_type, component_name,
                            life_km, life_months, 0, 0,
                            odometer + life_km if life_km > 0 else 0,
                            life_months, cost, mechanic, notes
                        ), mode=st.session_state.db_mode)
                        
                        # Update vehicle odometer
                        if odometer > vehicle_data['last_odometer']:
                            db.update_vehicle_odometer(vehicle_id, odometer, mode=st.session_state.db_mode)
                        
                        st.success("? Data servis berhasil disimpan!")
                        st.balloons()
                        st.rerun()
                    except Exception as e:
                        st.error(f"Gagal menyimpan servis: {e}")
                else:
                    st.error("Mohon isi semua field yang bertanda *")

# --- MODUL 6: DASHBOARD KENDARAAN ---
elif menu == "?? Dashboard Kendaraan":
    st.title("?? Dashboard Pemeliharaan Kendaraan")
    
    vehicles = db.get_vehicles(mode=st.session_state.db_mode)
    
    if vehicles.empty:
        st.warning("Belum ada data kendaraan.")
    else:
        # Summary Stats
        total_vehicles = len(vehicles)
        active_vehicles = len(vehicles[vehicles['status'] == 'Aktif'])
        total_odometer = vehicles['last_odometer'].sum()
        
        # Calculate total maintenance cost
        all_services = db.get_vehicle_services(mode=st.session_state.db_mode)
        total_cost = all_services['cost'].sum() if not all_services.empty else 0
        
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Kendaraan", total_vehicles)
        col2.metric("Kendaraan Aktif", active_vehicles)
        col3.metric("Total Odometer", f"{total_odometer:,} km")
        col4.metric("Total Biaya Servis", f"Rp {total_cost:,.0f}")
        
        st.markdown("---")
        
        # Vehicle health overview
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
            
            # Health score distribution
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("### Distribusi Health Score")
                health_bins = [0, 50, 70, 85, 100]
                health_labels = ['Kritis (<50%)', 'Perhatian (50-70%)', 'Baik (70-85%)', 'Sangat Baik (>85%)']
                health_df['Kategori'] = pd.cut(health_df['Health Score'], bins=health_bins, labels=health_labels)
                health_dist = health_df['Kategori'].value_counts()
                st.bar_chart(health_dist)
            
            with col2:
                st.markdown("### Biaya Servis per Kendaraan")
                cost_data = health_df.set_index('Kendaraan')['Total Biaya']
                st.bar_chart(cost_data)
            
            st.markdown("---")
            st.markdown("### Detail per Kendaraan")
            
            # Filter
            status_filter = st.multiselect(
                "Filter Status Kendaraan",
                health_df['Status'].unique().tolist(),
                default=health_df['Status'].unique().tolist()
            )
            
            filtered_df = health_df[health_df['Status'].isin(status_filter)]
            
            st.dataframe(
                filtered_df,
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
        
        # Detailed analysis per vehicle
        st.subheader("Analisis Detail per Kendaraan")
        
        selected_vehicle = st.selectbox(
            "Pilih Kendaraan untuk Analisis Detail",
            vehicles['vehicle_id'].tolist()
        )
        
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
                
                # Component status
                st.markdown("### Status Komponen")
                
                component_data = []
                for comp in health['next_services']:
                    status_emoji = "??" if comp['usage_percent'] < 70 else "??" if comp['usage_percent'] < 85 else "??" if comp['usage_percent'] < 95 else "?"
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
                
                # Service history
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
                    
                    # Cost trend
                    st.markdown("#### Tren Biaya Servis")
                    cost_trend = services.groupby(services['service_date'].dt.to_period('M'))['cost'].sum()
                    st.line_chart(cost_trend)
                else:
                    st.info("Belum ada riwayat servis")

# --- MODUL 7: ANALYTICS & REPORTS ---
elif menu == "?? Analytics & Reports":
    st.title("?? Analytics & Reports")
    
    tab_ac, tab_vehicle, tab_combined = st.tabs(["?? AC Analytics", "?? Vehicle Analytics", "?? Combined Report"])
    
    with tab_ac:
        st.subheader("Analisis Performa AC")
        
        logs = db.get_all_logs(mode=st.session_state.db_mode)
        
        if not logs.empty:
            # Date range filter
            col1, col2 = st.columns(2)
            logs['tanggal'] = pd.to_datetime(logs['tanggal'])
            min_date = logs['tanggal'].min()
            max_date = logs['tanggal'].max()
            
            start_date = col1.date_input("Tanggal Mulai", min_date)
            end_date = col2.date_input("Tanggal Akhir", max_date)
            
            filtered_logs = logs[(logs['tanggal'] >= pd.Timestamp(start_date)) & 
                                (logs['tanggal'] <= pd.Timestamp(end_date))]
            
            # Key metrics
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Total Maintenance", len(filtered_logs))
            col2.metric("Rata-rata Health Score", f"{filtered_logs['health_score'].mean():.1f}%")
            col3.metric("Rata-rata Delta T", f"{filtered_logs['delta_t'].mean():.1f}ÃÂ°C")
            col4.metric("Total Biaya Sparepart", f"Rp {filtered_logs['sparepart_cost'].sum():,.0f}")
            
            st.markdown("---")
            
            # Performance trends
            st.markdown("### Tren Performa")
            
            metric = st.selectbox("Pilih Metrik", ["Health Score", "Delta T", "Arus Listrik"])
            
            if metric == "Health Score":
                data = filtered_logs.pivot_table(index='tanggal', columns='asset_id', values='health_score', aggfunc='mean')
                title = "Tren Health Score"
            elif metric == "Delta T":
                data = filtered_logs.pivot_table(index='tanggal', columns='asset_id', values='delta_t', aggfunc='mean')
                title = "Tren Efisiensi (Delta T)"
            else:
                data = filtered_logs.pivot_table(index='tanggal', columns='asset_id', values='amp_kompresor', aggfunc='mean')
                title = "Tren Arus Listrik"
            
            st.line_chart(data)
            
            # Export option
            if st.button("?? Export to CSV"):
                csv = filtered_logs.to_csv(index=False)
                st.download_button(
                    label="Download CSV",
                    data=csv,
                    file_name=f"ac_report_{start_date}_{end_date}.csv",
                    mime="text/csv"
                )
        else:
            st.info("Belum ada data maintenance AC")
    
    with tab_vehicle:
        st.subheader("Analisis Performa Kendaraan")
        
        vehicles = db.get_vehicles(mode=st.session_state.db_mode)
        services = db.get_vehicle_services(mode=st.session_state.db_mode)
        
        if not vehicles.empty:
            # Summary metrics
            total_cost = services['cost'].sum() if not services.empty else 0
            avg_cost_per_vehicle = total_cost / len(vehicles) if len(vehicles) > 0 else 0
            
            col1, col2, col3 = st.columns(3)
            col1.metric("Total Biaya Servis", f"Rp {total_cost:,.0f}")
            col2.metric("Rata-rata per Kendaraan", f"Rp {avg_cost_per_vehicle:,.0f}")
            col3.metric("Total Servis", len(services))
            
            st.markdown("---")
            
            # Cost analysis
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
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.bar_chart(cost_df.set_index('Kendaraan')['Total Biaya'])
            
            with col2:
                st.dataframe(cost_df, use_container_width=True, hide_index=True)
            
            st.markdown("---")
            
            # Service frequency
            if not services.empty:
                st.markdown("### Frekuensi Servis")
                services['service_date'] = pd.to_datetime(services['service_date'])
                services['month'] = services['service_date'].dt.to_period('M')
                service_freq = services.groupby('month').size()
                st.line_chart(service_freq)
    
    with tab_combined:
        st.subheader("Laporan Gabungan")
        
        st.info("Fitur laporan gabungan akan menampilkan ringkasan semua aset (AC dan Kendaraan) dalam satu laporan.")
        
        # Summary all assets
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
            st.metric("Total Biaya", f"Rp {vehicle_services['cost'].sum():,.0f}" if not vehicle_services.empty else "Rp 0")

# --- MODUL 8: EDIT/HAPUS DATA ---
elif menu == "??? Edit/Hapus Data":
    st.title("??? Koreksi Data")
    
    # Check permissions
    if st.session_state.user_role not in ['admin']:
        st.error("? Hanya admin yang dapat mengedit/menghapus data.")
        st.stop()
    
    tab_ac, tab_vehicle, tab_bulk = st.tabs(["??? Hapus Log AC", "??? Hapus Servis Kendaraan", "?? Bulk Operations"])
    
    with tab_ac:
        logs = db.get_all_logs(mode=st.session_state.db_mode)
        if not logs.empty:
            st.warning("?? Hati-hati! Data yang dihapus tidak dapat dikembalikan.")
            
            # Filter options
            asset_filter = st.selectbox("Filter by Asset", ["All"] + logs['asset_id'].unique().tolist())
            
            if asset_filter != "All":
                logs = logs[logs['asset_id'] == asset_filter]
            
            sel = st.selectbox("Pilih Log AC", logs.apply(lambda x: f"ID: {x['id']} - {x['asset_id']} - {x['tanggal']} - Teknisi: {x['teknisi']}", axis=1))
            l_id = int(sel.split(" - ")[0].replace("ID: ", ""))
            
            # Show log details
            log_detail = logs[logs['id'] == l_id].iloc[0]
            st.json(log_detail.to_dict())
            
            if st.button("??? HAPUS LOG AC PERMANEN", type="primary"):
                if st.session_state.db_mode == 'real':
                    confirm = st.text_input("Ketik 'HAPUS' untuk konfirmasi")
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
            st.warning("?? Hati-hati! Data yang dihapus tidak dapat dikembalikan.")
            
            vehicle_filter = st.selectbox("Filter by Vehicle", ["All"] + services['vehicle_id'].unique().tolist())
            
            if vehicle_filter != "All":
                services = services[services['vehicle_id'] == vehicle_filter]
            
            sel = st.selectbox("Pilih Servis Kendaraan", 
                              services.apply(lambda x: f"ID: {x['id']} - {x['vehicle_id']} - {x['component_name']} - {x['service_date']} - Rp {x['cost']:,.0f}", axis=1))
            s_id = int(sel.split(" - ")[0].replace("ID: ", ""))
            
            # Show service details
            service_detail = services[services['id'] == s_id].iloc[0]
            st.json(service_detail.to_dict())
            
            if st.button("??? HAPUS SERVIS KENDARAAN", type="primary"):
                if st.session_state.db_mode == 'real':
                    confirm = st.text_input("Ketik 'HAPUS' untuk konfirmasi")
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
        st.warning("?? Operasi bulk akan mempengaruhi banyak data sekaligus. Gunakan dengan hati-hati!")
        
        # Backup database
        if st.button("?? Backup Database"):
            import shutil
            from datetime import datetime
            
            backup_path = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
            db_path = db.get_db_path(st.session_state.db_mode)
            
            shutil.copy(db_path, backup_path)
            st.success(f"Database dibackup ke: {backup_path}")
        
        # Clear old logs
        st.markdown("---")
        st.markdown("### Hapus Log Lama")
        
        days_to_keep = st.number_input("Hapus log lebih lama dari (hari)", min_value=30, value=365)
        
        if st.button("??? Hapus Log Lama"):
            if st.session_state.db_mode == 'real':
                confirm = st.text_input("Ketik 'HAPUS SEMUA LOG LAMA' untuk konfirmasi")
                if confirm == "HAPUS SEMUA LOG LAMA":
                    deleted = db.delete_old_logs(days_to_keep, mode=st.session_state.db_mode)
                    st.success(f"{deleted} log berhasil dihapus!")
            else:
                deleted = db.delete_old_logs(days_to_keep, mode=st.session_state.db_mode)
                st.success(f"{deleted} log berhasil dihapus!")

# --- MODUL 9: CETAK LAPORAN ---
elif menu == "??? Cetak Laporan":
    st.title("??? Preview Laporan Cetak")
    
    report_type = st.selectbox("Pilih Jenis Laporan", [
        "Laporan Maintenance AC",
        "Laporan Status Kendaraan",
        "Laporan Biaya Servis",
        "Laporan Semua Aset"
    ])
    
    if report_type == "Laporan Maintenance AC":
        logs = db.get_all_logs(mode=st.session_state.db_mode)
        if not logs.empty:
            # Filter options
            col1, col2 = st.columns(2)
            asset_filter = col1.selectbox("Pilih Asset", ["Semua"] + logs['asset_id'].unique().tolist())
            
            if asset_filter != "Semua":
                logs = logs[logs['asset_id'] == asset_filter]
            
            # Date filter
            logs['tanggal'] = pd.to_datetime(logs['tanggal'])
            date_range = col2.selectbox("Periode", ["Semua", "30 Hari Terakhir", "90 Hari Terakhir", "1 Tahun Terakhir"])
            
            if date_range == "30 Hari Terakhir":
                logs = logs[logs['tanggal'] > (datetime.now() - timedelta(days=30))]
            elif date_range == "90 Hari Terakhir":
                logs = logs[logs['tanggal'] > (datetime.now() - timedelta(days=90))]
            elif date_range == "1 Tahun Terakhir":
                logs = logs[logs['tanggal'] > (datetime.now() - timedelta(days=365))]
            
            st.markdown("---")
            
            # Report header
            st.markdown(f"""
            <div style="border: 2px solid #003366; padding: 25px; background: white;" class="report-container">
                <div style="text-align:center; border-bottom: 2px solid #CC0000; padding-bottom:10px;" class="report-header">
                    <h2 style="color:#003366; margin:0;">PT BESTPROFIT FUTURES SURABAYA</h2>
                    <p style="margin:5px; font-weight:bold;">LAPORAN MAINTENANCE AC</p>
                    <p style="margin:5px;">Periode: {date_range} | Asset: {asset_filter}</p>
                    <p style="margin:5px;">Tanggal Cetak: {datetime.now().strftime('%d %B %Y %H:%M')}</p>
                </div>
                
                <div style="margin-top:20px;">
                    <h4>Ringkasan:</h4>
                    <table style="width:100%;">
                        <tr>
                            <td>Total Maintenance: {len(logs)} log</td>
                            <td>Rata-rata Health Score: {logs['health_score'].mean():.1f}%</td>
                        </tr>
                        <tr>
                            <td>Total Biaya Sparepart: Rp {logs['sparepart_cost'].sum():,.0f}</td>
                            <td>Rata-rata Delta T: {logs['delta_t'].mean():.1f}ÃÂ°C</td>
                        </tr>
                    </table>
                </div>
                
                <hr>
                
                <h4>Detail Maintenance:</h4>
                <table style="width:100%; border-collapse: collapse;" class="data-table">
                    <thead>
                        <tr style="background:#003366; color:white;">
                            <th style="padding:8px;">Tanggal</th>
                            <th style="padding:8px;">Asset ID</th>
                            <th style="padding:8px;">Teknisi</th>
                            <th style="padding:8px;">Delta T</th>
                            <th style="padding:8px;">Health Score</th>
                            <th style="padding:8px;">Status</th>
                        </tr>
                    </thead>
                    <tbody>
            """, unsafe_allow_html=True)
            
            for _, row in logs.iterrows():
                status_color = "green" if row['health_score'] >= 70 else "orange" if row['health_score'] >= 50 else "red"
                st.markdown(f"""
                        <tr>
                            <td style="padding:8px;">{row['tanggal'].strftime('%d/%m/%Y')}</td>
                            <td style="padding:8px;">{row['asset_id']}</td>
                            <td style="padding:8px;">{row['teknisi']}</td>
                            <td style="padding:8px;">{row['delta_t']:.1f}ÃÂ°C</td>
                            <td style="padding:8px; color:{status_color}; font-weight:bold;">{row['health_score']}%</td>
                            <td style="padding:8px;">{row['test_run']}</td>
                        </tr>
                """, unsafe_allow_html=True)
            
            st.markdown("""
                    </tbody>
                </table>
                
                <hr>
                
                <div style="margin-top:30px; display:flex; justify-content:space-between;">
                    <div>
                        <p>Mengetahui,</p>
                        <br><br>
                        <p>_________________</p>
                        <p>Manager Operasional</p>
                    </div>
                    <div>
                        <p>Dibuat oleh,</p>
                        <br><br>
                        <p>_________________</p>
                        <p>Teknisi</p>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            st.info("?? Tekan Ctrl+P untuk menyimpan sebagai PDF.")
            
            # Export option
            if st.button("?? Download as HTML"):
                html_content = st.markdown("")
                st.download_button(
                    label="Download HTML",
                    data=html_content,
                    file_name=f"laporan_ac_{datetime.now().strftime('%Y%m%d')}.html",
                    mime="text/html"
                )
        else:
            st.info("Belum ada data maintenance AC")
    
    elif report_type == "Laporan Status Kendaraan":
        vehicles = db.get_vehicles(mode=st.session_state.db_mode)
        if not vehicles.empty:
            sel_v = st.selectbox("Pilih Kendaraan", ["Semua"] + vehicles['vehicle_id'].tolist())
            
            if sel_v == "Semua":
                vehicles_to_report = vehicles
            else:
                vehicles_to_report = vehicles[vehicles['vehicle_id'] == sel_v]
            
            st.markdown(f"""
            <div style="border: 2px solid #003366; padding: 25px; background: white;" class="report-container">
                <div style="text-align:center; border-bottom: 2px solid #CC0000; padding-bottom:10px;" class="report-header">
                    <h2 style="color:#003366; margin:0;">PT BESTPROFIT FUTURES SURABAYA</h2>
                    <p style="margin:5px; font-weight:bold;">LAPORAN STATUS KENDARAAN</p>
                    <p style="margin:5px;">Tanggal Cetak: {datetime.now().strftime('%d %B %Y %H:%M')}</p>
                </div>
            """, unsafe_allow_html=True)
            
            for _, v in vehicles_to_report.iterrows():
                health = analyze_vehicle_health(v['vehicle_id'], mode=st.session_state.db_mode)
                
                health_score = health.get('health_score', 0) if not health.get('error', False) else 0
                status_color = "green" if health_score >= 80 else "orange" if health_score >= 60 else "red"
                
                st.markdown(f"""
                <div style="margin-top:20px;">
                    <h4 style="color:#003366;">{v['vehicle_id']} - {v['brand']} {v['model']}</h4>
                    <table style="width:100%;">
                        <tr>
                            <td><b>Plat Nomor:</b> {v['plate_number']}</td>
                            <td><b>Tahun:</b> {v['year']}</td>
                        </tr>
                        <tr>
                            <td><b>Odometer:</b> {v['last_odometer']:,} km</td>
                            <td><b>Health Score:</b> <span style="color:{status_color}; font-weight:bold;">{health_score:.0f}%</span></td>
                        </tr>
                        <tr>
                            <td><b>Status:</b> {v['status']}</td>
                            <td><b>Kondisi:</b> {health.get('status', 'N/A')}</td>
                        </tr>
                    </table>
                    
                    <h5>Status Komponen:</h5>
                    <table style="width:100%; border-collapse: collapse;">
                        <thead>
                            <tr style="background:#003366; color:white;">
                                <th style="padding:5px;">Komponen</th>
                                <th style="padding:5px;">Pemakaian</th>
                                <th style="padding:5px;">Status</th>
                            </tr>
                        </thead>
                        <tbody>
                """, unsafe_allow_html=True)
                
                for comp in health.get('next_services', []):
                    usage = comp['usage_percent']
                    comp_color = "red" if usage >= 90 else "orange" if usage >= 75 else "green"
                    st.markdown(f"""
                            <tr>
                                <td style="padding:5px;">{comp['component']}</td>
                                <td style="padding:5px;">{usage:.0f}%</td>
                                <td style="padding:5px; color:{comp_color};">{comp['status']}</td>
                            </tr>
                    """, unsafe_allow_html=True)
                
                st.markdown("""
                        </tbody>
                    </table>
                </div>
                <hr>
                """, unsafe_allow_html=True)
            
            st.markdown("""
                <div style="margin-top:30px; display:flex; justify-content:space-between;">
                    <div>
                        <p>Mengetahui,</p>
                        <br><br>
                        <p>_________________</p>
                        <p>Manager Fleet</p>
                    </div>
                    <div>
                        <p>Dibuat oleh,</p>
                        <br><br>
                        <p>_________________</p>
                        <p>Staff Maintenance</p>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            st.info("?? Tekan Ctrl+P untuk menyimpan sebagai PDF.")
        else:
            st.info("Belum ada data kendaraan")
    
    elif report_type == "Laporan Biaya Servis":
        services = db.get_vehicle_services(mode=st.session_state.db_mode)
        
        if not services.empty:
            # Date filter
            services['service_date'] = pd.to_datetime(services['service_date'])
            min_date = services['service_date'].min()
            max_date = services['service_date'].max()
            
            col1, col2 = st.columns(2)
            start_date = col1.date_input("Tanggal Mulai", min_date)
            end_date = col2.date_input("Tanggal Akhir", max_date)
            
            filtered_services = services[(services['service_date'] >= pd.Timestamp(start_date)) & 
                                        (services['service_date'] <= pd.Timestamp(end_date))]
            
            total_cost = filtered_services['cost'].sum()
            
            st.markdown(f"""
            <div style="border: 2px solid #003366; padding: 25px; background: white;" class="report-container">
                <div style="text-align:center; border-bottom: 2px solid #CC0000; padding-bottom:10px;" class="report-header">
                    <h2 style="color:#003366; margin:0;">PT BESTPROFIT FUTURES SURABAYA</h2>
                    <p style="margin:5px; font-weight:bold;">LAPORAN BIAYA SERVIS KENDARAAN</p>
                    <p style="margin:5px;">Periode: {start_date.strftime('%d %B %Y')} - {end_date.strftime('%d %B %Y')}</p>
                </div>
                
                <div style="margin-top:20px;">
                    <h4>Ringkasan:</h4>
                    <table style="width:100%;">
                        <tr>
                            <td><b>Total Servis:</b> {len(filtered_services)} kali</td>
                            <td><b>Total Biaya:</b> Rp {total_cost:,.0f}</td>
                        </tr>
                        <tr>
                            <td><b>Rata-rata Biaya per Servis:</b> Rp {(total_cost/len(filtered_services) if len(filtered_services) > 0 else 0):,.0f}</td>
                            <td></td>
                        </tr>
                    </table>
                </div>
                
                <hr>
                
                <h4>Detail Biaya Servis:</h4>
                <table style="width:100%; border-collapse: collapse;">
                    <thead>
                        <tr style="background:#003366; color:white;">
                            <th style="padding:8px;">Tanggal</th>
                            <th style="padding:8px;">Kendaraan</th>
                            <th style="padding:8px;">Komponen</th>
                            <th style="padding:8px;">Jenis Servis</th>
                            <th style="padding:8px;">Biaya</th>
                        </tr>
                    </thead>
                    <tbody>
            """, unsafe_allow_html=True)
            
            for _, row in filtered_services.sort_values('service_date', ascending=False).iterrows():
                st.markdown(f"""
                        <tr>
                            <td style="padding:8px;">{row['service_date'].strftime('%d/%m/%Y')}</td>
                            <td style="padding:8px;">{row['vehicle_id']}</td>
                            <td style="padding:8px;">{row['component_name']}</td>
                            <td style="padding:8px;">{row['service_type']}</td>
                            <td style="padding:8px; text-align:right;">Rp {row['cost']:,.0f}</td>
                        </tr>
                """, unsafe_allow_html=True)
            
            st.markdown(f"""
                    </tbody>
                    <tfoot>
                        <tr style="background:#f0f0f0; font-weight:bold;">
                            <td colspan="4" style="padding:8px; text-align:right;">TOTAL:</td>
                            <td style="padding:8px; text-align:right;">Rp {total_cost:,.0f}</td>
                        </tr>
                    </tfoot>
                </table>
                
                <hr>
                
                <div style="margin-top:30px; display:flex; justify-content:space-between;">
                    <div>
                        <p>Mengetahui,</p>
                        <br><br>
                        <p>_________________</p>
                        <p>Manager Keuangan</p>
                    </div>
                    <div>
                        <p>Dibuat oleh,</p>
                        <br><br>
                        <p>_________________</p>
                        <p>Staff Maintenance</p>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            st.info("?? Tekan Ctrl+P untuk menyimpan sebagai PDF.")
        else:
            st.info("Belum ada data servis kendaraan")
    
    else:  # Laporan Semua Aset
        st.info("Fitur laporan komprehensif sedang dalam pengembangan")

# Footer
st.sidebar.markdown("---")
st.sidebar.markdown(f"""
<div style="text-align:center; color:white; font-size:0.8em;">
    <p>BPF Asset Management System v2.0</p>
    <p>ÃÂ© 2024 PT BESTPROFIT FUTURES</p>
    <p>Mode: {st.session_state.db_mode.upper()}</p>
</div>
""", unsafe_allow_html=True)