from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from .models import Material
from .serializers import MaterialSerializer


class MaterialViewSet(viewsets.ReadOnlyModelViewSet):
    """List and retrieve materials (read-only for regular users)."""
    queryset = Material.objects.filter(active=True)
    serializer_class = MaterialSerializer
    permission_classes = [IsAuthenticated]
