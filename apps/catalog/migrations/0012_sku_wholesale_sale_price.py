from django.db import migrations, models


def migrate_wholesale_m1(apps, schema_editor):
    ProductSKU = apps.get_model("catalog", "ProductSKU")
    for sku in ProductSKU.objects.all().iterator(chunk_size=500):
        updates = []
        if sku.party_price is not None:
            sku.wholesale_from_qty = sku.min_party
            updates.append("wholesale_from_qty")
        if sku.min_party != 1:
            sku.min_party = 1
            updates.append("min_party")
        if updates:
            sku.save(update_fields=updates)


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):
    dependencies = [
        ("catalog", "0011_productsku_foam_glue_fields"),
    ]

    operations = [
        migrations.AddField(
            model_name="productsku",
            name="wholesale_from_qty",
            field=models.PositiveIntegerField(
                blank=True,
                help_text="Від цієї кількості (включно) застосовується оптова ціна за шт.",
                null=True,
                verbose_name="Опт від (шт)",
            ),
        ),
        migrations.AddField(
            model_name="productsku",
            name="sale_price",
            field=models.DecimalField(
                blank=True,
                decimal_places=2,
                help_text="Лише для роздробу (qty нижче порога опту). Опт завжди без акції.",
                max_digits=12,
                null=True,
                verbose_name="Акційна ціна (роздріб)",
            ),
        ),
        migrations.RunPython(migrate_wholesale_m1, noop_reverse),
        migrations.AlterField(
            model_name="productsku",
            name="min_party",
            field=models.PositiveIntegerField(
                default=1,
                help_text="Мінімальна кількість шт у замовленні цього SKU. Крок кількості = 1.",
                verbose_name="Мін. кількість",
            ),
        ),
        migrations.AlterField(
            model_name="productsku",
            name="pack_qty",
            field=models.PositiveIntegerField(
                blank=True,
                help_text="Інформативно на картці: скільки штук в упаковці (не впливає на розрахунок).",
                null=True,
                verbose_name="Шт в упаковці",
            ),
        ),
        migrations.AlterField(
            model_name="productsku",
            name="party_price",
            field=models.DecimalField(
                blank=True,
                decimal_places=2,
                help_text="Грн за 1 шт при qty ≥ «Опт від». Без sale_price.",
                max_digits=12,
                null=True,
                verbose_name="Ціна опт (за шт)",
            ),
        ),
    ]
