from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("announcements", "0004_remove_announcement_status"),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name="announcement",
            name="unique_announcement_reference_key",
        ),
        migrations.RenameField(
            model_name="announcement",
            old_name="reference_key",
            new_name="idempotency_key",
        ),
        migrations.AddConstraint(
            model_name="announcement",
            constraint=models.UniqueConstraint(
                condition=models.Q(("idempotency_key", ""), _negated=True),
                fields=("idempotency_key",),
                name="unique_announcement_idempotency_key",
            ),
        ),
    ]
