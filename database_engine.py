import sqlite3
import pandas as pd
import numpy as np
import os
import hashlib
import logging
from datetime import datetime, timedelta
import random
from pathlib import Path
import json
import shutil

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database paths
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / 'data'
DATA_DIR.mkdir(exist_ok=True)

# Real database path
REAL_DB_PATH = DATA_DIR / 'bpf_ac_ai_system.db'

# Demo database path
DEMO_DB_PATH = DATA_DIR / 'bpf_ac_ai_system_demo.db'

# Backup directory
BACKUP_DIR = DATA_DIR / 'backups'
BACKUP_DIR.mkdir(exist_ok=True)

def get_db_path(mode='real'):
    """Get database path based on mode"""
    if mode == 'demo':
        return str(DEMO_DB_PATH)
    return str(REAL_DB_PATH)

def get_connection(mode='real'):
    """Get database connection with proper path and security settings"""
    db_path = get_db_path(mode)
    conn = sqlite3.connect(db_path, timeout=30)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA synchronous = NORMAL")
    return conn

def backup_database(mode='real'):
    """Create a backup of the database"""
    try:
        db_path = get_db_path(mode)
        if os.path.exists(db_path):
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_path = BACKUP_DIR / f"backup_{mode}_{timestamp}.db"
            shutil.copy(db_path, backup_path)
            
            # Keep only last 10 backups
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
    """Create database tables with enhanced schema"""
    conn = get_connection(mode)
    c = conn.cursor()
    
    # Master Aset AC with additional fields
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

    # Master Aset Kendaraan with additional fields
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

    # Log Maintenance AC with additional measurements
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
    
    # Log Servis Kendaraan with additional tracking
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
    
    # Komponen yang perlu dipantau
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
    
    # Audit log table for tracking changes
    c.execute('''CREATE TABLE IF NOT EXISTS audit_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    table_name TEXT NOT NULL,
                    record_id TEXT,
                    action TEXT NOT NULL,
                    user_name TEXT,
                    old_values TEXT,
                    new_values TEXT,
                    timestamp TEXT DEFAULT CURRENT_TIMESTAMP)''')
    
    # User sessions table
    c.execute('''CREATE TABLE IF NOT EXISTS user_sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT NOT NULL,
                    session_token TEXT UNIQUE,
                    login_time TEXT,
                    logout_time TEXT,
                    ip_address TEXT,
                    user_agent TEXT)''')
    
    # Create indexes for better performance
    c.execute('CREATE INDEX IF NOT EXISTS idx_logs_asset_date ON maintenance_logs(asset_id, tanggal)')
    c.execute('CREATE INDEX IF NOT EXISTS idx_logs_health ON maintenance_logs(health_score)')
    c.execute('CREATE INDEX IF NOT EXISTS idx_vehicle_services_vehicle ON vehicle_service_logs(vehicle_id, service_date)')
    c.execute('CREATE INDEX IF NOT EXISTS idx_vehicle_services_component ON vehicle_service_logs(component_name)')
    
    # Create triggers for updated_at
    c.execute('''
        CREATE TRIGGER IF NOT EXISTS update_assets_timestamp 
        AFTER UPDATE ON assets
        BEGIN
            UPDATE assets SET updated_at = CURRENT_TIMESTAMP WHERE asset_id = NEW.asset_id;
        END;
    ''')
    
    c.execute('''
        CREATE TRIGGER IF NOT EXISTS update_vehicles_timestamp 
        AFTER UPDATE ON vehicles
        BEGIN
            UPDATE vehicles SET updated_at = CURRENT_TIMESTAMP WHERE vehicle_id = NEW.vehicle_id;
        END;
    ''')
    
    conn.commit()
    conn.close()
    logger.info(f"Database created/verified successfully in {mode} mode")

