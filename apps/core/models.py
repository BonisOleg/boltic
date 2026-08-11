from django.core.cache import cache
from django.core.validators import RegexValidator
from django.db import models

_HEX = RegexValidator(
    regex=r"^#(?:[0-9a-fA-F]{3}){1,2}$",
    message="Вкажіть колір у форматі #RRGGBB",
)

SITE_BLOCKS_CACHE_KEY = "site_blocks_v1"


class SiteSettings(models.Model):
    """Singleton налаштувань сайту + тема (кольори) + бренд-медіа."""

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
    logo = models.ImageField("Логотип", upload_to="brand/", blank=True)
    favicon = models.ImageField("Favicon", upload_to="brand/", blank=True)
    meta_description = models.CharField(
        "SEO description (сайт)", max_length=300, blank=True
    )

    pickup_enabled = models.BooleanField("Самовивіз увімкнено", default=True)
    pickup_description = models.CharField(
        "Опис самовивозу",
        max_length=255,
        blank=True,
        default="Самовивіз зі складу — безкоштовно",
        help_text="Текст під опцією самовивозу на оформленні",
    )
    orders_email = models.EmailField(
        "Email сповіщень про замовлення",
        blank=True,
        help_text="Куди слати нові замовлення. Якщо порожньо — використовується Email сайту.",
    )

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
        cache.delete(SITE_BLOCKS_CACHE_KEY)

    def delete(self, *args, **kwargs) -> tuple[int, dict[str, int]]:
        return 0, {}

    @classmethod
    def get_solo(cls) -> "SiteSettings":
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj

    @classmethod
    def load(cls) -> "SiteSettings":
        cached = cache.get("site_settings")
        if cached is not None:
            return cached
        obj = cls.get_solo()
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


class SiteBlock(models.Model):
    """Секційний контент `(page, key)` — текст / фото / url / video."""

    class Page(models.TextChoices):
        HOME = "home", "Головна"
        SITE = "site", "Сайт"
        CONTACTS = "contacts", "Контакти"

    class ContentType(models.TextChoices):
        TEXT = "text", "Текст"
        IMAGE = "image", "Фото"
        URL = "url", "Посилання"
        VIDEO = "video", "Відео"

    page = models.CharField("Сторінка", max_length=32, choices=Page.choices)
    key = models.CharField("Ключ", max_length=64)
    label = models.CharField("Підпис", max_length=128, blank=True)
    content_type = models.CharField(
        "Тип",
        max_length=16,
        choices=ContentType.choices,
        default=ContentType.TEXT,
    )
    text_html = models.TextField("Текст", blank=True)
    image = models.ImageField("Зображення", upload_to="blocks/", blank=True)
    link_url = models.CharField("URL", max_length=512, blank=True)
    link_label = models.CharField("Текст посилання", max_length=128, blank=True)
    video_embed_url = models.URLField("Embed URL", blank=True)
    video_file = models.FileField("Відеофайл", upload_to="blocks/video/", blank=True)
    sort_order = models.PositiveSmallIntegerField("Порядок", default=0)
    is_active = models.BooleanField("Активний", default=True)

    class Meta:
        verbose_name = "Блок контенту"
        verbose_name_plural = "Блоки контенту"
        ordering = ["page", "sort_order", "key"]
        constraints = [
            models.UniqueConstraint(
                fields=["page", "key"], name="unique_site_block_page_key"
            ),
        ]

    def __str__(self) -> str:
        return f"{self.page}.{self.key}"

    @property
    def cache_key(self) -> str:
        return f"{self.page}.{self.key}"

    def save(self, *args, **kwargs) -> None:
        super().save(*args, **kwargs)
        cache.delete(SITE_BLOCKS_CACHE_KEY)


class HeroSlide(models.Model):
    """Карусель головної — N слайдів (фото + тексти + CTA)."""

    image = models.ImageField("Фото", upload_to="hero/", blank=True)
    title = models.CharField("Заголовок", max_length=255, blank=True)
    body = models.TextField("Текст", blank=True)
    cta_label = models.CharField(
        "Кнопка", max_length=128, blank=True, default="Перейти в каталог"
    )
    cta_url = models.CharField(
        "Посилання кнопки", max_length=512, blank=True, default="/katalog/"
    )
    alt_text = models.CharField("Alt", max_length=200, blank=True)
    sort_order = models.PositiveSmallIntegerField("Порядок", default=0)
    is_active = models.BooleanField("Активний", default=True)

    class Meta:
        verbose_name = "Hero-слайд"
        verbose_name_plural = "Hero-слайди"
        ordering = ("sort_order", "pk")

    def __str__(self) -> str:
        return self.title or f"Слайд #{self.pk}"


# Proxy CMS-секції (окремий модуль, імпорт для реєстрації в app)
from apps.core import cms_proxies as _cms_proxies  # noqa: E402,F401

HomeHeroSettings = _cms_proxies.HomeHeroSettings
HomeAdvantagesSettings = _cms_proxies.HomeAdvantagesSettings
HomeCatalogSettings = _cms_proxies.HomeCatalogSettings
HomePromoSettings = _cms_proxies.HomePromoSettings
HomeTopsSettings = _cms_proxies.HomeTopsSettings
HomeNewsSettings = _cms_proxies.HomeNewsSettings
HomeSeoSettings = _cms_proxies.HomeSeoSettings
HomeServicesSettings = _cms_proxies.HomeServicesSettings
SiteHeaderSettings = _cms_proxies.SiteHeaderSettings
SiteFooterSettings = _cms_proxies.SiteFooterSettings
ContactsPageSettings = _cms_proxies.ContactsPageSettings
