from drf_spectacular.utils import extend_schema
from rest_framework import viewsets
from rest_framework.permissions import DjangoModelPermissions

from .filters import GoalFilterSet
from .models import Goal
from .serializers import GoalSerializer


@extend_schema(tags=["goals"])
class GoalViewSet(viewsets.ModelViewSet):
    serializer_class = GoalSerializer
    filterset_class = GoalFilterSet
    permission_classes = [DjangoModelPermissions]
    queryset = Goal.objects.all()
