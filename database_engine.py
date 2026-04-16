import sqlite3
import pandas as pd

import os

# Tentukan path database
DB_PATH = os.environ.get('DB_PATH', os.path.join(os.path.dirname(__file__), 'bpf_ac_ai_system.db'))
# Jika running di Docker, gunakan path di /app/data
if os.path.exists('/.dockerenv') or os.environ.get('DOCKER_ENV') == 'true':
    DB_PATH = '/app/data/bpf_ac_ai_system.db'

def get_connection():
    """Get database connection with proper path"""
    return sqlite3.connect(DB_PATH)

def create_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    # Master Aset AC - Manageable Specs
    c.execute('''CREATE TABLE IF NOT EXISTS assets (
                    asset_id TEXT PRIMARY KEY, merk TEXT, tipe TEXT, 
                    kapasitas TEXT, lokasi TEXT, refrigerant TEXT)''')

    # Master Aset Kendaraan
    c.execute('''CREATE TABLE IF NOT EXISTS vehicles (
                    vehicle_id TEXT PRIMARY KEY, 
                    brand TEXT, 
                    model TEXT, 
                    year INTEGER,
                    plate_number TEXT,
                    color TEXT,
                    fuel_type TEXT,
                    status TEXT DEFAULT 'Aktif',
                    purchase_date TEXT,
                    last_odometer INTEGER DEFAULT 0,
                    notes TEXT)''')

    # Log Maintenance AC
    c.execute('''CREATE TABLE IF NOT EXISTS maintenance_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    asset_id TEXT, tanggal TEXT, teknisi TEXT,
                    v_supply REAL, amp_kompresor REAL, low_p REAL,
                    temp_ret REAL, temp_sup REAL, delta_t REAL,
                    drainage TEXT, test_run TEXT, health_score INTEGER,
                    sparepart_cost REAL, catatan TEXT,
                    FOREIGN KEY (asset_id) REFERENCES assets (asset_id))''')
    
    # Log Servis Kendaraan
    c.execute('''CREATE TABLE IF NOT EXISTS vehicle_service_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    vehicle_id TEXT,
                    service_date TEXT,
                    odometer INTEGER,
                    service_type TEXT,
                    component_name TEXT,
                    component_life_km INTEGER,
                    component_life_months INTEGER,
                    current_usage_km INTEGER,
                    current_usage_months INTEGER,
                    next_service_km INTEGER,
                    next_service_months INTEGER,
                    cost REAL,
                    mechanic_name TEXT,
                    notes TEXT,
                    FOREIGN KEY (vehicle_id) REFERENCES vehicles (vehicle_id))''')
    
    # Komponen yang perlu dipantau
    c.execute('''CREATE TABLE IF NOT EXISTS vehicle_components (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    component_name TEXT UNIQUE,
                    standard_life_km INTEGER,
                    standard_life_months INTEGER,
                    is_active INTEGER DEFAULT 1)''')
    
    conn.commit()
    conn.close()

