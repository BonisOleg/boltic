from django.core.cache import cache
from django.core.validators import RegexValidator
from django.db import models

_HEX = RegexValidator(
    regex=r"^#(?:[0-9a-fA-F]{3}){1,2}$",
    message="Вкажіть колір у форматі #RRGGBB",
)


class SiteSettings(models.Model):
    """Singleton налаштувань сайту + тема (кольори)."""

    site_name = models.CharField("Назва сайту", max_length=128, default="БОЛТіК°")
    phone = models.CharField("Телефон", max_length=64, blank=True)
    email = models.EmailField("Email", blank=True)
    address = models.TextField("Адреса", blank=True)
    social_json = models.JSONField("Соцмережі", default=dict, blank=True)
    order_hours = models.CharField(
        "Прийом замовлень",
        max_length=128,
        blank=True,
        default="цілодобово | без вихідних",
    )
    processing_hours = models.CharField(
        "Обробка замовлень",
        max_length=128,
        blank=True,
        default="Пн - Пт | 9:00 - 18:00",
    )

    # Тема — зелений primary з логотипу
    color_primary = models.CharField(
        "Primary (зелений)", max_length=7, default="#69BE68", validators=[_HEX]
    )
    color_primary_dark = models.CharField(
        "Primary темний", max_length=7, default="#48A848", validators=[_HEX]
    )
    color_secondary = models.CharField(
        "Secondary (синій)", max_length=7, default="#314780", validators=[_HEX]
    )
    color_accent = models.CharField(
        "Accent (жовтий)", max_length=7, default="#D6AE34", validators=[_HEX]
    )
    color_bg = models.CharField(
        "Фон сторінки", max_length=7, default="#ECEDEF", validators=[_HEX]
    )
    color_surface = models.CharField(
        "Поверхня / картки", max_length=7, default="#FFFFFF", validators=[_HEX]
    )
    color_text = models.CharField(
        "Текст", max_length=7, default="#212529", validators=[_HEX]
    )
    color_text_muted = models.CharField(
        "Текст вторинний", max_length=7, default="#6B6666", validators=[_HEX]
    )
    color_header_bg = models.CharField(
        "Фон хедера", max_length=7, default="#FFFFFF", validators=[_HEX]
    )
    color_header_top_bg = models.CharField(
        "Фон top-bar", max_length=7, default="#314780", validators=[_HEX]
    )
    color_header_top_text = models.CharField(
        "Текст top-bar", max_length=7, default="#FFFFFF", validators=[_HEX]
    )
    color_logo_bg = models.CharField(
        "Фон логоблоку", max_length=7, default="#69BE68", validators=[_HEX]
    )
    color_catalog_btn = models.CharField(
        "Кнопка Каталог", max_length=7, default="#69BE68", validators=[_HEX]
    )
    color_catalog_btn_text = models.CharField(
        "Текст кнопки Каталог", max_length=7, default="#FFFFFF", validators=[_HEX]
    )
    color_link = models.CharField(
        "Посилання", max_length=7, default="#48A848", validators=[_HEX]
    )
    color_success = models.CharField(
        "Успіх / наявність", max_length=7, default="#2E8B57", validators=[_HEX]
    )
    color_danger = models.CharField(
        "Акція / знижка", max_length=7, default="#D64545", validators=[_HEX]
    )
    color_border = models.CharField(
        "Бордери", max_length=7, default="#DEE2E6", validators=[_HEX]
    )

    class Meta:
        verbose_name = "Налаштування сайту"
        verbose_name_plural = "Налаштування сайту"

    def __str__(self) -> str:
        return self.site_name

    def save(self, *args, **kwargs) -> None:
        self.pk = 1
        super().save(*args, **kwargs)
        cache.delete("site_settings")

    def delete(self, *args, **kwargs) -> tuple[int, dict[str, int]]:
        return 0, {}

    @classmethod
    def load(cls) -> "SiteSettings":
        cached = cache.get("site_settings")
        if cached is not None:
            return cached
        obj, _ = cls.objects.get_or_create(pk=1)
        cache.set("site_settings", obj, 60)
        return obj

    def theme_css_vars(self) -> dict[str, str]:
        return {
            "--color-primary": self.color_primary,
            "--color-primary-dark": self.color_primary_dark,
            "--color-secondary": self.color_secondary,
            "--color-accent": self.color_accent,
            "--color-bg": self.color_bg,
            "--color-surface": self.color_surface,
            "--color-text": self.color_text,
            "--color-text-muted": self.color_text_muted,
            "--color-header-bg": self.color_header_bg,
            "--color-header-top-bg": self.color_header_top_bg,
            "--color-header-top-text": self.color_header_top_text,
            "--color-logo-bg": self.color_logo_bg,
            "--color-catalog-btn": self.color_catalog_btn,
            "--color-catalog-btn-text": self.color_catalog_btn_text,
            "--color-link": self.color_link,
            "--color-success": self.color_success,
            "--color-danger": self.color_danger,
            "--color-border": self.color_border,
        }
