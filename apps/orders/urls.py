from django.urls import path

from apps.orders import views

app_name = "orders"

urlpatterns = [
    path("oformlennya/", views.checkout, name="checkout"),
    path(
        "oformlennya/uspikh/<str:number>/",
        views.order_success,
        name="success",
    ),
]
