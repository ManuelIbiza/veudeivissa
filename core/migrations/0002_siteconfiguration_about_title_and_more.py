from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='siteconfiguration',
            name='about_image',
            field=models.ImageField(blank=True, null=True, upload_to='core/about/'),
        ),
        migrations.AddField(
            model_name='siteconfiguration',
            name='about_title',
            field=models.CharField(blank=True, default='Servicios musicales a medida', max_length=150),
        ),
        migrations.CreateModel(
            name='HeroImage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(blank=True, max_length=120)),
                ('image', models.ImageField(upload_to='core/hero/')),
                ('is_active', models.BooleanField(default=True)),
                ('display_order', models.PositiveIntegerField(default=0)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'Imagen hero',
                'verbose_name_plural': 'Imágenes hero',
                'ordering': ['display_order', 'id'],
            },
        ),
        migrations.CreateModel(
            name='EventFormat',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=120)),
                ('description', models.TextField()),
                ('image', models.ImageField(blank=True, null=True, upload_to='core/formats/')),
                ('is_active', models.BooleanField(default=True)),
                ('display_order', models.PositiveIntegerField(default=0)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'Formato',
                'verbose_name_plural': 'Formatos',
                'ordering': ['display_order', 'id'],
            },
        ),
        migrations.AlterField(
            model_name='siteconfiguration',
            name='hero_image',
            field=models.ImageField(blank=True, null=True, upload_to='core/hero/'),
        ),
    ]