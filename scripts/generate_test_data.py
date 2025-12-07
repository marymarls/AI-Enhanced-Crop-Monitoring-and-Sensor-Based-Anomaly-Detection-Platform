"""
Generate ONLY anomaly test data
Run this AFTER training the model
"""

import sys
import os
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from simulator.sensor_generator import SensorSimulator

def generate_test_data():
    """Generate anomaly scenarios for testing"""
    
    simulator = SensorSimulator()
    
    # Test plots with anomalies
    scenarios = [
        ('irrigation_failure', 4),
        ('heat_stress', 5),
        ('sensor_malfunction', 6),
        ('gradual_drift', 7)
    ]
    
    print("="*70)
    print("GENERATING TEST DATA (WITH ANOMALIES)")
    print("="*70 + "\n")
    
    for scenario, plot_id in scenarios:
        print(f"⚠️  Plot {plot_id}: {scenario}")
        
        readings, anomalies = simulator.simulate_with_anomalies(
            plot_id=plot_id,
            scenario=scenario,
            start_time=datetime.now()
        )
        
        print(f"   ✓ {readings} readings, {anomalies} anomalies\n")
    
    print("="*70)
    print("✅ TEST DATA COMPLETE")
    print("="*70)
    print("\nNEXT STEPS:")
    print("1. Check Django admin for anomaly events")
    print("2. Verify ML model detected the anomalies")
    print("="*70 + "\n")

if __name__ == "__main__":
    generate_test_data()