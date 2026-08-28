from rest_framework import permissions, viewsets

from .filters import GoalFilterSet
from .models import Goal
from .permissions import CanCreateGoal, CanDeleteGoal, CanModifyGoal
from .serializers import GoalSerializer


class GoalViewSet(viewsets.ModelViewSet):
    serializer_class = GoalSerializer
    queryset = Goal.objects.all()
    filterset_class = GoalFilterSet

    def get_permissions(self):
        permission_classes = []
        if self.action in ("list", "retrieve"):
            permission_classes = [permissions.IsAuthenticated]
        elif self.action == "create":
            permission_classes = [CanCreateGoal]
        elif self.action in ("update", "partial_update"):
            permission_classes = [CanModifyGoal]
        elif self.action == "destroy":
            permission_classes = [CanDeleteGoal]
        return [permission() for permission in permission_classes]
