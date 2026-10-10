from django.urls import URLPattern, URLResolver, include, path
from rest_framework.routers import DefaultRouter

from .views import AnnouncementDeliveryViewSet, AnnouncementViewSet

app_name: str = "announcements"

router: DefaultRouter = DefaultRouter()
router.register("", AnnouncementViewSet, basename="announcement")
router.register("deliveries", AnnouncementDeliveryViewSet, basename="delivery")

urlpatterns: list[URLPattern | URLResolver] = [path("", include(router.urls))]
