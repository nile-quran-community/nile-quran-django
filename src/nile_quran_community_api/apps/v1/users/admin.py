from django.contrib import admin

from . import models


@admin.register(models.User)
class UserAdmin(admin.ModelAdmin):
    list_display = ("username", "referrer", "roles", "is_active")

    @admin.display(description="User groups / roles")
    def roles(self, obj: models.User):
        ret: str = "-"
        if obj.groups.exists():
            ret = ", ".join(grp.name for grp in obj.groups.all())

        return ret


@admin.register(models.Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "value")
    search_fields = ("name",)


@admin.register(models.Activity)
class ActivityAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "category", "date")
    list_filter = ("category", "date")
    search_fields = ("user__username", "category__name")
