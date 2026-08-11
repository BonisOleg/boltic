"""Proxy-моделі CMS-секцій (не окремі таблиці)."""

from apps.core.models import SiteSettings


class HomeHeroSettings(SiteSettings):
    class Meta:
        proxy = True
        verbose_name = "Головна — Hero"
        verbose_name_plural = "Головна — Hero"


class HomeAdvantagesSettings(SiteSettings):
    class Meta:
        proxy = True
        verbose_name = "Головна — Переваги"
        verbose_name_plural = "Головна — Переваги"


class HomeCatalogSettings(SiteSettings):
    class Meta:
        proxy = True
        verbose_name = "Головна — Каталог"
        verbose_name_plural = "Головна — Каталог"


class HomePromoSettings(SiteSettings):
    class Meta:
        proxy = True
        verbose_name = "Головна — Акції"
        verbose_name_plural = "Головна — Акції"


class HomeTopsSettings(SiteSettings):
    class Meta:
        proxy = True
        verbose_name = "Головна — Лідери"
        verbose_name_plural = "Головна — Лідери"


class HomeNewsSettings(SiteSettings):
    class Meta:
        proxy = True
        verbose_name = "Головна — Новини"
        verbose_name_plural = "Головна — Новини"


class HomeSeoSettings(SiteSettings):
    class Meta:
        proxy = True
        verbose_name = "Головна — SEO-текст"
        verbose_name_plural = "Головна — SEO-текст"


class HomeServicesSettings(SiteSettings):
    class Meta:
        proxy = True
        verbose_name = "Головна — Сервіси"
        verbose_name_plural = "Головна — Сервіси"


class SiteHeaderSettings(SiteSettings):
    class Meta:
        proxy = True
        verbose_name = "Шапка сайту"
        verbose_name_plural = "Шапка сайту"


class SiteFooterSettings(SiteSettings):
    class Meta:
        proxy = True
        verbose_name = "Підвал сайту"
        verbose_name_plural = "Підвал сайту"


class ContactsPageSettings(SiteSettings):
    class Meta:
        proxy = True
        verbose_name = "Сторінка — Контакти"
        verbose_name_plural = "Сторінка — Контакти"
