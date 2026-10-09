from rest_framework.serializers import (
    ModelSerializer,
    ReadOnlyField,
    SlugRelatedField,
)

from ..users.models import User
from .models import Announcement


class AnnouncementSerializer(ModelSerializer):
    # Derived on the model, so read-only here: clients schedule with publish_at.
    status = ReadOnlyField()
    created_by = SlugRelatedField(
        queryset=User.objects.with_perm("announcements.add_announcement"),
        slug_field="username",
        required=True,
    )

    class Meta:
        model = Announcement
        fields = "__all__"
