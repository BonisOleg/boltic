from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods

from apps.accounts.models import UserProfile
from apps.cart.services import merge_on_login
from apps.core.http import safe_next
from apps.orders.forms import ProfileForm, RegisterForm
from apps.orders.models import Order
from apps.orders.services import orders_for_user


@require_http_methods(["GET", "POST"])
def login_view(request):
    next_url = safe_next(request)
    if request.user.is_authenticated:
        return redirect(next_url or "accounts:cabinet")
    error = ""
    if request.method == "POST":
        username = request.POST.get("username", "")
        password = request.POST.get("password", "")
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            merge_on_login(request, user)
            return redirect(next_url or "accounts:cabinet")
        error = "Невірний логін або пароль"
    return render(
        request, "accounts/login.html", {"error": error, "next_url": next_url}
    )


@require_http_methods(["GET", "POST"])
def register_view(request):
    next_url = safe_next(request)
    if request.user.is_authenticated:
        return redirect(next_url or "accounts:cabinet")
    form = RegisterForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        if User.objects.filter(username=form.cleaned_data["username"]).exists():
            messages.error(request, "Користувач уже існує")
        else:
            user = User.objects.create_user(
                username=form.cleaned_data["username"],
                email=form.cleaned_data.get("email") or "",
                password=form.cleaned_data["password1"],
            )
            UserProfile.objects.get_or_create(user=user)
            login(request, user)
            merge_on_login(request, user)
            return redirect(next_url or "accounts:cabinet")
    return render(
        request, "accounts/register.html", {"form": form, "next_url": next_url}
    )


def logout_view(request):
    logout(request)
    return redirect("content:home")


@login_required
def cabinet(request):
    return render(request, "accounts/cabinet.html")


@login_required
def cabinet_orders(request):
    return render(
        request,
        "accounts/orders.html",
        {"orders": orders_for_user(request.user)},
    )


@login_required
def cabinet_order_detail(request, number: str):
    order = get_object_or_404(Order, number=number, user=request.user)
    return render(request, "accounts/order_detail.html", {"order": order})


@login_required
@require_http_methods(["GET", "POST"])
def cabinet_profile(request):
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    form = ProfileForm(
        request.POST or None,
        initial={
            "phone": profile.phone,
            "company": profile.company,
            "default_shipping_address": profile.default_shipping_address,
        },
    )
    if request.method == "POST" and form.is_valid():
        profile.phone = form.cleaned_data["phone"]
        profile.company = form.cleaned_data["company"]
        profile.default_shipping_address = form.cleaned_data[
            "default_shipping_address"
        ]
        profile.save()
        messages.success(request, "Профіль збережено")
        return redirect("accounts:profile")
    return render(request, "accounts/profile.html", {"form": form})
