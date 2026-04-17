import sqlite3
import pandas as pd
import numpy as np
import os
import logging
from datetime import datetime, timedelta
import random
from pathlib import Path
import shutil

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database paths
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / 'data'
DATA_DIR.mkdir(exist_ok=True)

REAL_DB_PATH = DATA_DIR / 'bpf_ac_ai_system.db'
DEMO_DB_PATH = DATA_DIR / 'bpf_ac_ai_system_demo.db'
BACKUP_DIR = DATA_DIR / 'backups'
BACKUP_DIR.mkdir(exist_ok=True)

def get_db_path(mode='real'):
    """Get database path based on mode"""
    if mode == 'demo':
        return str(DEMO_DB_PATH)
    return str(REAL_DB_PATH)

def get_connection(mode='real'):
    """Get database connection"""
    db_path = get_db_path(mode)
    conn = sqlite3.connect(db_path, timeout=30)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def backup_database(mode='real'):
    """Create a backup of the database"""
    try:
        db_path = get_db_path(mode)
        if os.path.exists(db_path):
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_path = BACKUP_DIR / f"backup_{mode}_{timestamp}.db"
            shutil.copy(db_path, backup_path)
            
            backups = sorted(BACKUP_DIR.glob(f"backup_{mode}_*.db"))
            if len(backups) > 10:
                for old_backup in backups[:-10]:
                    old_backup.unlink()
            
            logger.info(f"Database backed up to {backup_path}")
            return str(backup_path)
    except Exception as e:
        logger.error(f"Backup failed: {e}")
        return None

def create_db(mode='real'):
    """Create database tables"""
    conn = get_connection(mode)
    c = conn.cursor()
    
    c.execute('''CREATE TABLE IF NOT EXISTS assets (
                    asset_id TEXT PRIMARY KEY, 
                    merk TEXT NOT NULL, 
                    tipe TEXT NOT NULL, 
                    kapasitas TEXT NOT NULL, 
                    lokasi TEXT NOT NULL, 
                    refrigerant TEXT NOT NULL,
                    installation_date TEXT,
                    warranty_until TEXT,
                    last_maintenance TEXT,
                    status TEXT DEFAULT 'Aktif',
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP)''')

    c.execute('''CREATE TABLE IF NOT EXISTS vehicles (
                    vehicle_id TEXT PRIMARY KEY, 
                    brand TEXT NOT NULL, 
                    model TEXT NOT NULL, 
                    year INTEGER NOT NULL,
                    plate_number TEXT UNIQUE NOT NULL,
                    color TEXT,
                    fuel_type TEXT NOT NULL,
                    status TEXT DEFAULT 'Aktif',
                    purchase_date TEXT NOT NULL,
                    last_odometer INTEGER DEFAULT 0,
                    notes TEXT,
                    insurance_until TEXT,
                    tax_until TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP)''')

    c.execute('''CREATE TABLE IF NOT EXISTS maintenance_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    asset_id TEXT NOT NULL,
                    tanggal TEXT NOT NULL,
                    teknisi TEXT NOT NULL,
                    v_supply REAL,
                    amp_kompresor REAL,
                    low_p REAL,
                    high_p REAL,
                    temp_ret REAL,
                    temp_sup REAL,
                    temp_outdoor REAL,
                    delta_t REAL,
                    drainage TEXT,
                    test_run TEXT,
                    health_score INTEGER,
                    sparepart_cost REAL DEFAULT 0,
                    catatan TEXT,
                    next_service_date TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (asset_id) REFERENCES assets (asset_id) ON DELETE CASCADE)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS vehicle_service_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    vehicle_id TEXT NOT NULL,
                    service_date TEXT NOT NULL,
                    odometer INTEGER NOT NULL,
                    service_type TEXT NOT NULL,
                    component_name TEXT NOT NULL,
                    component_life_km INTEGER DEFAULT 0,
                    component_life_months INTEGER DEFAULT 0,
                    current_usage_km INTEGER DEFAULT 0,
                    current_usage_months INTEGER DEFAULT 0,
                    next_service_km INTEGER DEFAULT 0,
                    next_service_months INTEGER DEFAULT 0,
                    cost REAL DEFAULT 0,
                    mechanic_name TEXT,
                    notes TEXT,
                    parts_replaced TEXT,
                    invoice_number TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (vehicle_id) REFERENCES vehicles (vehicle_id) ON DELETE CASCADE)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS vehicle_components (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    component_name TEXT UNIQUE NOT NULL,
                    standard_life_km INTEGER DEFAULT 0,
                    standard_life_months INTEGER DEFAULT 0,
                    is_active INTEGER DEFAULT 1,
                    category TEXT,
                    priority INTEGER DEFAULT 1,
                    estimated_cost REAL DEFAULT 0,
                    notes TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP)''')
    
    c.execute('CREATE INDEX IF NOT EXISTS idx_logs_asset_date ON maintenance_logs(asset_id, tanggal)')
    c.execute('CREATE INDEX IF NOT EXISTS idx_vehicle_services_vehicle ON vehicle_service_logs(vehicle_id, service_date)')
    
    conn.commit()
    conn.close()
    logger.info(f"Database created in {mode} mode")

