import typing as t

from django.contrib.auth.models import AbstractUser
from django.contrib.auth.validators import ASCIIUsernameValidator
from django.core.validators import MinValueValidator, RegexValidator
from django.db import models
from django.utils.translation import gettext_lazy as _
from django_stubs_ext import StrPromise

arabic_name_validator = RegexValidator(
    regex=r"^[؀-ۿ\s]+$",
    message=_("Only Arabic letters are allowed."),
)

username_validator = ASCIIUsernameValidator(
    message=_(
        "Enter a valid username. This value may contain only unaccented lowercase "
        "a-z and uppercase A-Z letters, numbers, and @/./+/-/_ characters."
    ),
)


class User(AbstractUser):
    class Meta:
        verbose_name = _("user")
        verbose_name_plural = _("users")
        permissions: t.Iterable[tuple[str, str | StrPromise]] = (
            ("change_user_activities", _("Can change the user's activities")),
        )
        ordering = ["id"]

    username = models.CharField(
        _("username"),
        max_length=150,
        unique=True,
        help_text=_(
            "Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only."
        ),
        validators=[username_validator],
        error_messages={
            "unique": _("A user with that username already exists."),
        },
    )
    first_name = models.CharField(
        _("first name"),
        max_length=150,
        blank=True,
        validators=[arabic_name_validator],
    )
    last_name = models.CharField(
        _("last name"),
        max_length=150,
        blank=True,
        validators=[arabic_name_validator],
    )
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
