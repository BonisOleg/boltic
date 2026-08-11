"""ContactBranch ModelFormSet для CMS-секції contacts."""

from __future__ import annotations

from django import forms
from django.forms import BaseModelFormSet, modelformset_factory
from unfold.widgets import UnfoldBooleanWidget

from apps.content.models import ContactBranch
from apps.core.admin_site_content_widgets import (
    CmsAdminTextareaWidget,
    CmsAdminTextInputWidget,
)


class ContactBranchForm(forms.ModelForm):
    class Meta:
        model = ContactBranch
        fields = (
            "name",
            "address",
            "phone",
            "email",
            "map_url",
            "sort_order",
            "is_active",
        )
        widgets = {
            "name": CmsAdminTextInputWidget(),
            "address": CmsAdminTextareaWidget(attrs={"rows": 2}),
            "phone": CmsAdminTextInputWidget(),
            "email": CmsAdminTextInputWidget(),
            "map_url": CmsAdminTextInputWidget(),
            "sort_order": forms.HiddenInput(),
            "is_active": UnfoldBooleanWidget(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name in ("name", "address", "phone", "email", "map_url"):
            self.fields[name].required = False

    def clean(self):
        cleaned = super().clean()
        name = (cleaned.get("name") or "").strip()
        address = (cleaned.get("address") or "").strip()
        phone = (cleaned.get("phone") or "").strip()
        email = (cleaned.get("email") or "").strip()
        map_url = (cleaned.get("map_url") or "").strip()
        has_content = bool(name or address or phone or email or map_url)
        if not has_content and self.empty_permitted:
            return cleaned
        if not name:
            self.add_error("name", "Обовʼязкове поле.")
        if not address:
            self.add_error("address", "Обовʼязкове поле.")
        if not phone:
            self.add_error("phone", "Обовʼязкове поле.")
        cleaned["name"] = name
        cleaned["address"] = address
        cleaned["phone"] = phone
        return cleaned


class ContactBranchBaseFormSet(BaseModelFormSet):
    def clean(self):
        super().clean()
        order = 0
        for form in self.forms:
            if not hasattr(form, "cleaned_data") or form.cleaned_data.get("DELETE"):
                continue
            name = (form.cleaned_data.get("name") or "").strip()
            address = (form.cleaned_data.get("address") or "").strip()
            phone = (form.cleaned_data.get("phone") or "").strip()
            if not name and not address and not phone:
                continue
            form.cleaned_data["sort_order"] = order
            form.instance.sort_order = order
            order += 1


def build_contact_branch_formset(data=None, files=None):
    FormSet = modelformset_factory(
        ContactBranch,
        form=ContactBranchForm,
        formset=ContactBranchBaseFormSet,
        extra=1,
        can_delete=True,
    )
    queryset = ContactBranch.objects.order_by("sort_order", "pk")
    return FormSet(data=data, files=files, queryset=queryset, prefix="contact_branches")