def init_bpf_assets(mode='real'):
    """Daftar 15 Aset AC sesuai Layout BPF SBY dengan data tambahan"""
    conn = get_connection(mode)
    c = conn.cursor()
    
    assets = [
        ("AC-01-R. BEST 8", "Daikin", "Split Duct", "60.000 Btu/h", "R. BEST 8", "R32", 
         "2020-01-15", "2025-01-15", "Aktif"),
        ("AC-02-R. BEST 7, OPERATIONAL", "Daikin", "Split Duct", "60.000 Btu/h", "R. BEST 7, OPERATIONAL", "R32",
         "2020-01-15", "2025-01-15", "Aktif"),
        ("AC-03-R. BEST 6", "Daikin", "Split Duct", "60.000 Btu/h", "R. BEST 6", "R32",
         "2020-01-15", "2025-01-15", "Aktif"),
        ("AC-04-R. BEST 5", "Daikin", "Split Duct", "60.000 Btu/h", "R. BEST 5", "R32",
         "2020-01-15", "2025-01-15", "Aktif"),
        ("AC-05-R. BEST 3, VIP 8", "Daikin", "Split Duct", "100.000 Btu/h", "R. BEST 3, VIP 8", "R32",
         "2020-01-15", "2025-01-15", "Aktif"),
        ("AC-06-R. BEST 2, VIP 6 & 7", "Daikin", "Split Duct", "60.000 Btu/h", "R. BEST 2, VIP 6 & 7", "R32",
         "2020-01-15", "2025-01-15", "Aktif"),
        ("AC-07-R. BEST 1, VIP 3 & 5", "Daikin", "Split Duct", "60.000 Btu/h", "R. BEST 1, VIP 3 & 5", "R32",
         "2020-01-15", "2025-01-15", "Aktif"),
        ("AC-08-R. KARAOKE", "Daikin", "Split Duct", "100.000 Btu/h", "R. KARAOKE", "R32",
         "2020-01-15", "2025-01-15", "Aktif"),
        ("AC-09-LOUNGE 1, 2, VIP 1, 2", "Daikin", "Split Duct", "60.000 Btu/h", "LOUNGE 1, 2, VIP 1, 2", "R32",
         "2020-01-15", "2025-01-15", "Aktif"),
        ("AC-10-R. BM & R. FINANCE", "Daikin", "Split Duct", "60.000 Btu/h", "R. BM & R. FINANCE", "R32",
         "2020-01-15", "2025-01-15", "Aktif"),
        ("AC-11-R. MEETING & RECEPTIONIST", "Daikin", "Split Duct", "60.000 Btu/h", "R. MEETING & RECEPTIONIST", "R32",
         "2020-01-15", "2025-01-15", "Aktif"),
        ("AC-12-R. TRAINER & R. SECRETARY", "Daikin", "Split Duct", "60.000 Btu/h", "R. TRAINER & R. SECRETARY", "R32",
         "2020-01-15", "2025-01-15", "Aktif"),
        ("AC-13-COMPLIANCE & TRAINING 2", "Daikin", "Split Duct", "60.000 Btu/h", "COMPLIANCE & TRAINING 2", "R32",
         "2020-01-15", "2025-01-15", "Aktif"),
        ("AC-14-IT & R. SERVER", "Daikin", "Split Duct", "60.000 Btu/h", "IT & R. SERVER", "R32",
         "2020-01-15", "2025-01-15", "Aktif"),
        ("AC-15-RUANG TRAINING 1", "Daikin", "Split Wall", "2 PK", "RUANG TRAINING 1", "R32",
         "2020-01-15", "2025-01-15", "Aktif")
    ]
    
    c.executemany("""
        INSERT OR IGNORE INTO assets 
        (asset_id, merk, tipe, kapasitas, lokasi, refrigerant, installation_date, warranty_until, status) 
        VALUES (?,?,?,?,?,?,?,?,?)
    """, assets)
    
    conn.commit()
    conn.close()
    logger.info(f"BPF assets initialized in {mode} mode")

def init_vehicle_components(mode='real'):
    """Inisialisasi komponen standar kendaraan dengan kategori"""
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
        ("V-Belt", 40000, 24, 1, "Mesin", 2, 450000, "Periksa setiap servis"),
        ("Timing Belt", 80000, 48, 1, "Mesin", 1, 2500000, "KRITIS - Ganti tepat waktu"),
        ("Shock Absorber", 60000, 48, 1, "Suspensi", 3, 3500000, "Ganti sesuai kondisi"),
        ("Bearing Roda", 60000, 48, 1, "Roda", 2, 1200000, "Periksa dan ganti jika perlu"),
        ("Water Pump", 80000, 60, 1, "Pendingin", 2, 1500000, "Ganti bersama timing belt"),
        ("Fuel Filter", 40000, 24, 1, "Bahan Bakar", 2, 450000, "Ganti untuk diesel, periksa untuk bensin"),
        ("Air Filter AC", 30000, 12, 1, "AC", 3, 350000, "Ganti untuk performa AC optimal"),
        ("Busi Glow Plug", 60000, 36, 1, "Pengapian", 2, 1200000, "Khusus mesin diesel"),
        ("Injector Cleaner", 30000, 12, 1, "Bahan Bakar", 3, 250000, "Service rutin")
    ]
    
    c.executemany("""
        INSERT OR IGNORE INTO vehicle_components 
        (component_name, standard_life_km, standard_life_months, is_active, category, priority, estimated_cost, notes) 
        VALUES (?,?,?,?,?,?,?,?)
    """, components)
    
    conn.commit()
    conn.close()
    logger.info(f"Vehicle components initialized in {mode} mode")

