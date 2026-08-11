"""Замінити кл.пр → кл.міц у назвах/slug каталогу."""

from __future__ import annotations

from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Q

from apps.catalog.models import ProductGroup, ProductImage, ProductSKU
from apps.catalog.strength_wording import fix_strength_slug, fix_strength_wording


class Command(BaseCommand):
    help = "кл.пр. / кл. пр. → кл.міц. / кл. міц. у групах, SKU, alt; оновити slug"

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true")

    def handle(self, *args, **options):
        dry = options["dry_run"]
        stats = {"groups": 0, "skus": 0, "images": 0, "slugs": 0}

        text_q = (
            Q(name__icontains="кл.пр")
            | Q(name__icontains="кл. пр")
            | Q(short_description__icontains="кл.пр")
            | Q(short_description__icontains="кл. пр")
            | Q(description__icontains="кл.пр")
            | Q(description__icontains="кл. пр")
            | Q(seo_title__icontains="кл.пр")
            | Q(seo_title__icontains="кл. пр")
            | Q(seo_description__icontains="кл.пр")
            | Q(seo_description__icontains="кл. пр")
            | Q(slug__icontains="клпр")
            | Q(slug__icontains="кл-пр")
        )

        groups = list(ProductGroup.objects.filter(text_q))
        skus = list(
            ProductSKU.objects.filter(
                Q(name__icontains="кл.пр") | Q(name__icontains="кл. пр")
            )
        )
        images = list(
            ProductImage.objects.filter(
                Q(alt__icontains="кл.пр") | Q(alt__icontains="кл. пр")
            )
        )

        used_slugs = set(
            ProductGroup.objects.exclude(
                pk__in=[g.pk for g in groups]
            ).values_list("slug", flat=True)
        )

        with transaction.atomic():
            for g in groups:
                new_name = fix_strength_wording(g.name)
                new_short = fix_strength_wording(g.short_description)
                new_desc = fix_strength_wording(g.description)
                new_seo_t = fix_strength_wording(g.seo_title)
                new_seo_d = fix_strength_wording(g.seo_description)
                new_slug = fix_strength_slug(g.slug)
                if new_slug != g.slug:
                    base = new_slug
                    n = 2
                    while new_slug in used_slugs:
                        new_slug = f"{base}-{n}"
                        n += 1
                    used_slugs.add(new_slug)
                    stats["slugs"] += 1
                else:
                    used_slugs.add(g.slug)

                changed = (
                    new_name != g.name
                    or new_short != g.short_description
                    or new_desc != g.description
                    or new_seo_t != g.seo_title
                    or new_seo_d != g.seo_description
                    or new_slug != g.slug
                )
                if not changed:
                    continue
                stats["groups"] += 1
                if dry:
                    self.stdout.write(
                        f"G#{g.pk}: {g.name!r} → {new_name!r}; "
                        f"slug {g.slug!r} → {new_slug!r}"
                    )
                    continue
                g.name = new_name
                g.short_description = new_short
                g.description = new_desc
                g.seo_title = new_seo_t
                g.seo_description = new_seo_d
                g.slug = new_slug
                g.save(
                    update_fields=[
                        "name",
                        "short_description",
                        "description",
                        "seo_title",
                        "seo_description",
                        "slug",
                        "updated_at",
                    ]
                )

            for sku in skus:
                new_name = fix_strength_wording(sku.name)
                if new_name == sku.name:
                    continue
                stats["skus"] += 1
                if dry:
                    self.stdout.write(f"SKU {sku.article}: {sku.name!r} → {new_name!r}")
                    continue
                sku.name = new_name
                sku.save(update_fields=["name"])

            for img in images:
                new_alt = fix_strength_wording(img.alt)
                if new_alt == img.alt:
                    continue
                stats["images"] += 1
                if dry:
                    self.stdout.write(f"IMG#{img.pk}: {img.alt!r} → {new_alt!r}")
                    continue
                img.alt = new_alt
                img.save(update_fields=["alt"])

            if dry:
                transaction.set_rollback(True)

        msg = (
            f"groups={stats['groups']} slugs={stats['slugs']} "
            f"skus={stats['skus']} images={stats['images']}"
        )
        if dry:
            self.stdout.write(self.style.WARNING(f"DRY-RUN {msg}"))
        else:
            self.stdout.write(self.style.SUCCESS(f"OK {msg}"))
