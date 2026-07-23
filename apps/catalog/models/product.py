from django.db import models
from django.utils.text import slugify

from .brand import Brand
from .category import Category


class ProductGroup(models.Model):
    """Картка товарної групи / PDP `/tovar/{slug}/`."""

    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name="product_groups",
        verbose_name="Категорія L2",
        limit_choices_to={"level": Category.Level.L2},
    )
    brand = models.ForeignKey(
        Brand,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="product_groups",
        verbose_name="Бренд",
    )
    name = models.CharField("Назва", max_length=255)
    slug = models.SlugField("Slug", max_length=255, unique=True)
    short_description = models.TextField("Короткий опис", blank=True)
    description = models.TextField("Опис", blank=True)
    standard = models.CharField("Стандарт", max_length=64, blank=True)
    material = models.CharField("Матеріал", max_length=128, blank=True)
    coating = models.CharField("Покриття", max_length=128, blank=True)
    industry = models.CharField("Галузь", max_length=128, blank=True)
    diameter_min = models.DecimalField(
        "Ø мін", max_digits=8, decimal_places=2, null=True, blank=True
    )
    diameter_max = models.DecimalField(
        "Ø макс", max_digits=8, decimal_places=2, null=True, blank=True
    )
    length_min = models.DecimalField(
        "L мін", max_digits=8, decimal_places=2, null=True, blank=True
    )
    length_max = models.DecimalField(
        "L макс", max_digits=8, decimal_places=2, null=True, blank=True
    )
    is_top = models.BooleanField("Топ", default=False)
    is_promo = models.BooleanField("Акція", default=False)
    is_active = models.BooleanField("Активна", default=True)
    seo_title = models.CharField("SEO title", max_length=255, blank=True)
    seo_description = models.TextField("SEO description", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Товарна група"
        verbose_name_plural = "Товарні групи"
        ordering = ["name"]
        indexes = [
            models.Index(fields=["category", "is_active"]),
        ]

    def __str__(self) -> str:
        return self.name

    def save(self, *args, **kwargs) -> None:
        if not self.slug:
            self.slug = slugify(self.name, allow_unicode=True)
        super().save(*args, **kwargs)


class ProductSKU(models.Model):
    """Рядок асортименту — одиниця купівлі."""

    class StockStatus(models.TextChoices):
        IN_STOCK = "in_stock", "В наявності"
        ON_ORDER = "on_order", "Під замовлення"

    group = models.ForeignKey(
        ProductGroup,
        on_delete=models.CASCADE,
        related_name="skus",
        verbose_name="Група",
    )
    article = models.CharField("Артикул", max_length=64, unique=True)
    name = models.CharField("Назва (з розміром)", max_length=255)
    size_label = models.CharField("Розмір", max_length=64)
    diameter = models.DecimalField(
        "Діаметр", max_digits=8, decimal_places=2, null=True, blank=True
    )
    length = models.DecimalField(
        "Довжина", max_digits=8, decimal_places=2, null=True, blank=True
    )
    thread_pitch = models.DecimalField(
        "Крок різьби", max_digits=6, decimal_places=2, null=True, blank=True
    )
    strength_class = models.CharField("Клас міцності", max_length=32, blank=True)
    min_party = models.PositiveIntegerField("Мін. партія", default=1)
    stock_status = models.CharField(
        "Наявність",
        max_length=16,
        choices=StockStatus.choices,
        default=StockStatus.IN_STOCK,
    )
    stock_qty = models.PositiveIntegerField("Кількість на складі", null=True, blank=True)
    price = models.DecimalField("Ціна за шт", max_digits=12, decimal_places=2)
    price_includes_vat = models.BooleanField("Ціна з ПДВ", default=True)
    vat_rate = models.DecimalField(
        "Ставка ПДВ %", max_digits=5, decimal_places=2, default=20
    )
    party_price = models.DecimalField(
        "Ціна партії", max_digits=12, decimal_places=2, null=True, blank=True
    )
    is_active = models.BooleanField("Активний", default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "SKU"
        verbose_name_plural = "SKU"
        ordering = ["diameter", "length", "article"]
        indexes = [
            models.Index(fields=["group", "is_active"]),
            models.Index(fields=["diameter", "length"]),
        ]

    def __str__(self) -> str:
        return f"{self.article} · {self.name}"


class ProductImage(models.Model):
    group = models.ForeignKey(
        ProductGroup,
        on_delete=models.CASCADE,
        related_name="images",
        verbose_name="Група",
    )
    image = models.ImageField("Зображення", upload_to="products/")
    alt = models.CharField("Alt", max_length=255, blank=True)
    sort_order = models.PositiveIntegerField("Порядок", default=0)
    is_primary = models.BooleanField("Головне", default=False)

    class Meta:
        verbose_name = "Зображення товару"
        verbose_name_plural = "Зображення товарів"
        ordering = ["sort_order", "id"]

    def __str__(self) -> str:
        return self.alt or f"Image #{self.pk}"


class ProductDocument(models.Model):
    """Вкладка «Документи» на PDP."""

    group = models.ForeignKey(
        ProductGroup,
        on_delete=models.CASCADE,
        related_name="documents",
        verbose_name="Група",
    )
    title = models.CharField("Назва", max_length=255)
    file = models.FileField("Файл", upload_to="product_docs/")
    sort_order = models.PositiveIntegerField("Порядок", default=0)

    class Meta:
        verbose_name = "Документ товару"
        verbose_name_plural = "Документи товарів"
        ordering = ["sort_order", "id"]

    def __str__(self) -> str:
        return self.title
