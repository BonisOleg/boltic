from django.core.management.base import BaseCommand
from django.utils.text import slugify

from apps.catalog.classification import BOLT_SCREW_L2
from apps.catalog.models import Category
from apps.content.models import HomeBlock, StaticPage
from apps.core.models import SiteSettings

TREE = [
    (
        "Болти, гвинти, стрижні",
        # детальні підкатегорії (замість плоских Болти/Гвинти)
        [name for name, _slug in BOLT_SCREW_L2],
    ),
    (
        "Гайки, шайби, гровери",
        ["Гайки", "Шайби", "Гровери"],
    ),
    (
        "Самонарізи, шурупи",
        ["Самонарізи", "Шурупи"],
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
        ["Болти", "Самонарізи", "Закладні елементи", "Фіксатори"],
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

STATIC_PAGES = [
    ("oplata-i-dostavka", "Оплата і доставка", "Текст про оплату та доставку."),
    ("povernennya-ta-obmin", "Повернення та обмін", "Повернення протягом 14 днів."),
    ("publichnyy-dohovir", "Публічний договір", "Текст оферти."),
    (
        "polityka-konfidentsiynosti",
        "Політика конфіденційності",
        "Політика обробки персональних даних.",
    ),
]


class Command(BaseCommand):
    help = "Seed категорій з каталог.docx + базові static pages"

    def handle(self, *args, **options):
        SiteSettings.load()
        HomeBlock.objects.get_or_create(
            key="hero",
            defaults={
                "title": "БОЛТіК°",
                "body": "Всі види кріплень",
                "sort_order": 0,
            },
        )
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
        for slug, title, body in STATIC_PAGES:
            StaticPage.objects.update_or_create(
                slug=slug,
                defaults={"title": title, "body": body, "is_published": True},
            )
        self.stdout.write(self.style.SUCCESS("Seed OK"))
