"""
Script to generate training data for the ML model
Run this first to populate your database with normal sensor readings
"""

import sys
import os
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from simulator.sensor_generator import SensorSimulator, test_connection
from simulator.config import TRAINING_PLOT_IDS, TRAINING_DAYS, SIMULATION_INTERVAL_MINUTES


def generate_training_data():
    """Generate multiple days of normal sensor data for ML training"""
    
    print("\n" + "="*70)
    print("GENERATING TRAINING DATA FOR ML MODEL")
    print("="*70)
    print(f"Plots: {TRAINING_PLOT_IDS}")
    print(f"Days per plot: {TRAINING_DAYS}")
    print(f"Reading interval: {SIMULATION_INTERVAL_MINUTES} minutes")
    print("="*70 + "\n")
    
    # Test connection first
    if not test_connection():
        print("\n❌ Cannot proceed without Django server running!")
        return False
    
    # Initialize simulator
    simulator = SensorSimulator()
    
    total_readings = 0
    
    # Generate data for each plot
    for plot_id in TRAINING_PLOT_IDS:
        print(f"\n{'#'*70}")
        print(f"# PLOT {plot_id}: Generating {TRAINING_DAYS} days of normal data")
        print(f"{'#'*70}\n")
        
        # Generate multiple days
        for day in range(TRAINING_DAYS):
            # Calculate start time for this day (going backwards from now)
            start_time = datetime.now() - timedelta(days=TRAINING_DAYS - day)
            
            print(f"\n--- Day {day + 1}/{TRAINING_DAYS} for Plot {plot_id} ---")
            
            readings = simulator.simulate_normal_day(
                plot_id=plot_id,
                start_hour=0,
                duration_hours=24,
                interval_minutes=SIMULATION_INTERVAL_MINUTES,
                start_time=start_time
            )
            
            total_readings += readings
            print(f"✓ Day {day + 1} complete: {readings} readings sent")
    
    print("\n" + "="*70)
    print("TRAINING DATA GENERATION COMPLETE!")
    print("="*70)
    print(f"Total readings sent: {total_readings}")
    print(f"Plots populated: {len(TRAINING_PLOT_IDS)}")
    print(f"Days per plot: {TRAINING_DAYS}")
    
    # Calculate expected readings
    readings_per_day = (24 * 60 // SIMULATION_INTERVAL_MINUTES) * 3  # 3 sensor types
    expected = readings_per_day * TRAINING_DAYS * len(TRAINING_PLOT_IDS)
    print(f"Expected readings: {expected}")
    print(f"Success rate: {(total_readings/expected)*100:.1f}%")
    
    print("\n" + "="*70)
    print("NEXT STEPS:")
    print("="*70)
    print("1. ✓ Training data generated")
    print("2. → Check Django admin: /admin/ to verify SensorReading entries")
    print("3. → Build ML model: ml_module/detector.py")
    print("4. → Train the model on this data")
    print("5. → Test with anomalies: python scripts/test_anomalies.py")
    print("="*70 + "\n")
    
    return True


if __name__ == "__main__":
    print("\n" + "🌾"*35)
    print("CROP MONITORING SYSTEM - TRAINING DATA GENERATOR")
    print("🌾"*35 + "\n")
    
    success = generate_training_data()
    
    if success:
        print("✅ Training data generation successful!\n")
    else:
        print("❌ Training data generation failed!\n")
        sys.exit(1)