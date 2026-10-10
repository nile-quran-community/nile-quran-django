from rest_framework.serializers import (
    ModelSerializer,
    ReadOnlyField,
    SlugRelatedField,
)

from .models import Announcement, AnnouncementDelivery


class AnnouncementDeliverySerializer(ModelSerializer):
    class Meta:
        model = AnnouncementDelivery
        fields = "__all__"


class AnnouncementSerializer(ModelSerializer):
    status = ReadOnlyField()
    deliveries = AnnouncementDeliverySerializer(many=True, read_only=True)
    created_by = SlugRelatedField(slug_field="username", read_only=True)

    class Meta:
        model = Announcement
        fields = "__all__"
