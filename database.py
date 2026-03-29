import sqlite3
from datetime import datetime
import os

DATABASE_NAME = 'bms_data.db'

def init_database():
    """
    Initialize the database and create tables if they don't exist
    """
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    
    # Create battery_readings table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS battery_readings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            voltage REAL NOT NULL,
            current REAL NOT NULL,
            temperature REAL NOT NULL,
            soc INTEGER NOT NULL,
            status TEXT,
            health TEXT
        )
    ''')
    
    # Create alerts table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            alert_type TEXT NOT NULL,
            message TEXT NOT NULL,
            severity TEXT NOT NULL
        )
    ''')
    
    # Create settings table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS settings (
            id INTEGER PRIMARY KEY,
            voltage_min REAL DEFAULT 11.0,
            voltage_max REAL DEFAULT 14.0,
            current_max REAL DEFAULT 5.0,
            temperature_max REAL DEFAULT 45.0,
            soc_min INTEGER DEFAULT 20
        )
    ''')
    
    # Insert default settings if not exists
    cursor.execute('SELECT COUNT(*) FROM settings')
    if cursor.fetchone()[0] == 0:
        cursor.execute('''
            INSERT INTO settings (id, voltage_min, voltage_max, current_max, temperature_max, soc_min)
            VALUES (1, 11.0, 14.0, 5.0, 45.0, 20)
        ''')
    
    conn.commit()
    conn.close()
    print("✓ Database initialized successfully")

def save_reading(voltage, current, temperature, soc, status, health):
    """
    Save a battery reading to the database
    """
    try:
        conn = sqlite3.connect(DATABASE_NAME)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO battery_readings (voltage, current, temperature, soc, status, health)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (voltage, current, temperature, soc, status, health))
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Error saving reading: {e}")
        return False

def get_recent_readings(limit=100):
    """
    Get the most recent battery readings
    """
    try:
        conn = sqlite3.connect(DATABASE_NAME)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, timestamp, voltage, current, temperature, soc, status, health
            FROM battery_readings
            ORDER BY timestamp DESC
            LIMIT ?
        ''', (limit,))
        
        readings = cursor.fetchall()
        conn.close()
        
        # Convert to list of dictionaries
        result = []
        for row in readings:
            result.append({
                'id': row[0],
                'timestamp': row[1],
                'voltage': row[2],
                'current': row[3],
                'temperature': row[4],
                'soc': row[5],
                'status': row[6],
                'health': row[7]
            })
        
        return result
    except Exception as e:
        print(f"Error getting readings: {e}")
        return []

def get_readings_by_date(start_date, end_date):
    """
    Get readings between two dates
    """
    try:
        conn = sqlite3.connect(DATABASE_NAME)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, timestamp, voltage, current, temperature, soc, status, health
            FROM battery_readings
            WHERE timestamp BETWEEN ? AND ?
            ORDER BY timestamp ASC
        ''', (start_date, end_date))
        
        readings = cursor.fetchall()
        conn.close()
        
        result = []
        for row in readings:
            result.append({
                'id': row[0],
                'timestamp': row[1],
                'voltage': row[2],
                'current': row[3],
                'temperature': row[4],
                'soc': row[5],
                'status': row[6],
                'health': row[7]
            })
        
        return result
    except Exception as e:
        print(f"Error getting readings by date: {e}")
        return []

def save_alert(alert_type, message, severity):
    """
    Save an alert to the database
    """
    try:
        conn = sqlite3.connect(DATABASE_NAME)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO alerts (alert_type, message, severity)
            VALUES (?, ?, ?)
        ''', (alert_type, message, severity))
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Error saving alert: {e}")
        return False

def get_recent_alerts(limit=50):
    """
    Get recent alerts
    """
    try:
        conn = sqlite3.connect(DATABASE_NAME)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, timestamp, alert_type, message, severity
            FROM alerts
            ORDER BY timestamp DESC
            LIMIT ?
        ''', (limit,))
        
        alerts = cursor.fetchall()
        conn.close()
        
        result = []
        for row in alerts:
            result.append({
                'id': row[0],
                'timestamp': row[1],
                'alert_type': row[2],
                'message': row[3],
                'severity': row[4]
            })
        
        return result
    except Exception as e:
        print(f"Error getting alerts: {e}")
        return []

def get_settings():
    """
    Get current settings
    """
    try:
        conn = sqlite3.connect(DATABASE_NAME)
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM settings WHERE id = 1')
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                'voltage_min': row[1],
                'voltage_max': row[2],
                'current_max': row[3],
                'temperature_max': row[4],
                'soc_min': row[5]
            }
        return None
    except Exception as e:
        print(f"Error getting settings: {e}")
        return None

def update_settings(voltage_min, voltage_max, current_max, temperature_max, soc_min):
    """
    Update settings
    """
    try:
        conn = sqlite3.connect(DATABASE_NAME)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE settings
            SET voltage_min = ?, voltage_max = ?, current_max = ?, temperature_max = ?, soc_min = ?
            WHERE id = 1
        ''', (voltage_min, voltage_max, current_max, temperature_max, soc_min))
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Error updating settings: {e}")
        return False