def init_sample_vehicles(mode='real'):
    """Contoh data kendaraan kantor dengan data lengkap"""
    conn = get_connection(mode)
    c = conn.cursor()
    
    vehicles = [
        ("VH-001", "Toyota", "Innova", 2020, "B 1234 ABC", "Hitam", "Bensin", "Aktif", 
         "2020-01-15", 85000, "Mobil Operasional Direktur", "2025-01-15", "2025-01-15"),
        ("VH-002", "Honda", "CRV", 2021, "B 5678 DEF", "Putih", "Bensin", "Aktif", 
         "2021-03-20", 45000, "Mobil Operasional Manager", "2026-03-20", "2025-03-20"),
        ("VH-003", "Mitsubishi", "Xpander", 2022, "B 9012 GHI", "Silver", "Bensin", "Aktif", 
         "2022-06-10", 28000, "Mobil Antar Jemput Karyawan", "2027-06-10", "2025-06-10"),
        ("VH-004", "Suzuki", "Carry", 2019, "B 3456 JKL", "Putih", "Bensin", "Aktif", 
         "2019-11-05", 120000, "Mobil Operasional Logistik", "2024-11-05", "2024-11-05"),
        ("VH-005", "Toyota", "Hiace", 2018, "B 7890 MNO", "Abu-abu", "Solar", "Aktif", 
         "2018-08-12", 180000, "Mobil Antar Jemput & Operasional", "2023-08-12", "2024-08-12")
    ]
    
    c.executemany("""
        INSERT OR IGNORE INTO vehicles 
        (vehicle_id, brand, model, year, plate_number, color, fuel_type, status, 
         purchase_date, last_odometer, notes, insurance_until, tax_until) 
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
    """, vehicles)
    
    conn.commit()
    conn.close()
    logger.info(f"Sample vehicles initialized in {mode} mode")

