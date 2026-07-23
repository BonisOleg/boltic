from django.urls import path

from apps.payments import views

app_name = "payments"

urlpatterns = [
    path("payments/liqpay/callback/", views.liqpay_callback, name="liqpay_callback"),
    path("payments/liqpay/result/", views.liqpay_result, name="liqpay_result"),
]
