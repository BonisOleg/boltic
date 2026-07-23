from django.conf import settings
from django.db import models


class UserProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="profile",
        verbose_name="Користувач",
    )
    phone = models.CharField("Телефон", max_length=32, blank=True)
    company = models.CharField("Компанія", max_length=255, blank=True)
    default_shipping_address = models.TextField("Адреса доставки", blank=True)

    class Meta:
        verbose_name = "Профіль"
        verbose_name_plural = "Профілі"

    def __str__(self) -> str:
        return f"Профіль {self.user_id}"