def init_bpf_assets(mode='real'):
    """Initialize BPF assets"""
    conn = get_connection(mode)
    c = conn.cursor()
    
    assets = [
        ("AC-01-R. BEST 8", "Daikin", "Split Duct", "60.000 Btu/h", "R. BEST 8", "R32", "2020-01-15", "2025-01-15", "Aktif"),
        ("AC-02-R. BEST 7, OPERATIONAL", "Daikin", "Split Duct", "60.000 Btu/h", "R. BEST 7, OPERATIONAL", "R32", "2020-01-15", "2025-01-15", "Aktif"),
        ("AC-03-R. BEST 6", "Daikin", "Split Duct", "60.000 Btu/h", "R. BEST 6", "R32", "2020-01-15", "2025-01-15", "Aktif"),
        ("AC-04-R. BEST 5", "Daikin", "Split Duct", "60.000 Btu/h", "R. BEST 5", "R32", "2020-01-15", "2025-01-15", "Aktif"),
        ("AC-05-R. BEST 3, VIP 8", "Daikin", "Split Duct", "100.000 Btu/h", "R. BEST 3, VIP 8", "R32", "2020-01-15", "2025-01-15", "Aktif"),
        ("AC-06-R. BEST 2, VIP 6 & 7", "Daikin", "Split Duct", "60.000 Btu/h", "R. BEST 2, VIP 6 & 7", "R32", "2020-01-15", "2025-01-15", "Aktif"),
        ("AC-07-R. BEST 1, VIP 3 & 5", "Daikin", "Split Duct", "60.000 Btu/h", "R. BEST 1, VIP 3 & 5", "R32", "2020-01-15", "2025-01-15", "Aktif"),
        ("AC-08-R. KARAOKE", "Daikin", "Split Duct", "100.000 Btu/h", "R. KARAOKE", "R32", "2020-01-15", "2025-01-15", "Aktif"),
        ("AC-09-LOUNGE 1, 2, VIP 1, 2", "Daikin", "Split Duct", "60.000 Btu/h", "LOUNGE 1, 2, VIP 1, 2", "R32", "2020-01-15", "2025-01-15", "Aktif"),
        ("AC-10-R. BM & R. FINANCE", "Daikin", "Split Duct", "60.000 Btu/h", "R. BM & R. FINANCE", "R32", "2020-01-15", "2025-01-15", "Aktif"),
        ("AC-11-R. MEETING & RECEPTIONIST", "Daikin", "Split Duct", "60.000 Btu/h", "R. MEETING & RECEPTIONIST", "R32", "2020-01-15", "2025-01-15", "Aktif"),
        ("AC-12-R. TRAINER & R. SECRETARY", "Daikin", "Split Duct", "60.000 Btu/h", "R. TRAINER & R. SECRETARY", "R32", "2020-01-15", "2025-01-15", "Aktif"),
        ("AC-13-COMPLIANCE & TRAINING 2", "Daikin", "Split Duct", "60.000 Btu/h", "COMPLIANCE & TRAINING 2", "R32", "2020-01-15", "2025-01-15", "Aktif"),
        ("AC-14-IT & R. SERVER", "Daikin", "Split Duct", "60.000 Btu/h", "IT & R. SERVER", "R32", "2020-01-15", "2025-01-15", "Aktif"),
        ("AC-15-RUANG TRAINING 1", "Daikin", "Split Wall", "2 PK", "RUANG TRAINING 1", "R32", "2020-01-15", "2025-01-15", "Aktif")
    ]
    
    c.executemany("""
        INSERT OR IGNORE INTO assets 
        (asset_id, merk, tipe, kapasitas, lokasi, refrigerant, installation_date, warranty_until, status) 
        VALUES (?,?,?,?,?,?,?,?,?)
    """, assets)
    
    conn.commit()
    conn.close()