def generate_dummy_ac_logs(logs_per_asset=100, mode='demo'):
    """Generate extensive dummy AC maintenance logs"""
    conn = get_connection(mode)
    
    # Get all assets
    assets_df = pd.read_sql_query("SELECT asset_id FROM assets", conn)
    asset_ids = assets_df['asset_id'].tolist()
    
    # Start from 2 years ago
    start_date = datetime.now() - timedelta(days=730)
    
    dummy_logs = []
    teknisi_list = ['Andi Wijaya', 'Budi Santoso', 'Cahyo Purnomo', 'Dedi Kurniawan', 'Eko Prasetyo', 
                    'Fajar Setiawan', 'Gunawan Wibowo', 'Hendra Gunawan', 'Irfan Maulana', 'Joko Susilo']
    
    logger.info(f"Generating {logs_per_asset} logs per asset for {len(asset_ids)} assets...")
    
    for asset_idx, asset_id in enumerate(asset_ids):
        # Generate unique degradation pattern per asset
        base_amp = 15 + (hash(asset_id) % 10)
        base_delta_t = 12 - (hash(asset_id) % 5)
        degradation_rate = 0.02 + (hash(asset_id) % 5) * 0.005
        
        for i in range(logs_per_asset):
            # Progressive date (every 3-10 days)
            days_offset = i * random.randint(3, 10)
            log_date = start_date + timedelta(days=days_offset)
            
            # Skip if date is in future
            if log_date > datetime.now():
                continue
            
            # Simulate seasonal effects
            month_factor = 1 + 0.1 * np.sin(2 * np.pi * log_date.month / 12)
            
            # Simulate degradation over time
            degradation_factor = 1 + (i / logs_per_asset) * degradation_rate * 10
            
            # Generate parameters with realistic variations
            amp = base_amp * degradation_factor * month_factor + np.random.normal(0, 1.5)
            amp = max(8, min(35, amp))
            
            temp_ret = 24 + np.random.normal(0, 1)
            temp_sup = temp_ret - (base_delta_t / degradation_factor) + np.random.normal(0, 0.8)
            delta_t = temp_ret - temp_sup
            delta_t = max(2, min(15, delta_t))
            
            v_supply = 380 + np.random.normal(0, 8)
            low_p = 140 + np.random.normal(0, 12)
            high_p = 350 + np.random.normal(0, 20)
            temp_outdoor = 32 + 5 * np.sin(2 * np.pi * log_date.month / 12) + np.random.normal(0, 2)
            
            # Calculate health score
            health_score = 100
            if delta_t < 12:
                health_score -= (12 - delta_t) * 5
            if amp > 25:
                health_score -= (amp - 25) * 3
            elif amp > 20:
                health_score -= (amp - 20) * 2
            
            health_score = max(20, min(100, int(health_score)))
            
            # Add random anomalies
            if random.random() < 0.05:  # 5% chance of anomaly
                health_score = max(20, health_score - random.randint(20, 40))
                delta_t = max(2, delta_t - random.uniform(3, 6))
                amp = amp * random.uniform(1.2, 1.5)
            
            # Determine status
            drainage = random.choice(['Lancar'] * 8 + ['Tersumbat', 'Perlu Pembersihan'])
            test_run = 'Normal' if health_score >= 65 else 'Abnormal'
            teknisi = random.choice(teknisi_list)
            
            # Cost based on issues found
            sparepart_cost = 0
            if health_score < 70:
                sparepart_cost = random.randint(150000, 2000000)
            elif health_score < 85:
                sparepart_cost = random.randint(0, 500000)
            
            # Generate notes
            notes_options = [
                "Servis rutin bulanan - semua normal",
                "Pembersihan filter dan evaporator",
                "Pengecekan tekanan freon - normal",
                "Pembersihan menyeluruh unit indoor",
                "Pengecekan kompresor dan kelistrikan",
                "Perlu perhatian pada tekanan freon",
                "Freon perlu ditambah",
                "Filter kotor - sudah dibersihkan",
                "Drainase tersumbat - sudah dibersihkan",
                "Kompresor bekerja normal",
                "Suhu tidak optimal - perlu pengecekan",
                "Ditemukan kebocoran kecil - sudah diperbaiki",
                ""
            ]
            catatan = random.choice(notes_options)
            
            # Next service recommendation
            next_service = log_date + timedelta(days=90) if health_score > 70 else log_date + timedelta(days=30)
            
            dummy_logs.append((
                asset_id,
                log_date.strftime('%Y-%m-%d'),
                teknisi,
                round(v_supply, 1),
                round(amp, 2),
                round(low_p, 1),
                round(high_p, 1),
                round(temp_ret, 1),
                round(temp_sup, 1),
                round(temp_outdoor, 1),
                round(delta_t, 1),
                drainage,
                test_run,
                health_score,
                sparepart_cost,
                catatan,
                next_service.strftime('%Y-%m-%d')
            ))
        
        if (asset_idx + 1) % 5 == 0:
            logger.info(f"Generated logs for {asset_idx + 1}/{len(asset_ids)} assets")
    
    # Batch insert for better performance
    c = conn.cursor()
    batch_size = 100
    for i in range(0, len(dummy_logs), batch_size):
        batch = dummy_logs[i:i+batch_size]
        c.executemany("""
            INSERT INTO maintenance_logs 
            (asset_id, tanggal, teknisi, v_supply, amp_kompresor, low_p, high_p, 
             temp_ret, temp_sup, temp_outdoor, delta_t, drainage, test_run, 
             health_score, sparepart_cost, catatan, next_service_date) 
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, batch)
    
    conn.commit()
    conn.close()
    logger.info(f"? Generated {len(dummy_logs)} dummy AC maintenance logs")

def generate_dummy_vehicle_services(services_per_vehicle=50, mode='demo'):
    """Generate extensive dummy vehicle service logs"""
    conn = get_connection(mode)
    
    # Get all vehicles
    vehicles_df = pd.read_sql_query("SELECT vehicle_id, last_odometer, purchase_date FROM vehicles", conn)
    
    # Get components
    components_df = pd.read_sql_query("SELECT component_name, standard_life_km, standard_life_months, estimated_cost FROM vehicle_components WHERE is_active = 1", conn)
    
    start_date = datetime.now() - timedelta(days=1095)  # 3 years ago
    
    dummy_services = []
    mechanic_list = ['Bengkel Maju Jaya', 'Auto2000', 'Bengkel Jaya Motor', 'Montir Internal BPF',
                     'Honda Authorized Service', 'Toyota Authorized Service', 'Bengkel Cepat Tepat',
                     'Car Care Center', 'Bengkel Sejahtera', 'Master Mechanic']
    
    logger.info(f"Generating {services_per_vehicle} services per vehicle for {len(vehicles_df)} vehicles...")
    
    for v_idx, vehicle in vehicles_df.iterrows():
        vehicle_id = vehicle['vehicle_id']
        current_odometer = vehicle['last_odometer']
        purchase_date = pd.to_datetime(vehicle['purchase_date'])
        
        # Calculate average km per month for realistic odometer progression
        months_since_purchase = (datetime.now() - purchase_date).days / 30
        avg_km_per_month = current_odometer / max(1, months_since_purchase)
        
        for i in range(services_per_vehicle):
            # Progressive date (every 20-40 days)
            days_offset = i * random.randint(20, 40)
            service_date = start_date + timedelta(days=days_offset)
            
            # Skip if date is in future
            if service_date > datetime.now():
                continue
            
            # Progressive odometer
            months_from_start = (service_date - start_date).days / 30
            service_odometer = int(avg_km_per_month * months_from_start)
            service_odometer = min(current_odometer, max(0, service_odometer))
            service_odometer += random.randint(-2000, 2000)
            
            # Select component based on realistic service patterns
            if i % 5 == 0:  # Regular oil change
                component = components_df[components_df['component_name'] == 'Oli Mesin'].iloc[0]
            elif i % 10 == 0:  # Major service
                component = components_df[components_df['priority'] == 1].sample(1).iloc[0]
            else:
                component = components_df.sample(1).iloc[0]
            
            component_name = component['component_name']
            life_km = component['standard_life_km']
            life_months = component['standard_life_months']
            base_cost = component['estimated_cost']
            
            # Add realistic cost variation
            cost = base_cost * random.uniform(0.8, 1.3)
            
            # Determine service type
            if 'Oli' in component_name or 'Filter' in component_name:
                service_type = 'Servis Rutin'
            elif random.random() < 0.7:
                service_type = 'Penggantian Komponen'
            else:
                service_type = random.choice(['Perbaikan', 'Servis Rutin', 'Inspeksi'])
            
            mechanic = random.choice(mechanic_list)
            
            next_km = service_odometer + life_km if life_km > 0 else 0
            next_months = life_months
            
            # Generate notes
            notes = f"Servis {component_name} - "
            if service_type == 'Servis Rutin':
                notes += "Servis rutin berkala"
            elif service_type == 'Penggantian Komponen':
                notes += f"Penggantian {component_name} sesuai jadwal"
            else:
                notes += "Pengecekan dan perbaikan"
            
            # Parts replaced
            parts_replaced = component_name if service_type == 'Penggantian Komponen' else ''
            
            # Invoice number
            invoice_number = f"INV/{vehicle_id}/{service_date.strftime('%Y%m%d')}/{random.randint(100, 999)}"
            
            dummy_services.append((
                vehicle_id,
                service_date.strftime('%Y-%m-%d'),
                service_odometer,
                service_type,
                component_name,
                life_km,
                life_months,
                0,  # current_usage_km
                0,  # current_usage_months
                next_km,
                next_months,
                round(cost, -3),  # Round to nearest thousand
                mechanic,
                notes,
                parts_replaced,
                invoice_number
            ))
        
        if (v_idx + 1) % 5 == 0:
            logger.info(f"Generated services for {v_idx + 1}/{len(vehicles_df)} vehicles")
    
    # Batch insert
    c = conn.cursor()
    batch_size = 100
    for i in range(0, len(dummy_services), batch_size):
        batch = dummy_services[i:i+batch_size]
        c.executemany("""
            INSERT INTO vehicle_service_logs 
            (vehicle_id, service_date, odometer, service_type, component_name,
             component_life_km, component_life_months, current_usage_km,
             current_usage_months, next_service_km, next_service_months, 
             cost, mechanic_name, notes, parts_replaced, invoice_number) 
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, batch)
        
        # Update vehicle odometer if higher
        for service in batch:
            vehicle_id = service[0]
            odometer = service[2]
            c.execute("""
                UPDATE vehicles SET last_odometer = ? 
                WHERE vehicle_id = ? AND last_odometer < ?
            """, (odometer, vehicle_id, odometer))
    
    conn.commit()
    conn.close()
    logger.info(f"? Generated {len(dummy_services)} dummy vehicle service logs")

