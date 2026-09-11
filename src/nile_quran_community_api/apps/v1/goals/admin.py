from django.contrib import admin

from .models import Goal


@admin.register(Goal)
class GoalAdmin(admin.ModelAdmin):
    list_display = ("title", "current", "target", "start_date", "end_date")
