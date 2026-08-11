from django.db import models
from django.utils.text import slugify


class Brand(models.Model):
    name = models.CharField("Назва", max_length=255)
    slug = models.SlugField("Slug", max_length=255, unique=True, allow_unicode=True)
    logo = models.ImageField("Логотип", upload_to="brands/", blank=True)
    description = models.TextField("Опис", blank=True)
    is_active = models.BooleanField("Активний", default=True)

    class Meta:
        verbose_name = "Бренд"
        verbose_name_plural = "Бренди"
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name

    def save(self, *args, **kwargs) -> None:
        if not self.slug:
            self.slug = slugify(self.name, allow_unicode=True)
        super().save(*args, **kwargs)
