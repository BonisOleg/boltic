"""Нове дерево: Болти/Гвинти/Стрижні/Меблеве + нерж L2; рознос H101."""

from __future__ import annotations

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils.text import slugify

from apps.catalog.classification import (
    LEGACY_L1_SLUG,
    resolve_goods_category,
)
from apps.catalog.models import Category, ProductGroup, ProductSKU


class Command(BaseCommand):
    help = (
        "Після seed_catalog: переносить ProductGroup у нове дерево, "
        "розносить комплект H101, деактивує застарілий L1"
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Лише показати зміни без запису",
        )

    def handle(self, *args, **options):
        dry = options["dry_run"]
        cats = self._load_l2_map()
        if not cats:
            self.stderr.write("Немає нових L2 — спочатку: python3 manage.py seed_catalog")
            return

        with transaction.atomic():
            moved = self._move_groups(cats, dry)
            split = self._split_h101(cats, dry)
            deactivated = self._deactivate_legacy(dry)
            if dry:
                transaction.set_rollback(True)

        self.stdout.write(
            self.style.SUCCESS(
                f"{'[dry-run] ' if dry else ''}"
                f"груп→{moved}, H101 SKU→{split}, деактивовано категорій→{deactivated}"
            )
        )

    def _load_l2_map(self) -> dict[tuple[str, str], Category]:
        out: dict[tuple[str, str], Category] = {}
        for c in Category.objects.filter(level=Category.Level.L2).select_related(
            "parent"
        ):
            if c.parent_id is None:
                continue
            out[(c.parent.slug, c.slug)] = c
        return out

    def _target_for_group(self, group: ProductGroup) -> tuple[str, str]:
        probe = f"{group.name} {group.material or ''}".strip()
        return resolve_goods_category(probe, "")

    def _move_groups(
        self, cats: dict[tuple[str, str], Category], dry: bool
    ) -> int:
        moved = 0
        legacy_l1 = Category.objects.filter(
            parent=None, slug=LEGACY_L1_SLUG
        ).first()

        for group in ProductGroup.objects.select_related(
            "category", "category__parent"
        ).all():
            # пропускаємо мішаний H101 — його розносить _split_h101
            if self._is_h101_kit(group):
                continue

            parent = group.category.parent if group.category_id else None
            in_scope = False
            if parent and legacy_l1 and parent.id == legacy_l1.id:
                in_scope = True
            elif parent and parent.slug in {
                "болти",
                "гвинти",
                "стрижні",
                "меблеве-кріплення",
                "гайки-шайби-гровери",
                "саморізи-шурупи",
            }:
                in_scope = True
            elif group.category and group.category.slug in {
                "гайки",
                "шайби",
                "гровери",
                "саморізи",
            }:
                in_scope = True

            if not in_scope:
                continue

            l1, l2 = self._target_for_group(group)
            target = cats.get((l1, l2))
            if target is None:
                self.stderr.write(f"Немає {l1}/{l2} для «{group.name}»")
                continue

            if group.category_id == target.id:
                continue

            self.stdout.write(
                f"→ {group.name}: {group.category.path} ⇒ {target.path}"
            )
            if not dry:
                group.category = target
                group.save(update_fields=["category", "updated_at"])
            moved += 1
        return moved

    def _is_h101_kit(self, group: ProductGroup) -> bool:
        n = (group.name or "").lower()
        return "h101" in n or (
            "болт" in n and "гайка" in n and "шайба" in n and "нерж" in n
        )

    def _ensure_group(
        self,
        category: Category,
        name: str,
        *,
        material: str = "А2 нержавіюча сталь",
        dry: bool,
    ) -> ProductGroup:
        slug = slugify(name, allow_unicode=True)[:200] or "group"
        existing = ProductGroup.objects.filter(slug=slug).first()
        if existing:
            if not dry and existing.category_id != category.id:
                existing.category = category
                existing.material = existing.material or material
                existing.is_active = True
                existing.save()
            return existing
        if dry:
            return ProductGroup(
                category=category,
                name=name,
                slug=slug,
                material=material,
                is_active=True,
            )
        return ProductGroup.objects.create(
            category=category,
            name=name,
            slug=slug,
            material=material,
            short_description=name,
            is_active=True,
        )

    def _split_h101(
        self, cats: dict[tuple[str, str], Category], dry: bool
    ) -> int:
        kit = None
        for g in ProductGroup.objects.all():
            if self._is_h101_kit(g):
                kit = g
                break
        if kit is None:
            self.stdout.write("H101 комплект не знайдено — пропуск")
            return 0

        bolt_cat = cats.get(("болти", "болти-нержавіючі"))
        nut_cat = cats.get(("гайки-шайби-гровери", "гайки-нержавіючі"))
        wash_cat = cats.get(("гайки-шайби-гровери", "шайби-нержавіючі"))
        if not all((bolt_cat, nut_cat, wash_cat)):
            self.stderr.write("Немає нерж L2 для розносу H101")
            return 0

        bolt_g = self._ensure_group(
            bolt_cat, "Болт нерж (код H101)", dry=dry
        )
        nut_g = self._ensure_group(
            nut_cat, "Гайка нерж (код H101)", dry=dry
        )
        wash_g = self._ensure_group(
            wash_cat, "Шайба нерж (код H101)", dry=dry
        )

        moved_skus = 0
        for sku in ProductSKU.objects.filter(group=kit):
            n = (sku.name or "").lower()
            if "гайк" in n:
                target = nut_g
            elif "шайб" in n:
                target = wash_g
            else:
                target = bolt_g
            self.stdout.write(f"  SKU {sku.article} → {target.name}")
            if not dry:
                sku.group = target
                sku.save(update_fields=["group", "updated_at"])
            moved_skus += 1

        if not dry:
            kit.is_active = False
            kit.save(update_fields=["is_active", "updated_at"])
            self.stdout.write(self.style.WARNING(f"Деактивовано комплект: {kit.name}"))
        else:
            self.stdout.write(f"[dry-run] деактивувати комплект: {kit.name}")
        return moved_skus

    def _deactivate_legacy(self, dry: bool) -> int:
        n = 0
        legacy = Category.objects.filter(parent=None, slug=LEGACY_L1_SLUG).first()
        if legacy is None:
            return 0
        children = list(Category.objects.filter(parent=legacy))
        for cat in children + [legacy]:
            left = ProductGroup.objects.filter(
                category=cat, is_active=True
            ).count()
            if left and cat.level == Category.Level.L2:
                # активні групи на застарілій L2 — не деактивуємо silently
                self.stderr.write(
                    f"Увага: на {cat.path} лишилось {left} активних груп"
                )
            if cat.is_active:
                self.stdout.write(f"деактивація: {cat.path}")
                if not dry:
                    cat.is_active = False
                    cat.save(update_fields=["is_active"])
                n += 1
        return n
