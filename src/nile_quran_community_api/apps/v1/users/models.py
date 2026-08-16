import typing as t

from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator
from django.db import models
from django.utils.translation import gettext_lazy as _
from django_stubs_ext import StrPromise


class User(AbstractUser):
    class Meta:
        verbose_name = _("user")
        verbose_name_plural = _("users")
        permissions: t.Iterable[tuple[str, str | StrPromise]] = (
            ("change_user_activities", _("Can change the user's activities")),
        )
        ordering = ["id"]

    email = models.EmailField(
        _("email address"),
        unique=True,
        blank=False,
        null=False,
    )
    referrer: models.ForeignKey = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        help_text=_("User referrer reference."),
        related_name="referred",
    )
    supervisor: models.ForeignKey = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        help_text=_("User supervisor reference (required for students)."),
        related_name="supervised",
    )


class Category(models.Model):
    class Meta:
        verbose_name = _("Category")
        verbose_name_plural = _("Categories")
        ordering = ["id"]

    name: models.CharField = models.CharField(
        _("name"),
        max_length=255,
        blank=False,
        null=False,
        unique=True,
    )
    value: models.IntegerField = models.IntegerField(
        _("value"),
        blank=False,
        null=False,
    )

    def __str__(self) -> str:
        return self.name


class Activity(models.Model):
    class Meta:
        verbose_name = _("Activity")
        verbose_name_plural = _("Activities")
        ordering = ["-date"]

    user: models.ForeignKey = models.ForeignKey(
        User,
        null=False,
        blank=False,
        on_delete=models.CASCADE,
        related_name="activities",
        verbose_name=_("user"),
    )
    category: models.ForeignKey = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        verbose_name=_("category"),
    )
    date: models.DateTimeField = models.DateTimeField(
        _("date"),
        blank=False,
        null=False,
    )
    multiplier: models.PositiveIntegerField = models.PositiveIntegerField(
        _("multiplier"),
        default=1,
        blank=False,
        null=False,
        validators=[MinValueValidator(1)],
    )

    def __str__(self) -> str:
        return f"{self.user} - {self.category} - {self.date}"
