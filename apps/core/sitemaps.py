from django.contrib.sitemaps import Sitemap
from django.urls import reverse

from apps.catalog.models import Brand, Category, Collection, ProductGroup
from apps.content.models import NewsPost, Promotion, StaticPage


class StaticViewSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.6

    def items(self):
        return [
            "content:home",
            "catalog:root",
            "catalog:brand_list",
            "content:promo_list",
            "content:news_list",
            "content:contacts",
            "cart:detail",
        ]

    def location(self, item):
        return reverse(item)


class CategorySitemap(Sitemap):
    changefreq = "daily"
    priority = 0.7

    def items(self):
        return Category.objects.filter(is_active=True)

    def location(self, obj):
        return reverse("catalog:category", kwargs={"path": obj.url_path})


class ProductSitemap(Sitemap):
    changefreq = "daily"
    priority = 0.8

    def items(self):
        return ProductGroup.objects.filter(is_active=True)

    def lastmod(self, obj):
        return obj.updated_at

    def location(self, obj):
        return reverse("catalog:product", kwargs={"slug": obj.slug})


class BrandSitemap(Sitemap):
    def items(self):
        return Brand.objects.filter(is_active=True)

    def location(self, obj):
        return reverse("catalog:brand_detail", kwargs={"slug": obj.slug})


class CollectionSitemap(Sitemap):
    def items(self):
        return Collection.objects.filter(is_published=True)

    def location(self, obj):
        return reverse("catalog:collection", kwargs={"slug": obj.slug})


class PromotionSitemap(Sitemap):
    def items(self):
        return Promotion.objects.filter(is_published=True)

    def location(self, obj):
        return reverse("content:promo_detail", kwargs={"slug": obj.slug})


class NewsSitemap(Sitemap):
    def items(self):
        return NewsPost.objects.filter(is_published=True)

    def location(self, obj):
        return reverse("content:news_detail", kwargs={"slug": obj.slug})


class StaticPageSitemap(Sitemap):
    def items(self):
        return StaticPage.objects.filter(is_published=True)

    def location(self, obj):
        return f"/{obj.slug}/"


SITEMAPS = {
    "static": StaticViewSitemap,
    "categories": CategorySitemap,
    "products": ProductSitemap,
    "brands": BrandSitemap,
    "collections": CollectionSitemap,
    "promotions": PromotionSitemap,
    "news": NewsSitemap,
    "pages": StaticPageSitemap,
}
