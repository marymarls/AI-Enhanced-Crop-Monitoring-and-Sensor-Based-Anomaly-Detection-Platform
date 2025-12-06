"""
Configuration settings for the sensor simulator
"""

# Django API Configuration
API_BASE_URL = "http://localhost:8000"  # Your Django server URL
AUTH_TOKEN = None  # Add JWT token here if authentication is required

# Simulation Parameters
SIMULATION_INTERVAL_MINUTES = 30  # How often to send readings (in minutes)
SIMULATION_DURATION_HOURS = 24    # Duration of each simulation (in hours)

# Sensor Normal Ranges (for realistic data generation)
SENSOR_RANGES = {
    'moisture': {
        'min': 30,
        'max': 80,
        'normal_base': 60,
        'daily_decrease_rate': 1.2,  # % per hour
        'irrigation_boost': 15,      # % increase after irrigation
        'noise_std': 2               # Standard deviation for random noise
    },
    'temperature': {
        'min': 10,
        'max': 40,
        'normal_base': 23,           # Average temperature
        'amplitude': 8,              # Temperature swing (day/night)
        'noise_std': 1               # Standard deviation for random noise
    },
    'humidity': {
        'min': 20,
        'max': 95,
        'temp_correlation': -1.5,    # Humidity decreases as temp increases
        'noise_std': 3               # Standard deviation for random noise
    }
}

# Irrigation Schedule (hours when irrigation occurs)
IRRIGATION_HOURS = [6, 18]  # 6 AM and 6 PM

# Plot IDs for simulation (must exist in your database!)
TRAINING_PLOT_IDS = [1, 2, 3]  # Plots for normal data generation
TESTING_PLOT_IDS = [4, 5, 6, 7]  # Plots for anomaly testing

# Anomaly Parameters
ANOMALY_CONFIGS = {
    'irrigation_failure': {
        'moisture_drop_percentage': 20,
        'start_hour': 10,
        'end_hour': 14
    },
    'heat_stress': {
        'temperature_spike_percentage': 25,
        'start_hour': 12,
        'end_hour': 16
    },
    'sensor_malfunction': {
        'spike_percentage': 40,
        'trigger_hour': 15
    },
    'gradual_drift': {
        'drift_factor_max': 0.02,
        'duration_hours': 24
    }
}

# Training Data Generation
TRAINING_DAYS = 3  # Number of days of normal data to generate
TRAINING_PLOTS_COUNT = 3  # Number of plots to simulate

# API Endpoints
API_ENDPOINTS = {
    'sensor_readings': f'{API_BASE_URL}/api/sensor-readings/',
    'anomalies': f'{API_BASE_URL}/api/anomalies/',
    'recommendations': f'{API_BASE_URL}/api/recommendations/'
}

# Logging
VERBOSE = True  # Print detailed logs during simulation
LOG_FILE = 'simulator_logs.txt'  # Optional: log to file