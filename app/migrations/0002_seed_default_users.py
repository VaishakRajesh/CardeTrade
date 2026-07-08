from django.db import migrations
from django.contrib.auth.hashers import make_password


def seed_users(apps, schema_editor):
    User = apps.get_model('app', 'User')
    users_data = [
        dict(username='admin', email='admin@cardetrade.in', password=make_password('admin123'),
             role='admin', phone='+91-0000000000', region='All India',
             is_staff=True, is_superuser=True, is_active=True),
        dict(username='pm1', email='pm@cardetrade.in', password=make_password('pm123'),
             role='product_manager', phone='+91-1111111111', region='Kerala',
             is_staff=True, is_superuser=False, is_active=True),
        dict(username='farmer1', email='farmer@cardetrade.in', password=make_password('farmer123'),
             role='farmer', phone='+91-2222222222', region='Idukki, Kerala',
             is_staff=False, is_superuser=False, is_active=True),
        dict(username='trader1', email='trader@cardetrade.in', password=make_password('trader123'),
             role='trader', phone='+91-3333333333', region='Mumbai, Maharashtra',
             is_staff=False, is_superuser=False, is_active=True),
    ]
    for data in users_data:
        User.objects.get_or_create(
            email=data['email'],
            defaults=data
        )


def reverse_seed(apps, schema_editor):
    User = apps.get_model('app', 'User')
    User.objects.filter(
        username__in=['admin', 'pm1', 'farmer1', 'trader1']
    ).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(seed_users, reverse_seed),
    ]