def init_bpf_assets():
    """Daftar 15 Aset AC sesuai Layout BPF SBY"""
    assets = [
        ("AC-01-R. BEST 8", "Daikin", "Split Duct", "60.000 Btu/h", "R. BEST 8", "R32"),
        ("AC-02-R. BEST 7, OPERATIONAL", "Daikin", "Split Duct", "60.000 Btu/h", "R. BEST 7, OPERATIONAL", "R32"),
        ("AC-03-R. BEST 6", "Daikin", "Split Duct", "60.000 Btu/h", "R. BEST 6", "R32"),
        ("AC-04-R. BEST 5", "Daikin", "Split Duct", "60.000 Btu/h", "R. BEST 5", "R32"),
        ("AC-05-R. BEST 3, VIP 8", "Daikin", "Split Duct", "100.000 Btu/h", "R. BEST 3, VIP 8", "R32"),
        ("AC-06-R. BEST 2, VIP 6 & 7", "Daikin", "Split Duct", "60.000 Btu/h", "R. BEST 2, VIP 6 & 7", "R32"),
        ("AC-07-R. BEST 1, VIP 3 & 5", "Daikin", "Split Duct", "60.000 Btu/h", "R. BEST 1, VIP 3 & 5", "R32"),
        ("AC-08-R. KARAOKE", "Daikin", "Split Duct", "100.000 Btu/h", "R. KARAOKE", "R32"),
        ("AC-09-LOUNGE 1, 2, VIP 1, 2", "Daikin", "Split Duct", "60.000 Btu/h", "LOUNGE 1, 2, VIP 1, 2", "R32"),
        ("AC-10-R. BM & R. FINANCE", "Daikin", "Split Duct", "60.000 Btu/h", "R. BM & R. FINANCE", "R32"),
        ("AC-11-R. MEETING & RECEPTIONIST", "Daikin", "Split Duct", "60.000 Btu/h", "R. MEETING & RECEPTIONIST", "R32"),
        ("AC-12-R. TRAINER & R. SECRETARY", "Daikin", "Split Duct", "60.000 Btu/h", "R. TRAINER & R. SECRETARY", "R32"),
        ("AC-13-COMPLIANCE & TRAINING 2", "Daikin", "Split Duct", "60.000 Btu/h", "COMPLIANCE & TRAINING 2", "R32"),
        ("AC-14-IT & R. SERVER", "Daikin", "Split Duct", "60.000 Btu/h", "IT & R. SERVER", "R32"),
        ("AC-15-RUANG TRAINING 1", "Daikin", "Split Wall", "2 PK", "RUANG TRAINING 1", "R32")
    ]
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.executemany("INSERT OR IGNORE INTO assets VALUES (?,?,?,?,?,?)", assets)
    conn.commit()
    conn.close()

def init_vehicle_components():
    """Inisialisasi komponen standar kendaraan"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    components = [
        ("Oli Mesin", 5000, 6, 1),
        ("Oli Transmisi", 40000, 24, 1),
        ("Ban", 40000, 36, 1),
        ("Aki", 0, 24, 1),
        ("Filter Oli", 5000, 6, 1),
        ("Filter Udara", 20000, 12, 1),
        ("Busi", 20000, 12, 1),
        ("Kampas Rem Depan", 30000, 18, 1),
        ("Kampas Rem Belakang", 40000, 24, 1),
        ("Pendingin (Radiator)", 40000, 24, 1),
        ("V-Belt", 40000, 24, 1)
    ]
    
    c.executemany("INSERT OR IGNORE INTO vehicle_components (component_name, standard_life_km, standard_life_months, is_active) VALUES (?,?,?,?)", components)
    conn.commit()
    conn.close()

def init_sample_vehicles():
    """Contoh data kendaraan kantor"""
    vehicles = [
        ("VH-001", "Toyota", "Innova", 2020, "B 1234 ABC", "Hitam", "Bensin", "Aktif", "2020-01-15", 85000, "Mobil Operasional Direktur"),
        ("VH-002", "Honda", "CRV", 2021, "B 5678 DEF", "Putih", "Bensin", "Aktif", "2021-03-20", 45000, "Mobil Operasional Manager"),
        ("VH-003", "Mitsubishi", "Xpander", 2022, "B 9012 GHI", "Silver", "Bensin", "Aktif", "2022-06-10", 28000, "Mobil Antar Jemput Karyawan"),
        ("VH-004", "Suzuki", "Carry", 2019, "B 3456 JKL", "Putih", "Bensin", "Aktif", "2019-11-05", 120000, "Mobil Operasional Logistik"),
        ("VH-005", "Toyota", "Hiace", 2018, "B 7890 MNO", "Abu-abu", "Solar", "Aktif", "2018-08-12", 180000, "Mobil Antar Jemput & Operasional")
    ]
    
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.executemany("INSERT OR IGNORE INTO vehicles VALUES (?,?,?,?,?,?,?,?,?,?,?)", vehicles)
    conn.commit()
    conn.close()

# Fungsi CRUD untuk Kendaraan
def get_vehicles():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT * FROM vehicles ORDER BY vehicle_id", conn)
    conn.close()
    return df

def add_vehicle(data):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""INSERT INTO vehicles 
                 (vehicle_id, brand, model, year, plate_number, color, fuel_type, status, purchase_date, last_odometer, notes) 
                 VALUES (?,?,?,?,?,?,?,?,?,?,?)""", data)
    conn.commit()
    conn.close()

