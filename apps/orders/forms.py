from django import forms

from apps.orders.models import Order


class CheckoutForm(forms.Form):
    customer_name = forms.CharField(label="Імʼя", max_length=255)
    phone = forms.CharField(label="Телефон", max_length=32)
    email = forms.EmailField(label="Email", required=False)
    shipping_method = forms.CharField(
        label="Спосіб доставки", max_length=128, required=False
    )
    shipping_address = forms.CharField(
        label="Адреса", widget=forms.Textarea(attrs={"rows": 3}), required=False
    )
    comment = forms.CharField(
        label="Коментар", widget=forms.Textarea(attrs={"rows": 2}), required=False
    )


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
