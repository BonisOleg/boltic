from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.utils.text import slugify

from apps.catalog.models import Category
from apps.content.static_page_defaults import ensure_static_pages
from apps.core.models import SiteSettings

TREE = [
    (
        "Болти",
        ["Болти", "Болти нержавіючі"],
    ),
    (
        "Гвинти",
        ["Гвинти", "Гвинти нержавіючі"],
    ),
    (
        "Стрижні",
        ["Стрижні", "Стрижні нержавіючі"],
    ),
    (
        "Меблеве кріплення",
        ["Меблеве кріплення"],
    ),
    (
        "Гайки, шайби, гровери",
        [
            "Гайки",
            "Гайки нержавіючі",
            "Шайби",
            "Шайби нержавіючі",
            "Гровери",
            "Гровери нержавіючі",
        ],
    ),
    (
        "Саморізи, шурупи",
        ["Саморізи", "Саморізи нержавіючі", "Шурупи"],
    ),
    (
        "Заклепки, шплінти, штифти",
        ["Заклепки", "Шплінти", "Штифти"],
    ),
    (
        "Дюбелі, анкери",
        ["Дюбелі", "Анкери"],
    ),
    (
        "Хомути, пластини, цвяхи",
        ["Хомути", "Пластини", "Цвяхи"],
    ),
    (
        "Такелаж, троси, ланцюги",
        ["Такелаж", "Троси", "Ланцюги"],
    ),
    (
        "Автокріплення",
        ["Болти", "Саморізи", "Закладні елементи", "Фіксатори"],
    ),
    (
        "Витратні матеріали",
        ["Бури та свердла", "Біти", "Тримачі біт", "Диски", "Стяжки"],
    ),
    (
        "Піни, клеї, герметики",
        ["Піни", "Клеї", "Герметики"],
    ),
    (
        "Підшипники, сальники",
        ["Підшипники", "Сальники"],
    ),
    (
        "Композитна арматура, сітка, фіксатори, клинки",
        ["Композитна арматура", "Композитна сітка", "Фіксатори", "Клинки"],
    ),
]

class Command(BaseCommand):
    help = "Seed категорій каталогу + базові static pages"

    def handle(self, *args, **options):
        SiteSettings.load()
        call_command("seed_site_blocks")
        call_command("seed_hero_slides")
        for i, (l1_name, children) in enumerate(TREE):
            l1_slug = slugify(l1_name, allow_unicode=True)
            l1, _ = Category.objects.update_or_create(
                parent=None,
                slug=l1_slug,
                defaults={
                    "name": l1_name,
                    "level": Category.Level.L1,
                    "sort_order": i,
                    "is_active": True,
                },
            )
            for j, child_name in enumerate(children):
                child_slug = slugify(child_name, allow_unicode=True)
                Category.objects.update_or_create(
                    parent=l1,
                    slug=child_slug,
                    defaults={
                        "name": child_name,
                        "level": Category.Level.L2,
                        "sort_order": j,
                        "is_active": True,
                    },
                )
        stats = ensure_static_pages()
        self.stdout.write(
            self.style.SUCCESS(
                "Seed OK "
                f"(pages +{stats['created']} ~{stats['updated']} skip={stats['skipped']})"
            )
        )
