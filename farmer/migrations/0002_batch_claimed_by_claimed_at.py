from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('farmer', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='batch',
            name='claimed_by',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='claimed_batches',
                limit_choices_to={'role': 'product_manager'},
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AddField(
            model_name='batch',
            name='claimed_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
