from django.contrib import admin

from .models import Announcement, AnnouncementDelivery


@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ("type", "title", "status", "created_at")

    def get_queryset(self, request):
        # status reads the delivery rows; without this the list is one query per row.
        return super().get_queryset(request).prefetch_related("deliveries")


@admin.register(AnnouncementDelivery)
class AnnouncementDeliveryAdmin(admin.ModelAdmin):
    list_display = ("channel", "status", "external_id", "delivered_at")
