from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("orders", "0002_order_access_token"),
    ]

    operations = [
        migrations.AlterField(
            model_name="order",
            name="customer_name",
            field=models.CharField(max_length=255, verbose_name="ПІБ"),
        ),
        migrations.AlterField(
            model_name="order",
            name="payment_status",
            field=models.CharField(
                choices=[
                    ("pending", "Очікує (офлайн)"),
                    ("paid", "Оплачено"),
                    ("failed", "Помилка"),
                ],
                default="pending",
                max_length=16,
                verbose_name="Оплата",
            ),
        ),
        migrations.AlterField(
            model_name="order",
            name="shipping_method",
            field=models.CharField(
                blank=True,
                choices=[
                    ("pickup", "Самовивіз"),
                    ("nova_poshta", "Нова Пошта"),
                ],
                max_length=32,
                verbose_name="Доставка",
            ),
        ),
        migrations.AlterField(
            model_name="order",
            name="shipping_address",
            field=models.TextField(
                blank=True, verbose_name="Адреса / деталі доставки"
            ),
        ),
        migrations.AddField(
            model_name="order",
            name="np_delivery_type",
            field=models.CharField(
                blank=True,
                choices=[
                    ("warehouse", "Відділення"),
                    ("postomat", "Поштомат"),
                ],
                max_length=16,
                verbose_name="Тип НП",
            ),
        ),
        migrations.AddField(
            model_name="order",
            name="np_city",
            field=models.CharField(
                blank=True, max_length=255, verbose_name="Місто НП"
            ),
        ),
        migrations.AddField(
            model_name="order",
            name="np_city_ref",
            field=models.CharField(
                blank=True, max_length=64, verbose_name="CityRef НП"
            ),
        ),
        migrations.AddField(
            model_name="order",
            name="np_warehouse",
            field=models.CharField(
                blank=True,
                max_length=512,
                verbose_name="Відділення/поштомат",
            ),
        ),
        migrations.AddField(
            model_name="order",
            name="np_warehouse_ref",
            field=models.CharField(
                blank=True, max_length=64, verbose_name="WarehouseRef НП"
            ),
        ),
    ]
