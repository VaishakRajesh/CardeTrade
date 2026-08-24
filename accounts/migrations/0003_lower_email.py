from django.db import migrations
from django.db.models.functions import Lower


def lowercase_emails(apps, schema_editor):
    """Normalize all stored emails to lowercase for case-insensitive login."""
    User = apps.get_model('accounts', 'User')
    User.objects.exclude(email__isnull=True).update(email=Lower('email'))


def reverse_lowercase_emails(apps, schema_editor):
    # Email case cannot be reliably restored; reverse is a no-op.
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0002_initial'),
    ]

    operations = [
        migrations.RunPython(lowercase_emails, reverse_lowercase_emails),
    ]
