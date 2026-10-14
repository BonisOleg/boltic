"""Посів історії старих slug (dry-run за замовчуванням; --apply для запису)."""

from __future__ import annotations

import re

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils.text import slugify

from apps.catalog.models import ProductGroup, ProductSlugHistory

_STRENGTH_HYPHEN_REV = re.compile(r"кл-міц", re.IGNORECASE)
_STRENGTH_GLUED_REV = re.compile(r"клміц", re.IGNORECASE)
_KM_SLUG_REV = re.compile(r"(^|-)сталь($|-)", re.IGNORECASE)


def reverse_strength_slug(slug: str) -> str:
    if not slug:
        return slug
    s = _STRENGTH_HYPHEN_REV.sub("кл-пр", slug)
    s = _STRENGTH_GLUED_REV.sub("клпр", s)
    return s


def reverse_km_slug(slug: str) -> str:
    if not slug:
        return slug
    return _KM_SLUG_REV.sub(lambda m: f"{m.group(1)}км{m.group(2)}", slug)


def candidate_old_slugs(group: ProductGroup) -> list[str]:
    """Ймовірні старі slug: slugify(name) + reverse fix_strength/fix_km."""
    candidates: list[str] = []
    from_name = slugify(group.name, allow_unicode=True)
    if from_name and from_name != group.slug:
        candidates.append(from_name)

    for transform in (reverse_strength_slug, reverse_km_slug):
        rev = transform(group.slug)
        if rev and rev != group.slug and rev not in candidates:
            candidates.append(rev)
        if from_name:
            rev_name = transform(from_name)
            if rev_name and rev_name != group.slug and rev_name not in candidates:
                candidates.append(rev_name)
    return candidates


class Command(BaseCommand):
    help = (
        "Посів ProductSlugHistory: slugify(name) і reverse кл-міц/сталь→км; "
        "dry-run за замовчуванням, --apply щоб записати; --pair old:new"
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--apply",
            action="store_true",
            help="Записати в БД (без прапорця — лише dry-run)",
        )
        parser.add_argument(
            "--pair",
            action="append",
            default=[],
            metavar="OLD:NEW",
            help="Явна пара old_slug:current_slug (можна кілька разів)",
        )

    def handle(self, *args, **options):
        apply = options["apply"]
        pairs = options["pair"] or []

        existing_slugs = set(ProductGroup.objects.values_list("slug", flat=True))
        existing_history = set(
            ProductSlugHistory.objects.values_list("old_slug", flat=True)
        )

        planned: list[tuple[str, ProductGroup]] = []

        for raw in pairs:
            if ":" not in raw:
                self.stderr.write(self.style.ERROR(f"Невірний --pair {raw!r}"))
                continue
            old, new = raw.split(":", 1)
            old, new = old.strip(), new.strip()
            if not old or not new:
                self.stderr.write(self.style.ERROR(f"Порожній --pair {raw!r}"))
                continue
            group = ProductGroup.objects.filter(slug=new).first()
            if group is None:
                self.stderr.write(self.style.ERROR(f"Немає товару зі slug={new!r}"))
                continue
            if old in existing_slugs:
                self.stdout.write(
                    self.style.WARNING(f"пропуск {old!r}: зайнятий ProductGroup")
                )
                continue
            planned.append((old, group))

        for group in ProductGroup.objects.all().iterator():
            for old in candidate_old_slugs(group):
                if old in existing_slugs:
                    continue
                planned.append((old, group))

        # унікальність old_slug: перший виграє
        seen_old: set[str] = set()
        unique: list[tuple[str, ProductGroup]] = []
        for old, group in planned:
            if old in seen_old or old in existing_history:
                continue
            seen_old.add(old)
            unique.append((old, group))

        for old, group in unique:
            self.stdout.write(f"{old!r} → {group.slug!r} (#{group.pk})")

        if not apply:
            self.stdout.write(
                self.style.WARNING(
                    f"DRY-RUN: {len(unique)} записів (без --apply нічого не записано)"
                )
            )
            return

        with transaction.atomic():
            created = 0
            for old, group in unique:
                ProductSlugHistory.objects.filter(old_slug=group.slug).delete()
                _, was_created = ProductSlugHistory.objects.update_or_create(
                    old_slug=old,
                    defaults={"product": group},
                )
                if was_created:
                    created += 1
            self.stdout.write(
                self.style.SUCCESS(f"OK: записано/оновлено {len(unique)} (new={created})")
            )