def generate_dummy_vehicles(count=15, mode='demo'):
    """Generate additional dummy vehicles for demo mode"""
    conn = get_connection(mode)
    c = conn.cursor()
    
    brands = ['Toyota', 'Honda', 'Mitsubishi', 'Suzuki', 'Daihatsu', 'Nissan', 'Mazda', 'Hyundai', 'Kia', 'Wuling']
    models = {
        'Toyota': ['Avanza', 'Innova', 'Fortuner', 'Rush', 'Yaris', 'Vios', 'Camry', 'Hilux'],
        'Honda': ['Brio', 'Jazz', 'City', 'Civic', 'HR-V', 'CR-V', 'Mobilio', 'BR-V'],
        'Mitsubishi': ['Xpander', 'Pajero', 'Triton', 'Outlander', 'L300', 'Colt Diesel'],
        'Suzuki': ['Ertiga', 'XL7', 'Carry', 'APV', 'Baleno', 'Ignis', 'S-Presso'],
        'Daihatsu': ['Xenia', 'Terios', 'Sigra', 'Ayla', 'Rocky', 'Gran Max'],
        'Nissan': ['Livina', 'March', 'Kicks', 'Navara', 'Serena', 'Terra'],
        'Mazda': ['CX-3', 'CX-5', 'CX-9', '2', '3', 'BT-50'],
        'Hyundai': ['Creta', 'Palisade', 'Santa Fe', 'Staria', 'Ioniq'],
        'Kia': ['Seltos', 'Sonet', 'Grand Carnival', 'Picanto'],
        'Wuling': ['Confero', 'Cortez', 'Almaz', 'Formo']
    }
    colors = ['Hitam', 'Putih', 'Silver', 'Abu-abu', 'Merah', 'Biru', 'Coklat', 'Hijau']
    fuel_types = ['Bensin', 'Solar', 'Listrik', 'Hybrid']
    statuses = ['Aktif', 'Aktif', 'Aktif', 'Aktif', 'Service', 'Nonaktif']
    
    # Get existing vehicle IDs
    existing = pd.read_sql_query("SELECT vehicle_id FROM vehicles", conn)
    existing_ids = set(existing['vehicle_id'].tolist())
    
    new_vehicles = []
    for i in range(count):
        # Generate unique ID
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
        status = random.choice(statuses)
        
        # Purchase date between 1-5 years ago
        purchase_date = datetime.now() - timedelta(days=random.randint(365, 1825))
        
        # Odometer based on age
        months_old = (datetime.now() - purchase_date).days / 30
        avg_km_per_month = random.randint(1000, 3000)
        odometer = int(months_old * avg_km_per_month)
        
        notes = f"Kendaraan operasional {brand} {model}"
        insurance_until = (datetime.now() + timedelta(days=random.randint(180, 540))).strftime('%Y-%m-%d')
        tax_until = (datetime.now() + timedelta(days=random.randint(90, 450))).strftime('%Y-%m-%d')
        
        new_vehicles.append((
            new_id, brand, model, year, plate, color, fuel, status,
            purchase_date.strftime('%Y-%m-%d'), odometer, notes, insurance_until, tax_until
        ))
    
    c.executemany("""
        INSERT OR IGNORE INTO vehicles 
        (vehicle_id, brand, model, year, plate_number, color, fuel_type, status,
         purchase_date, last_odometer, notes, insurance_until, tax_until)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
    """, new_vehicles)
    
    conn.commit()
    conn.close()
    logger.info(f"? Generated {len(new_vehicles)} additional dummy vehicles")

