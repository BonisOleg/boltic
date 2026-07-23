from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from apps.catalog.models import ProductGroup


class Review(models.Model):
    group = models.ForeignKey(
        ProductGroup,
        on_delete=models.CASCADE,
        related_name="reviews",
        verbose_name="Товарна група",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="reviews",
        verbose_name="Користувач",
    )
    rating = models.PositiveSmallIntegerField(
        "Оцінка",
        validators=[MinValueValidator(1), MaxValueValidator(5)],
    )
    body = models.TextField("Текст")
    is_published = models.BooleanField("Опубліковано", default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Відгук"
        verbose_name_plural = "Відгуки"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["group", "is_published"]),
        ]

    def __str__(self) -> str:
        return f"{self.group} · {self.rating}★"
