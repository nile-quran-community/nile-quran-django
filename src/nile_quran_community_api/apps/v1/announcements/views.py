from drf_spectacular.utils import extend_schema
from rest_framework import viewsets
from rest_framework.permissions import DjangoModelPermissions

from .filters import AnnouncementDeliveryFilterSet, AnnouncementFilterSet
from .models import Announcement, AnnouncementDelivery
from .serializers import AnnouncementDeliverySerializer, AnnouncementSerializer


@extend_schema(tags=["announcements"])
class AnnouncementViewSet(viewsets.ModelViewSet):
    serializer_class = AnnouncementSerializer
    filterset_class = AnnouncementFilterSet
    permission_classes = [DjangoModelPermissions]
    queryset = Announcement.objects.prefetch_related("deliveries")


@extend_schema(tags=["announcements"])
class AnnouncementDeliveryViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = AnnouncementDeliverySerializer
    filterset_class = AnnouncementDeliveryFilterSet
    permission_classes = [DjangoModelPermissions]
    queryset = AnnouncementDelivery.objects.select_related("announcement")
