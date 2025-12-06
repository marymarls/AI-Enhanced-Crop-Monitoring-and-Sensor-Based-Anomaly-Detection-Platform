from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from .models import FarmProfile, FieldPlot, SensorReading, AnomalyEvent, AgentRecommendation
from .serializers import (
    FarmProfileSerializer,
    FieldPlotSerializer,
    SensorReadingSerializer,
    AnomalyEventSerializer,
    AgentRecommendationSerializer
)


class FarmProfileViewSet(viewsets.ModelViewSet):
    queryset = FarmProfile.objects.all()
    serializer_class = FarmProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        
        # If not admin, show only user's farms
        if not user.is_staff:
            queryset = queryset.filter(owner=user)
        
        # Apply optional filters from query parameters
        owner_name = self.request.query_params.get('owner', None)
        location = self.request.query_params.get('location', None)

        if owner_name and user.is_staff:
            queryset = queryset.filter(owner__username__icontains=owner_name)
        if location:
            queryset = queryset.filter(location__icontains=location)

        return queryset


class FieldPlotViewSet(viewsets.ModelViewSet):
    queryset = FieldPlot.objects.select_related('farm').all()
    serializer_class = FieldPlotSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        
        # If not admin, show only user's plots
        if not user.is_staff:
            queryset = queryset.filter(farm__owner=user)
        
        # Apply optional farm filter
        farm_id = self.request.query_params.get('farm', None)
        if farm_id:
            queryset = queryset.filter(farm_id=farm_id)

        return queryset


# CSRF exempt for sensor data ingestion (IoT simulator doesn't have CSRF tokens)
@method_decorator(csrf_exempt, name='dispatch')
class SensorReadingViewSet(viewsets.ModelViewSet):
    queryset = SensorReading.objects.select_related('plot').all()
    serializer_class = SensorReadingSerializer
    permission_classes = [AllowAny]  # No authentication for sensor ingestion
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Apply optional filters
        plot_id = self.request.query_params.get('plot', None)
        sensor_type = self.request.query_params.get('sensor_type', None)

        if plot_id:
            queryset = queryset.filter(plot_id=plot_id)
        if sensor_type:
            queryset = queryset.filter(sensor_type=sensor_type)

        # Order by timestamp and limit
        return queryset.order_by('-timestamp')[:1000]

    def create(self, request, *args, **kwargs):
        """Ingest sensor data with validation"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        
        # Get the created sensor reading instance
        sensor_reading = serializer.instance
        
        # TODO: Trigger ML anomaly detection here (Week 2)
        # This will be implemented when you build your ML module
        
        headers = self.get_success_headers(serializer.data)
        return Response(
            serializer.data, 
            status=status.HTTP_201_CREATED, 
            headers=headers
        )


class AnomalyEventViewSet(viewsets.ModelViewSet):
    queryset = AnomalyEvent.objects.select_related('plot__farm').all()
    serializer_class = AnomalyEventSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        
        # If not admin, show only user's anomalies
        if not user.is_staff:
            queryset = queryset.filter(plot__farm__owner=user)
        
        # Apply optional filters
        plot_id = self.request.query_params.get('plot', None)
        severity = self.request.query_params.get('severity', None)
        anomaly_type = self.request.query_params.get('anomaly_type', None)

        if plot_id:
            queryset = queryset.filter(plot_id=plot_id)
        if severity:
            queryset = queryset.filter(severity=severity)
        if anomaly_type:
            queryset = queryset.filter(anomaly_type__icontains=anomaly_type)

        return queryset[:100]


class AgentRecommendationViewSet(viewsets.ModelViewSet):
    queryset = AgentRecommendation.objects.select_related('anomaly_event__plot').all()
    serializer_class = AgentRecommendationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        
        # If not admin, show only user's recommendations
        if not user.is_staff:
            queryset = queryset.filter(anomaly_event__plot__farm__owner=user)
        
        # Apply optional filters
        anomaly_id = self.request.query_params.get('anomaly', None)
        min_confidence = self.request.query_params.get('min_confidence', None)

        if anomaly_id:
            queryset = queryset.filter(anomaly_event_id=anomaly_id)
        if min_confidence:
            try:
                min_conf = float(min_confidence)
                queryset = queryset.filter(confidence__gte=min_conf)
            except ValueError:
                pass

        return queryset[:100]