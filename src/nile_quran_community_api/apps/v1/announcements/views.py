from drf_spectacular.utils import extend_schema
from rest_framework import viewsets
from rest_framework.permissions import DjangoModelPermissions

from .filters import AnnouncementFilterSet
from .models import Announcement
from .serializers import AnnouncementSerializer


@extend_schema(tags=["announcements"])
class AnnouncementViewSet(viewsets.ModelViewSet):
    serializer_class = AnnouncementSerializer
    filterset_class = AnnouncementFilterSet
    permission_classes = [DjangoModelPermissions]
    queryset = Announcement.objects.all()
