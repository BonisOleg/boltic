from django import forms

from apps.core.models import SiteSettings
from apps.orders.constants import (
    NP_TYPE_POSTOMAT,
    NP_TYPE_WAREHOUSE,
    SHIPPING_NOVA_POSHTA,
    SHIPPING_PICKUP,
)
from apps.orders.models import Order
from apps.orders.validators import (
    PHONE_PREFIX,
    normalize_ua_phone,
    validate_customer_name,
    validate_ua_phone,
)


class ContactForm(forms.Form):
    customer_name = forms.CharField(
        label="ПІБ",
        max_length=255,
        widget=forms.TextInput(
            attrs={
                "autocomplete": "name",
                "placeholder": "Прізвище Імʼя",
                "inputmode": "text",
                "data-validate-name": "1",
            }
        ),
    )
    phone = forms.CharField(
        label="Телефон",
        max_length=13,
        widget=forms.TextInput(
            attrs={
                "autocomplete": "tel",
                "placeholder": "+380XXXXXXXXX",
                "inputmode": "tel",
                "data-phone-mask": "1",
                "data-phone-prefix": PHONE_PREFIX,
                "maxlength": "13",
            }
        ),
    )
    email = forms.EmailField(
        label="Email",
        required=False,
        widget=forms.EmailInput(
            attrs={
                "autocomplete": "email",
                "placeholder": "email@example.com",
                "inputmode": "email",
                "data-validate-email": "1",
            }
        ),
        error_messages={
            "invalid": "Вкажіть коректний email",
        },
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        phone = self.initial.get("phone")
        if phone:
            self.initial["phone"] = normalize_ua_phone(str(phone))
        elif not self.is_bound:
            self.initial.setdefault("phone", PHONE_PREFIX)

    def clean_customer_name(self):
        return validate_customer_name(self.cleaned_data["customer_name"])

    def clean_phone(self):
        return validate_ua_phone(self.cleaned_data["phone"])

    def clean_email(self):
        email = (self.cleaned_data.get("email") or "").strip()
        return email


class DeliveryForm(forms.Form):
    shipping_method = forms.ChoiceField(
        label="Спосіб доставки",
        choices=Order.ShippingMethod.choices,
        widget=forms.RadioSelect,
    )
    np_delivery_type = forms.ChoiceField(
        label="Тип доставки НП",
        choices=Order.NpDeliveryType.choices,
        required=False,
        widget=forms.RadioSelect,
    )
    np_city = forms.CharField(label="Місто", max_length=255, required=False)
    np_city_ref = forms.CharField(max_length=64, required=False, widget=forms.HiddenInput)
    np_warehouse = forms.CharField(
        label="Відділення / поштомат", max_length=512, required=False
    )
    np_warehouse_ref = forms.CharField(
        max_length=64, required=False, widget=forms.HiddenInput
    )
    comment = forms.CharField(
        label="Коментар",
        required=False,
        widget=forms.Textarea(
            attrs={
                "rows": 3,
                "placeholder": "Додаткова інформація",
            }
        ),
    )

    def __init__(self, *args, pickup_enabled: bool = True, **kwargs):
        super().__init__(*args, **kwargs)
        self.pickup_enabled = pickup_enabled

    def clean(self):
        cleaned = super().clean()
        method = cleaned.get("shipping_method")
        if method == SHIPPING_PICKUP:
            if not self.pickup_enabled:
                self.add_error(
                    "shipping_method", "Самовивіз тимчасово недоступний"
                )
                return cleaned
            cleaned["np_delivery_type"] = ""
            cleaned["np_city"] = ""
            cleaned["np_city_ref"] = ""
            cleaned["np_warehouse"] = ""
            cleaned["np_warehouse_ref"] = ""
            return cleaned

        if method == SHIPPING_NOVA_POSHTA:
            np_type = cleaned.get("np_delivery_type") or ""
            if np_type not in (NP_TYPE_WAREHOUSE, NP_TYPE_POSTOMAT):
                self.add_error(
                    "np_delivery_type", "Оберіть відділення або поштомат"
                )
            if not cleaned.get("np_city_ref") or not cleaned.get("np_city"):
                self.add_error("np_city", "Оберіть місто зі списку Нової Пошти")
            if not cleaned.get("np_warehouse_ref") or not cleaned.get("np_warehouse"):
                self.add_error(
                    "np_warehouse", "Оберіть відділення або поштомат зі списку"
                )
        return cleaned


class ReviewForm(forms.Form):
    rating = forms.IntegerField(min_value=1, max_value=5, label="Оцінка")
    body = forms.CharField(widget=forms.Textarea(attrs={"rows": 4}), label="Відгук")


class RegisterForm(forms.Form):
    username = forms.CharField(max_length=150)
    email = forms.EmailField(required=False)
    password1 = forms.CharField(widget=forms.PasswordInput)
    password2 = forms.CharField(widget=forms.PasswordInput)

    def clean(self):
        cleaned = super().clean()
        if cleaned.get("password1") != cleaned.get("password2"):
            raise forms.ValidationError("Паролі не збігаються")
        return cleaned


class ProfileForm(forms.Form):
    phone = forms.CharField(max_length=32, required=False)
    company = forms.CharField(max_length=255, required=False)
    default_shipping_address = forms.CharField(
        widget=forms.Textarea(attrs={"rows": 3}), required=False
    )


def pickup_is_enabled() -> bool:
    return bool(SiteSettings.load().pickup_enabled)
