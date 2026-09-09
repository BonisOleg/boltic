from django.urls import path

from apps.catalog import views
from apps.catalog.google_feed import google_merchant_feed
from apps.core import urlconverters  # noqa: F401 — register uslug

app_name = "catalog"

urlpatterns = [
    path("feeds/google.xml", google_merchant_feed, name="google_feed"),
    path("katalog/", views.CatalogRootView.as_view(), name="root"),
    path("katalog/search/", views.search, name="search"),
    path("katalog/<path:path>/", views.CategoryView.as_view(), name="category"),
    path("tovar/<uslug:slug>/", views.ProductDetailView.as_view(), name="product"),
    path(
        "tovar/<uslug:slug>/sku/<str:article>/",
        views.SKUDetailView.as_view(),
        name="sku_detail",
    ),
    path(
        "tovar/<uslug:slug>/vidguk/",
        views.product_review,
        name="product_review",
    ),
    path("brendy/", views.BrandListView.as_view(), name="brand_list"),
    path("brendy/<uslug:slug>/", views.BrandDetailView.as_view(), name="brand_detail"),
    path(
        "pidbirka/<uslug:slug>/",
        views.CollectionDetailView.as_view(),
        name="collection",
    ),
]
