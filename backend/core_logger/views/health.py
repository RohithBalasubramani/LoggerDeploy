"""
Health Check View

Provides health check endpoint for monitoring.
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny


class HealthView(APIView):
    """
    Health check endpoint.

    GET /health/
    Returns service status (unauthenticated).
    """
    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request):
        return Response({
            'status': 'ok',
            'agent': 'plc-logger',
            'version': '0.1.0'
        })
