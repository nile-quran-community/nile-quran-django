from django.core.validators import MinValueValidator
from django.db import models
from django.utils.timezone import localdate
from django.utils.translation import gettext_lazy as _


class Goal(models.Model):
    class Meta:
        verbose_name = _("Goal")
        verbose_name_plural = _("Goals")
        ordering = ["created_at"]

    title: models.CharField = models.CharField(
        _("title"),
        max_length=255,
        blank=False,
        null=False,
    )
    description: models.CharField = models.CharField(
        _("description"),
        max_length=255,
        blank=True,
        null=True,
    )
    current: models.IntegerField = models.IntegerField(
        _("current"),
        validators=[MinValueValidator(0)],
    )
    target: models.IntegerField = models.IntegerField(
        _("target"),
        validators=[MinValueValidator(0)],
    )
    created_at: models.DateField = models.DateField(
        _("created at"),
        auto_now_add=True,
    )
    start_date: models.DateField = models.DateField(
        _("start date"),
        default=localdate,
        blank=False,
        null=True,
    )
    end_date: models.DateField = models.DateField(
        _("end date"),
        blank=False,
        null=True,
        default=None,
    )
