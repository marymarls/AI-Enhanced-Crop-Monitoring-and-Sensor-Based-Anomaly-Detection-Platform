from django.contrib import admin
from .models import FarmProfile, FieldPlot, SensorReading, AnomalyEvent, AgentRecommendation


@admin.register(FarmProfile)
class FarmProfileAdmin(admin.ModelAdmin):
    list_display = ['id', 'location', 'owner', 'crop_type', 'size', 'created_at']
    list_filter = ['crop_type', 'created_at']
    search_fields = ['location', 'owner__username', 'crop_type']
    ordering = ['-created_at']


@admin.register(FieldPlot)
class FieldPlotAdmin(admin.ModelAdmin):
    list_display = ['id', 'plot_name', 'farm', 'crop_variety', 'created_at']
    list_filter = ['farm', 'crop_variety', 'created_at']
    search_fields = ['plot_name', 'farm__location', 'crop_variety']
    ordering = ['-created_at']


@admin.register(SensorReading)
class SensorReadingAdmin(admin.ModelAdmin):
    list_display = ['id', 'plot', 'sensor_type', 'value', 'timestamp', 'source']
    list_filter = ['sensor_type', 'timestamp', 'source']
    search_fields = ['plot__plot_name', 'plot__farm__location']
    ordering = ['-timestamp']
    readonly_fields = ['timestamp']


@admin.register(AnomalyEvent)
class AnomalyEventAdmin(admin.ModelAdmin):
    list_display = ['id', 'plot', 'anomaly_type', 'severity', 'model_confidence', 'timestamp']
    list_filter = ['severity', 'anomaly_type', 'timestamp']
    search_fields = ['plot__plot_name', 'anomaly_type']
    ordering = ['-timestamp']
    readonly_fields = ['timestamp']


@admin.register(AgentRecommendation)
class AgentRecommendationAdmin(admin.ModelAdmin):
    list_display = ['id', 'anomaly_event', 'recommended_action', 'confidence', 'timestamp']
    list_filter = ['confidence', 'timestamp']
    search_fields = ['recommended_action', 'explanation_text']
    ordering = ['-timestamp']
    readonly_fields = ['timestamp']