def get_database_stats():
    """
    Get statistics about the database
    """
    try:
        conn = sqlite3.connect(DATABASE_NAME)
        cursor = conn.cursor()
        
        # Total readings
        cursor.execute('SELECT COUNT(*) FROM battery_readings')
        total_readings = cursor.fetchone()[0]
        
        # Total alerts
        cursor.execute('SELECT COUNT(*) FROM alerts')
        total_alerts = cursor.fetchone()[0]
        
        # First reading date
        cursor.execute('SELECT MIN(timestamp) FROM battery_readings')
        first_reading = cursor.fetchone()[0]
        
        # Last reading date
        cursor.execute('SELECT MAX(timestamp) FROM battery_readings')
        last_reading = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            'total_readings': total_readings,
            'total_alerts': total_alerts,
            'first_reading': first_reading,
            'last_reading': last_reading
        }
    except Exception as e:
        print(f"Error getting stats: {e}")
        return None

# ========== DEVICE MANAGEMENT FUNCTIONS ==========

def init_devices_table():
    """
    Initialize devices table for ESP32 device management
    """
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS devices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            device_id TEXT UNIQUE NOT NULL,
            device_name TEXT NOT NULL,
            api_token TEXT UNIQUE NOT NULL,
            status TEXT NOT NULL,
            registered_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            last_seen DATETIME,
            total_readings INTEGER DEFAULT 0,
            notes TEXT
        )
    ''')
    
    conn.commit()
    conn.close()
    print("✓ Devices table initialized")

def register_device(device_id, device_name, notes=""):
    """
    Register a new ESP32 device (status: pending)
    """
    try:
        import secrets
        
        conn = sqlite3.connect(DATABASE_NAME)
        cursor = conn.cursor()
        
        # Generate unique API token
        api_token = secrets.token_urlsafe(32)
        
        cursor.execute('''
            INSERT INTO devices (device_id, device_name, api_token, status, notes)
            VALUES (?, ?, ?, 'pending', ?)
        ''', (device_id, device_name, api_token, notes))
        
        conn.commit()
        conn.close()
        return True, api_token
    except sqlite3.IntegrityError:
        return False, "Device already exists"
    except Exception as e:
        print(f"Error registering device: {e}")
        return False, str(e)

def get_all_devices():
    """
    Get all registered devices
    """
    try:
        conn = sqlite3.connect(DATABASE_NAME)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, device_id, device_name, api_token, status, 
                   registered_at, last_seen, total_readings, notes
            FROM devices
            ORDER BY registered_at DESC
        ''')
        
        devices = cursor.fetchall()
        conn.close()
        
        result = []
        for row in devices:
            result.append({
                'id': row[0],
                'device_id': row[1],
                'device_name': row[2],
                'api_token': row[3],
                'status': row[4],
                'registered_at': row[5],
                'last_seen': row[6],
                'total_readings': row[7],
                'notes': row[8]
            })
        
        return result
    except Exception as e:
        print(f"Error getting devices: {e}")
        return []

def get_device_by_token(api_token):
    """
    Get device by API token
    """
    try:
        conn = sqlite3.connect(DATABASE_NAME)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, device_id, device_name, status
            FROM devices
            WHERE api_token = ?
        ''', (api_token,))
        
        device = cursor.fetchone()
        conn.close()
        
        if device:
            return {
                'id': device[0],
                'device_id': device[1],
                'device_name': device[2],
                'status': device[3]
            }
        return None
    except Exception as e:
        print(f"Error getting device by token: {e}")
        return None

def approve_device(device_id):
    """
    Approve a pending device
    """
    try:
        conn = sqlite3.connect(DATABASE_NAME)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE devices
            SET status = 'approved'
            WHERE device_id = ?
        ''', (device_id,))
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Error approving device: {e}")
        return False

def block_device(device_id):
    """
    Block a device
    """
    try:
        conn = sqlite3.connect(DATABASE_NAME)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE devices
            SET status = 'blocked'
            WHERE device_id = ?
        ''', (device_id,))
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Error blocking device: {e}")
        return False

def delete_device(device_id):
    """
    Delete a device
    """
    try:
        conn = sqlite3.connect(DATABASE_NAME)
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM devices WHERE device_id = ?', (device_id,))
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Error deleting device: {e}")
        return False

def update_device_activity(api_token):
    """
    Update device last seen time and increment readings count
    """
    try:
        conn = sqlite3.connect(DATABASE_NAME)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE devices
            SET last_seen = CURRENT_TIMESTAMP,
                total_readings = total_readings + 1
            WHERE api_token = ?
        ''', (api_token,))
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Error updating device activity: {e}")
        return False

def get_pending_devices_count():
    """
    Get count of pending devices
    """
    try:
        conn = sqlite3.connect(DATABASE_NAME)
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM devices WHERE status = 'pending'")
        count = cursor.fetchone()[0]
        
        conn.close()
        return count
    except Exception as e:
        print(f"Error getting pending count: {e}")
        return 0

# Initialize devices table when module loads
try:
    init_devices_table()
except:
    pass

# Initialize database when module is imported
if __name__ == "__main__":
    init_database()
    print("Database module ready!")