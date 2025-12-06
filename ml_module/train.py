"""
Training script for anomaly detection model
Run this after generating training data
"""

import django
import os
import sys

# Setup Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'DS2_SOA.settings')
django.setup()

from crop_app.models import SensorReading
from ml_module.detector import AnomalyDetector
from django.utils import timezone
from datetime import timedelta


def train_model():
    """Train the anomaly detection model on normal sensor data"""
    
    print("\n" + "="*70)
    print("TRAINING ANOMALY DETECTION MODEL")
    print("="*70 + "\n")
    
    # Get training data (last 7 days of sensor readings)
    cutoff = timezone.now() - timedelta(days=7)
    sensor_readings = SensorReading.objects.filter(
        timestamp__gte=cutoff
    ).order_by('timestamp')
    
    print(f"Querying sensor readings from last 7 days...")
    print(f"Cutoff date: {cutoff}")
    print(f"Total readings found: {sensor_readings.count()}")
    
    if sensor_readings.count() < 50:
        print("\n❌ ERROR: Insufficient training data!")
        print(f"   Need at least 50 readings, found {sensor_readings.count()}")
        print("\n💡 Solution: Run the simulator first to generate data:")
        print("   python scripts/train_model.py")
        return False
    
    # Show data distribution
    print("\nData distribution by sensor type:")
    for sensor_type in ['moisture', 'temperature', 'humidity']:
        count = sensor_readings.filter(sensor_type=sensor_type).count()
        print(f"  {sensor_type}: {count} readings")
    
    print("\nData distribution by plot:")
    from django.db.models import Count
    plot_counts = sensor_readings.values('plot_id').annotate(
        count=Count('id')
    ).order_by('plot_id')
    for item in plot_counts:
        print(f"  Plot {item['plot_id']}: {item['count']} readings")
    
    # Train the model
    print("\n" + "-"*70)
    print("Starting model training...")
    print("-"*70 + "\n")
    
    detector = AnomalyDetector()
    
    try:
        results = detector.train(sensor_readings, save=True)
        
        print("\n" + "="*70)
        print("✅ TRAINING COMPLETE!")
        print("="*70)
        print(f"Samples used: {results['n_samples']}")
        print(f"Features: {results['n_features']}")
        print(f"Anomalies detected in training: {results['n_anomalies_detected']} ({results['anomaly_rate']:.1f}%)")
        print(f"Mean anomaly score: {results['score_mean']:.3f}")
        print("="*70 + "\n")
        
        # Test the model
        print("Testing model on a sample reading...")
        test_reading = sensor_readings.last()
        result = detector.predict(test_reading)
        
        print(f"\nTest prediction:")
        print(f"  Reading: {test_reading.sensor_type} = {test_reading.value}")
        print(f"  Is anomaly: {result['is_anomaly']}")
        print(f"  Confidence: {result['confidence']:.2f}")
        print(f"  Type: {result['anomaly_type']}")
        
        print("\n" + "="*70)
        print("NEXT STEPS:")
        print("="*70)
        print("1. ✓ Model trained and saved")
        print("2. → Test anomaly detection: python scripts/test_anomalies.py")
        print("3. → Restart Django to load the new model")
        print("4. → Run simulator with anomalies to test detection")
        print("="*70 + "\n")
        
        return True
        
    except Exception as e:
        print(f"\n❌ ERROR during training: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = train_model()
    sys.exit(0 if success else 1)