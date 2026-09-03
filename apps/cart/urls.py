from django.urls import path

from apps.cart import views

app_name = "cart"

urlpatterns = [
    path("koshyk/", views.cart_detail, name="detail"),
    path("koshyk/add/", views.cart_add, name="add"),
    path("koshyk/update/", views.cart_update_all, name="update_all"),
    path("koshyk/update/<int:item_id>/", views.cart_update, name="update"),
    path("koshyk/remove/<int:item_id>/", views.cart_remove, name="remove"),
    path("koshyk/count/", views.cart_count, name="count"),
    path("bazhane/", views.wishlist, name="wishlist"),
    path("bazhane/zminyty/", views.wishlist_toggle_view, name="wishlist_toggle"),
]
