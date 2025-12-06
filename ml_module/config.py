"""
ML Module Configuration
Settings for anomaly detection model
"""

import os
from pathlib import Path

# Base directory for ml_module
BASE_DIR = Path(__file__).resolve().parent

# Model storage
MODEL_DIR = BASE_DIR / 'models'
MODEL_DIR.mkdir(exist_ok=True)  # Create if doesn't exist

MODEL_FILE = MODEL_DIR / 'isolation_forest.pkl'
SCALER_FILE = MODEL_DIR / 'scaler.pkl'

# Isolation Forest Parameters
ISOLATION_FOREST_CONFIG = {
    'n_estimators': 100,           # Number of trees
    'contamination': 0.1,          # Expected proportion of anomalies (10%)
    'random_state': 42,            # For reproducibility
    'max_samples': 'auto',         # Samples per tree
    'max_features': 1.0,           # Features per tree
}

# Training Configuration
TRAINING_CONFIG = {
    'min_samples': 50,             # Minimum samples needed to train
    'lookback_hours': 168,         # Use last 7 days for training (168 hours)
    'test_size': 0.2,              # 20% for testing
}

# Anomaly Thresholds (for rule-based classification)
THRESHOLDS = {
    'moisture': {
        'critical_low': 35,        # Below this = irrigation failure
        'critical_high': 85,       # Above this = sensor malfunction
        'normal_min': 45,
        'normal_max': 75,
        'sudden_drop': 10,         # % drop in 1 hour
        'sudden_spike': 15,        # % spike in 1 hour
    },
    'temperature': {
        'critical_low': 10,        # Below this = cold stress
        'critical_high': 35,       # Above this = heat stress
        'normal_min': 18,
        'normal_max': 28,
        'sudden_drop': 5,          # °C drop in 1 hour
        'sudden_spike': 8,         # °C spike in 1 hour
    },
    'humidity': {
        'critical_low': 30,        # Below this = dry stress
        'critical_high': 85,       # Above this = excess moisture
        'normal_min': 45,
        'normal_max': 75,
        'sudden_drop': 15,         # % drop in 1 hour
        'sudden_spike': 20,        # % spike in 1 hour
    }
}

# Anomaly Type Classification
ANOMALY_TYPES = {
    'irrigation_failure': {
        'description': 'Sudden moisture drop detected',
        'severity': 'high',
        'recommendation': 'Check irrigation system immediately',
    },
    'heat_stress': {
        'description': 'Temperature exceeds safe range',
        'severity': 'high',
        'recommendation': 'Increase irrigation frequency, provide shade',
    },
    'cold_stress': {
        'description': 'Temperature below safe range',
        'severity': 'medium',
        'recommendation': 'Monitor crop health, consider protective measures',
    },
    'dry_stress': {
        'description': 'Humidity critically low',
        'severity': 'medium',
        'recommendation': 'Increase irrigation, monitor soil moisture',
    },
    'excess_moisture': {
        'description': 'Humidity critically high',
        'severity': 'medium',
        'recommendation': 'Improve drainage, reduce irrigation',
    },
    'sensor_malfunction': {
        'description': 'Sensor reading out of expected range',
        'severity': 'low',
        'recommendation': 'Check sensor calibration and connections',
    },
    'gradual_drift': {
        'description': 'Gradual deviation from baseline',
        'severity': 'low',
        'recommendation': 'Monitor trend, recalibrate sensors if needed',
    },
}

# Feature Configuration
FEATURES = [
    'value',                       # Current sensor value
    'hour_of_day',                 # Time features
    'day_of_week',
    'rolling_mean_6h',             # Rolling statistics
    'rolling_std_6h',
    'value_change_1h',             # Change over time
    'deviation_from_daily_mean',   # Deviation metrics
]

# Logging
VERBOSE = True                     # Print detailed logs
LOG_PREDICTIONS = True             # Log all predictions