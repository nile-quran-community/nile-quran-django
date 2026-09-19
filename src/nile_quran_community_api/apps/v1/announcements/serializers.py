from rest_framework.serializers import ModelSerializer, SlugRelatedField

from ..users.models import User
from .models import Announcement


class AnnouncementSerializer(ModelSerializer):
    created_by = SlugRelatedField(
        queryset=User.objects.with_perm("announcements.add_announcement"),
        slug_field="username",
        required=True,
    )

    class Meta:
        model = Announcement
        fields = "__all__"
