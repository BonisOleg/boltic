from django.contrib import admin
from unfold.admin import ModelAdmin, TabularInline

from apps.catalog.admin_io import register_catalog_io_urls
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
from apps.core.admin_utils import ImagePreviewMixin, TinyMCEAdminMixin

register_catalog_io_urls()


class ProductImageInline(ImagePreviewMixin, TabularInline):
    model = ProductImage
    extra = 0
    fields = ("image", "image_preview", "alt", "is_primary", "sort_order")
    readonly_fields = ("image_preview",)
    verbose_name = "Зображення"
    verbose_name_plural = "Зображення · формат 4:3 (1200×900), інакше обрізається"

    @admin.display(description="Превʼю")
    def image_preview(self, obj):
        return self.get_image_preview(obj)


class ProductDocumentInline(TabularInline):
    model = ProductDocument
    extra = 0


class ProductSKUInline(ImagePreviewMixin, TabularInline):
    model = ProductSKU
    extra = 0
    fields = (
        "article",
        "name",
        "size_label",
        "price",
        "party_price",
        "min_party",
        "stock_status",
        "image",
        "image_preview",
        "is_active",
    )
    readonly_fields = ("image_preview",)

    @admin.display(description="Превʼю")
    def image_preview(self, obj):
        return self.get_image_preview(obj, height=56)


@admin.register(Category)
class CategoryAdmin(ModelAdmin):
    list_display = ("name", "level", "path", "is_active", "sort_order")
    list_filter = ("level", "is_active")
    list_filter_submit = True
    search_fields = ("name", "slug", "path")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Brand)
class BrandAdmin(ModelAdmin):
    list_display = ("name", "slug", "is_active")
    search_fields = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(ProductGroup)
class ProductGroupAdmin(TinyMCEAdminMixin, ModelAdmin):
    list_display = ("name", "category", "brand", "is_top", "is_promo", "is_active")
    list_filter = ("is_active", "is_top", "is_promo", "category")
    list_filter_submit = True
    search_fields = ("name", "slug", "standard")
    prepopulated_fields = {"slug": ("name",)}
    autocomplete_fields = ("category", "brand")
    tinymce_fields = ("description",)
    inlines = [ProductSKUInline, ProductImageInline, ProductDocumentInline]
    fieldsets = (
        (
            None,
            {
                "fields": (
                    "name",
                    "slug",
                    "category",
                    "brand",
                    "short_description",
                    "description",
                    "standard",
                    "material",
                    "coating",
                    "industry",
                )
            },
        ),
        (
            "Розміри",
            {
                "fields": (
                    "diameter_min",
                    "diameter_max",
                    "length_min",
                    "length_max",
                )
            },
        ),
        ("Прапорці", {"fields": ("is_top", "is_promo", "is_active")}),
        (
            "SEO",
            {
                "classes": ("collapse",),
                "fields": ("seo_title", "seo_description"),
            },
        ),
    )


@admin.register(ProductSKU)
class ProductSKUAdmin(ImagePreviewMixin, ModelAdmin):
    list_display = (
        "article",
        "name",
        "size_label",
        "price",
        "party_price",
        "min_party",
        "stock_status",
        "has_image",
        "is_active",
    )
    list_display_links = ("article", "name")
    list_editable = ("price", "party_price", "min_party")
    list_filter = ("stock_status", "is_active")
    list_filter_submit = True
    search_fields = ("article", "name", "size_label")
    autocomplete_fields = ("group",)
    readonly_fields = ("image_preview",)
    fieldsets = (
        (
            None,
            {
                "fields": (
                    "group",
                    "article",
                    "name",
                    "size_label",
                    "diameter",
                    "length",
                    "thread_pitch",
                    "strength_class",
                )
            },
        ),
        (
            "Ціна та наявність",
            {
                "fields": (
                    "price",
                    "party_price",
                    "min_party",
                    "stock_status",
                    "stock_qty",
                    "price_includes_vat",
                    "vat_rate",
                    "is_active",
                )
            },
        ),
        (
            "Фото",
            {"fields": ("image", "image_preview")},
        ),
    )

    @admin.display(description="Фото", boolean=True)
    def has_image(self, obj):
        return bool(obj.image)

    @admin.display(description="Превʼю")
    def image_preview(self, obj):
        return self.get_image_preview(obj, height=120)


@admin.register(Collection)
class CollectionAdmin(ModelAdmin):
    list_display = ("title", "slug", "is_published")
    prepopulated_fields = {"slug": ("title",)}
    filter_horizontal = ("groups",)


class FacetValueInline(TabularInline):
    model = FacetValue
    extra = 0
    fields = ("value", "slug", "sort_order")


@admin.register(FacetAttribute)
class FacetAttributeAdmin(ModelAdmin):
    list_display = ("code", "name", "sort_order")
    prepopulated_fields = {"code": ("name",)}
    inlines = [FacetValueInline]


@admin.register(SKUFacet)
class SKUFacetAdmin(ModelAdmin):
    list_display = ("sku", "value")
    search_fields = ("sku__article", "value__value")
    raw_id_fields = ("sku", "value")
