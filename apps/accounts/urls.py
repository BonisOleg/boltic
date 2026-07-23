from django.urls import path

from apps.accounts import views

app_name = "accounts"

urlpatterns = [
    path("login/", views.login_view, name="login"),
    path("register/", views.register_view, name="register"),
    path("logout/", views.logout_view, name="logout"),
    path("kabinet/", views.cabinet, name="cabinet"),
    path("kabinet/zamovlennya/", views.cabinet_orders, name="orders"),
    path(
        "kabinet/zamovlennya/<str:number>/",
        views.cabinet_order_detail,
        name="order_detail",
    ),
    path("kabinet/profil/", views.cabinet_profile, name="profile"),
]
