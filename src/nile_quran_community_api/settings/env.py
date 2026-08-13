import os
from pathlib import Path

import dj_database_url
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv(os.getenv("DJANGO_ENV_FILEPATH", BASE_DIR / "env/dev.env"))

DEBUG: bool = os.getenv("DJANGO_DEBUG", "true").lower() == "true"

ALLOWED_HOSTS: list[str] = os.getenv("DJANGO_ALLOWED_HOSTS", "").split(",")

CORS_ALLOW_ALL_ORIGINS: bool = os.getenv("DJANGO_ENVIRONMENT", "").upper() != "PROD"

CSRF_TRUSTED_ORIGINS: list[str] = os.getenv("CSRF_TRUSTED_ORIGINS", "").split(",")

SECRET_KEY: str = os.getenv(
    "DJANGO_SECRET_KEY",
    "django-dev-d6d=nm0@u_1+&f_go09c8w07-t8@z$wr*(wi(vn*$a9!bk=^o3",
)

# WARN: Database defaults to db.sqlite in nile_quran_community_api directory if DATABASE_URL is not set
# Refer to https://pypi.org/project/dj-database-url/ for URL schemas for different databases
DATABASES: dict[str, dj_database_url.DBConfig] = {
    "default": dj_database_url.config(
        conn_max_age=600,
        conn_health_checks=True,
        default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}",
    ),
}
