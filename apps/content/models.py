from django.db import models
from django.utils.text import slugify

from apps.catalog.models import ProductGroup


class HomeBlock(models.Model):
    key = models.SlugField("Ключ", max_length=64, unique=True)
    title = models.CharField("Заголовок", max_length=255, blank=True)
    body = models.TextField("Текст", blank=True)
    is_active = models.BooleanField("Активний", default=True)
    sort_order = models.PositiveIntegerField("Порядок", default=0)

    class Meta:
        verbose_name = "Блок головної"
        verbose_name_plural = "Блоки головної"
        ordering = ["sort_order", "key"]

    def __str__(self) -> str:
        return self.key


class Promotion(models.Model):
    title = models.CharField("Назва", max_length=255)
    slug = models.SlugField("Slug", max_length=255, unique=True)
    body = models.TextField("Текст", blank=True)
    starts_at = models.DateTimeField("Початок", null=True, blank=True)
    ends_at = models.DateTimeField("Кінець", null=True, blank=True)
    is_published = models.BooleanField("Опубліковано", default=False)
    groups = models.ManyToManyField(
        ProductGroup,
        blank=True,
        related_name="promotions",
        verbose_name="Товари",
    )

    class Meta:
        verbose_name = "Акція"
        verbose_name_plural = "Акції"
        ordering = ["-starts_at", "title"]

    def __str__(self) -> str:
        return self.title

    def save(self, *args, **kwargs) -> None:
        if not self.slug:
            self.slug = slugify(self.title, allow_unicode=True)
        super().save(*args, **kwargs)


class NewsPost(models.Model):
    title = models.CharField("Назва", max_length=255)
    slug = models.SlugField("Slug", max_length=255, unique=True)
    body = models.TextField("Текст")
    published_at = models.DateTimeField("Дата публікації", null=True, blank=True)
    is_published = models.BooleanField("Опубліковано", default=False)

    class Meta:
        verbose_name = "Новина"
        verbose_name_plural = "Новини"
        ordering = ["-published_at", "-id"]

    def __str__(self) -> str:
        return self.title

    def save(self, *args, **kwargs) -> None:
        if not self.slug:
            self.slug = slugify(self.title, allow_unicode=True)
        super().save(*args, **kwargs)


class StaticPage(models.Model):
    slug = models.SlugField("Slug", max_length=128, unique=True)
    title = models.CharField("Заголовок", max_length=255)
    body = models.TextField("Текст")
    seo_title = models.CharField("SEO title", max_length=255, blank=True)
    seo_description = models.TextField("SEO description", blank=True)
    is_published = models.BooleanField("Опубліковано", default=True)

    class Meta:
        verbose_name = "Статична сторінка"
        verbose_name_plural = "Статичні сторінки"
        ordering = ["slug"]

    def __str__(self) -> str:
        return self.title


class ContactBranch(models.Model):
    name = models.CharField("Назва", max_length=255)
    address = models.TextField("Адреса")
    phone = models.CharField("Телефон", max_length=64)
    email = models.EmailField("Email", blank=True)
    map_url = models.URLField("Карта", blank=True)
    sort_order = models.PositiveIntegerField("Порядок", default=0)
    is_active = models.BooleanField("Активна", default=True)

    class Meta:
        verbose_name = "Філія"
        verbose_name_plural = "Філії"
        ordering = ["sort_order", "name"]

    def __str__(self) -> str:
        return self.name
