"""
Generate ONLY normal training data
Run this BEFORE training the model
"""

import sys
import os
from datetime import datetime, timedelta

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from simulator.sensor_generator import SensorSimulator
import requests


def test_connection():
    """Test connection to Django API"""
    try:
        response = requests.get("http://localhost:8000", timeout=5)
        return True
    except:
        print("❌ Django not running!")
        return False


def generate_training_data():
    """Generate normal data for ML training"""
    
    if not test_connection():
        return False
    
    simulator = SensorSimulator()
    
    TRAINING_PLOTS = [1, 2, 3]  # Only training plots
    TRAINING_DAYS = 2           # 2 days is enough
    INTERVAL_MINUTES = 30       # Every 30 minutes
    
    print("="*70)
    print("GENERATING TRAINING DATA (NORMAL DATA ONLY)")
    print("="*70)
    print(f"Plots: {TRAINING_PLOTS}")
    print(f"Days: {TRAINING_DAYS}")
    print(f"Interval: {INTERVAL_MINUTES} minutes")
    print("="*70 + "\n")
    
    total = 0
    
    for plot_id in TRAINING_PLOTS:
        print(f"\n📊 PLOT {plot_id}")
        
        for day in range(TRAINING_DAYS):
            start_time = datetime.now() - timedelta(days=(TRAINING_DAYS - day))
            
            print(f"  Day {day + 1}/{TRAINING_DAYS}: {start_time.strftime('%Y-%m-%d')}")
            
            readings = simulator.simulate_normal_day(
                plot_id=plot_id,
                duration_hours=24,
                interval_minutes=INTERVAL_MINUTES,
                start_time=start_time
            )
            
            total += readings
            print(f"  ✓ {readings} readings generated")
    
    print("\n" + "="*70)
    print(f"✅ TRAINING DATA COMPLETE: {total} readings")
    print("="*70)
    print("\n📋 NEXT STEPS:")
    print("1. Verify data in Django admin")
    print("2. Train ML model: python ml_module/train.py")
    print("3. Generate anomalies: python scripts/generate_test_anomalies.py")
    print("="*70 + "\n")
    
    return True


if __name__ == "__main__":
    generate_training_data()