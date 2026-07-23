from django.contrib import admin

from apps.catalog.models import (
    Brand,
    Category,
    Collection,
    FacetAttribute,
    FacetValue,
    ProductDocument,
    ProductGroup,
    ProductImage,
    ProductSKU,
    SKUFacet,
)


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 0


class ProductDocumentInline(admin.TabularInline):
    model = ProductDocument
    extra = 0


class ProductSKUInline(admin.TabularInline):
    model = ProductSKU
    extra = 0
    fields = (
        "article",
        "name",
        "size_label",
        "price",
        "min_party",
        "stock_status",
        "is_active",
    )


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "level", "path", "is_active", "sort_order")
    list_filter = ("level", "is_active")
    search_fields = ("name", "slug", "path")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "is_active")
    search_fields = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(ProductGroup)
class ProductGroupAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "brand", "is_top", "is_promo", "is_active")
    list_filter = ("is_active", "is_top", "is_promo", "category")
    search_fields = ("name", "slug", "standard")
    prepopulated_fields = {"slug": ("name",)}
    inlines = [ProductSKUInline, ProductImageInline, ProductDocumentInline]


@admin.register(ProductSKU)
class ProductSKUAdmin(admin.ModelAdmin):
    list_display = (
        "article",
        "name",
        "size_label",
        "price",
        "stock_status",
        "is_active",
    )
    list_filter = ("stock_status", "is_active")
    search_fields = ("article", "name", "size_label")


@admin.register(Collection)
class CollectionAdmin(admin.ModelAdmin):
    list_display = ("title", "slug", "is_published")
    prepopulated_fields = {"slug": ("title",)}
    filter_horizontal = ("groups",)


class FacetValueInline(admin.TabularInline):
    model = FacetValue
    extra = 0
    fields = ("value", "slug", "sort_order")


@admin.register(FacetAttribute)
class FacetAttributeAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "sort_order")
    prepopulated_fields = {"code": ("name",)}
    inlines = [FacetValueInline]


@admin.register(SKUFacet)
class SKUFacetAdmin(admin.ModelAdmin):
    list_display = ("sku", "value")
    list_filter = ("value__attribute",)