# Fungsi CRUD untuk AC Assets
def get_assets(mode='real'):
    """Get all AC assets"""
    conn = get_connection(mode)
    df = pd.read_sql_query("SELECT * FROM assets ORDER BY asset_id", conn)
    conn.close()
    return df

def add_asset(data, mode='real'):
    """Add new AC asset"""
    conn = get_connection(mode)
    c = conn.cursor()
    c.execute("""
        INSERT INTO assets 
        (asset_id, merk, tipe, kapasitas, lokasi, refrigerant, installation_date, status) 
        VALUES (?,?,?,?,?,?,date('now'),'Aktif')
    """, data)
    conn.commit()
    conn.close()
    logger.info(f"Added new asset: {data[0]}")

def update_asset(asset_id, data, mode='real'):
    """Update AC asset"""
    conn = get_connection(mode)
    c = conn.cursor()
    c.execute("""
        UPDATE assets 
        SET merk=?, tipe=?, kapasitas=?, lokasi=?, refrigerant=?, updated_at=CURRENT_TIMESTAMP
        WHERE asset_id=?
    """, (*data, asset_id))
    conn.commit()
    conn.close()
    logger.info(f"Updated asset: {asset_id}")

def delete_asset(asset_id, mode='real'):
    """Delete AC asset"""
    conn = get_connection(mode)
    c = conn.cursor()
    c.execute("DELETE FROM assets WHERE asset_id=?", (asset_id,))
    conn.commit()
    conn.close()
    logger.info(f"Deleted asset: {asset_id}")

def add_log(data, mode='real'):
    """Add maintenance log"""
    conn = get_connection(mode)
    c = conn.cursor()
    
    # If data has fewer columns than expected, pad with None
    if len(data) == 14:
        data = list(data)
        data.extend([None, None])  # Add high_p and temp_outdoor
    elif len(data) == 15:
        data = list(data)
        data.append(None)  # Add temp_outdoor
    
    c.execute("""
        INSERT INTO maintenance_logs 
        (asset_id, tanggal, teknisi, v_supply, amp_kompresor, low_p, 
         temp_ret, temp_sup, delta_t, drainage, test_run, health_score, 
         sparepart_cost, catatan, high_p, temp_outdoor) 
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
    """, data[:16])
    
    # Update last_maintenance in assets
    c.execute("""
        UPDATE assets 
        SET last_maintenance = ? 
        WHERE asset_id = ?
    """, (data[1], data[0]))
    
    conn.commit()
    conn.close()
    logger.info(f"Added maintenance log for asset: {data[0]}")

