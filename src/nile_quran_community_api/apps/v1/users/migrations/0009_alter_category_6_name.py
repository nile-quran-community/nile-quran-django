from django.db import migrations
from django.utils.translation import gettext_noop


def update_team_activity_category(apps, _):
    Category = apps.get_model("users", "Category")

    Category.objects.filter(id=6).update(
        name=gettext_noop("Contributing to team activities"),
    )


def revert_team_activity_category(apps, _):
    Category = apps.get_model("users", "Category")

    Category.objects.filter(id=6).update(
        name=gettext_noop("Attending team meeting"),
    )


class Migration(migrations.Migration):
    dependencies = [
        ("users", "0008_activity_multiplier"),
    ]

    operations = [
        migrations.RunPython(
            update_team_activity_category,
            revert_team_activity_category,
        ),
    ]