def init_vehicle_components(mode='real'):
    """Initialize vehicle components"""
    conn = get_connection(mode)
    c = conn.cursor()
    
    components = [
        ("Oli Mesin", 5000, 6, 1, "Mesin", 1, 500000, "Ganti setiap 5,000 km atau 6 bulan"),
        ("Oli Transmisi", 40000, 24, 1, "Transmisi", 2, 750000, "Ganti setiap 40,000 km atau 2 tahun"),
        ("Ban", 40000, 36, 1, "Roda", 2, 3500000, "Rotasi dan ganti sesuai keausan"),
        ("Aki", 0, 24, 1, "Kelistrikan", 2, 1200000, "Ganti setiap 2 tahun"),
        ("Filter Oli", 5000, 6, 1, "Mesin", 1, 85000, "Ganti bersama oli mesin"),
        ("Filter Udara", 20000, 12, 1, "Mesin", 2, 150000, "Ganti setiap 20,000 km atau 1 tahun"),
        ("Filter AC", 20000, 12, 1, "AC", 3, 200000, "Ganti untuk kualitas udara"),
        ("Busi", 20000, 12, 1, "Pengapian", 2, 350000, "Ganti setiap 20,000 km"),
        ("Kampas Rem Depan", 30000, 18, 1, "Rem", 1, 850000, "Periksa setiap servis"),
        ("Kampas Rem Belakang", 40000, 24, 1, "Rem", 1, 750000, "Periksa setiap servis"),
        ("Pendingin Radiator", 40000, 24, 1, "Pendingin", 2, 350000, "Ganti setiap 40,000 km"),
        ("Timing Belt", 80000, 48, 1, "Mesin", 1, 2500000, "KRITIS - Ganti tepat waktu"),
    ]
    
    c.executemany("""
        INSERT OR IGNORE INTO vehicle_components 
        (component_name, standard_life_km, standard_life_months, is_active, category, priority, estimated_cost, notes) 
        VALUES (?,?,?,?,?,?,?,?)
    """, components)
    
    conn.commit()
    conn.close()

def init_sample_vehicles(mode='real'):
    """Initialize sample vehicles"""
    conn = get_connection(mode)
    c = conn.cursor()
    
    vehicles = [
        ("VH-001", "Toyota", "Innova", 2020, "B 1234 ABC", "Hitam", "Bensin", "Aktif", "2020-01-15", 85000, "Mobil Operasional Direktur", "2025-01-15", "2025-01-15"),
        ("VH-002", "Honda", "CRV", 2021, "B 5678 DEF", "Putih", "Bensin", "Aktif", "2021-03-20", 45000, "Mobil Operasional Manager", "2026-03-20", "2025-03-20"),
        ("VH-003", "Mitsubishi", "Xpander", 2022, "B 9012 GHI", "Silver", "Bensin", "Aktif", "2022-06-10", 28000, "Mobil Antar Jemput Karyawan", "2027-06-10", "2025-06-10"),
        ("VH-004", "Suzuki", "Carry", 2019, "B 3456 JKL", "Putih", "Bensin", "Aktif", "2019-11-05", 120000, "Mobil Operasional Logistik", "2024-11-05", "2024-11-05"),
        ("VH-005", "Toyota", "Hiace", 2018, "B 7890 MNO", "Abu-abu", "Solar", "Aktif", "2018-08-12", 180000, "Mobil Antar Jemput & Operasional", "2023-08-12", "2024-08-12")
    ]
    
    c.executemany("""
        INSERT OR IGNORE INTO vehicles 
        (vehicle_id, brand, model, year, plate_number, color, fuel_type, status, purchase_date, last_odometer, notes, insurance_until, tax_until) 
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
    """, vehicles)
    
    conn.commit()
    conn.close()

