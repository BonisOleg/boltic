from django.urls import path

from apps.orders import views

app_name = "orders"

urlpatterns = [
    path("oformlennya/", views.checkout_contact, name="checkout"),
    path(
        "oformlennya/dostavka/",
        views.checkout_delivery,
        name="checkout_delivery",
    ),
    path(
        "oformlennya/pidtverdzhennya/",
        views.checkout_confirm,
        name="checkout_confirm",
    ),
    path("oformlennya/api/np/cities/", views.np_cities, name="np_cities"),
    path(
        "oformlennya/api/np/warehouses/",
        views.np_warehouses,
        name="np_warehouses",
    ),
    path(
        "oformlennya/uspikh/<str:number>/",
        views.order_success,
        name="success",
    ),
]
