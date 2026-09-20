from django.contrib.auth.models import AbstractUser
from django.contrib.auth.validators import ASCIIUsernameValidator
from django.core.validators import MaxValueValidator, MinValueValidator, RegexValidator
from django.db import models
from django.db.models.functions import Lower
from django.utils.translation import gettext_lazy as _
from phonenumber_field.modelfields import PhoneNumberField

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


class AcademicStatus(models.TextChoices):
    UNDERGRADUATE = "undergraduate", _("Undergraduate student")
    POSTGRADUATE = "postgraduate", _("Postgraduate student")
    OTHER = "other", _("Other")


class Faculty(models.TextChoices):
    ENGINEERING = "engineering", _("Engineering")
    COMPUTER_SCIENCE = "computer_science", _("Computer Science / AI")
    BUSINESS = "business", _("Business Administration")
    BIOTECHNOLOGY = "biotechnology", _("Biotechnology")
    OTHER = "other", _("Other")


class AcademicYear(models.TextChoices):
    FIRST = "1", _("First year")
    SECOND = "2", _("Second year")
    THIRD = "3", _("Third year")
    FOURTH = "4", _("Fourth year")
    FIFTH = "5", _("Fifth year")
    GRADUATE = "graduate", _("Graduate")


class TajweedLevel(models.TextChoices):
    BEGINNER = "beginner", _("Beginner (no prior exposure to tajweed rules)")
    INTERMEDIATE = "intermediate", _("Intermediate (basic knowledge of tajweed rules)")
    PROFICIENT = "proficient", _("Proficient (skilled knowledge of tajweed rules)")


class User(AbstractUser):
    class Meta:
        verbose_name = _("user")
        verbose_name_plural = _("users")
        ordering = ["id"]
        constraints = [
            models.UniqueConstraint(
                Lower("username"),
                name="unique_username_ci",
                violation_error_message=_("A user with that username already exists."),
            ),
        ]

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

    # NOTE: community profile fields. Self-editable (see CanModifyUser), collected
    # progressively after signup rather than required at registration time.
    phone_number = PhoneNumberField(
        _("phone number"), blank=True, help_text=_("Include your country code.")
    )
    birth_date = models.DateField(_("birth date"), null=True, blank=True)

    academic_status = models.CharField(
        _("academic status"),
        max_length=20,
        choices=AcademicStatus.choices,
        blank=True,
    )
    academic_status_other = models.CharField(
        _("academic status (other)"), max_length=100, blank=True
    )

    faculty = models.CharField(
        _("faculty"), max_length=20, choices=Faculty.choices, blank=True
    )
    faculty_other = models.CharField(_("faculty (other)"), max_length=100, blank=True)

    academic_year = models.CharField(
        _("academic year"),
        max_length=10,
        choices=AcademicYear.choices,
        blank=True,
    )

    residence = models.CharField(_("residence"), max_length=255, blank=True)
    hometown = models.CharField(_("hometown"), max_length=255, blank=True)

    memorized_juz = models.PositiveSmallIntegerField(
        _("memorized Quran parts (juz)"),
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(30)],
    )
    tajweed_level = models.CharField(
        _("tajweed level"),
        max_length=15,
        choices=TajweedLevel.choices,
        blank=True,
    )

    has_islamic_studies = models.BooleanField(
        _("has prior Islamic studies"), null=True, blank=True
    )
    islamic_studies_source = models.CharField(
        _("Islamic studies source"), max_length=255, blank=True
    )

    skills = models.TextField(_("skills"), blank=True)

    @property
    def is_profile_complete(self) -> bool:
        """
        Whether every community profile field has been filled in.
        """
        required: list[object] = [
            self.phone_number,
            self.birth_date,
            self.academic_status,
            self.faculty,
            self.academic_year,
            self.residence,
            self.hometown,
            self.memorized_juz is not None,
            self.tajweed_level,
            self.has_islamic_studies is not None,
        ]
        if self.academic_status == AcademicStatus.OTHER:
            required.append(self.academic_status_other)
        if self.faculty == Faculty.OTHER:
            required.append(self.faculty_other)
        if self.has_islamic_studies:
            required.append(self.islamic_studies_source)
        return all(required)


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
