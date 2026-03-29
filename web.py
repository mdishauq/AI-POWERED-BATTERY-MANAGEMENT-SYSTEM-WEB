from flask import Flask, render_template, jsonify, request, redirect, url_for, flash, session
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from datetime import datetime
import random
import database
import ai_model

app = Flask(__name__)
app.secret_key = 'BMS_Final_Year_Project_2024_SecureKey_RondomString_Xdksdio'  # Change this to a random string

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to access this page.'

# Initialize database on startup
database.init_database()

# ========== USER MANAGEMENT ==========

# Simple user class (in production, use a database)
class User(UserMixin):
    def __init__(self, id, username, password):
        self.id = id
        self.username = username
        self.password = password

# User database (CHANGE THESE CREDENTIALS!)
users = {
    'ishauq': User(1, "ishauq", "ishauq123"),  # Change username and password!
}

@login_manager.user_loader
def load_user(user_id):
    for user in users.values():
        if str(user.id) == str(user_id):
            return user
    return None

# ========== AUTHENTICATION ROUTES ==========

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login page"""
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = users.get(username)
        
        if user and user.password == password:
            login_user(user)
            flash('Login successful!', 'success')
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('home'))
        else:
            flash('Invalid username or password', 'error')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    """Logout user"""
    logout_user()
    flash('You have been logged out.', 'success')
    return redirect(url_for('login'))

# ========== BATTERY DATA FUNCTIONS ==========

# Simulated battery data (later this will come from ESP32)
def get_battery_data():
    """
    This function simulates getting data from ESP32
    Later you'll replace this with actual MQTT/HTTP data
    """
    voltage = round(random.uniform(11.5, 12.8), 2)
    current = round(random.uniform(0.5, 3.5), 2)
    temperature = round(random.uniform(25, 45), 1)
    soc = random.randint(60, 100)
    status = 'Charging' if current > 0 else 'Discharging'
    health = 'Good'
    
    # Save to database
    database.save_reading(voltage, current, temperature, soc, status, health)
    
    # Check for alerts
    settings = database.get_settings()
    if settings:
        if temperature > settings['temperature_max']:
            database.save_alert('Temperature', f'High temperature: {temperature}°C', 'warning')
        if voltage < settings['voltage_min']:
            database.save_alert('Voltage', f'Low voltage: {voltage}V', 'danger')
        if soc < settings['soc_min']:
            database.save_alert('SOC', f'Low battery: {soc}%', 'warning')
    
    return {
        'voltage': voltage,
        'current': current,
        'temperature': temperature,
        'soc': soc,
        'status': status,
        'health': health,
        'timestamp': datetime.now().strftime("%H:%M:%S")
    }

# ========== PROTECTED ROUTES ==========

@app.route('/')
@login_required
def home():
    """Home page"""
    return render_template('home.html', user=current_user)

@app.route('/dashboard')
@login_required
def dashboard():
    """Main dashboard page"""
    battery_data = get_battery_data()
    return render_template('dashboard.html', battery=battery_data, user=current_user)

@app.route('/api/battery-data')
@login_required
def api_battery_data():
    """
    API endpoint - returns JSON data
    JavaScript will call this to get live updates
    """
    data = get_battery_data()
    return jsonify(data)

@app.route('/history')
@login_required
def history():
    """Historical data page"""
    limit = request.args.get('limit', 100, type=int)
    readings = database.get_recent_readings(limit)
    stats = database.get_database_stats()
    return render_template('history.html', readings=readings, stats=stats, user=current_user)

@app.route('/api/history')
@login_required
def api_history():
    """API endpoint for historical data"""
    limit = request.args.get('limit', 100, type=int)
    readings = database.get_recent_readings(limit)
    return jsonify(readings)

@app.route('/alerts')
@login_required
def alerts():
    """Alerts page"""
    alerts = database.get_recent_alerts(50)
    return render_template('alerts.html', alerts=alerts, user=current_user)

@app.route('/api/alerts')
@login_required
def api_alerts():
    """API endpoint for alerts"""
    alerts = database.get_recent_alerts(50)
    return jsonify(alerts)

@app.route('/settings')
@login_required
def settings():
    """Settings page"""
    current_settings = database.get_settings()
    return render_template('settings.html', settings=current_settings, user=current_user)

@app.route('/api/settings', methods=['GET', 'POST'])
@login_required
def api_settings():
    """API endpoint for settings"""
    if request.method == 'POST':
        data = request.json
        success = database.update_settings(
            data['voltage_min'],
            data['voltage_max'],
            data['current_max'],
            data['temperature_max'],
            data['soc_min']
        )
        return jsonify({'success': success})
    else:
        settings = database.get_settings()
        return jsonify(settings)

@app.route('/about')
@login_required
def about():
    """About page"""
    return render_template('about.html', user=current_user)


# ========== ESP32 SIMULATOR (For testing without hardware) ==========

@app.route('/simulator')
@login_required
def simulator():
    """ESP32 simulator page - for testing without hardware"""
    return render_template('simulator.html', user=current_user)

@app.route('/api/simulate-esp32', methods=['POST'])
@login_required
def simulate_esp32():
    """Simulate ESP32 sending data"""
    try:
        data = request.json
        
        # Send to the same endpoint ESP32 would use
        voltage = float(data['voltage'])
        current = float(data['current'])
        temperature = float(data['temperature'])
        soc = int(data['soc'])
        status = data.get('status', 'Charging')
        health = data.get('health', 'Good')
        
        # Save to database
        database.save_reading(voltage, current, temperature, soc, status, health)
        
        # Check for alerts
        settings = database.get_settings()
        if settings:
            if temperature > settings['temperature_max']:
                database.save_alert('Temperature', f'High temperature: {temperature}°C', 'warning')
            if voltage < settings['voltage_min']:
                database.save_alert('Voltage', f'Low voltage: {voltage}V', 'danger')
            if soc < settings['soc_min']:
                database.save_alert('SOC', f'Low battery: {soc}%', 'warning')
        
        return jsonify({'success': True, 'message': 'Simulated data sent successfully'})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    
# ========== DEVICE MANAGEMENT ROUTES ==========

@app.route('/devices')
@login_required
def devices():
    """Device management page"""
    all_devices = database.get_all_devices()
    pending_count = database.get_pending_devices_count()
    return render_template('devices.html', devices=all_devices, pending_count=pending_count, user=current_user)

@app.route('/api/devices')
@login_required
def api_devices():
    """API endpoint for devices list"""
    devices = database.get_all_devices()
    return jsonify(devices)

@app.route('/api/device/approve', methods=['POST'])
@login_required
def api_approve_device():
    """Approve a pending device"""
    try:
        data = request.json
        device_id = data.get('device_id')
        
        success = database.approve_device(device_id)
        
        if success:
            return jsonify({'success': True, 'message': 'Device approved successfully'})
        else:
            return jsonify({'success': False, 'error': 'Failed to approve device'}), 500
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/device/block', methods=['POST'])
@login_required
def api_block_device():
    """Block a device"""
    try:
        data = request.json
        device_id = data.get('device_id')
        
        success = database.block_device(device_id)
        
        if success:
            return jsonify({'success': True, 'message': 'Device blocked successfully'})
        else:
            return jsonify({'success': False, 'error': 'Failed to block device'}), 500
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/device/delete', methods=['POST'])
@login_required
def api_delete_device():
    """Delete a device"""
    try:
        data = request.json
        device_id = data.get('device_id')
        
        success = database.delete_device(device_id)
        
        if success:
            return jsonify({'success': True, 'message': 'Device deleted successfully'})
        else:
            return jsonify({'success': False, 'error': 'Failed to delete device'}), 500
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# ========== ESP32 DEVICE REGISTRATION (No login required) ==========

@app.route('/api/device/register', methods=['POST'])
def api_register_device():
    """
    ESP32 device registration endpoint
    ESP32 sends: {"device_id": "ESP32_XXXXXX", "device_name": "Battery Pack 1"}
    """
    try:
        data = request.json
        device_id = data.get('device_id')
        device_name = data.get('device_name', f'Device {device_id}')
        notes = data.get('notes', '')
        
        if not device_id:
            return jsonify({'success': False, 'error': 'device_id is required'}), 400
        
        success, result = database.register_device(device_id, device_name, notes)
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Device registration pending approval',
                'status': 'pending',
                'device_id': device_id
            })
        else:
            # Check if device already exists
            devices = database.get_all_devices()
            for device in devices:
                if device['device_id'] == device_id:
                    return jsonify({
                        'success': True,
                        'message': 'Device already registered',
                        'status': device['status'],
                        'device_id': device_id,
                        'api_token': device['api_token'] if device['status'] == 'approved' else None
                    })
            
            return jsonify({'success': False, 'error': result}), 500
            
    except Exception as e:
        print(f"Error in device registration: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

# ========== UPDATED ESP32 DATA RECEIVER (With Token Authentication) ==========

@app.route('/api/esp32-data', methods=['POST'])
def receive_esp32_data():
    """
    Receive data from ESP32 via HTTP POST
    ESP32 must include api_token in headers or JSON
    """
    try:
        # Get API token from header or JSON
        api_token = request.headers.get('X-API-Token') or request.json.get('api_token')
        
        if not api_token:
            return jsonify({'success': False, 'error': 'API token required'}), 401
        
        # Verify device
        device = database.get_device_by_token(api_token)
        
        if not device:
            return jsonify({'success': False, 'error': 'Invalid API token'}), 401
        
        if device['status'] != 'approved':
            return jsonify({'success': False, 'error': f'Device status: {device["status"]}'}), 403
        
        data = request.json
        
        # Validate required fields
        required_fields = ['voltage', 'current', 'temperature', 'soc']
        for field in required_fields:
            if field not in data:
                return jsonify({'success': False, 'error': f'Missing field: {field}'}), 400
        
        # Extract data
        voltage = float(data['voltage'])
        current = float(data['current'])
        temperature = float(data['temperature'])
        soc = int(data['soc'])
        status = data.get('status', 'Unknown')
        health = data.get('health', 'Unknown')
        
        # Save to database
        database.save_reading(voltage, current, temperature, soc, status, health)
        
        # Update device activity
        database.update_device_activity(api_token)
        
        # Check for alerts
        settings = database.get_settings()
        if settings:
            if temperature > settings['temperature_max']:
                database.save_alert('Temperature', f'High temperature: {temperature}°C', 'warning')
            if voltage < settings['voltage_min']:
                database.save_alert('Voltage', f'Low voltage: {voltage}V', 'danger')
            if voltage > settings['voltage_max']:
                database.save_alert('Voltage', f'High voltage: {voltage}V', 'danger')
            if soc < settings['soc_min']:
                database.save_alert('SOC', f'Low battery: {soc}%', 'warning')
            if current > settings['current_max']:
                database.save_alert('Current', f'High current: {current}A', 'warning')
        
        print(f"✓ Data from {device['device_name']}: V={voltage}V, I={current}A, T={temperature}°C, SOC={soc}%")
        
        return jsonify({'success': True, 'message': 'Data received successfully'})
        
    except Exception as e:
        print(f"✗ Error receiving ESP32 data: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500
    
# ========== AI FEATURES ==========

@app.route('/ai-dashboard')
@login_required
def ai_dashboard():
    """AI-powered battery analytics dashboard"""
    ai = ai_model.BatteryAI()
    ai_data = ai.get_ai_summary()
    return render_template('ai_dashboard.html', ai_data=ai_data, user=current_user)

@app.route('/api/ai-analysis')
@login_required
def api_ai_analysis():
    """API endpoint for AI analysis"""
    ai = ai_model.BatteryAI()
    analysis = ai.get_ai_summary()
    return jsonify(analysis)    

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)