def get_all_logs(mode='real'):
    """Get all maintenance logs with asset info"""
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
    """Delete maintenance log"""
    conn = get_connection(mode)
    c = conn.cursor()
    c.execute("DELETE FROM maintenance_logs WHERE id=?", (log_id,))
    conn.commit()
    conn.close()
    logger.info(f"Deleted maintenance log: {log_id}")

def delete_old_logs(days_to_keep, mode='real'):
    """Delete logs older than specified days"""
    conn = get_connection(mode)
    c = conn.cursor()
    cutoff_date = (datetime.now() - timedelta(days=days_to_keep)).strftime('%Y-%m-%d')
    c.execute("DELETE FROM maintenance_logs WHERE tanggal < ?", (cutoff_date,))
    deleted = c.rowcount
    conn.commit()
    conn.close()
    logger.info(f"Deleted {deleted} old logs")
    return deleted

# Fungsi CRUD untuk Kendaraan
def get_vehicles(mode='real'):
    """Get all vehicles"""
    conn = get_connection(mode)
    df = pd.read_sql_query("SELECT * FROM vehicles ORDER BY vehicle_id", conn)
    conn.close()
    return df

def add_vehicle(data, mode='real'):
    """Add new vehicle"""
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
    logger.info(f"Added new vehicle: {data[0]}")

def update_vehicle(vehicle_id, data, mode='real'):
    """Update vehicle"""
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
    logger.info(f"Updated vehicle: {vehicle_id}")

def update_vehicle_odometer(vehicle_id, odometer, mode='real'):
    """Update vehicle odometer"""
    conn = get_connection(mode)
    c = conn.cursor()
    c.execute("""
        UPDATE vehicles 
        SET last_odometer = ?, updated_at = CURRENT_TIMESTAMP
        WHERE vehicle_id = ? AND last_odometer < ?
    """, (odometer, vehicle_id, odometer))
    conn.commit()
    conn.close()

def delete_vehicle(vehicle_id, mode='real'):
    """Delete vehicle"""
    conn = get_connection(mode)
    c = conn.cursor()
    c.execute("DELETE FROM vehicles WHERE vehicle_id=?", (vehicle_id,))
    conn.commit()
    conn.close()
    logger.info(f"Deleted vehicle: {vehicle_id}")

# Fungsi CRUD untuk Servis Kendaraan
def add_vehicle_service(data, mode='real'):
    """Add vehicle service log"""
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
    logger.info(f"Added service log for vehicle: {data[0]}")

def get_vehicle_services(vehicle_id=None, mode='real'):
    """Get vehicle service logs"""
    conn = get_connection(mode)
    if vehicle_id:
        df = pd.read_sql_query("""
            SELECT * FROM vehicle_service_logs 
            WHERE vehicle_id = ? 
            ORDER BY service_date DESC, id DESC
        """, conn, params=(vehicle_id,))
    else:
        df = pd.read_sql_query("""
            SELECT * FROM vehicle_service_logs 
            ORDER BY service_date DESC, id DESC
        """, conn)
    conn.close()
    return df

def delete_vehicle_service(service_id, mode='real'):
    """Delete vehicle service log"""
    conn = get_connection(mode)
    c = conn.cursor()
    c.execute("DELETE FROM vehicle_service_logs WHERE id=?", (service_id,))
    conn.commit()
    conn.close()
    logger.info(f"Deleted vehicle service: {service_id}")

# Fungsi untuk Vehicle Components
def get_vehicle_components(mode='real'):
    """Get all vehicle components"""
    conn = get_connection(mode)
    df = pd.read_sql_query("""
        SELECT * FROM vehicle_components 
        WHERE is_active = 1 
        ORDER BY priority, component_name
    """, conn)
    conn.close()
    return df

def add_vehicle_component(data, mode='real'):
    """Add vehicle component"""
    conn = get_connection(mode)
    c = conn.cursor()
    c.execute("""
        INSERT INTO vehicle_components 
        (component_name, standard_life_km, standard_life_months, is_active) 
        VALUES (?,?,?,?)
    """, data[:4])
    conn.commit()
    conn.close()
    logger.info(f"Added vehicle component: {data[0]}")

def update_vehicle_component(component_id, data, mode='real'):
    """Update vehicle component"""
    conn = get_connection(mode)
    c = conn.cursor()
    c.execute("""
        UPDATE vehicle_components 
        SET component_name=?, standard_life_km=?, standard_life_months=?, 
            is_active=?, updated_at=CURRENT_TIMESTAMP
        WHERE id=?
    """, (*data, component_id))
    conn.commit()
    conn.close()
    logger.info(f"Updated vehicle component: {component_id}")

