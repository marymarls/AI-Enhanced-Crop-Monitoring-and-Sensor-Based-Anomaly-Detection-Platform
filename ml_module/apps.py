"""
ML Module Django App Configuration
"""

from django.apps import AppConfig


class MlModuleConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'ml_module'
    verbose_name = 'ML Anomaly Detection Module'
    
    def ready(self):
        """
        Called when Django starts.
        Import signals to register them with Django.
        """
        #import ml_module.signals  # This registers the signal handlers
        pass