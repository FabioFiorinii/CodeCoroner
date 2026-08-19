from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand

User = get_user_model()

ADMIN_EMAIL = 'admin@codecoroner.dev'
ADMIN_USERNAME = 'admin'
ADMIN_PASSWORD = 'adminadmin'
DEFAULT_GROUP = 'default'


def ensure_base():
    """Create the base install data (admin user + default group).

    Idempotent: safe to run on every container start.
    """
    group, _ = Group.objects.get_or_create(name=DEFAULT_GROUP)
    user, created = User.objects.get_or_create(
        email=ADMIN_EMAIL,
        defaults={'username': ADMIN_USERNAME},
    )
    user.username = ADMIN_USERNAME
    user.is_superuser = True
    user.is_staff = True
    user.set_password(ADMIN_PASSWORD)
    user.save()
    user.groups.add(group)
    return user, group, created


class Command(BaseCommand):
    help = 'Create the base install data: admin user and default group'

    def handle(self, *_args, **_options):  # noqa: ARG002
        user, group, created = ensure_base()
        self.stdout.write(
            self.style.SUCCESS(
                f'Base seed ok: {user.email} ({"created" if created else "existing"}) '
                f'in group "{group.name}"'
            )
        )
