"""Розбити «Свердло Haisser» на метал / бетон / інше."""

from __future__ import annotations

import re
from pathlib import Path

from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils.text import slugify

from apps.catalog.models import ProductGroup, ProductImage, ProductSKU

SOURCE_GROUP_ID = 21

NAME_METAL = "Свердла Haisser по металу"
NAME_CONCRETE = "Свердла Haisser по бетону"
NAME_OTHER = "Інші свердла Haisser"


def _classify(name: str) -> str:
    n = (name or "").lower().replace("ё", "е")
    # латинська C на початку назви
    n = n.replace("cвердл", "свердл")
    if "бетон" in n:
        return "concrete"
    if "п/м" in n or "по мет" in n or "метал" in n:
        return "metal"
    return "other"


def _fix_sku_name(name: str) -> str:
    text = name or ""
    # Latin C → Cyrillic С in «Свердло»
    text = re.sub(r"(?i)^cвердл", "Свердл", text)
    text = re.sub(r" {2,}", " ", text)
    return text.strip()


class Command(BaseCommand):
    help = "Свердло Haisser → по металу / по бетону / інші (+ копія фото)"

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true")

    def handle(self, *args, **options):
        dry = options["dry_run"]
        src = (
            ProductGroup.objects.filter(pk=SOURCE_GROUP_ID)
            .select_related("category")
            .first()
        )
        if src is None:
            self.stderr.write(f"Немає ProductGroup id={SOURCE_GROUP_ID}")
            return

        skus = list(ProductSKU.objects.filter(group=src).order_by("article"))
        buckets = {"metal": [], "concrete": [], "other": []}
        for sku in skus:
            buckets[_classify(sku.name)].append(sku)

        self.stdout.write(
            f"source={src.id} «{src.name}» → "
            f"metal={len(buckets['metal'])} "
            f"concrete={len(buckets['concrete'])} "
            f"other={len(buckets['other'])}"
        )

        with transaction.atomic():
            metal = src
            metal.name = NAME_METAL
            metal.slug = slugify(NAME_METAL, allow_unicode=True)
            metal.short_description = NAME_METAL
            if not dry:
                metal.save(
                    update_fields=[
                        "name",
                        "slug",
                        "short_description",
                        "updated_at",
                    ]
                )
            self.stdout.write(f"  metal id={metal.id} slug={metal.slug}")

            concrete = self._ensure_group(src.category, NAME_CONCRETE, dry)
            other = self._ensure_group(src.category, NAME_OTHER, dry)

            for sku in skus:
                new_name = _fix_sku_name(sku.name)
                kind = _classify(sku.name)
                target = metal
                if kind == "concrete":
                    target = concrete
                elif kind == "other":
                    target = other

                changed = []
                if new_name != sku.name:
                    changed.append(f"name → {new_name!r}")
                    if not dry:
                        sku.name = new_name
                if sku.group_id != getattr(target, "id", None):
                    changed.append(f"group → {target.name}")
                    if not dry:
                        sku.group = target
                if changed:
                    self.stdout.write(f"  {sku.article}: " + "; ".join(changed))
                    if not dry:
                        sku.save(update_fields=["name", "group", "updated_at"])

            if not dry:
                self._copy_images(metal, [concrete, other])

            if dry:
                transaction.set_rollback(True)
                self.stdout.write(self.style.WARNING("dry-run: rollback"))
            else:
                self.stdout.write(
                    self.style.SUCCESS(
                        f"done metal={ProductSKU.objects.filter(group=metal).count()} "
                        f"concrete={ProductSKU.objects.filter(group=concrete).count()} "
                        f"other={ProductSKU.objects.filter(group=other).count()}"
                    )
                )

    def _ensure_group(self, category, name: str, dry: bool) -> ProductGroup:
        slug = slugify(name, allow_unicode=True)
        existing = ProductGroup.objects.filter(slug=slug).first()
        if existing:
            self.stdout.write(f"  reuse id={existing.id} slug={slug}")
            return existing
        self.stdout.write(f"  create slug={slug}")
        if dry:
            return ProductGroup(
                id=0, category=category, name=name, slug=slug, is_active=True
            )
        return ProductGroup.objects.create(
            category=category,
            name=name,
            slug=slug,
            short_description=name,
            is_active=True,
        )

    def _copy_images(self, src: ProductGroup, targets: list[ProductGroup]) -> None:
        src_imgs = list(src.images.all())
        if not src_imgs:
            self.stdout.write("  no source images to copy")
            return
        for tgt in targets:
            if tgt.images.exists():
                self.stdout.write(f"  skip images for {tgt.slug} — already has")
                continue
            for im in src_imgs:
                im.image.open("rb")
                data = im.image.read()
                fname = Path(im.image.name).name
                new_im = ProductImage(
                    group=tgt,
                    alt=tgt.name,
                    sort_order=im.sort_order,
                    is_primary=im.is_primary,
                )
                new_im.image.save(
                    f"{tgt.slug}_{fname}", ContentFile(data), save=True
                )
                self.stdout.write(f"  image → {tgt.slug}: {new_im.image.name}")
            for im in src.images.all():
                if im.alt != src.name:
                    im.alt = src.name
                    im.save(update_fields=["alt"])
