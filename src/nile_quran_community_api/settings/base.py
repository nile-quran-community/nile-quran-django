from collections.abc import Iterable
from datetime import timedelta
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from typing import Any

from django.utils.translation import gettext_lazy as _

from ..apps import v1

BASE_DIR = Path(__file__).resolve().parent.parent

INSTALLED_APPS: list[str] = [
    # NOTE: django apps
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # NOTE: drf apps
    "rest_framework",
    "drf_spectacular",
    "django_filters",
    "corsheaders",
    "phonenumber_field",
    # NOTE: API v1 apps
    *v1.APPS,
]

MIDDLEWARE: list[str] = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

TEMPLATES: list[dict] = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

ROOT_URLCONF: str = "nile_quran_community_api.urls"

WSGI_APPLICATION: str = "nile_quran_community_api.wsgi.application"

AUTH_PASSWORD_VALIDATORS: list[dict[str, str]] = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


LANGUAGE_CODE: str = "en-us"

TIME_ZONE: str = "UTC"

USE_I18N: bool = True

LANGUAGE_CODE = "en"
LANGUAGES = [
    ("en", _("English")),
    ("ar", _("Arabic")),
]

LOCALE_PATHS = [
    BASE_DIR / "locale",
    BASE_DIR / "apps" / "v1" / "users" / "locale",
    BASE_DIR / "apps" / "v1" / "goals" / "locale",
]

USE_TZ: bool = True

STATIC_URL: str = "static/"

STATIC_ROOT: Path = BASE_DIR / "staticfiles"

DEFAULT_AUTO_FIELD: str = "django.db.models.BigAutoField"

AUTH_USER_MODEL: str = "users.User"

SIMPLE_JWT: dict[str, Any] = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=30),
}

REST_FRAMEWORK: dict[str, int | Iterable] = {
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_RENDERER_CLASSES": ("rest_framework.renderers.JSONRenderer",),
    "DEFAULT_PARSER_CLASSES": ("rest_framework.parsers.JSONParser",),
    "DEFAULT_PERMISSION_CLASSES": ("rest_framework.permissions.IsAuthenticated",),
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_FILTER_BACKENDS": ("django_filters.rest_framework.DjangoFilterBackend",),
    "DEFAULT_PAGINATION_CLASS": ("rest_framework.pagination.PageNumberPagination"),
    "PAGE_SIZE": 50,
    "EXCEPTION_HANDLER": "nile_quran_community_api.exceptions.custom_exception_handler",
}

STORAGES = {
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    }
}

API_VERSION: str = "0.0.0"
try:
    API_VERSION = version("nile_quran_community_api")
except PackageNotFoundError:
    pass

SPECTACULAR_SETTINGS: dict[str, str | bool] = {
    "TITLE": "Nile Quran Community API",
    "DESCRIPTION": "Nile Quran Community API for keeping track of achievements",
    "VERSION": API_VERSION,
}

# NOTE: Group name to permissions mapping
GROUP_PERMISSIONS: dict[str, tuple[str, ...]] = {
    # NOTE: Main roles
    "Admin": (
        "add_user",
        "view_user",
        "change_user",
        "delete_user",
        "add_group",
        "view_group",
        "change_group",
        "delete_group",
        "add_activity",
        "view_activity",
        "change_activity",
        "delete_activity",
        "add_goal",
        "view_goal",
        "change_goal",
        "delete_goal",
        "add_announcement",
        "view_announcement",
        "change_announcement",
        "delete_announcement",
    ),
    "Supervisor": (
        "view_user",
        "add_activity",
        "view_activity",
        "change_activity",
        "delete_activity",
        "view_goal",
        "view_announcement",
    ),
    "Student": (
        "view_user",
        "view_activity",
        "view_goal",
        "view_announcement",
    ),
    # NOTE: Additional NQC teams
    "Treasurer": (
        "add_goal",
        "view_goal",
        "change_goal",
        "delete_goal",
    ),
    "Media": (
        "add_goal",
        "view_goal",
        "change_goal",
        "delete_goal",
        "add_announcement",
        "view_announcement",
        "change_announcement",
        "delete_announcement",
    ),
    "Developer": (),
    "Researcher": (),
    "Beast": (),
}
