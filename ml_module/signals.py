"""
Django Signals for Automatic Anomaly Detection
Automatically runs ML model when sensor reading is saved
"""

from django.db.models.signals import post_save
from django.dispatch import receiver
from crop_app.models import SensorReading, AnomalyEvent
from .detector import AnomalyDetector
from .config import VERBOSE


# Global detector instance (loaded once, reused)
_detector = None

def get_detector():
    """Get or create global detector instance"""
    global _detector
    if _detector is None:
        _detector = AnomalyDetector()
    return _detector


@receiver(post_save, sender=SensorReading)
def detect_anomaly_on_save(sender, instance, created, **kwargs):
    """
    Automatically detect anomalies when a new sensor reading is saved.
    
    This signal is triggered every time a SensorReading is created.
    It runs the ML model and creates an AnomalyEvent if needed.
    
    Args:
        sender: The model class (SensorReading)
        instance: The actual SensorReading object that was saved
        created: Boolean - True if this is a new reading, False if updated
        **kwargs: Additional arguments from Django
    """
    # Only process new readings, not updates
    if not created:
        return
    
    try:
        # Get detector
        detector = get_detector()
        
        # Check if model is trained
        if not detector.is_trained():
            if VERBOSE:
                print(f"⚠️  ML model not trained yet. Skipping anomaly detection for reading {instance.id}")
            return
        
        # Run prediction
        result = detector.predict(instance)
        
        # If anomaly detected, create AnomalyEvent
        if result['is_anomaly']:
            anomaly = AnomalyEvent.objects.create(
                plot=instance.plot,
                anomaly_type=result['anomaly_type'],
                severity=result['severity'],
                model_confidence=result['confidence'],
                # Store additional info if your model has these fields:
                # explanation=result['explanation'],
                # sensor_reading=instance,
            )
            
            if VERBOSE:
                print(f"🚨 Anomaly detected and saved!")
                print(f"   Reading ID: {instance.id}")
                print(f"   Plot: {instance.plot_id}")
                print(f"   Type: {result['anomaly_type']}")
                print(f"   Severity: {result['severity']}")
                print(f"   Confidence: {result['confidence']:.2f}")
                print(f"   Anomaly ID: {anomaly.id}")
        
        elif VERBOSE:
            print(f"✓ Normal reading processed: {instance.sensor_type}={instance.value} (Plot {instance.plot_id})")
    
    except Exception as e:
        # Don't crash if ML fails - just log the error
        print(f"⚠️  Error in anomaly detection signal: {e}")
        import traceback
        if VERBOSE:
            traceback.print_exc()