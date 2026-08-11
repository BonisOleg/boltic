from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0003_cms_siteblock_hero_brand"),
    ]

    operations = [
        migrations.AddField(
            model_name="sitesettings",
            name="pickup_enabled",
            field=models.BooleanField(
                default=True, verbose_name="Самовивіз увімкнено"
            ),
        ),
        migrations.AddField(
            model_name="sitesettings",
            name="pickup_description",
            field=models.CharField(
                blank=True,
                default="Самовивіз зі складу — безкоштовно",
                help_text="Текст під опцією самовивозу на оформленні",
                max_length=255,
                verbose_name="Опис самовивозу",
            ),
        ),
        migrations.AddField(
            model_name="sitesettings",
            name="orders_email",
            field=models.EmailField(
                blank=True,
                help_text="Куди слати нові замовлення. Якщо порожньо — використовується Email сайту.",
                max_length=254,
                verbose_name="Email сповіщень про замовлення",
            ),
        ),
    ]
