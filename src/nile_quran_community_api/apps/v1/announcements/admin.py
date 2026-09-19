from django.contrib import admin

from .models import Announcement, AnnouncementDelivery


@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ("type", "title", "status", "created_at")


@admin.register(AnnouncementDelivery)
class AnnouncementDeliveryAdmin(admin.ModelAdmin):
    list_display = ("channel", "status", "external_id", "delivered_at")