def generate_dummy_ac_logs(logs_per_asset=50, mode='demo'):
    """Generate dummy AC logs"""
    conn = get_connection(mode)
    assets_df = pd.read_sql_query("SELECT asset_id FROM assets", conn)
    asset_ids = assets_df['asset_id'].tolist()
    
    start_date = datetime.now() - timedelta(days=365)
    dummy_logs = []
    teknisi_list = ['Andi', 'Budi', 'Cahyo', 'Dedi', 'Eko']
    
    for asset_id in asset_ids:
        for i in range(logs_per_asset):
            days_offset = i * random.randint(3, 10)
            log_date = start_date + timedelta(days=days_offset)
            if log_date > datetime.now():
                continue
            
            amp = 15 + random.uniform(-2, 10)
            delta_t = 10 + random.uniform(-3, 5)
            health_score = max(20, min(100, int(80 + random.uniform(-30, 20))))
            
            dummy_logs.append((
                asset_id, log_date.strftime('%Y-%m-%d'), random.choice(teknisi_list),
                380, round(amp, 2), 140, 350, 24, 24-delta_t, 32, round(delta_t, 1),
                'Lancar', 'Normal' if health_score > 65 else 'Abnormal', health_score,
                random.randint(0, 500000), '', None
            ))
    
    c = conn.cursor()
    for batch in [dummy_logs[i:i+100] for i in range(0, len(dummy_logs), 100)]:
        c.executemany("""
            INSERT INTO maintenance_logs 
            (asset_id, tanggal, teknisi, v_supply, amp_kompresor, low_p, high_p, 
             temp_ret, temp_sup, temp_outdoor, delta_t, drainage, test_run, 
             health_score, sparepart_cost, catatan, next_service_date) 
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, batch)
    
    conn.commit()
    conn.close()
    logger.info(f"Generated {len(dummy_logs)} dummy AC logs")

def generate_dummy_vehicle_services(services_per_vehicle=30, mode='demo'):
    """Generate dummy vehicle services"""
    conn = get_connection(mode)
    vehicles_df = pd.read_sql_query("SELECT vehicle_id, last_odometer FROM vehicles", conn)
    components_df = pd.read_sql_query("SELECT component_name, standard_life_km, standard_life_months, estimated_cost FROM vehicle_components WHERE is_active = 1", conn)
    
    start_date = datetime.now() - timedelta(days=730)
    dummy_services = []
    
    for _, vehicle in vehicles_df.iterrows():
        vehicle_id = vehicle['vehicle_id']
        current_odometer = vehicle['last_odometer']
        
        for i in range(services_per_vehicle):
            days_offset = i * random.randint(20, 40)
            service_date = start_date + timedelta(days=days_offset)
            if service_date > datetime.now():
                continue
            
            service_odometer = int(current_odometer * (i / services_per_vehicle)) + random.randint(-1000, 1000)
            service_odometer = max(0, min(current_odometer, service_odometer))
            
            component = components_df.sample(1).iloc[0]
            cost = component['estimated_cost'] * random.uniform(0.8, 1.3)
            
            dummy_services.append((
                vehicle_id, service_date.strftime('%Y-%m-%d'), service_odometer,
                'Servis Rutin' if i % 3 == 0 else 'Penggantian Komponen',
                component['component_name'], component['standard_life_km'],
                component['standard_life_months'], 0, 0,
                service_odometer + component['standard_life_km'] if component['standard_life_km'] > 0 else 0,
                component['standard_life_months'], round(cost, -3),
                'Bengkel Resmi', f"Servis {component['component_name']}", '', f"INV-{random.randint(1000,9999)}"
            ))
    
    c = conn.cursor()
    for batch in [dummy_services[i:i+100] for i in range(0, len(dummy_services), 100)]:
        c.executemany("""
            INSERT INTO vehicle_service_logs 
            (vehicle_id, service_date, odometer, service_type, component_name,
             component_life_km, component_life_months, current_usage_km,
             current_usage_months, next_service_km, next_service_months, 
             cost, mechanic_name, notes, parts_replaced, invoice_number) 
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, batch)
    
    conn.commit()
    conn.close()
    logger.info(f"Generated {len(dummy_services)} dummy vehicle services")

