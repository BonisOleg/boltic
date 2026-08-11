from django.db import models
from django.utils.text import slugify

from .product import ProductGroup


class Collection(models.Model):
    """Підбірка `/pidbirka/{slug}/`."""

    title = models.CharField("Назва", max_length=255)
    slug = models.SlugField("Slug", max_length=255, unique=True, allow_unicode=True)
    description = models.TextField("Опис", blank=True)
    is_published = models.BooleanField("Опубліковано", default=False)
    groups = models.ManyToManyField(
        ProductGroup,
        blank=True,
        related_name="collections",
        verbose_name="Товарні групи",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Підбірка"
        verbose_name_plural = "Підбірки"
        ordering = ["title"]

    def __str__(self) -> str:
        return self.title

    def save(self, *args, **kwargs) -> None:
        if not self.slug:
            self.slug = slugify(self.title, allow_unicode=True)
        super().save(*args, **kwargs)
