"""
Anomaly Detection Model
Uses Isolation Forest to detect sensor anomalies
"""

import joblib
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from datetime import timedelta
from django.utils import timezone

from .config import (
    MODEL_FILE, SCALER_FILE, ISOLATION_FOREST_CONFIG,
    THRESHOLDS, ANOMALY_TYPES, VERBOSE
)
from .preprocessing import SensorDataPreprocessor, validate_sensor_reading


class AnomalyDetector:
    """
    Anomaly detection system for agricultural sensor data
    Uses Isolation Forest algorithm + rule-based classification
    """
    
    def __init__(self):
        self.model = None
        self.scaler = None
        self.preprocessor = SensorDataPreprocessor()
        self._load_model()
    
    def _load_model(self):
        """Load trained model and scaler from disk"""
        try:
            if MODEL_FILE.exists():
                self.model = joblib.load(MODEL_FILE)
                if VERBOSE:
                    print(f"✓ Loaded model from {MODEL_FILE}")
            
            if SCALER_FILE.exists():
                self.scaler = joblib.load(SCALER_FILE)
                if VERBOSE:
                    print(f"✓ Loaded scaler from {SCALER_FILE}")
        except Exception as e:
            print(f"⚠️  Could not load model: {e}")
            self.model = None
            self.scaler = None
    
    def train(self, sensor_readings=None, save=True):
        """
        Train the anomaly detection model
        
        Args:
            sensor_readings: QuerySet of normal SensorReading objects
                           If None, loads from database (last 7 days)
            save: Whether to save trained model to disk
            
        Returns:
            dict: Training results with metrics
        """
        from crop_app.models import SensorReading
        
        # Get training data
        if sensor_readings is None:
            cutoff = timezone.now() - timedelta(hours=168)  # Last 7 days
            sensor_readings = SensorReading.objects.filter(
                timestamp__gte=cutoff
            ).order_by('timestamp')
        
        if sensor_readings.count() < 50:
            raise ValueError(
                f"Insufficient training data. Need at least 50 samples, got {sensor_readings.count()}"
            )
        
        print(f"\n{'='*60}")
        print(f"TRAINING ANOMALY DETECTION MODEL")
        print(f"{'='*60}")
        print(f"Training samples: {sensor_readings.count()}")
        
        # Prepare features
        X, y, df = self.preprocessor.prepare_training_data(sensor_readings)
        
        print(f"Features: {self.preprocessor.get_feature_names()}")
        print(f"Feature matrix shape: {X.shape}")
        
        # Scale features
        self.scaler = StandardScaler()
        X_scaled = self.scaler.fit_transform(X)
        
        # Train Isolation Forest
        self.model = IsolationForest(**ISOLATION_FOREST_CONFIG)
        self.model.fit(X_scaled)
        
        # Get anomaly scores for training data
        scores = self.model.score_samples(X_scaled)
        predictions = self.model.predict(X_scaled)
        
        # Calculate statistics
        n_anomalies = np.sum(predictions == -1)
        anomaly_rate = (n_anomalies / len(predictions)) * 100
        
        print(f"\nTraining Results:")
        print(f"  Detected anomalies: {n_anomalies} ({anomaly_rate:.1f}%)")
        print(f"  Anomaly score range: [{scores.min():.3f}, {scores.max():.3f}]")
        print(f"  Mean score: {scores.mean():.3f}")
        
        # Save model
        if save:
            joblib.dump(self.model, MODEL_FILE)
            joblib.dump(self.scaler, SCALER_FILE)
            print(f"\n✓ Model saved to {MODEL_FILE}")
            print(f"✓ Scaler saved to {SCALER_FILE}")
        
        print(f"{'='*60}\n")
        
        return {
            'n_samples': len(X),
            'n_features': X.shape[1],
            'n_anomalies_detected': int(n_anomalies),
            'anomaly_rate': float(anomaly_rate),
            'score_mean': float(scores.mean()),
            'score_std': float(scores.std()),
        }
    
    def predict(self, reading, return_details=True):
        """
        Predict if a sensor reading is an anomaly
        
        Args:
            reading: SensorReading object
            return_details: Whether to return detailed classification
            
        Returns:
            dict: {
                'is_anomaly': bool,
                'confidence': float (0-1),
                'anomaly_score': float,
                'anomaly_type': str,
                'severity': str,
                'explanation': str
            }
        """
        # Validate reading
        is_valid, error = validate_sensor_reading(reading)
        if not is_valid:
            return {
                'is_anomaly': True,
                'confidence': 1.0,
                'anomaly_type': 'sensor_malfunction',
                'severity': 'high',
                'explanation': f"Invalid sensor reading: {error}"
            }
        
        # Check if model is trained
        if self.model is None:
            return self._rule_based_detection(reading)
        
        try:
            # Prepare features
            X = self.preprocessor.prepare_single_reading(reading)
            X_scaled = self.scaler.transform(X)
            
            # Predict
            prediction = self.model.predict(X_scaled)[0]  # -1 = anomaly, 1 = normal
            score = self.model.score_samples(X_scaled)[0]
            
            is_anomaly = prediction == -1
            
            # Convert score to confidence (0-1 range)
            # Isolation Forest scores are negative, more negative = more anomalous
            confidence = self._score_to_confidence(score)
            
            # Classify anomaly type
            if is_anomaly:
                anomaly_type, severity, explanation = self._classify_anomaly(reading)
            else:
                anomaly_type = None
                severity = None
                explanation = "Sensor reading within normal range"
            
            result = {
                'is_anomaly': bool(is_anomaly),
                'confidence': float(confidence),
                'anomaly_score': float(score),
                'anomaly_type': anomaly_type,
                'severity': severity,
                'explanation': explanation
            }
            
            if VERBOSE and is_anomaly:
                print(f"🚨 Anomaly detected: {anomaly_type} (confidence: {confidence:.2f})")
            
            return result
            
        except Exception as e:
            print(f"⚠️  Prediction error: {e}")
            return self._rule_based_detection(reading)
    
    def _rule_based_detection(self, reading):
        """
        Fallback rule-based anomaly detection
        Used when ML model is not available
        """
        sensor_type = reading.sensor_type
        value = reading.value
        
        if sensor_type not in THRESHOLDS:
            return {
                'is_anomaly': False,
                'confidence': 0.0,
                'anomaly_type': None,
                'severity': None,
                'explanation': f"Unknown sensor type: {sensor_type}"
            }
        
        thresholds = THRESHOLDS[sensor_type]
        
        # Check critical thresholds
        if value < thresholds['critical_low']:
            if sensor_type == 'moisture':
                anomaly_type = 'irrigation_failure'
            elif sensor_type == 'temperature':
                anomaly_type = 'cold_stress'
            else:
                anomaly_type = 'dry_stress'
            
            return {
                'is_anomaly': True,
                'confidence': 0.9,
                'anomaly_type': anomaly_type,
                'severity': 'high',
                'explanation': f"{sensor_type} critically low: {value}"
            }
        
        if value > thresholds['critical_high']:
            if sensor_type == 'temperature':
                anomaly_type = 'heat_stress'
            elif sensor_type == 'humidity':
                anomaly_type = 'excess_moisture'
            else:
                anomaly_type = 'sensor_malfunction'
            
            return {
                'is_anomaly': True,
                'confidence': 0.9,
                'anomaly_type': anomaly_type,
                'severity': 'high',
                'explanation': f"{sensor_type} critically high: {value}"
            }
        
        # Normal reading
        return {
            'is_anomaly': False,
            'confidence': 0.0,
            'anomaly_type': None,
            'severity': None,
            'explanation': "Reading within normal range (rule-based check)"
        }
    
    def _classify_anomaly(self, reading):
        """
        Classify the type of anomaly based on sensor reading
        
        Returns:
            tuple: (anomaly_type, severity, explanation)
        """
        sensor_type = reading.sensor_type
        value = reading.value
        thresholds = THRESHOLDS.get(sensor_type, {})
        
        # Check critical thresholds
        if value < thresholds.get('critical_low', 0):
            if sensor_type == 'moisture':
                return 'irrigation_failure', 'high', f"Soil moisture critically low: {value:.1f}%"
            elif sensor_type == 'temperature':
                return 'cold_stress', 'medium', f"Temperature critically low: {value:.1f}°C"
            else:
                return 'dry_stress', 'medium', f"Humidity critically low: {value:.1f}%"
        
        if value > thresholds.get('critical_high', 100):
            if sensor_type == 'temperature':
                return 'heat_stress', 'high', f"Temperature critically high: {value:.1f}°C"
            elif sensor_type == 'humidity':
                return 'excess_moisture', 'medium', f"Humidity critically high: {value:.1f}%"
            else:
                return 'sensor_malfunction', 'low', f"Sensor reading abnormally high: {value:.1f}"
        
        # Default: general anomaly
        return 'sensor_anomaly', 'low', f"Unusual {sensor_type} reading: {value:.1f}"
    
    def _score_to_confidence(self, score):
        """
        Convert Isolation Forest anomaly score to confidence (0-1)
        
        Isolation Forest scores typically range from -0.5 to 0.5
        More negative = more anomalous
        """
        # Normalize score to 0-1 range
        # Scores typically: [-0.5, 0.5]
        # We want: anomalous (negative) → high confidence
        normalized = -score  # Flip so negative becomes positive
        confidence = np.clip(normalized, 0, 1)
        
        return confidence
    
    def is_trained(self):
        """Check if model is trained and ready"""
        return self.model is not None and self.scaler is not None