def generate_dummy_vehicles(count=10, mode='demo'):
    """Generate additional dummy vehicles"""
    conn = get_connection(mode)
    c = conn.cursor()
    
    brands = ['Toyota', 'Honda', 'Mitsubishi', 'Suzuki', 'Daihatsu']
    models = {'Toyota': ['Avanza', 'Innova', 'Fortuner'], 'Honda': ['Brio', 'Jazz', 'CR-V'], 
              'Mitsubishi': ['Xpander', 'Pajero'], 'Suzuki': ['Ertiga', 'Carry'], 'Daihatsu': ['Xenia', 'Terios']}
    colors = ['Hitam', 'Putih', 'Silver', 'Abu-abu']
    fuel_types = ['Bensin', 'Solar']
    
    existing = pd.read_sql_query("SELECT vehicle_id FROM vehicles", conn)
    existing_ids = set(existing['vehicle_id'].tolist())
    
    new_vehicles = []
    for i in range(count):
        while True:
            new_id = f"VH-{random.randint(100, 999):03d}"
            if new_id not in existing_ids:
                existing_ids.add(new_id)
                break
        
        brand = random.choice(brands)
        model = random.choice(models[brand])
        year = random.randint(2018, 2024)
        plate = f"B {random.randint(1000, 9999)} {''.join(random.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZ', k=3))}"
        color = random.choice(colors)
        fuel = random.choice(fuel_types)
        status = random.choice(['Aktif', 'Aktif', 'Aktif', 'Service'])
        purchase_date = datetime.now() - timedelta(days=random.randint(365, 1825))
        months_old = (datetime.now() - purchase_date).days / 30
        odometer = int(months_old * random.randint(1000, 2500))
        
        new_vehicles.append((
            new_id, brand, model, year, plate, color, fuel, status,
            purchase_date.strftime('%Y-%m-%d'), odometer, f"Kendaraan operasional {brand} {model}",
            (datetime.now() + timedelta(days=random.randint(180, 540))).strftime('%Y-%m-%d'),
            (datetime.now() + timedelta(days=random.randint(90, 450))).strftime('%Y-%m-%d')
        ))
    
    c.executemany("""
        INSERT OR IGNORE INTO vehicles 
        (vehicle_id, brand, model, year, plate_number, color, fuel_type, status,
         purchase_date, last_odometer, notes, insurance_until, tax_until)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
    """, new_vehicles)
    
    conn.commit()
    conn.close()
    logger.info(f"Generated {len(new_vehicles)} additional dummy vehicles")

# CRUD Functions
def get_assets(mode='real'):
    conn = get_connection(mode)
    df = pd.read_sql_query("SELECT * FROM assets ORDER BY asset_id", conn)
    conn.close()
    return df

def add_asset(data, mode='real'):
    conn = get_connection(mode)
    c = conn.cursor()
    c.execute("""
        INSERT INTO assets 
        (asset_id, merk, tipe, kapasitas, lokasi, refrigerant, installation_date, status) 
        VALUES (?,?,?,?,?,?,date('now'),'Aktif')
    """, data)
    conn.commit()
    conn.close()

def update_asset(asset_id, data, mode='real'):
    conn = get_connection(mode)
    c = conn.cursor()
    c.execute("""
        UPDATE assets 
        SET merk=?, tipe=?, kapasitas=?, lokasi=?, refrigerant=?, updated_at=CURRENT_TIMESTAMP
        WHERE asset_id=?
    """, (*data, asset_id))
    conn.commit()
    conn.close()

def delete_asset(asset_id, mode='real'):
    conn = get_connection(mode)
    c = conn.cursor()
    c.execute("DELETE FROM assets WHERE asset_id=?", (asset_id,))
    conn.commit()
    conn.close()

def add_log(data, mode='real'):
    conn = get_connection(mode)
    c = conn.cursor()
    if len(data) < 16:
        data = list(data) + [None] * (16 - len(data))
    c.execute("""
        INSERT INTO maintenance_logs 
        (asset_id, tanggal, teknisi, v_supply, amp_kompresor, low_p, 
         temp_ret, temp_sup, delta_t, drainage, test_run, health_score, 
         sparepart_cost, catatan, high_p, temp_outdoor) 
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
    """, data[:16])
    c.execute("UPDATE assets SET last_maintenance = ? WHERE asset_id = ?", (data[1], data[0]))
    conn.commit()
    conn.close()

def get_all_logs(mode='real'):
    conn = get_connection(mode)
    df = pd.read_sql_query("""
        SELECT m.*, a.lokasi, a.merk, a.kapasitas 
        FROM maintenance_logs m 
        JOIN assets a ON m.asset_id = a.asset_id 
        ORDER BY m.tanggal DESC, m.id DESC
    """, conn)
    conn.close()
    return df

def delete_log(log_id, mode='real'):
    conn = get_connection(mode)
    c = conn.cursor()
    c.execute("DELETE FROM maintenance_logs WHERE id=?", (log_id,))
    conn.commit()
    conn.close()

