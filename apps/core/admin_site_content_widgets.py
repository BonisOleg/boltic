"""Dark-readable CMS widgets (без bg-white)."""

from __future__ import annotations

from django.contrib.admin.widgets import AdminTextareaWidget, AdminTextInputWidget
from unfold.widgets import INPUT_CLASSES, TEXTAREA_CLASSES

_SKIP_CLASSES = frozenset(
    {
        "bg-white",
        "text-font-default-light",
        "border-base-200",
        "dark:bg-base-900",
        "dark:border-base-700",
        "dark:text-font-default-dark",
    }
)
_FORCE_CLASSES = (
    "bg-base-900",
    "text-base-100",
    "border-base-700",
    "placeholder-base-400",
)


def cms_control_classes(base_classes) -> list[str]:
    classes = [c for c in list(base_classes) if c not in _SKIP_CLASSES]
    for forced in _FORCE_CLASSES:
        if forced not in classes:
            classes.append(forced)
    return classes


class CmsAdminTextInputWidget(AdminTextInputWidget):
    def __init__(self, attrs=None):
        attrs = dict(attrs or {})
        existing = attrs.get("class", "")
        merged = cms_control_classes(INPUT_CLASSES)
        if existing:
            merged = list(dict.fromkeys([*merged, *existing.split()]))
        attrs["class"] = " ".join(merged)
        super().__init__(attrs=attrs)


class CmsAdminTextareaWidget(AdminTextareaWidget):
    def __init__(self, attrs=None):
        attrs = dict(attrs or {})
        rows = attrs.pop("rows", 3)
        existing = attrs.get("class", "")
        merged = cms_control_classes(TEXTAREA_CLASSES)
        if existing:
            merged = list(dict.fromkeys([*merged, *existing.split()]))
        attrs["class"] = " ".join(merged)
        attrs["rows"] = rows
        super().__init__(attrs=attrs)


def apply_readable_widget(widget) -> None:
    """Замінює класи Unfold input на dark-readable (SiteSettings)."""
    from django.forms.widgets import CheckboxInput, ClearableFileInput, Select
    from tinymce.widgets import TinyMCE

    if isinstance(widget, (CheckboxInput, ClearableFileInput, Select, TinyMCE)):
        return
    css = widget.attrs.get("class", "")
    parts = [p for p in css.split() if p not in _SKIP_CLASSES]
    for forced in _FORCE_CLASSES:
        if forced not in parts:
            parts.append(forced)
    widget.attrs["class"] = " ".join(parts)
