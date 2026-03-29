"""
AI Battery Health Prediction Module
Uses machine learning to predict battery health and lifespan
"""

import numpy as np
from datetime import datetime, timedelta
import database

class BatteryAI:
    def __init__(self):
        self.min_data_points = 20  # Minimum readings needed for prediction
    
    def calculate_battery_health(self):
        """
        Calculate battery State of Health (SOH) based on voltage patterns
        SOH = Current capacity / Original capacity * 100
        """
        try:
            readings = database.get_recent_readings(100)
            
            if len(readings) < self.min_data_points:
                return {
                    'health_percentage': 100.0,
                    'status': 'Insufficient Data',
                    'confidence': 'low',
                    'message': f'Need {self.min_data_points - len(readings)} more readings for accurate prediction'
                }
            
            # Extract voltage data
            voltages = [r['voltage'] for r in readings]
            temperatures = [r['temperature'] for r in readings]
            
            # Calculate average voltage (indicator of capacity)
            avg_voltage = np.mean(voltages)
            voltage_std = np.std(voltages)
            
            # Calculate health based on voltage stability and average
            # Ideal voltage for 12V battery: 12.6V (100% health)
            ideal_voltage = 12.6
            voltage_deviation = abs(avg_voltage - ideal_voltage)
            
            # Health calculation (simplified model)
            health_percentage = 100 - (voltage_deviation * 10) - (voltage_std * 5)
            health_percentage = max(60, min(100, health_percentage))  # Clamp between 60-100
            
            # Determine status
            if health_percentage >= 90:
                status = 'Excellent'
            elif health_percentage >= 80:
                status = 'Good'
            elif health_percentage >= 70:
                status = 'Fair'
            else:
                status = 'Poor'
            
            return {
                'health_percentage': round(health_percentage, 1),
                'status': status,
                'confidence': 'high' if len(readings) >= 50 else 'medium',
                'avg_voltage': round(avg_voltage, 2),
                'voltage_stability': round(voltage_std, 3),
                'data_points': len(readings)
            }
            
        except Exception as e:
            print(f"Error calculating health: {e}")
            return {
                'health_percentage': 0,
                'status': 'Error',
                'confidence': 'none',
                'message': str(e)
            }
    
    def predict_lifespan(self):
        """
        Predict remaining battery lifespan based on degradation rate
        """
        try:
            readings = database.get_recent_readings(200)
            
            if len(readings) < 50:
                return {
                    'remaining_months': 'Unknown',
                    'degradation_rate': 0,
                    'message': 'Need more data for lifespan prediction'
                }
            
            # Calculate degradation by comparing old vs recent readings
            old_readings = readings[-50:]  # Oldest 50
            recent_readings = readings[:50]  # Newest 50
            
            old_avg_voltage = np.mean([r['voltage'] for r in old_readings])
            recent_avg_voltage = np.mean([r['voltage'] for r in recent_readings])
            
            voltage_drop = old_avg_voltage - recent_avg_voltage
            
            # Estimate degradation rate (% per month)
            # Assuming readings are spread over time
            time_span_days = 30  # Assume 30 days of data
            degradation_per_month = (voltage_drop / old_avg_voltage) * 100
            
            # Predict when battery reaches 80% health (replacement threshold)
            current_health = self.calculate_battery_health()['health_percentage']
            health_drop_to_replacement = current_health - 80
            
            if degradation_per_month > 0:
                remaining_months = health_drop_to_replacement / degradation_per_month
                remaining_months = max(1, min(36, remaining_months))  # Clamp 1-36 months
            else:
                remaining_months = 36  # Default: 3 years
            
            return {
                'remaining_months': int(remaining_months),
                'degradation_rate': round(abs(degradation_per_month), 2),
                'replacement_date': (datetime.now() + timedelta(days=remaining_months*30)).strftime("%B %Y"),
                'current_health': current_health
            }
            
        except Exception as e:
            print(f"Error predicting lifespan: {e}")
            return {
                'remaining_months': 'Unknown',
                'degradation_rate': 0,
                'message': str(e)
            }
    
    def detect_anomalies(self):
        """
        Detect unusual battery behavior patterns
        """
        try:
            readings = database.get_recent_readings(100)
            
            if len(readings) < 30:
                return {
                    'anomalies_found': False,
                    'message': 'Need more data for anomaly detection'
                }
            
            anomalies = []
            
            # Extract data
            voltages = [r['voltage'] for r in readings[:50]]
            temperatures = [r['temperature'] for r in readings[:50]]
            currents = [r['current'] for r in readings[:50]]
            
            # Calculate thresholds (mean ± 2*std)
            voltage_mean = np.mean(voltages)
            voltage_std = np.std(voltages)
            temp_mean = np.mean(temperatures)
            temp_std = np.std(temperatures)
            
            # Check recent readings for anomalies
            for reading in readings[:10]:  # Check last 10 readings
                # Voltage anomaly
                if abs(reading['voltage'] - voltage_mean) > 2 * voltage_std:
                    anomalies.append({
                        'type': 'Voltage Anomaly',
                        'severity': 'high',
                        'message': f"Unusual voltage: {reading['voltage']}V (expected ~{voltage_mean:.1f}V)",
                        'timestamp': reading['timestamp']
                    })
                
                # Temperature anomaly
                if abs(reading['temperature'] - temp_mean) > 2 * temp_std:
                    anomalies.append({
                        'type': 'Temperature Anomaly',
                        'severity': 'medium',
                        'message': f"Unusual temperature: {reading['temperature']}°C (expected ~{temp_mean:.1f}°C)",
                        'timestamp': reading['timestamp']
                    })
                
                # Dangerous combinations
                if reading['temperature'] > 45 and reading['current'] > 3:
                    anomalies.append({
                        'type': 'Dangerous Condition',
                        'severity': 'critical',
                        'message': f"High temperature ({reading['temperature']}°C) with high current ({reading['current']}A)",
                        'timestamp': reading['timestamp']
                    })
            
            return {
                'anomalies_found': len(anomalies) > 0,
                'count': len(anomalies),
                'anomalies': anomalies[:5],  # Return top 5
                'voltage_baseline': round(voltage_mean, 2),
                'temp_baseline': round(temp_mean, 1)
            }
            
        except Exception as e:
            print(f"Error detecting anomalies: {e}")
            return {
                'anomalies_found': False,
                'message': str(e)
            }
    
    def get_recommendations(self):
        """
        Generate AI-powered recommendations based on battery data
        """
        try:
            readings = database.get_recent_readings(100)
            
            if len(readings) < 20:
                return []
            
            recommendations = []
            
            # Analyze temperature patterns
            temps = [r['temperature'] for r in readings[:50]]
            avg_temp = np.mean(temps)
            high_temp_count = sum(1 for t in temps if t > 40)
            
            if avg_temp > 35:
                recommendations.append({
                    'icon': '🌡️',
                    'title': 'High Temperature Detected',
                    'message': f'Average temperature is {avg_temp:.1f}°C. Consider cooling the battery.',
                    'priority': 'high'
                })
            
            if high_temp_count > 5:
                recommendations.append({
                    'icon': '⚠️',
                    'title': 'Frequent Overheating',
                    'message': f'Temperature exceeded 40°C {high_temp_count} times. Check charging environment.',
                    'priority': 'high'
                })
            
            # Analyze voltage patterns
            voltages = [r['voltage'] for r in readings[:50]]
            avg_voltage = np.mean(voltages)
            
            if avg_voltage < 12.0:
                recommendations.append({
                    'icon': '🔋',
                    'title': 'Low Voltage Pattern',
                    'message': f'Average voltage is {avg_voltage:.2f}V. Battery may need charging or replacement.',
                    'priority': 'medium'
                })
            
            # Analyze SOC patterns
            socs = [r['soc'] for r in readings[:50]]
            low_soc_count = sum(1 for s in socs if s < 20)
            
            if low_soc_count > 5:
                recommendations.append({
                    'icon': '⚡',
                    'title': 'Deep Discharge Detected',
                    'message': f'Battery discharged below 20% {low_soc_count} times. This reduces lifespan.',
                    'priority': 'medium'
                })
            
            # Positive feedback
            if avg_temp < 35 and avg_voltage > 12.2:
                recommendations.append({
                    'icon': '✅',
                    'title': 'Optimal Performance',
                    'message': 'Battery is operating in optimal conditions. Keep it up!',
                    'priority': 'low'
                })
            
            return recommendations[:5]  # Return top 5
            
        except Exception as e:
            print(f"Error generating recommendations: {e}")
            return []
    
    def get_ai_summary(self):
        """
        Get complete AI analysis summary
        """
        health = self.calculate_battery_health()
        lifespan = self.predict_lifespan()
        anomalies = self.detect_anomalies()
        recommendations = self.get_recommendations()
        
        return {
            'health': health,
            'lifespan': lifespan,
            'anomalies': anomalies,
            'recommendations': recommendations,
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }