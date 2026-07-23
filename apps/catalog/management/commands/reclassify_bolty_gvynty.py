from django.core.management.base import BaseCommand
from django.db import transaction

from apps.catalog.classification import (
    BOLT_SCREW_L2,
    LEGACY_FLAT_L2_SLUGS,
    resolve_bolt_screw_l2_slug,
)
from apps.catalog.models import Category, ProductGroup


class Command(BaseCommand):
    help = (
        "Створює детальні L2 під «Болти, гвинти, стрижні» "
        "і розносить ProductGroup по підкатегоріях"
    )

    def handle(self, *args, **options):
        with transaction.atomic():
            l1 = Category.objects.filter(
                path="болти-гвинти-стрижні/", level=Category.Level.L1
            ).first()
            if l1 is None:
                self.stderr.write("L1 не знайдено — спочатку seed_catalog")
                return

            # Гарантувати L2
            by_slug: dict[str, Category] = {}
            for i, (name, slug) in enumerate(BOLT_SCREW_L2):
                cat, _ = Category.objects.update_or_create(
                    parent=l1,
                    slug=slug,
                    defaults={
                        "name": name,
                        "level": Category.Level.L2,
                        "sort_order": i,
                        "is_active": True,
                    },
                )
                # path оновлюється в save()
                cat.save()
                by_slug[slug] = cat
                self.stdout.write(f"L2 OK: {cat.path}")

            moved = []
            for group in ProductGroup.objects.select_related("category").all():
                # лише товари з цього L1 (або старі плоскі bolty/gvynty)
                parent = group.category.parent
                if parent is None or parent.id != l1.id:
                    continue

                target_slug = resolve_bolt_screw_l2_slug(
                    group.name, group.standard
                )
                target = by_slug.get(target_slug)
                if target is None:
                    self.stderr.write(
                        f"Немає L2 {target_slug} для {group.name}"
                    )
                    continue

                # Виправлення назви лемішного
                new_name = group.name
                if "лемішний10" in group.name.replace(" ", ""):
                    new_name = "Болт лемішний 10,9 к.м."

                changed = group.category_id != target.id or group.name != new_name
                if changed:
                    old = group.category.path
                    group.category = target
                    group.name = new_name
                    if "леміш" in new_name.lower() and not group.material:
                        group.material = "к.м."
                    group.save()
                    moved.append((group.name, old, target.path))
                    self.stdout.write(
                        f"→ {group.name}\n   {old}  ⇒  {target.path}"
                    )

            # Деактивувати порожні плоскі «Болти» / «Гвинти»
            for slug in LEGACY_FLAT_L2_SLUGS:
                legacy = Category.objects.filter(parent=l1, slug=slug).first()
                if legacy is None:
                    continue
                left = ProductGroup.objects.filter(category=legacy).count()
                if left == 0:
                    legacy.is_active = False
                    legacy.save(update_fields=["is_active"])
                    self.stdout.write(
                        self.style.WARNING(f"Деактивовано порожню: {legacy.path}")
                    )
                else:
                    self.stdout.write(
                        self.style.ERROR(
                            f"У {legacy.path} лишилось {left} груп — не чіпаємо"
                        )
                    )

            self.stdout.write(
                self.style.SUCCESS(f"Перенесено/оновлено: {len(moved)} груп")
            )
            self._print_summary(l1)

    def _print_summary(self, l1: Category) -> None:
        self.stdout.write("\n=== Підсумок L1 ===")
        for l2 in Category.objects.filter(parent=l1).order_by("sort_order", "name"):
            n = ProductGroup.objects.filter(category=l2).count()
            status = "ON" if l2.is_active else "OFF"
            self.stdout.write(f"[{status}] {l2.name}: {n} груп ({l2.path})")
