from django.urls import URLPattern, URLResolver, include, path
from rest_framework.routers import DefaultRouter

from .views import AnnouncementViewSet

app_name: str = "announcements"

router: DefaultRouter = DefaultRouter()
router.register("", AnnouncementViewSet, basename="announcement")
urlpatterns: list[URLPattern | URLResolver] = [path("", include(router.urls))]
