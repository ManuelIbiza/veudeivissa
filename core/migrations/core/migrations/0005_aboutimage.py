from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0004_heroimage'),
    ]

    operations = [
        migrations.CreateModel(
            name='AboutImage',
            fields=[
                (
                    'id',
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name='ID'
                    )
                ),
                (
                    'title',
                    models.CharField(
                        blank=True,
                        max_length=120
                    )
                ),
                (
                    'image',
                    models.ImageField(
                        upload_to='core/about/'
                    )
                ),
                (
                    'is_active',
                    models.BooleanField(
                        default=True
                    )
                ),
                (
                    'display_order',
                    models.PositiveIntegerField(
                        default=0
                    )
                ),
                (
                    'created_at',
                    models.DateTimeField(
                        auto_now_add=True
                    )
                ),
                (
                    'updated_at',
                    models.DateTimeField(
                        auto_now=True
                    )
                ),
            ],
            options={
                'verbose_name': 'Imagen about',
                'verbose_name_plural': 'Imágenes about',
                'ordering': ['display_order', 'id'],
            },
        ),
    ]