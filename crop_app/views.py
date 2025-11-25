from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, BasePermission
from .models import FarmProfile, FieldPlot, SensorReading, AnomalyEvent, AgentRecommendation
from .serializers import (
    FarmProfileSerializer,
    FieldPlotSerializer,
    SensorReadingSerializer,
    AnomalyEventSerializer,
    AgentRecommendationSerializer
)

class IsFarmerOrAdmin(BasePermission):
    """
    Custom permission to only allow:
    - Admins: Full access to everything
    - Farmers: Access only to their own farms/plots/data
    """
    
    def has_permission(self, request, view):
        # User must be authenticated
        return request.user and request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        # Admins can do anything
        if request.user.is_staff:
            return True
        
        # For FarmProfile: check if user is the owner
        if isinstance(obj, FarmProfile):
            return obj.owner == request.user
        
        # For FieldPlot: check if user owns the farm
        if isinstance(obj, FieldPlot):
            return obj.farm.owner == request.user
        
        # For SensorReading: check through plot -> farm -> owner
        if isinstance(obj, SensorReading):
            return obj.plot.farm.owner == request.user
        
        # For AnomalyEvent: check through plot -> farm -> owner
        if isinstance(obj, AnomalyEvent):
            return obj.plot.farm.owner == request.user
        
        # For AgentRecommendation: check through anomaly -> plot -> farm -> owner
        if isinstance(obj, AgentRecommendation):
            return obj.anomaly_event.plot.farm.owner == request.user
        
        return False


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

        if owner_name and user.is_staff:  # Only admins can filter by other owners
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


class SensorReadingViewSet(viewsets.ModelViewSet):
    queryset = SensorReading.objects.select_related('plot').all()
    serializer_class = SensorReadingSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        
        # If not admin, show only user's sensor readings
        if not user.is_staff:
            queryset = queryset.filter(plot__farm__owner=user)
        
        # Apply optional filters
        plot_id = self.request.query_params.get('plot', None)
        sensor_type = self.request.query_params.get('sensor_type', None)

        if plot_id:
            queryset = queryset.filter(plot_id=plot_id)
        if sensor_type:
            queryset = queryset.filter(sensor_type=sensor_type)

        # Limit to recent readings for performance (last 1000)
        return queryset[:1000]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)


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

        return queryset[:100]  # Limit results


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