def update_vehicle(vehicle_id, data):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""UPDATE vehicles 
                 SET brand=?, model=?, year=?, plate_number=?, color=?, 
                     fuel_type=?, status=?, purchase_date=?, last_odometer=?, notes=?
                 WHERE vehicle_id=?""", (*data, vehicle_id))
    conn.commit()
    conn.close()

def delete_vehicle(vehicle_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("DELETE FROM vehicles WHERE vehicle_id=?", (vehicle_id,))
    conn.commit()
    conn.close()

# Fungsi CRUD untuk Servis Kendaraan
def add_vehicle_service(data):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""INSERT INTO vehicle_service_logs 
                 (vehicle_id, service_date, odometer, service_type, component_name, 
                  component_life_km, component_life_months, current_usage_km, 
                  current_usage_months, next_service_km, next_service_months, cost, mechanic_name, notes) 
                 VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""", data)
    # Update last odometer di tabel vehicles
    c.execute("UPDATE vehicles SET last_odometer = ? WHERE vehicle_id = ?", (data[2], data[0]))
    conn.commit()
    conn.close()

def get_vehicle_services(vehicle_id=None):
    conn = sqlite3.connect(DB_PATH)
    if vehicle_id:
        df = pd.read_sql_query("SELECT * FROM vehicle_service_logs WHERE vehicle_id = ? ORDER BY service_date DESC", conn, params=(vehicle_id,))
    else:
        df = pd.read_sql_query("SELECT * FROM vehicle_service_logs ORDER BY service_date DESC", conn)
    conn.close()
    return df

def delete_vehicle_service(service_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("DELETE FROM vehicle_service_logs WHERE id=?", (service_id,))
    conn.commit()
    conn.close()

def get_vehicle_components():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT * FROM vehicle_components WHERE is_active = 1 ORDER BY component_name", conn)
    conn.close()
    return df

def add_vehicle_component(data):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO vehicle_components (component_name, standard_life_km, standard_life_months, is_active) VALUES (?,?,?,?)", data)
    conn.commit()
    conn.close()

def update_vehicle_component(component_id, data):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE vehicle_components SET component_name=?, standard_life_km=?, standard_life_months=?, is_active=? WHERE id=?", (*data, component_id))
    conn.commit()
    conn.close()

# Fungsi untuk AC (existing)
def get_assets():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT * FROM assets", conn)
    conn.close()
    return df

def update_asset(asset_id, data):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE assets SET merk=?, tipe=?, kapasitas=?, lokasi=?, refrigerant=? WHERE asset_id=?", (*data, asset_id))
    conn.commit()
    conn.close()

def add_log(data):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO maintenance_logs (asset_id, tanggal, teknisi, v_supply, amp_kompresor, low_p, temp_ret, temp_sup, delta_t, drainage, test_run, health_score, sparepart_cost, catatan) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)", data)
    conn.commit()
    conn.close()

def get_all_logs():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT m.*, a.lokasi, a.merk, a.kapasitas FROM maintenance_logs m JOIN assets a ON m.asset_id = a.asset_id ORDER BY m.tanggal ASC", conn)
    conn.close()
    return df

def delete_log(log_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("DELETE FROM maintenance_logs WHERE id=?", (log_id,))
    conn.commit()
    conn.close()