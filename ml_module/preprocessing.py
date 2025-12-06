"""
Data Preprocessing for Anomaly Detection
Prepares sensor readings for ML model
"""

import numpy as np
import pandas as pd
from datetime import timedelta
from django.utils import timezone


class SensorDataPreprocessor:
    """Preprocess sensor readings for anomaly detection"""
    
    def __init__(self):
        self.features = [
            'value',
            'hour_of_day',
            'day_of_week',
            'rolling_mean_6h',
            'rolling_std_6h',
            'value_change_1h',
            'deviation_from_daily_mean',
        ]
    
    def prepare_training_data(self, sensor_readings):
        """
        Prepare sensor readings for model training
        
        Args:
            sensor_readings: QuerySet of SensorReading objects
            
        Returns:
            tuple: (X_features, y_labels, df) - features, labels (all 0 for normal), dataframe
        """
        # Convert QuerySet to DataFrame
        df = self._queryset_to_dataframe(sensor_readings)
        
        if df.empty:
            raise ValueError("No sensor readings provided for training")
        
        # Engineer features
        df = self._engineer_features(df)
        
        # Extract features
        X = df[self.features].values
        
        # For training on normal data, all labels are 0 (normal)
        y = np.zeros(len(df))
        
        # Handle NaN values (from rolling calculations)
        X = np.nan_to_num(X, nan=0.0)
        
        return X, y, df
    
    def prepare_single_reading(self, reading, recent_readings=None):
        """
        Prepare a single sensor reading for prediction
        
        Args:
            reading: SensorReading object
            recent_readings: QuerySet of recent readings for context (last 24 hours)
            
        Returns:
            numpy.ndarray: Feature vector for prediction
        """
        # Get recent readings if not provided
        if recent_readings is None:
            from crop_app.models import SensorReading
            cutoff = timezone.now() - timedelta(hours=24)
            recent_readings = SensorReading.objects.filter(
                plot=reading.plot,
                sensor_type=reading.sensor_type,
                timestamp__gte=cutoff
            ).order_by('timestamp')
        
        # Convert to DataFrame
        df = self._queryset_to_dataframe(recent_readings)
        
        # Add current reading
        current_row = {
            'timestamp': reading.timestamp,
            'value': reading.value,
            'sensor_type': reading.sensor_type,
            'plot_id': reading.plot_id,
        }
        df = pd.concat([df, pd.DataFrame([current_row])], ignore_index=True)
        
        # Engineer features
        df = self._engineer_features(df)
        
        # Get features for the last row (current reading)
        features = df[self.features].iloc[-1].values
        
        # Handle NaN
        features = np.nan_to_num(features, nan=0.0)
        
        return features.reshape(1, -1)
    
    def _queryset_to_dataframe(self, queryset):
        """Convert Django QuerySet to pandas DataFrame"""
        data = list(queryset.values(
            'id', 'timestamp', 'value', 'sensor_type', 'plot_id'
        ))
        
        if not data:
            return pd.DataFrame()
        
        df = pd.DataFrame(data)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df = df.sort_values('timestamp')
        
        return df
    
    def _engineer_features(self, df):
        """
        Engineer features from raw sensor data
        
        Features:
        - Basic: value, hour_of_day, day_of_week
        - Rolling statistics: mean, std over 6 hours
        - Change metrics: value change over 1 hour
        - Deviation: deviation from daily mean
        """
        if df.empty:
            return df
        
        # Time-based features
        df['hour_of_day'] = df['timestamp'].dt.hour
        df['day_of_week'] = df['timestamp'].dt.dayofweek
        
        # Group by plot and sensor type for rolling calculations
        for (plot_id, sensor_type), group in df.groupby(['plot_id', 'sensor_type']):
            idx = group.index
            
            # Rolling statistics (6-hour window = ~12 readings at 30min intervals)
            df.loc[idx, 'rolling_mean_6h'] = group['value'].rolling(
                window=12, min_periods=1
            ).mean()
            
            df.loc[idx, 'rolling_std_6h'] = group['value'].rolling(
                window=12, min_periods=1
            ).std()
            
            # Value change over last hour (~2 readings)
            df.loc[idx, 'value_change_1h'] = group['value'].diff(periods=2)
            
            # Daily mean
            df.loc[idx, 'daily_mean'] = group.set_index('timestamp')['value'].resample(
                '24H'
            ).transform('mean')
            
            # Deviation from daily mean
            df.loc[idx, 'deviation_from_daily_mean'] = (
                group['value'] - df.loc[idx, 'daily_mean']
            )
        
        # Fill NaN values from calculations
        df['rolling_std_6h'] = df['rolling_std_6h'].fillna(0)
        df['value_change_1h'] = df['value_change_1h'].fillna(0)
        df['deviation_from_daily_mean'] = df['deviation_from_daily_mean'].fillna(0)
        
        return df
    
    def get_feature_names(self):
        """Return list of feature names"""
        return self.features


def validate_sensor_reading(reading):
    """
    Validate sensor reading is within reasonable bounds
    
    Args:
        reading: SensorReading object
        
    Returns:
        tuple: (is_valid, error_message)
    """
    sensor_type = reading.sensor_type
    value = reading.value
    
    # Define absolute bounds (beyond which data is clearly invalid)
    bounds = {
        'moisture': (0, 100),
        'temperature': (-20, 60),
        'humidity': (0, 100),
    }
    
    if sensor_type not in bounds:
        return False, f"Unknown sensor type: {sensor_type}"
    
    min_val, max_val = bounds[sensor_type]
    
    if value < min_val or value > max_val:
        return False, f"{sensor_type} value {value} out of bounds ({min_val}-{max_val})"
    
    return True, None