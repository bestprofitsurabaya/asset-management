import streamlit as st
import database_engine as db
import pandas as pd
import numpy as np
import os
from datetime import datetime, timedelta
from sklearn.linear_model import LinearRegression

# Inisialisasi
db.create_db()
db.init_bpf_assets()
db.init_vehicle_components()
db.init_sample_vehicles()

st.set_page_config(page_title="BPF Asset Management System", layout="wide")

# --- UI THEME: RED & BLUE BPF ---
st.markdown("""
    <style>
    .main { background-color: #f0f2f6; }
    
    /* Perbaikan untuk sidebar - hanya styling background, tidak mengganggu teks */
    [data-testid="stSidebar"] { 
        background-color: #003366 !important; 
    }
    
    /* Biarkan teks sidebar menggunakan warna default Streamlit */
    [data-testid="stSidebar"] .stSelectbox label,
    [data-testid="stSidebar"] .stSelectbox div,
    [data-testid="stSidebar"] .stMarkdown {
        color: white !important;
    }
    
    /* Style untuk button */
    .stButton>button { 
        background-color: #CC0000; 
        color: white; 
        border-radius: 8px; 
        width: 100%; 
        height: 50px; 
        font-weight: bold; 
        border: none; 
    }
    .stButton>button:hover { 
        background-color: #990000; 
        color: white; 
    }
    
    /* Cards for vehicles */
    .vehicle-card {
        background: white;
        padding: 15px;
        border-radius: 10px;
        border-left: 5px solid #CC0000;
        margin-bottom: 10px;
        box-shadow: 2px 2px 5px rgba(0,0,0,0.1);
    }
    
    /* Formatting untuk PDF Print */
    @media print {
        header, [data-testid="stSidebar"], .stButton, .no-print, .stTabs { display: none !important; }
        .main { width: 100% !important; padding: 0 !important; }
        .report-header { border-bottom: 3px solid #CC0000; margin-bottom: 20px; }
    }
    
    /* Pastikan teks di selectbox terbaca */
    .stSelectbox div[data-baseweb="select"] {
        color: black !important;
    }
    
    .stSelectbox div[data-baseweb="select"] div {
        color: black !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- FUNGSI AI: PREDICTIVE HEALTH untuk AC ---
def analyze_predictive_maintenance(asset_id):
    logs = db.get_all_logs()
    unit_logs = logs[logs['asset_id'] == asset_id].copy()
    
    if len(unit_logs) < 2:
        return "Data Belum Cukup", "Normal"

    # Konversi tanggal ke angka (hari sejak awal)
    unit_logs['tgl_dt'] = pd.to_datetime(unit_logs['tanggal'])
    base_date = unit_logs['tgl_dt'].min()
    unit_logs['days'] = (unit_logs['tgl_dt'] - base_date).dt.days
    
    # ML: Regresi Linear Health Score
    X = unit_logs[['days']].values
    y = unit_logs['health_score'].values
    model = LinearRegression().fit(X, y)
    
    # Prediksi kapan Health Score < 65% (Batas Kritis)
    m = model.coef_[0]
    c = model.intercept_
    
    if m >= 0:
        pred_msg = "Kondisi Stabil/Membaik"
    else:
        days_to_fail = (65 - c) / m
        fail_date = base_date + timedelta(days=int(days_to_fail))
        pred_msg = fail_date.strftime('%d %b %Y')

    # Anomali Detection (Z-Score Amperage)
    avg_amp = unit_logs['amp_kompresor'].mean()
    last_amp = unit_logs['amp_kompresor'].iloc[-1]
    status = "Normal"
    if last_amp > (avg_amp * 1.25):
        status = "⚠️ Anomali Arus Tinggi"
    
    return pred_msg, status

# --- FUNGSI PREDICTIVE UNTUK KENDARAAN ---
def analyze_vehicle_health(vehicle_id):
    services = db.get_vehicle_services(vehicle_id)
    
    # Jika belum ada data servis sama sekali
    if services.empty:
        vehicle = db.get_vehicles()
        if not vehicle.empty:
            vehicle_data = vehicle[vehicle['vehicle_id'] == vehicle_id]
            if not vehicle_data.empty:
                vehicle_data = vehicle_data.iloc[0]
                purchase_date = pd.to_datetime(vehicle_data['purchase_date'])
                current_date = datetime.now()
                months_used = (current_date.year - purchase_date.year) * 12 + (current_date.month - purchase_date.month)
                
                return {
                    "status": "Belum Ada Data Servis",
                    "health_score": 100,
                    "next_services": [],
                    "current_odometer": vehicle_data['last_odometer'],
                    "months_used": months_used,
                    "error": False
                }
    
    vehicle = db.get_vehicles()
    if vehicle.empty:
        return {
            "status": "Data Kendaraan Tidak Ditemukan",
            "health_score": 0,
            "next_services": [],
            "current_odometer": 0,
            "months_used": 0,
            "error": True
        }
    
    vehicle_data = vehicle[vehicle['vehicle_id'] == vehicle_id]
    if vehicle_data.empty:
        return {
            "status": "Data Kendaraan Tidak Ditemukan",
            "health_score": 0,
            "next_services": [],
            "current_odometer": 0,
            "months_used": 0,
            "error": True
        }
    
    vehicle_data = vehicle_data.iloc[0]
    current_odometer = vehicle_data['last_odometer']
    purchase_date = pd.to_datetime(vehicle_data['purchase_date'])
    current_date = datetime.now()
    months_used = (current_date.year - purchase_date.year) * 12 + (current_date.month - purchase_date.month)
    
    # Dapatkan komponen yang perlu diganti
    components = db.get_vehicle_components()
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
        
        # Hitung persentase usage
        km_percent = 0
        month_percent = 0
        
        if comp['standard_life_km'] > 0:
            km_percent = (km_since / comp['standard_life_km'] * 100)
            km_percent = min(100, km_percent)
        
        if comp['standard_life_months'] > 0:
            month_percent = (months_since / comp['standard_life_months'] * 100)
            month_percent = min(100, month_percent)
        
        max_percent = max(km_percent, month_percent)
        
        status = "Good"
        color = "green"
        if max_percent >= 90:
            status = "CRITICAL - Segera Ganti"
            color = "red"
        elif max_percent >= 75:
            status = "Warning - Persiapan Ganti"
            color = "orange"
        
        next_services.append({
            'component': comp['component_name'],
            'km_used': km_since,
            'km_limit': comp['standard_life_km'],
            'months_used': months_since,
            'months_limit': comp['standard_life_months'],
            'usage_percent': max_percent,
            'status': status,
            'color': color
        })
    
    # Hitung health score overall
    if len(next_services) > 0:
        avg_usage = sum([s['usage_percent'] for s in next_services]) / len(next_services)
        health_score = max(0, 100 - avg_usage)
    else:
        health_score = 100
    
    # Tentukan status keseluruhan
    if health_score >= 70:
        overall_status = "Baik"
    elif health_score >= 50:
        overall_status = "Perlu Perhatian"
    else:
        overall_status = "Kritis - Segera Tindak Lanjut"
    
    return {
        "status": overall_status,
        "health_score": health_score,
        "next_services": next_services,
        "current_odometer": current_odometer,
        "months_used": months_used,
        "error": False
    }

# --- SIDEBAR NAVIGATION ---
menu = st.sidebar.selectbox("PILIH MODUL", [
    "📊 AI Dashboard", 
    "⚙️ Manage Master Aset AC", 
    "📝 Input Log SOW AC", 
    "🚗 Manage Kendaraan", 
    "🔧 Input Servis Kendaraan",
    "📊 Dashboard Kendaraan",
    "🛠️ Edit/Hapus Data", 
    "🖨️ Cetak Laporan"
])

# --- MODUL 1: AI DASHBOARD AC ---
if menu == "📊 AI Dashboard":
    st.title("🤖 BPF Smart Maintenance Analytics - AC")
    
    tab_ai, tab_layout = st.tabs(["💡 AI Prediksi & Statistik", "🗺️ Layout Graha Bukopin"])
    
    with tab_ai:
        assets = db.get_assets()
        logs = db.get_all_logs()
        
        st.subheader("Estimasi Kerusakan & Kesiapan Unit AC (AI)")
        for i in range(0, len(assets), 3):
            cols = st.columns(3)
            for j in range(3):
                if i+j < len(assets):
                    as_id = assets.iloc[i+j]['asset_id']
                    pred, anomaly = analyze_predictive_maintenance(as_id)
                    with cols[j]:
                        st.markdown(f"""
                        <div style="background:white; padding:15px; border-left: 5px solid #003366; border-radius:5px; margin-bottom:10px; box-shadow: 2px 2px 5px rgba(0,0,0,0.1);">
                            <b style="color:#003366;">{as_id}</b><br>
                            <small>Estimasi Servis Besar:</small><br>
                            <b style="color:#CC0000; font-size:1.1em;">{pred}</b><br>
                            <small style="color:gray;">Status: {anomaly}</small>
                        </div>
                        """, unsafe_allow_html=True)
        
        if not logs.empty:
            st.divider()
            st.subheader("Tren Efisiensi (Delta T) Seluruh Unit")
            st.line_chart(logs.pivot(index='tanggal', columns='asset_id', values='delta_t'))

    with tab_layout:
        st.subheader("Peta Penempatan Unit (Graha Bukopin Lt. 11)")
        c1, c2 = st.columns(2)
        if os.path.exists("layout_indoor.jpg"): 
            c1.image("layout_indoor.jpg", caption="Layout Indoor")
        else:
            c1.info("Upload gambar layout_indoor.jpg untuk tampilan layout")
        if os.path.exists("layout_outdoor.jpg"): 
            c2.image("layout_outdoor.jpg", caption="Layout Outdoor")
        else:
            c2.info("Upload gambar layout_outdoor.jpg untuk tampilan layout")

# --- MODUL 2: MANAGE MASTER ASET AC ---
elif menu == "⚙️ Manage Master Aset AC":
    st.title("⚙️ Manajemen Spesifikasi Aset AC")
    as_df = db.get_assets()
    sel_as = st.selectbox("Pilih Aset AC untuk Edit Spek", as_df['asset_id'].tolist())
    curr = as_df[as_df['asset_id'] == sel_as].iloc[0]
    
    with st.form("edit_as_form"):
        col1, col2 = st.columns(2)
        m_merk = col1.text_input("Merk", value=curr['merk'])
        m_tipe = col1.text_input("Tipe", value=curr['tipe'])
        m_kap = col2.text_input("Kapasitas", value=curr['kapasitas'])
        m_lok = col2.text_input("Detail Lokasi", value=curr['lokasi'])
        m_ref = st.text_input("Refrigerant", value=curr['refrigerant'])
        
        if st.form_submit_button("💾 UPDATE SPESIFIKASI"):
            db.update_asset(sel_as, (m_merk, m_tipe, m_kap, m_lok, m_ref))
            st.success("Spesifikasi Berhasil Diperbarui!")
            st.rerun()

# --- MODUL 3: INPUT LOG SOW AC ---
elif menu == "📝 Input Log SOW AC":
    st.title("📝 Form Servis Berkala AC (SOW BPF)")
    assets = db.get_assets()
    with st.form("input_log_form", clear_on_submit=True):
        a_id = st.selectbox("ID Aset AC", assets['asset_id'].tolist())
        c1, c2 = st.columns(2)
        tek = c1.text_input("Nama Teknisi")
        tgl = c2.date_input("Tanggal Pelaksanaan")
        
        st.markdown("### ⚡ Parameter Pengukuran")
        c3, c4, c5, c6 = st.columns(4)
        v = c3.number_input("Voltase (V)", value=380.0)
        amp = c4.number_input("Arus Listrik (A)")
        low_p = c5.number_input("Pressure Low (Psi)", value=140.0)
        t_ret = c6.number_input("Suhu Return (°C)")
        
        c7, c8 = st.columns(2)
        t_sup = c7.number_input("Suhu Supply (°C)")
        drain = c8.selectbox("Drainase", ["Lancar", "Tersumbat"])
        
        test = st.selectbox("Status Run", ["Normal", "Abnormal"])
        catatan = st.text_area("Catatan LHO")

        if st.form_submit_button("🚀 SIMPAN DATA"):
            dt = t_ret - t_sup
            # Heuristic Score: Delta T ideal > 10C
            score = 100 if dt >= 10 and drain == "Lancar" else 65
            db.add_log((a_id, str(tgl), tek, v, amp, low_p, t_ret, t_sup, dt, drain, test, score, 0, catatan))
            st.success("Laporan Berhasil Disimpan!")
            st.rerun()

# --- MODUL 4: MANAGE KENDARAAN ---
elif menu == "🚗 Manage Kendaraan":
    st.title("🚗 Manajemen Aset Kendaraan Kantor")
    
    tab_list, tab_add, tab_edit = st.tabs(["📋 Daftar Kendaraan", "➕ Tambah Kendaraan", "✏️ Edit/Hapus Kendaraan"])
    
    with tab_list:
        vehicles = db.get_vehicles()
        if not vehicles.empty:
            for _, v in vehicles.iterrows():
                health = analyze_vehicle_health(v['vehicle_id'])
                
                # Cek error
                if health.get('error', False):
                    status_color = "#6c757d"
                    health_score_display = "N/A"
                    status_text = health.get('status', 'Error')
                else:
                    health_score = health.get('health_score', 0)
                    status_color = "#28a745" if health_score > 70 else "#ffc107" if health_score > 50 else "#dc3545"
                    health_score_display = f"{health_score:.0f}%"
                    status_text = health.get('status', 'Unknown')
                
                st.markdown(f"""
                <div class="vehicle-card">
                    <table style="width:100%;">
                        <tr>
                            <td style="width:60%;">
                                <b style="font-size:1.2em;">{v['vehicle_id']} - {v['brand']} {v['model']}</b><br>
                                <small>Plat: {v['plate_number']} | Tahun: {v['year']} | Warna: {v['color']}</small><br>
                                <small>Odometer: {v['last_odometer']:,} km | Status: {v['status']}</small>
                            </td>
                            <td style="width:40%; text-align:right;">
                                <div style="background:#f0f0f0; border-radius:10px; padding:5px;">
                                    <b>Health Score</b><br>
                                    <span style="font-size:1.5em; color:{status_color}; font-weight:bold;">{health_score_display}</span><br>
                                    <small>{status_text}</small>
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
            col1, col2 = st.columns(2)
            vid = col1.text_input("ID Kendaraan*", placeholder="Contoh: VH-006")
            brand = col1.text_input("Merek*")
            model = col1.text_input("Model*")
            year = col2.number_input("Tahun*", min_value=2000, max_value=2026, step=1)
            plate = col2.text_input("Plat Nomor*")
            color = col2.text_input("Warna")
            
            col3, col4 = st.columns(2)
            fuel = col3.selectbox("Jenis BBM", ["Bensin", "Solar", "Listrik", "Hybrid"])
            status = col3.selectbox("Status", ["Aktif", "Nonaktif", "Service"])
            purchase_date = col4.date_input("Tanggal Beli", datetime.now())
            last_odometer = col4.number_input("Odometer Terakhir (km)", min_value=0, step=1000)
            
            notes = st.text_area("Catatan")
            
            if st.form_submit_button("💾 SIMPAN KENDARAAN"):
                if vid and brand and model and plate:
                    db.add_vehicle((vid, brand, model, year, plate, color, fuel, status, str(purchase_date), last_odometer, notes))
                    st.success(f"Kendaraan {vid} berhasil ditambahkan!")
                    st.rerun()
                else:
                    st.error("Mohon isi field yang bertanda *")
    
    with tab_edit:
        vehicles = db.get_vehicles()
        if not vehicles.empty:
            sel_vehicle = st.selectbox("Pilih Kendaraan", vehicles['vehicle_id'].tolist())
            v_data = vehicles[vehicles['vehicle_id'] == sel_vehicle].iloc[0]
            
            with st.form("edit_vehicle_form"):
                col1, col2 = st.columns(2)
                e_brand = col1.text_input("Merek", value=v_data['brand'])
                e_model = col1.text_input("Model", value=v_data['model'])
                e_year = col2.number_input("Tahun", value=int(v_data['year']), min_value=2000, max_value=2026)
                e_plate = col2.text_input("Plat Nomor", value=v_data['plate_number'])
                e_color = col2.text_input("Warna", value=v_data['color'] if v_data['color'] else "")
                
                col3, col4 = st.columns(2)
                e_fuel = col3.selectbox("Jenis BBM", ["Bensin", "Solar", "Listrik", "Hybrid"], 
                                       index=["Bensin", "Solar", "Listrik", "Hybrid"].index(v_data['fuel_type']))
                e_status = col3.selectbox("Status", ["Aktif", "Nonaktif", "Service"],
                                         index=["Aktif", "Nonaktif", "Service"].index(v_data['status']))
                e_purchase = col4.date_input("Tanggal Beli", pd.to_datetime(v_data['purchase_date']))
                e_odometer = col4.number_input("Odometer (km)", value=int(v_data['last_odometer']), min_value=0)
                
                e_notes = st.text_area("Catatan", value=v_data['notes'] if v_data['notes'] else "")
                
                col_btn1, col_btn2 = st.columns(2)
                if col_btn1.form_submit_button("✏️ UPDATE"):
                    db.update_vehicle(sel_vehicle, (e_brand, e_model, e_year, e_plate, e_color, e_fuel, e_status, str(e_purchase), e_odometer, e_notes))
                    st.success("Data kendaraan berhasil diupdate!")
                    st.rerun()
                
                if col_btn2.form_submit_button("🗑️ HAPUS", type="secondary"):
                    db.delete_vehicle(sel_vehicle)
                    st.success("Kendaraan berhasil dihapus!")
                    st.rerun()
        else:
            st.info("Belum ada data kendaraan untuk diedit.")

# --- MODUL 5: INPUT SERVIS KENDARAAN ---
elif menu == "🔧 Input Servis Kendaraan":
    st.title("🔧 Input Servis / Penggantian Komponen Kendaraan")
    
    vehicles = db.get_vehicles()
    if vehicles.empty:
        st.warning("Belum ada data kendaraan. Silakan tambah kendaraan terlebih dahulu.")
    else:
        col1, col2 = st.columns(2)
        with col1:
            vehicle_id = st.selectbox("Pilih Kendaraan", vehicles['vehicle_id'].tolist())
            vehicle_data = vehicles[vehicles['vehicle_id'] == vehicle_id].iloc[0]
            st.info(f"Odometer saat ini: {vehicle_data['last_odometer']:,} km")
        
        with st.form("service_form", clear_on_submit=True):
            service_date = st.date_input("Tanggal Servis", datetime.now())
            odometer = st.number_input("Odometer saat servis (km)", min_value=0, step=1000, value=int(vehicle_data['last_odometer']))
            
            components = db.get_vehicle_components()
            component_list = components['component_name'].tolist()
            component_name = st.selectbox("Komponen yang Diganti", component_list + ["Lainnya (isi di catatan)"])
            
            service_type = st.selectbox("Jenis Servis", ["Servis Rutin", "Perbaikan", "Penggantian Komponen", "Turun Mesin", "Lainnya"])
            mechanic = st.text_input("Nama Montir/Bengkel")
            cost = st.number_input("Biaya (Rp)", min_value=0, step=50000, value=0)
            notes = st.text_area("Catatan Servis / Komponen Lainnya")
            
            # Auto-calculate next service based on component standard
            comp_standard = components[components['component_name'] == component_name] if component_name in component_list else None
            if comp_standard is not None and not comp_standard.empty:
                life_km = comp_standard.iloc[0]['standard_life_km']
                life_months = comp_standard.iloc[0]['standard_life_months']
                next_km = odometer + life_km if life_km > 0 else 0
                st.info(f"⚠️ Standar komponen {component_name}: ganti setiap {life_km:,} km atau {life_months} bulan")
            else:
                life_km = st.number_input("Life time komponen (km)", min_value=0, step=1000, help="0 jika tidak berdasarkan jarak")
                life_months = st.number_input("Life time komponen (bulan)", min_value=0, step=1, help="0 jika tidak berdasarkan waktu")
                next_km = odometer + life_km if life_km > 0 else 0
            
            if st.form_submit_button("💾 SIMPAN SERVIS"):
                # Cari standard komponen
                comp = components[components['component_name'] == component_name] if component_name in component_list else None
                if comp is not None and not comp.empty:
                    life_km = comp.iloc[0]['standard_life_km']
                    life_months = comp.iloc[0]['standard_life_months']
                else:
                    life_km = 0
                    life_months = 0
                
                db.add_vehicle_service((
                    vehicle_id, str(service_date), odometer, service_type, component_name,
                    life_km, life_months, 0, 0,
                    odometer + life_km if life_km > 0 else 0,
                    life_months, cost, mechanic, notes
                ))
                st.success("Data servis berhasil disimpan!")
                st.rerun()

# --- MODUL 6: DASHBOARD KENDARAAN ---
elif menu == "📊 Dashboard Kendaraan":
    st.title("📊 Dashboard Pemeliharaan Kendaraan")
    
    vehicles = db.get_vehicles()
    if vehicles.empty:
        st.warning("Belum ada data kendaraan.")
    else:
        # Summary Stats
        total_vehicles = len(vehicles)
        active_vehicles = len(vehicles[vehicles['status'] == 'Aktif'])
        
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Kendaraan", total_vehicles)
        col2.metric("Kendaraan Aktif", active_vehicles)
        col3.metric("Total Odometer Gabungan", f"{vehicles['last_odometer'].sum():,} km")
        
        st.divider()
        
        # Detail per kendaraan
        st.subheader("Status Kesehatan & Jadwal Servis Mendatang")
        
        for _, v in vehicles.iterrows():
            health = analyze_vehicle_health(v['vehicle_id'])
            
            # Cek apakah ada error
            if health.get('error', False):
                with st.expander(f"🚗 {v['vehicle_id']} - {v['brand']} {v['model']} ({v['plate_number']})"):
                    st.warning(health['status'])
                continue
            
            with st.expander(f"🚗 {v['vehicle_id']} - {v['brand']} {v['model']} ({v['plate_number']})"):
                col_a, col_b = st.columns([2, 1])
                
                with col_a:
                    # Health score dengan warna yang aman
                    health_score = health.get('health_score', 0)
                    delta_text = "Perlu Perhatian" if health_score < 60 else "Baik" if health_score > 0 else "Belum Ada Data"
                    st.metric("Health Score", f"{health_score:.0f}%" if health_score > 0 else "N/A", 
                             delta=delta_text)
                    st.write(f"**Odometer:** {health.get('current_odometer', 0):,} km")
                    st.write(f"**Usia:** {health.get('months_used', 0)} bulan")
                
                with col_b:
                    st.write("**Komponen yang perlu dicek:**")
                    next_services = health.get('next_services', [])
                    if next_services:
                        for comp in next_services:
                            if comp.get('usage_percent', 0) >= 75:
                                color = "🔴" if comp.get('usage_percent', 0) >= 90 else "🟠"
                                st.write(f"{color} **{comp['component']}**: {comp.get('usage_percent', 0):.0f}%")
                    else:
                        st.write("✅ Semua komponen dalam kondisi baik")
                
                # Tabel jadwal servis
                st.write("**Detail Pemakaian Komponen:**")
                service_data = []
                for comp in next_services:
                    km_text = f"{comp.get('km_used', 0):,} / {comp.get('km_limit', 0):,}" if comp.get('km_limit', 0) > 0 else "N/A"
                    month_text = f"{comp.get('months_used', 0)} / {comp.get('months_limit', 0)}" if comp.get('months_limit', 0) > 0 else "N/A"
                    service_data.append({
                        "Komponen": comp.get('component', 'Unknown'),
                        "Pemakaian (km)": km_text,
                        "Pemakaian (bulan)": month_text,
                        "Status": comp.get('status', 'Unknown')
                    })
                
                if service_data:
                    st.dataframe(pd.DataFrame(service_data), use_container_width=True)
                else:
                    st.info("Belum ada data pemakaian komponen")
                
                # Riwayat servis
                services = db.get_vehicle_services(v['vehicle_id'])
                if not services.empty:
                    st.write("**Riwayat Servis Terakhir:**")
                    st.dataframe(services[['service_date', 'odometer', 'component_name', 'service_type', 'cost']].head(5), 
                                use_container_width=True)

# --- MODUL 7: EDIT/HAPUS DATA ---
elif menu == "🛠️ Edit/Hapus Data":
    st.title("🛠️ Koreksi Data")
    
    tab_ac, tab_vehicle = st.tabs(["🗑️ Hapus Log AC", "🗑️ Hapus Servis Kendaraan"])
    
    with tab_ac:
        logs = db.get_all_logs()
        if not logs.empty:
            sel = st.selectbox("Pilih Log AC", logs.apply(lambda x: f"{x['id']} - {x['asset_id']} ({x['tanggal']})", axis=1))
            l_id = int(sel.split(" - ")[0])
            if st.button("🗑️ HAPUS LOG AC PERMANEN"):
                db.delete_log(l_id)
                st.success("Log Terhapus!")
                st.rerun()
        else:
            st.info("Tidak ada log AC")
    
    with tab_vehicle:
        services = db.get_vehicle_services()
        if not services.empty:
            sel = st.selectbox("Pilih Servis Kendaraan", 
                              services.apply(lambda x: f"{x['id']} - {x['vehicle_id']} - {x['component_name']} ({x['service_date']})", axis=1))
            s_id = int(sel.split(" - ")[0])
            if st.button("🗑️ HAPUS SERVIS KENDARAAN"):
                db.delete_vehicle_service(s_id)
                st.success("Servis kendaraan terhapus!")
                st.rerun()
        else:
            st.info("Tidak ada data servis kendaraan")

# --- MODUL 8: CETAK LAPORAN ---
elif menu == "🖨️ Cetak Laporan":
    st.title("🖨️ Preview Laporan Cetak")
    
    report_type = st.selectbox("Pilih Jenis Laporan", ["Laporan AC", "Laporan Kendaraan", "Laporan Semua Aset"])
    
    if report_type == "Laporan AC":
        logs = db.get_all_logs()
        if not logs.empty:
            sel_l = st.selectbox("Pilih Riwayat LHO AC", logs['id'].tolist())
            r = logs[logs['id'] == sel_l].iloc[0]
            
            st.markdown(f"""
            <div style="border: 2px solid #003366; padding: 25px; background: white;">
                <div style="text-align:center; border-bottom: 2px solid #CC0000; padding-bottom:10px;">
                    <h2 style="color:#003366; margin:0;">PT BESTPROFIT FUTURES SURABAYA</h2>
                    <p style="margin:5px; font-weight:bold;">LAPORAN HASIL OPNAME AC (LHO)</p>
                </div>
                <table style="width:100%; margin-top:20px;">
                    <tr><td><b>Asset ID:</b> {r['asset_id']}</td><td><b>Tanggal:</b> {r['tanggal']}</td></tr>
                    <tr><td><b>Lokasi:</b> {r['lokasi']}</td><td><b>Kapasitas:</b> {r['kapasitas']}</td></tr>
                    <tr><td><b>Teknisi:</b> {r['teknisi']}</td><td><b>Health Score:</b> {r['health_score']}/100</td></tr>
                </table>
                <hr>
                <h4>Parameter Pengukuran:</h4>
                <ul>
                    <li>Efisiensi (Delta T): {r['delta_t']} °C</li>
                    <li>Arus Listrik: {r['amp_kompresor']} A</li>
                    <li>Tekanan Low: {r['low_p']} Psi</li>
                    <li>Status: {r['test_run']}</li>
                </ul>
                <p><b>Rekomendasi:</b> {r['catatan']}</p>
            </div>
            """, unsafe_allow_html=True)
            st.info("💡 Tekan Ctrl+P untuk menyimpan sebagai PDF.")
        else:
            st.info("Belum ada data LHO AC")
    
    elif report_type == "Laporan Kendaraan":
        vehicles = db.get_vehicles()
        if not vehicles.empty:
            sel_v = st.selectbox("Pilih Kendaraan", vehicles['vehicle_id'].tolist())
            v_data = vehicles[vehicles['vehicle_id'] == sel_v].iloc[0]
            health = analyze_vehicle_health(sel_v)
            services = db.get_vehicle_services(sel_v)
            
            health_score_display = f"{health.get('health_score', 0):.0f}%" if not health.get('error', False) else "N/A"
            
            st.markdown(f"""
            <div style="border: 2px solid #003366; padding: 25px; background: white;">
                <div style="text-align:center; border-bottom: 2px solid #CC0000; padding-bottom:10px;">
                    <h2 style="color:#003366; margin:0;">PT BESTPROFIT FUTURES SURABAYA</h2>
                    <p style="margin:5px; font-weight:bold;">LAPORAN STATUS KENDARAAN</p>
                </div>
                <table style="width:100%; margin-top:20px;">
                    <tr><td><b>ID Kendaraan:</b> {v_data['vehicle_id']}</td><td><b>Plat Nomor:</b> {v_data['plate_number']}</td></tr>
                    <tr><td><b>Merek/Model:</b> {v_data['brand']} {v_data['model']}</td><td><b>Tahun:</b> {v_data['year']}</td></tr>
                    <tr><td><b>Odometer:</b> {v_data['last_odometer']:,} km</td><td><b>Health Score:</b> {health_score_display}</td></tr>
                </table>
                <hr>
                <h4>Status Komponen:</h4>
                <table style="width:100%; border-collapse: collapse;">
                    <tr style="background:#f0f0f0;">
                        <th style="padding:8px; text-align:left;">Komponen</th>
                        <th style="padding:8px; text-align:left;">Pemakaian</th>
                        <th style="padding:8px; text-align:left;">Status</th>
                    </tr>
            """, unsafe_allow_html=True)
            
            next_services = health.get('next_services', [])
            if next_services:
                for comp in next_services:
                    usage = comp.get('usage_percent', 0)
                    if usage >= 75:
                        color = 'red' if usage >= 90 else 'orange'
                        st.markdown(f"""
                            <tr>
                                <td style="padding:8px;">{comp.get('component', 'Unknown')}</td>
                                <td style="padding:8px;">{usage:.0f}%</td>
                                <td style="padding:8px; color:{color};">{comp.get('status', 'Unknown')}</td>
                            </tr>
                        """, unsafe_allow_html=True)
            else:
                st.markdown("""
                    <tr>
                        <td colspan="3" style="padding:8px; text-align:center;">Semua komponen dalam kondisi baik</td>
                    </tr>
                """, unsafe_allow_html=True)
            
            st.markdown("</table>", unsafe_allow_html=True)
            
            if not services.empty:
                st.markdown("""
                <hr>
                <h4>Riwayat Servis:</h4>
                <table style="width:100%; border-collapse: collapse;">
                    <tr style="background:#f0f0f0;">
                        <th style="padding:8px; text-align:left;">Tanggal</th>
                        <th style="padding:8px; text-align:left;">Odometer</th>
                        <th style="padding:8px; text-align:left;">Komponen</th>
                        <th style="padding:8px; text-align:left;">Biaya</th>
                    </tr>
                """, unsafe_allow_html=True)
                
                for _, s in services.head(10).iterrows():
                    st.markdown(f"""
                        <tr>
                            <td style="padding:8px;">{s['service_date']}</td>
                            <td style="padding:8px;">{s['odometer']:,} km</td>
                            <td style="padding:8px;">{s['component_name']}</td>
                            <td style="padding:8px;">Rp {s['cost']:,.0f}</td>
                        </tr>
                    """, unsafe_allow_html=True)
                
                st.markdown("</table>", unsafe_allow_html=True)
            
            st.markdown("</div>", unsafe_allow_html=True)
            st.info("💡 Tekan Ctrl+P untuk menyimpan sebagai PDF.")
        else:
            st.info("Belum ada data kendaraan")
    
    else:  # Laporan Semua Aset
        st.info("Fitur laporan komprehensif sedang dalam pengembangan")