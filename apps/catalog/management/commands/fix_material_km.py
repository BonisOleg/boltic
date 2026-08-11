"""Замінити матеріал/текст «к.м.» → «сталь» і перезібрати фасети."""

from __future__ import annotations

from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Q

from apps.catalog.facet_sync import sync_facets_from_skus
from apps.catalog.material_wording import (
    MATERIAL_STEEL,
    fix_km_slug,
    fix_km_wording,
    is_km_material,
    normalize_material,
)
from apps.catalog.models import FacetValue, ProductGroup, ProductImage, ProductSKU


class Command(BaseCommand):
    help = "к.м. → сталь у material, назвах, alt, slug; sync facets"

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true")

    def handle(self, *args, **options):
        dry = options["dry_run"]
        stats = {
            "groups": 0,
            "materials": 0,
            "slugs": 0,
            "skus": 0,
            "images": 0,
        }

        groups = list(
            ProductGroup.objects.filter(
                Q(material__icontains="к.м")
                | Q(material__iexact="к.м")
                | Q(material__iexact="к.м.")
                | Q(name__icontains="к.м")
                | Q(short_description__icontains="к.м")
                | Q(description__icontains="к.м")
                | Q(seo_title__icontains="к.м")
                | Q(seo_description__icontains="к.м")
                | Q(slug__regex=r"(^|-)км($|-)")
                | Q(material__icontains="конструкційна сталь")
            )
        )
        skus = list(ProductSKU.objects.filter(name__icontains="к.м"))
        images = list(ProductImage.objects.filter(alt__icontains="к.м"))

        used_slugs = set(
            ProductGroup.objects.exclude(pk__in=[g.pk for g in groups]).values_list(
                "slug", flat=True
            )
        )

        with transaction.atomic():
            for g in groups:
                new_material = (
                    normalize_material(g.material)
                    if is_km_material(g.material)
                    or "конструкційна сталь" in (g.material or "").lower()
                    else g.material
                )
                if is_km_material(g.material):
                    new_material = MATERIAL_STEEL

                new_name = fix_km_wording(g.name)
                new_short = fix_km_wording(g.short_description)
                new_desc = fix_km_wording(g.description)
                new_seo_t = fix_km_wording(g.seo_title)
                new_seo_d = fix_km_wording(g.seo_description)
                new_slug = fix_km_slug(g.slug)

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

                if new_material != g.material:
                    stats["materials"] += 1

                changed = (
                    new_material != g.material
                    or new_name != g.name
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
                        f"G#{g.pk} mat {g.material!r}→{new_material!r} | "
                        f"{g.name!r}→{new_name!r} | slug {g.slug!r}→{new_slug!r}"
                    )
                    continue
                g.material = new_material
                g.name = new_name
                g.short_description = new_short
                g.description = new_desc
                g.seo_title = new_seo_t
                g.seo_description = new_seo_d
                g.slug = new_slug
                g.save(
                    update_fields=[
                        "material",
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
                new_name = fix_km_wording(sku.name)
                if new_name == sku.name:
                    continue
                stats["skus"] += 1
                if dry:
                    self.stdout.write(f"SKU {sku.article}: {sku.name!r} → {new_name!r}")
                    continue
                sku.name = new_name
                sku.save(update_fields=["name"])

            for img in images:
                new_alt = fix_km_wording(img.alt)
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
                self.stdout.write(
                    self.style.WARNING(
                        f"DRY-RUN groups={stats['groups']} "
                        f"materials={stats['materials']} slugs={stats['slugs']} "
                        f"skus={stats['skus']} images={stats['images']}"
                    )
                )
                return

            # прибрати старі фасет-мітки матеріалу
            FacetValue.objects.filter(
                attribute__code="material",
                value__icontains="к.м",
            ).delete()
            facet_stats = sync_facets_from_skus()

        self.stdout.write(
            self.style.SUCCESS(
                f"OK groups={stats['groups']} materials={stats['materials']} "
                f"slugs={stats['slugs']} skus={stats['skus']} "
                f"images={stats['images']} facets={facet_stats}"
            )
        )
