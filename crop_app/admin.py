from django.contrib import admin
from .models import FarmProfile, FieldPlot, SensorReading, AnomalyEvent, AgentRecommendation


class FarmProfileAdmin(admin.ModelAdmin):
    list_display = ['owner', 'location', 'size', 'crop_type', 'created_at']
    list_filter = ['crop_type', 'location']
    search_fields = ['owner', 'location']


class FieldPlotAdmin(admin.ModelAdmin):
    list_display = ['plot_name', 'crop_variety', 'farm', 'created_at']
    list_filter = ['crop_variety', 'farm']
    search_fields = ['plot_name', 'crop_variety']


class SensorReadingAdmin(admin.ModelAdmin):
    list_display = ['timestamp', 'plot', 'sensor_type', 'value', 'source']
    list_filter = ['sensor_type', 'source']
    search_fields = ['plot__plot_name']


class AnomalyEventAdmin(admin.ModelAdmin):
    list_display = ['timestamp', 'plot', 'anomaly_type', 'severity', 'model_confidence']
    list_filter = ['severity', 'anomaly_type']
    search_fields = ['plot__plot_name', 'anomaly_type']


class AgentRecommendationAdmin(admin.ModelAdmin):
    list_display = ['timestamp', 'anomaly_event', 'recommended_action', 'confidence']
    list_filter = ['confidence']
    search_fields = ['recommended_action', 'explanation_text']


admin.site.register(FarmProfile, FarmProfileAdmin)
admin.site.register(FieldPlot, FieldPlotAdmin)
admin.site.register(SensorReading, SensorReadingAdmin)
admin.site.register(AnomalyEvent, AnomalyEventAdmin)
admin.site.register(AgentRecommendation, AgentRecommendationAdmin)