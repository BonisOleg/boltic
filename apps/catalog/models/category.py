from django.core.exceptions import ValidationError
from django.db import models
from django.utils.text import slugify


class Category(models.Model):
    """Дерево каталогу L1–L2. L3 = ProductGroup (див. tables.md)."""

    class Level(models.IntegerChoices):
        L1 = 1, "L1"
        L2 = 2, "L2"

    parent = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="children",
        verbose_name="Батьківська",
    )
    name = models.CharField("Назва", max_length=255)
    slug = models.SlugField("Slug", max_length=255)
    path = models.CharField("Шлях", max_length=512, unique=True, db_index=True)
    level = models.PositiveSmallIntegerField("Рівень", choices=Level.choices)
    sort_order = models.PositiveIntegerField("Порядок", default=0)
    is_active = models.BooleanField("Активна", default=True)
    seo_title = models.CharField("SEO title", max_length=255, blank=True)
    seo_description = models.TextField("SEO description", blank=True)

    class Meta:
        verbose_name = "Категорія"
        verbose_name_plural = "Категорії"
        ordering = ["sort_order", "name"]
        constraints = [
            models.UniqueConstraint(
                fields=["parent", "slug"],
                name="catalog_category_parent_slug_uniq",
            ),
        ]

    def __str__(self) -> str:
        return self.name

    @property
    def url_path(self) -> str:
        return self.path.strip("/")

    def clean(self) -> None:
        if self.parent is None and self.level != self.Level.L1:
            raise ValidationError({"level": "Корінь має бути L1."})
        if self.parent is not None and self.level != self.Level.L2:
            raise ValidationError({"level": "Дочірня категорія має бути L2."})
        if self.parent is not None and self.parent.level != self.Level.L1:
            raise ValidationError({"parent": "Батько має бути L1."})

    def save(self, *args, **kwargs) -> None:
        if not self.slug:
            self.slug = slugify(self.name, allow_unicode=True)
        if self.parent_id:
            self.level = self.Level.L2
            self.path = f"{self.parent.path.rstrip('/')}/{self.slug}/"
        else:
            self.level = self.Level.L1
            self.path = f"{self.slug}/"
        super().save(*args, **kwargs)