def delete_old_logs(days_to_keep, mode='real'):
    conn = get_connection(mode)
    c = conn.cursor()
    cutoff_date = (datetime.now() - timedelta(days=days_to_keep)).strftime('%Y-%m-%d')
    c.execute("DELETE FROM maintenance_logs WHERE tanggal < ?", (cutoff_date,))
    deleted = c.rowcount
    conn.commit()
    conn.close()
    return deleted

def get_vehicles(mode='real'):
    conn = get_connection(mode)
    df = pd.read_sql_query("SELECT * FROM vehicles ORDER BY vehicle_id", conn)
    conn.close()
    return df

def add_vehicle(data, mode='real'):
    conn = get_connection(mode)
    c = conn.cursor()
    c.execute("""
        INSERT INTO vehicles 
        (vehicle_id, brand, model, year, plate_number, color, fuel_type, status, 
         purchase_date, last_odometer, notes) 
        VALUES (?,?,?,?,?,?,?,?,?,?,?)
    """, data[:11])
    conn.commit()
    conn.close()

def update_vehicle(vehicle_id, data, mode='real'):
    conn = get_connection(mode)
    c = conn.cursor()
    c.execute("""
        UPDATE vehicles 
        SET brand=?, model=?, year=?, plate_number=?, color=?, 
            fuel_type=?, status=?, purchase_date=?, last_odometer=?, notes=?,
            updated_at=CURRENT_TIMESTAMP
        WHERE vehicle_id=?
    """, (*data[:10], vehicle_id))
    conn.commit()
    conn.close()

def update_vehicle_odometer(vehicle_id, odometer, mode='real'):
    conn = get_connection(mode)
    c = conn.cursor()
    c.execute("UPDATE vehicles SET last_odometer = ? WHERE vehicle_id = ? AND last_odometer < ?", 
              (odometer, vehicle_id, odometer))
    conn.commit()
    conn.close()

def delete_vehicle(vehicle_id, mode='real'):
    conn = get_connection(mode)
    c = conn.cursor()
    c.execute("DELETE FROM vehicles WHERE vehicle_id=?", (vehicle_id,))
    conn.commit()
    conn.close()

def add_vehicle_service(data, mode='real'):
    conn = get_connection(mode)
    c = conn.cursor()
    c.execute("""
        INSERT INTO vehicle_service_logs 
        (vehicle_id, service_date, odometer, service_type, component_name,
         component_life_km, component_life_months, current_usage_km,
         current_usage_months, next_service_km, next_service_months, 
         cost, mechanic_name, notes) 
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)
    """, data[:14])
    conn.commit()
    conn.close()

def get_vehicle_services(vehicle_id=None, mode='real'):
    conn = get_connection(mode)
    if vehicle_id:
        df = pd.read_sql_query("""
            SELECT * FROM vehicle_service_logs 
            WHERE vehicle_id = ? 
            ORDER BY service_date DESC, id DESC
        """, conn, params=(vehicle_id,))
    else:
        df = pd.read_sql_query("SELECT * FROM vehicle_service_logs ORDER BY service_date DESC, id DESC", conn)
    conn.close()
    return df

def delete_vehicle_service(service_id, mode='real'):
    conn = get_connection(mode)
    c = conn.cursor()
    c.execute("DELETE FROM vehicle_service_logs WHERE id=?", (service_id,))
    conn.commit()
    conn.close()

def get_vehicle_components(mode='real'):
    conn = get_connection(mode)
    df = pd.read_sql_query("SELECT * FROM vehicle_components WHERE is_active = 1 ORDER BY priority, component_name", conn)
    conn.close()
    return df

def add_vehicle_component(data, mode='real'):
    conn = get_connection(mode)
    c = conn.cursor()
    c.execute("""
        INSERT INTO vehicle_components 
        (component_name, standard_life_km, standard_life_months, is_active) 
        VALUES (?,?,?,?)
    """, data[:4])
    conn.commit()
    conn.close()

if __name__ == "__main__":
    print("Initializing BPF Asset Management Database...")
    create_db('real')
    init_bpf_assets('real')
    init_vehicle_components('real')
    init_sample_vehicles('real')
    print("Real database initialized!")
    
    print("Initializing Demo Database...")
    create_db('demo')
    init_bpf_assets('demo')
    init_vehicle_components('demo')
    init_sample_vehicles('demo')
    generate_dummy_vehicles(10, 'demo')
    generate_dummy_ac_logs(50, 'demo')
    generate_dummy_vehicle_services(30, 'demo')
    print("Demo database initialized!")