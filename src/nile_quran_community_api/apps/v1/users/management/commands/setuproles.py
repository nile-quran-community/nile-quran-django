from django.contrib.auth.models import Group, Permission
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Create user roles and assign permissions"

    def handle(self, *args, **kwargs) -> None:
        self.stdout.write(self.style.MIGRATE_HEADING("Setup roles:"))
        students, _ = Group.objects.get_or_create(name="Student")
        supervisors, _ = Group.objects.get_or_create(name="Supervisor")
        admins, _ = Group.objects.get_or_create(name="Admin")

        students.permissions.set(
            [
                Permission.objects.get(codename="view_user"),
                Permission.objects.get(codename="view_activity"),
                Permission.objects.get(codename="view_goal"),
            ]
        )
        supervisors.permissions.set(
            [
                Permission.objects.get(codename="view_user"),
                Permission.objects.get(codename="add_activity"),
                Permission.objects.get(codename="view_activity"),
                Permission.objects.get(codename="change_activity"),
                Permission.objects.get(codename="delete_activity"),
                Permission.objects.get(codename="view_goal"),
            ]
        )
        admins.permissions.set(
            [
                Permission.objects.get(codename="add_user"),
                Permission.objects.get(codename="view_user"),
                Permission.objects.get(codename="change_user"),
                Permission.objects.get(codename="delete_user"),
                Permission.objects.get(codename="add_group"),
                Permission.objects.get(codename="view_group"),
                Permission.objects.get(codename="change_group"),
                Permission.objects.get(codename="delete_group"),
                Permission.objects.get(codename="add_activity"),
                Permission.objects.get(codename="view_activity"),
                Permission.objects.get(codename="change_activity"),
                Permission.objects.get(codename="delete_activity"),
                Permission.objects.get(codename="add_goal"),
                Permission.objects.get(codename="view_goal"),
                Permission.objects.get(codename="change_goal"),
                Permission.objects.get(codename="delete_goal"),
            ]
        )
        self.stdout.write("  Roles and permissions successfully set up.")
