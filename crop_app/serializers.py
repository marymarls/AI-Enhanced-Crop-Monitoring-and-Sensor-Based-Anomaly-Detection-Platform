from rest_framework import serializers
from .models import FarmProfile, FieldPlot, SensorReading, AnomalyEvent, AgentRecommendation


class FarmProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = FarmProfile
        fields = '__all__'


class FieldPlotSerializer(serializers.ModelSerializer):
    farm_owner = serializers.CharField(source='farm.owner', read_only=True)

    class Meta:
        model = FieldPlot
        fields = ['id', 'farm', 'farm_owner', 'crop_variety', 'plot_name', 'created_at']


class SensorReadingSerializer(serializers.ModelSerializer):
    plot_id = serializers.IntegerField(write_only=True)
    
    class Meta:
        model = SensorReading
        fields = ['id', 'timestamp', 'plot_id', 'sensor_type', 'value', 'source']
        read_only_fields = ['id', 'timestamp']

    def create(self, validated_data):
        """Create sensor reading with plot_id"""
        plot_id = validated_data.pop('plot_id')
        
        # Get the plot instance
        try:
            plot = FieldPlot.objects.get(id=plot_id)
        except FieldPlot.DoesNotExist:
            raise serializers.ValidationError(f"Plot with id {plot_id} does not exist")
        
        # Create the sensor reading with the plot instance
        validated_data['plot'] = plot
        return super().create(validated_data)
    
    def validate_sensor_type(self, value):
        """Validate sensor type is valid"""
        valid_types = ['moisture', 'temperature', 'humidity']
        if value not in valid_types:
            raise serializers.ValidationError(f"Invalid sensor type. Must be one of {valid_types}")
        return value

    def validate_value(self, value):
        """Basic range validation"""
        if value < 0 or value > 200:
            raise serializers.ValidationError("Sensor value out of reasonable range (0-200)")
        return value
    
    def validate_timestamp(self, value):
        """Validate timestamp format and not in future"""
        from django.utils import timezone
        if value and value > timezone.now():
            raise serializers.ValidationError("Timestamp cannot be in the future")
        return value


class AgentRecommendationSerializer(serializers.ModelSerializer):
    class Meta:
        model = AgentRecommendation
        fields = ['id', 'timestamp', 'anomaly_event', 'recommended_action',
                'explanation_text', 'confidence']
        read_only_fields = ['timestamp']


class AnomalyEventSerializer(serializers.ModelSerializer):
    plot_info = FieldPlotSerializer(source='plot', read_only=True)
    recommendation = AgentRecommendationSerializer(read_only=True)

    class Meta:
        model = AnomalyEvent
        fields = ['id', 'timestamp', 'plot', 'plot_info', 'anomaly_type', 'severity',
                  'model_confidence', 'recommendation']
        read_only_fields = ['timestamp']