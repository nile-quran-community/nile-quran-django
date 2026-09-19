from django.conf import settings
from django.contrib.auth.models import Group, Permission
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Create user roles and assign permissions"
    _BASE_INDENT = "  "

    def _indent(self, level: int, text: str) -> str:
        return (self._BASE_INDENT * level) + text

    def handle(self, *args, **kwargs) -> None:
        self.stdout.write(self.style.MIGRATE_HEADING("Setup roles:"))

        for name, perms in settings.GROUP_PERMISSIONS.items():
            group, _ = Group.objects.get_or_create(name=name)
            if len(perms) > 0:
                group.permissions.set(Permission.objects.filter(codename__in=perms))

                perm_names = group.permissions.values_list("name", flat=True)
                self.stdout.write(self._indent(1, f"{name} permissions:"))
                self.stdout.write(
                    "\n".join(map(lambda p: self._indent(2, p), perm_names))
                )
