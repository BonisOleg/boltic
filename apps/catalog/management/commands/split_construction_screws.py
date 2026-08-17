"""Виправити одруківки і розбити «Шуруп констукційний» на 3 групи."""

from __future__ import annotations

import re

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils.text import slugify

from apps.catalog.models import ProductGroup, ProductSKU

SOURCE_GROUP_ID = 114

NAME_POTAY = "Шуруп конструкційний потай"
NAME_PRESS = "Шуруп конструкційний з прес-шайбою"
NAME_OTHER = "Шуруп конструкційний інше"


def _classify(name: str) -> str:
    n = (name or "").lower().replace("ё", "е")
    if "прес" in n and "шайб" in n:
        return "press"
    if "гол/потай" in n or "гол/пот" in n or "потай" in n:
        return "potay"
    return "other"


def _fix_sku_name(name: str) -> str:
    text = name or ""
    text = text.replace("констукційн", "конструкційн")
    text = text.replace("кострукційн", "конструкційн")
    text = text.replace("Констукційн", "Конструкційн")
    text = text.replace("Кострукційн", "Конструкційн")
    # артикул злипся: гол/потай1447 → гол/потай (лише ≥3 цифри без пробілу)
    text = re.sub(r"(гол/потай)(\d{3,})", r"\1 ", text, flags=re.I)
    text = re.sub(r"\bгол/пот\b", "гол/потай", text, flags=re.I)
    # кома перед текстом («,жовтий»), але не десяткова («3,0»)
    text = re.sub(r",(?=[^\s\d])", ", ", text)
    text = re.sub(r" {2,}", " ", text)
    # відкат випадкового «3, 0» → «3,0»
    text = re.sub(r"(\d),\s+(\d)", r"\1,\2", text)
    return text.strip()


class Command(BaseCommand):
    help = (
        "Шуруп конструкційний: виправити одруківки; "
        "розбити на потай / прес-шайба / інше"
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Лише показати план, без запису",
        )

    def handle(self, *args, **options):
        dry = options["dry_run"]
        src = ProductGroup.objects.filter(pk=SOURCE_GROUP_ID).select_related(
            "category"
        ).first()
        if src is None:
            self.stderr.write(f"Немає ProductGroup id={SOURCE_GROUP_ID}")
            return

        skus = list(ProductSKU.objects.filter(group=src).order_by("article"))
        buckets = {"potay": [], "press": [], "other": []}
        for sku in skus:
            buckets[_classify(sku.name)].append(sku)

        self.stdout.write(
            f"source={src.id} «{src.name}» → "
            f"потай={len(buckets['potay'])} "
            f"прес={len(buckets['press'])} "
            f"інше={len(buckets['other'])}"
        )

        with transaction.atomic():
            potay = src
            potay.name = NAME_POTAY
            potay.slug = slugify(NAME_POTAY, allow_unicode=True)
            potay.short_description = NAME_POTAY
            if not dry:
                potay.save(
                    update_fields=[
                        "name",
                        "slug",
                        "short_description",
                        "updated_at",
                    ]
                )
            self.stdout.write(f"  potay id={potay.id} slug={potay.slug}")

            for img in potay.images.all():
                if img.alt and (
                    "констукц" in img.alt.lower() or "кострукц" in img.alt.lower()
                ):
                    self.stdout.write(f"  image alt: {img.alt!r} → {NAME_POTAY!r}")
                    if not dry:
                        img.alt = NAME_POTAY
                        img.save(update_fields=["alt"])

            press = self._ensure_group(
                category=src.category,
                name=NAME_PRESS,
                dry=dry,
            )
            other = self._ensure_group(
                category=src.category,
                name=NAME_OTHER,
                dry=dry,
            )

            name_fixes = 0
            for sku in skus:
                new_name = _fix_sku_name(sku.name)
                target = potay
                kind = _classify(sku.name)
                if kind == "press":
                    target = press
                elif kind == "other":
                    target = other

                changed = []
                if new_name != sku.name:
                    changed.append(f"name {sku.name!r} → {new_name!r}")
                    name_fixes += 1
                    if not dry:
                        sku.name = new_name
                if sku.group_id != target.id:
                    changed.append(f"group → {target.name} ({target.id})")
                    if not dry:
                        sku.group = target
                if changed:
                    self.stdout.write(f"  {sku.article}: " + "; ".join(changed))
                    if not dry:
                        sku.save(update_fields=["name", "group", "updated_at"])

            if dry:
                transaction.set_rollback(True)
                self.stdout.write(self.style.WARNING("dry-run: rollback"))
            else:
                self.stdout.write(
                    self.style.SUCCESS(
                        f"done: name_fixes={name_fixes} "
                        f"potay={ProductSKU.objects.filter(group=potay).count()} "
                        f"press={ProductSKU.objects.filter(group=press).count()} "
                        f"other={ProductSKU.objects.filter(group=other).count()}"
                    )
                )

    def _ensure_group(
        self, *, category, name: str, dry: bool
    ) -> ProductGroup:
        slug = slugify(name, allow_unicode=True)
        existing = ProductGroup.objects.filter(slug=slug).first()
        if existing:
            self.stdout.write(f"  reuse id={existing.id} slug={slug}")
            return existing
        self.stdout.write(f"  create slug={slug}")
        if dry:
            # placeholder object for dry-run moves logging
            g = ProductGroup(
                id=0,
                category=category,
                name=name,
                slug=slug,
                short_description=name,
                is_active=True,
            )
            return g
        return ProductGroup.objects.create(
            category=category,
            name=name,
            slug=slug,
            short_description=name,
            is_active=True,
        )
