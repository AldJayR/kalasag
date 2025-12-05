"""
KALASAG - Barangay Information System
Database Schema and Initialization Module
"""

import sqlite3
import os
from datetime import datetime
import hashlib


DATABASE_PATH = "kalasag.db"


def get_connection():
    """Get a database connection with foreign keys enabled."""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.row_factory = sqlite3.Row
    return conn


def hash_password(password: str) -> str:
    """Hash a password using SHA-256."""
    return hashlib.sha256(password.encode()).hexdigest()


def init_database():
    """Initialize the database with all required tables."""
    conn = get_connection()
    cursor = conn.cursor()
    
    # ========================================
    # MASTER DATA TABLES
    # ========================================
    
    # purok Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS purok (
            purok_id INTEGER PRIMARY KEY AUTOINCREMENT,
            purok_name TEXT NOT NULL UNIQUE,
            assigned_tanod_leader TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # household Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS household (
            hh_id INTEGER PRIMARY KEY AUTOINCREMENT,
            house_number TEXT NOT NULL,
            street_name TEXT NOT NULL,
            purok_id INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (purok_id) REFERENCES purok(purok_id)
        )
    """)
    
    # resident Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS resident (
            res_id INTEGER PRIMARY KEY AUTOINCREMENT,
            first_name TEXT NOT NULL,
            middle_name TEXT,
            last_name TEXT NOT NULL,
            alias TEXT,
            birthdate DATE,
            sex TEXT CHECK(sex IN ('Male', 'Female')),
            civil_status TEXT CHECK(civil_status IN ('Single', 'Married', 'Widowed', 'Separated', 'Divorced')),
            occupation TEXT,
            purok_id INTEGER,
            hh_id INTEGER,
            is_indigent INTEGER DEFAULT 0,
            status TEXT DEFAULT 'Active' CHECK(status IN ('Active', 'Deceased', 'Moved Out')),
            photo_blob BLOB,
            contact_number TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (purok_id) REFERENCES purok(purok_id),
            FOREIGN KEY (hh_id) REFERENCES household(hh_id)
        )
    """)
    
    # user Table (for authentication)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            full_name TEXT NOT NULL,
            role TEXT NOT NULL CHECK(role IN ('Captain', 'Secretary', 'Tanod', 'Admin')),
            is_active INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP
        )
    """)
    
    # ========================================
    # TRANSACTION TABLES (BLOTTER)
    # ========================================
    
    # incident_type Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS incident_type (
            type_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            severity INTEGER NOT NULL CHECK(severity BETWEEN 1 AND 5),
            description TEXT
        )
    """)
    
    # blotter_case Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS blotter_case (
            case_id INTEGER PRIMARY KEY AUTOINCREMENT,
            case_number TEXT NOT NULL UNIQUE,
            date_time TIMESTAMP NOT NULL,
            narrative TEXT NOT NULL,
            purok_id INTEGER,
            type_id INTEGER,
            status TEXT DEFAULT 'Pending' CHECK(status IN ('Pending', 'Amicable Settlement', 'Escalated to PNP', 'Closed')),
            recorded_by INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (purok_id) REFERENCES purok(purok_id),
            FOREIGN KEY (type_id) REFERENCES incident_type(type_id),
            FOREIGN KEY (recorded_by) REFERENCES user(user_id)
        )
    """)
    
    # case_involvement Table (Links resident to blotter_case)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS case_involvement (
            link_id INTEGER PRIMARY KEY AUTOINCREMENT,
            case_id INTEGER NOT NULL,
            res_id INTEGER NOT NULL,
            role TEXT NOT NULL CHECK(role IN ('Complainant', 'Respondent', 'Witness')),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (case_id) REFERENCES blotter_case(case_id) ON DELETE CASCADE,
            FOREIGN KEY (res_id) REFERENCES resident(res_id),
            UNIQUE(case_id, res_id, role)
        )
    """)
    
    # ========================================
    # DOCUMENT LOG TABLES
    # ========================================
    
    # doc_log Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS doc_log (
            doc_id INTEGER PRIMARY KEY AUTOINCREMENT,
            control_number TEXT NOT NULL UNIQUE,
            res_id INTEGER NOT NULL,
            doc_type TEXT NOT NULL CHECK(doc_type IN ('Clearance', 'Indigency', 'Permit', 'Residency', 'Business Permit')),
            purpose TEXT,
            amount REAL DEFAULT 0,
            or_number TEXT,
            issued_by INTEGER,
            issued_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (res_id) REFERENCES resident(res_id),
            FOREIGN KEY (issued_by) REFERENCES user(user_id)
        )
    """)
    
    # ========================================
    # AUDIT LOG TABLE
    # ========================================
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS audit_log (
            log_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            action TEXT NOT NULL,
            table_name TEXT,
            record_id INTEGER,
            old_values TEXT,
            new_values TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES user(user_id)
        )
    """)
    
    # ========================================
    # INDEXES FOR PERFORMANCE
    # ========================================
    
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_resident_name ON resident(last_name, first_name)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_resident_purok ON resident(purok_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_resident_household ON resident(hh_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_blotter_date ON blotter_case(date_time)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_blotter_purok ON blotter_case(purok_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_blotter_status ON blotter_case(status)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_case_involvement_res ON case_involvement(res_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_doc_log_res ON doc_log(res_id)")
    
    conn.commit()
    conn.close()
    print("✅ Database initialized successfully!")


def seed_default_data():
    """Seed the database with default/sample data."""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Seed default Puroks (if empty)
    cursor.execute("SELECT COUNT(*) FROM purok")
    if cursor.fetchone()[0] == 0:
        puroks = [
            ("Purok 1 - Sampaguita", None),
            ("Purok 2 - Rosal", None),
            ("Purok 3 - Gumamela", None),
            ("Purok 4 - Santan", None),
            ("Purok 5 - Ilang-Ilang", None),
            ("Purok 6 - Orchid", None),
            ("Purok 7 - Dahlia", None),
        ]
        cursor.executemany("INSERT INTO purok (purok_name, assigned_tanod_leader) VALUES (?, ?)", puroks)
        print("✅ Default Puroks seeded.")
    
    # Seed default Incident Types (if empty)
    cursor.execute("SELECT COUNT(*) FROM incident_type")
    if cursor.fetchone()[0] == 0:
        incident_types = [
            ("Theft", 4, "Stealing of property"),
            ("Physical Assault", 5, "Physical violence against a person"),
            ("Verbal Assault / Threat", 3, "Verbal threats or harassment"),
            ("Trespassing", 2, "Unauthorized entry to property"),
            ("Vandalism", 3, "Destruction of property"),
            ("Noise Complaint", 1, "Excessive noise disturbance"),
            ("Domestic Dispute", 3, "Conflict within household"),
            ("Neighborhood Dispute", 2, "Conflict between neighbors"),
            ("Lost/Found Item", 1, "Report of lost or found property"),
            ("Stray Animals", 1, "Complaint about stray animals"),
            ("Illegal Gambling", 3, "Unauthorized gambling activities"),
            ("Public Intoxication", 2, "Disorderly conduct due to alcohol"),
        ]
        cursor.executemany("INSERT INTO incident_type (name, severity, description) VALUES (?, ?, ?)", incident_types)
        print("✅ Default Incident Types seeded.")
    
    # Seed default Admin user (if empty)
    cursor.execute("SELECT COUNT(*) FROM user")
    if cursor.fetchone()[0] == 0:
        default_password = hash_password("admin123")
        cursor.execute("""
            INSERT INTO user (username, password_hash, full_name, role) 
            VALUES (?, ?, ?, ?)
        """, ("admin", default_password, "System Administrator", "Admin"))
        print("✅ Default Admin user created (username: admin, password: admin123)")
    
    conn.commit()
    conn.close()


def generate_control_number(doc_type: str) -> str:
    """Generate a unique control number for documents."""
    conn = get_connection()
    cursor = conn.cursor()
    
    year = datetime.now().strftime("%Y")
    prefix = {
        "Clearance": "CLR",
        "Indigency": "IND",
        "Permit": "PRM",
        "Residency": "RES",
        "Business Permit": "BUS"
    }.get(doc_type, "DOC")
    
    # Get the last control number for this type and year
    cursor.execute("""
        SELECT control_number FROM doc_log 
        WHERE control_number LIKE ? 
        ORDER BY doc_id DESC LIMIT 1
    """, (f"{prefix}-{year}-%",))
    
    result = cursor.fetchone()
    if result:
        last_num = int(result[0].split("-")[-1])
        new_num = last_num + 1
    else:
        new_num = 1
    
    conn.close()
    return f"{prefix}-{year}-{new_num:05d}"


def generate_case_number() -> str:
    """Generate a unique case number for blotter cases."""
    conn = get_connection()
    cursor = conn.cursor()
    
    year = datetime.now().strftime("%Y")
    month = datetime.now().strftime("%m")
    
    cursor.execute("""
        SELECT case_number FROM blotter_case 
        WHERE case_number LIKE ? 
        ORDER BY case_id DESC LIMIT 1
    """, (f"BLT-{year}{month}-%",))
    
    result = cursor.fetchone()
    if result:
        last_num = int(result[0].split("-")[-1])
        new_num = last_num + 1
    else:
        new_num = 1
    
    conn.close()
    return f"BLT-{year}{month}-{new_num:04d}"


def check_recidivist(res_id: int) -> dict:
    """Check if a resident has prior blotter records as a respondent."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT COUNT(*) as count, GROUP_CONCAT(bc.case_number) as cases
        FROM case_involvement ci
        JOIN blotter_case bc ON ci.case_id = bc.case_id
        WHERE ci.res_id = ? AND ci.role = 'Respondent'
    """, (res_id,))
    
    result = cursor.fetchone()
    conn.close()
    
    return {
        "is_recidivist": result["count"] > 0,
        "prior_cases": result["count"],
        "case_numbers": result["cases"].split(",") if result["cases"] else []
    }


def log_audit(user_id: int, action: str, table_name: str = None, 
              record_id: int = None, old_values: str = None, new_values: str = None):
    """Log an action to the audit trail."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO audit_log (user_id, action, table_name, record_id, old_values, new_values)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (user_id, action, table_name, record_id, old_values, new_values))
    
    conn.commit()
    conn.close()


def backup_database(backup_path: str = None) -> str:
    """Create a backup of the database."""
    import shutil
    
    if backup_path is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = f"backup_kalasag_{timestamp}.db"
    
    shutil.copy2(DATABASE_PATH, backup_path)
    print(f"✅ Database backed up to: {backup_path}")
    return backup_path


def export_to_csv(table_name: str, output_path: str = None) -> str:
    """Export a table to CSV format."""
    import csv
    
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute(f"SELECT * FROM {table_name}")
    rows = cursor.fetchall()
    columns = [description[0] for description in cursor.description]
    
    if output_path is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = f"export_{table_name}_{timestamp}.csv"
    
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(columns)
        writer.writerows(rows)
    
    conn.close()
    print(f"✅ Table '{table_name}' exported to: {output_path}")
    return output_path


# Initialize database when module is run directly
if __name__ == "__main__":
    print("🛡️ KALASAG Database Initialization")
    print("=" * 40)
    init_database()
    seed_default_data()
    print("=" * 40)
    print("✅ Setup complete!")