# Audit functions
def log_audit(table_name, record_id, action, user_name, old_values=None, new_values=None, mode='real'):
    """Log audit trail"""
    try:
        conn = get_connection(mode)
        c = conn.cursor()
        c.execute("""
            INSERT INTO audit_logs 
            (table_name, record_id, action, user_name, old_values, new_values) 
            VALUES (?,?,?,?,?,?)
        """, (table_name, str(record_id), action, user_name, 
              json.dumps(old_values) if old_values else None,
              json.dumps(new_values) if new_values else None))
        conn.commit()
        conn.close()
    except Exception as e:
        logger.error(f"Failed to log audit: {e}")

def get_audit_logs(table_name=None, limit=100, mode='real'):
    """Get audit logs"""
    conn = get_connection(mode)
    if table_name:
        df = pd.read_sql_query("""
            SELECT * FROM audit_logs 
            WHERE table_name = ? 
            ORDER BY timestamp DESC 
            LIMIT ?
        """, conn, params=(table_name, limit))
    else:
        df = pd.read_sql_query("""
            SELECT * FROM audit_logs 
            ORDER BY timestamp DESC 
            LIMIT ?
        """, conn, params=(limit,))
    conn.close()
    return df

# Statistics functions
def get_dashboard_stats(mode='real'):
    """Get dashboard statistics"""
    conn = get_connection(mode)
    
    stats = {}
    
    # AC stats
    assets = pd.read_sql_query("SELECT COUNT(*) as count FROM assets", conn)
    stats['total_ac'] = assets['count'].iloc[0]
    
    logs = pd.read_sql_query("""
        SELECT COUNT(*) as count, AVG(health_score) as avg_health 
        FROM maintenance_logs 
        WHERE tanggal >= date('now', '-30 days')
    """, conn)
    stats['recent_logs'] = logs['count'].iloc[0]
    stats['avg_ac_health'] = logs['avg_health'].iloc[0] if logs['avg_health'].iloc[0] else 0
    
    # Vehicle stats
    vehicles = pd.read_sql_query("SELECT COUNT(*) as count FROM vehicles", conn)
    stats['total_vehicles'] = vehicles['count'].iloc[0]
    
    active_vehicles = pd.read_sql_query("SELECT COUNT(*) as count FROM vehicles WHERE status = 'Aktif'", conn)
    stats['active_vehicles'] = active_vehicles['count'].iloc[0]
    
    services = pd.read_sql_query("""
        SELECT COUNT(*) as count, SUM(cost) as total_cost 
        FROM vehicle_service_logs 
        WHERE service_date >= date('now', '-30 days')
    """, conn)
    stats['recent_services'] = services['count'].iloc[0]
    stats['recent_cost'] = services['total_cost'].iloc[0] if services['total_cost'].iloc[0] else 0
    
    conn.close()
    return stats

# Database maintenance functions
def vacuum_database(mode='real'):
    """Optimize database"""
    conn = get_connection(mode)
    conn.execute("VACUUM")
    conn.close()
    logger.info(f"Database vacuumed in {mode} mode")

def get_database_size(mode='real'):
    """Get database file size"""
    db_path = get_db_path(mode)
    if os.path.exists(db_path):
        size_bytes = os.path.getsize(db_path)
        size_mb = size_bytes / (1024 * 1024)
        return round(size_mb, 2)
    return 0

# Initialize database when module is imported
if __name__ == "__main__":
    print("?? Initializing BPF Asset Management Database...")
    create_db('real')
    init_bpf_assets('real')
    init_vehicle_components('real')
    init_sample_vehicles('real')
    print("? Real database initialized successfully!")
    
    print("\n?? Initializing Demo Database with extensive dummy data...")
    create_db('demo')
    init_bpf_assets('demo')
    init_vehicle_components('demo')
    init_sample_vehicles('demo')
    generate_dummy_vehicles(15, 'demo')
    generate_dummy_ac_logs(100, 'demo')
    generate_dummy_vehicle_services(50, 'demo')
    print("? Demo database initialized with extensive dummy data!")
    
    # Show stats
    stats = get_dashboard_stats('demo')
    print(f"\n?? Demo Database Stats:")
    print(f"   - Total AC: {stats['total_ac']}")
    print(f"   - Total Vehicles: {stats['total_vehicles']}")
    print(f"   - Recent AC Logs (30d): {stats['recent_logs']}")
    print(f"   - Recent Vehicle Services (30d): {stats['recent_services']}")