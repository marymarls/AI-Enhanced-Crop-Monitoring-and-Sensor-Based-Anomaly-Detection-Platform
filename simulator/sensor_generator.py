"""
Agricultural Sensor Data Simulator
Generates realistic time-series sensor data and sends it to Django API
"""

import requests
import numpy as np
import time
from datetime import datetime, timedelta
import json
import sys
import os

# Add parent directory to path to import config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from simulator.config import (
    API_BASE_URL, AUTH_TOKEN, SENSOR_RANGES, IRRIGATION_HOURS,
    SIMULATION_INTERVAL_MINUTES, API_ENDPOINTS, VERBOSE
)


class SensorSimulator:
    def __init__(self, api_base_url=None, auth_token=None):
        """
        Initialize the sensor simulator
        
        Args:
            api_base_url: Base URL of your Django API
            auth_token: JWT token for authentication (optional)
        """
        self.api_base_url = api_base_url or API_BASE_URL
        self.auth_token = auth_token or AUTH_TOKEN
        self.headers = {
            'Content-Type': 'application/json',
        }
        if self.auth_token:
            self.headers['Authorization'] = f'Bearer {self.auth_token}'
    
    def generate_baseline_moisture(self, hour_of_day, base_moisture=None):
        """Generate realistic soil moisture with diurnal pattern"""
        if base_moisture is None:
            base_moisture = SENSOR_RANGES['moisture']['normal_base']
        
        config = SENSOR_RANGES['moisture']
        
        # Base pattern: gradual decrease during day
        moisture = base_moisture - (hour_of_day * config['daily_decrease_rate'])
        
        # Irrigation events
        if hour_of_day in IRRIGATION_HOURS:
            moisture += config['irrigation_boost']
        
        # Add random noise
        moisture += np.random.normal(0, config['noise_std'])
        
        # Keep in realistic bounds
        return max(config['min'], min(config['max'], moisture))
    
    def generate_baseline_temperature(self, hour_of_day, season_offset=0):
        """Generate realistic temperature with diurnal cycle"""
        config = SENSOR_RANGES['temperature']
        
        # Base temperature follows sine wave (peaks at hour 14 = 2 PM)
        temp = config['normal_base'] + config['amplitude'] * np.sin((hour_of_day - 6) * np.pi / 12)
        
        # Add season offset and noise
        temp += season_offset + np.random.normal(0, config['noise_std'])
        
        return max(config['min'], min(config['max'], temp))
    
    def generate_baseline_humidity(self, temperature):
        """Generate humidity inversely correlated with temperature"""
        config = SENSOR_RANGES['humidity']
        
        # Inverse relationship with temperature
        humidity = 90 + (temperature * config['temp_correlation'])
        
        # Add noise
        humidity += np.random.normal(0, config['noise_std'])
        
        return max(config['min'], min(config['max'], humidity))
    
    def inject_anomaly_sudden_drop(self, normal_value, drop_percentage=15):
        """Inject sudden drop anomaly (e.g., irrigation failure)"""
        return normal_value * (1 - drop_percentage / 100)
    
    def inject_anomaly_spike(self, normal_value, spike_percentage=30):
        """Inject sudden spike (e.g., sensor malfunction)"""
        return normal_value * (1 + spike_percentage / 100)
    
    def inject_anomaly_drift(self, normal_value, drift_factor=0.05):
        """Inject gradual drift (sensor calibration error)"""
        return normal_value * (1 + drift_factor)
    
    def send_sensor_reading(self, plot_id, sensor_type, value, timestamp=None):
        """
        Send a sensor reading to Django API
        
        Args:
            plot_id: ID of the field plot
            sensor_type: 'moisture', 'temperature', or 'humidity'
            value: Sensor reading value
            timestamp: Optional timestamp (defaults to now)
        
        Returns:
            bool: True if successful, False otherwise
        """
        if timestamp is None:
            timestamp = datetime.now().isoformat()
        
        data = {
            'plot_id': plot_id,
            'sensor_type': sensor_type,
            'value': round(value, 2),
            'timestamp': timestamp,
            'source': 'simulator'
        }
        
        try:
            response = requests.post(
                API_ENDPOINTS['sensor_readings'],
                headers=self.headers,
                json=data,
                timeout=5
            )
            
            if response.status_code in [200, 201]:
                if VERBOSE:
                    print(f"✓ Sent {sensor_type:11s}: {value:6.2f} for plot {plot_id} at {timestamp[:16]}")
                return True
            else:
                print(f"✗ Error {response.status_code}: {response.text}")
                return False
                
        except requests.exceptions.RequestException as e:
            print(f"✗ Connection error: {e}")
            return False
    
    def simulate_normal_day(self, plot_id, start_hour=0, duration_hours=24, 
                           interval_minutes=None, start_time=None):
        """
        Simulate a normal day of sensor readings
        
        Args:
            plot_id: Field plot ID
            start_hour: Starting hour (0-23)
            duration_hours: How many hours to simulate
            interval_minutes: Interval between readings (uses config default if None)
            start_time: Starting timestamp (uses now if None)
        
        Returns:
            int: Number of successful readings sent
        """
        if interval_minutes is None:
            interval_minutes = SIMULATION_INTERVAL_MINUTES
        
        if start_time is None:
            start_time = datetime.now()
        
        print(f"\n{'='*70}")
        print(f"SIMULATING NORMAL DAY - Plot {plot_id}")
        print(f"Start time: {start_time.strftime('%Y-%m-%d %H:%M')}")
        print(f"Duration: {duration_hours} hours | Interval: {interval_minutes} min")
        print(f"{'='*70}\n")
        
        base_moisture = SENSOR_RANGES['moisture']['normal_base']
        readings_per_hour = 60 // interval_minutes
        total_readings = duration_hours * readings_per_hour
        successful_sends = 0
        
        for i in range(total_readings):
            hour_of_day = (start_hour + (i // readings_per_hour)) % 24
            
            # Generate realistic sensor values
            moisture = self.generate_baseline_moisture(hour_of_day, base_moisture)
            temperature = self.generate_baseline_temperature(hour_of_day)
            humidity = self.generate_baseline_humidity(temperature)
            
            # Update base moisture for next iteration
            base_moisture = moisture
            
            # Calculate timestamp
            timestamp = start_time + timedelta(minutes=i * interval_minutes)
            
            # Send readings
            if self.send_sensor_reading(plot_id, 'moisture', moisture, timestamp.isoformat()):
                successful_sends += 1
            if self.send_sensor_reading(plot_id, 'temperature', temperature, timestamp.isoformat()):
                successful_sends += 1
            if self.send_sensor_reading(plot_id, 'humidity', humidity, timestamp.isoformat()):
                successful_sends += 1
        
        print(f"\n✓ Completed: {successful_sends}/{total_readings * 3} readings sent successfully for plot {plot_id}\n")
        return successful_sends
    
    def simulate_with_anomalies(self, plot_id, scenario='irrigation_failure', start_time=None):
        """
        Simulate sensor data with specific anomaly scenarios
        
        Args:
            plot_id: Field plot ID
            scenario: 'irrigation_failure', 'heat_stress', 'sensor_malfunction', 'gradual_drift'
            start_time: Starting timestamp (uses now if None)
        
        Returns:
            tuple: (total_readings, anomaly_count)
        """
        if start_time is None:
            start_time = datetime.now()
        
        print(f"\n{'='*70}")
        print(f"SIMULATING ANOMALY SCENARIO: {scenario}")
        print(f"Plot: {plot_id}")
        print(f"Start time: {start_time.strftime('%Y-%m-%d %H:%M')}")
        print(f"{'='*70}\n")
        
        base_moisture = SENSOR_RANGES['moisture']['normal_base']
        anomaly_count = 0
        
        for hour in range(24):
            moisture = self.generate_baseline_moisture(hour, base_moisture)
            temperature = self.generate_baseline_temperature(hour)
            humidity = self.generate_baseline_humidity(temperature)
            
            # Inject anomalies based on scenario
            if scenario == 'irrigation_failure' and 10 <= hour <= 14:
                moisture = self.inject_anomaly_sudden_drop(moisture, drop_percentage=20)
                anomaly_count += 1
                print(f"⚠️  ANOMALY INJECTED: Irrigation failure at hour {hour} (moisture: {moisture:.2f}%)")
            
            elif scenario == 'heat_stress' and 12 <= hour <= 16:
                temperature = self.inject_anomaly_spike(temperature, spike_percentage=25)
                anomaly_count += 1
                print(f"⚠️  ANOMALY INJECTED: Heat stress at hour {hour} (temp: {temperature:.2f}°C)")
            
            elif scenario == 'sensor_malfunction' and hour == 15:
                moisture = self.inject_anomaly_spike(moisture, spike_percentage=40)
                anomaly_count += 1
                print(f"⚠️  ANOMALY INJECTED: Sensor malfunction at hour {hour} (moisture: {moisture:.2f}%)")
            
            elif scenario == 'gradual_drift':
                drift_factor = 0.02 * (hour / 24)
                moisture = self.inject_anomaly_drift(moisture, drift_factor)
                if hour % 6 == 0:
                    anomaly_count += 1
                    print(f"⚠️  ANOMALY: Gradual drift at hour {hour} (drift: {drift_factor:.3f})")
            
            base_moisture = moisture
            
            # Send readings
            timestamp = start_time + timedelta(hours=hour)
            self.send_sensor_reading(plot_id, 'moisture', moisture, timestamp.isoformat())
            self.send_sensor_reading(plot_id, 'temperature', temperature, timestamp.isoformat())
            self.send_sensor_reading(plot_id, 'humidity', humidity, timestamp.isoformat())
        
        print(f"\n✓ Completed anomaly scenario: {scenario}")
        print(f"  Anomalies injected: {anomaly_count}\n")
        return (24 * 3, anomaly_count)


def test_connection():
    """Test connection to Django API"""
    print("="*70)
    print("TESTING CONNECTION TO DJANGO API")
    print("="*70)
    print(f"API URL: {API_ENDPOINTS['sensor_readings']}")
    
    try:
        response = requests.get(API_BASE_URL, timeout=5)
        print(f"✓ Django server is reachable!")
        print(f"  Status: {response.status_code}")
        return True
    except requests.exceptions.RequestException as e:
        print(f"✗ Cannot reach Django server: {e}")
        print(f"\nMake sure Django is running:")
        print(f"  python manage.py runserver")
        return False


# At the END of sensor_generator.py

if __name__ == "__main__":
    print("\n" + "="*70)
    print("SENSOR SIMULATOR - Manual Test")
    print("="*70 + "\n")
    
    # Test connection first
    if not test_connection():
        sys.exit(1)
    
    # Initialize simulator
    simulator = SensorSimulator()
    
    # Run a quick test
    print("\nRunning quick test: 6 hours of normal data for plot 1...\n")
    simulator.simulate_normal_day(plot_id=1, duration_hours=6, interval_minutes=30)