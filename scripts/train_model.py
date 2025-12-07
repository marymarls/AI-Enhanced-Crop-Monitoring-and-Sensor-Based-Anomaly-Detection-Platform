import django
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'DS2_SOA.settings')
django.setup()

from ml_module.detector import AnomalyDetector

def train_model():
    print("\n" + "="*70)
    print("TRAINING ANOMALY DETECTION MODEL")
    print("="*70 + "\n")
    
    detector = AnomalyDetector(contamination=0.05)  # Lower to 5%
    
    # Train on plots 1, 2, 3
    metrics = detector.train(plot_ids=[1, 2, 3], verbose=True)
    
    print("\n✅ TRAINING COMPLETE!")
    print("\nNEXT STEPS:")
    print("1. Test detection with anomalies")
    print("2. Integrate into Django views")
    print("3. Connect to AI agent")
    
    return True

if __name__ == "__main__":
    train_model()