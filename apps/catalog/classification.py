"""Правила розфасовки ProductGroup → L2 підкатегорія."""

from __future__ import annotations


def resolve_bolt_screw_l2_slug(name: str, standard: str = "") -> str:
    """
    Повертає slug L2 під L1 «Болти, гвинти, стрижні»
    (українські SEO-slug, як у seed_catalog).
    """
    n = (name or "").lower()
    std = (standard or "").upper().replace(" ", " ")

    if "леміш" in n:
        return "болти-лемішні"
    if "норійн" in n or "норий" in n or "нор." in n:
        return "болти-норійні"
    if "меблев" in n or "конфірмат" in n:
        return "болти-меблеві"
    if "прес" in n or "967" in n:
        return "гвинти-з-прес-шайбою"
    if "7991" in n or "потай" in n or "DIN 7991" in std:
        return "гвинти-потайні"
    if "гвинт" in n or "DIN 912" in std or "912" in std:
        return "гвинти-з-внутрішнім-шестигранником"
    if "шпильк" in n or "стриж" in n:
        return "стрижні"
    if "болт" in n or any(
        s in std for s in ("DIN 933", "DIN 931", "DIN 960", "DIN 961")
    ):
        return "болти-з-шестигранною-головкою"
    return "болти-з-шестигранною-головкою"


def resolve_goods_category(
    group_name: str,
    product_name: str = "",
) -> tuple[str, str]:
    """
    Excel «Група товарів» / назва → (l1_slug, l2_slug).

    Основний сигнал — назва групи; назва товару лише як допоміжна.
    """
    g = (group_name or "").strip().lower()
    p = (product_name or "").strip().lower()
    # для класифікації групи не підмішуємо «свердло» з назви саморіза тощо
    text = g if g else p
    both = f"{g} {p}".strip()

    # службові / слабкі групи — дивимось на товар
    if not g or g in {"різне", "спец.замовлення", "спец замовлення"} or g.startswith("спец"):
        if g.startswith("спец") or g in {"спец.замовлення", "спец замовлення"}:
            return "витратні-матеріали", "стяжки"
        text = both or p

    # --- автокріплення ---
    if "саморіз автомоб" in text or ("автомоб" in text and "саморіз" in text):
        return "автокріплення", "самонарізи"

    # --- дюбелі / анкери ---
    if "анкер" in text:
        return "дюбелі-анкери", "анкери"
    if "дюбель" in text:
        return "дюбелі-анкери", "дюбелі"

    # --- заклепки / шплінти ---
    if "заклеп" in text:
        return "заклепки-шплінти-штифти", "заклепки"
    if "шплінт" in text:
        return "заклепки-шплінти-штифти", "шплінти"
    if "штифт" in text:
        return "заклепки-шплінти-штифти", "штифти"

    # --- такелаж (до «гайка» через римгайка) ---
    if "римболт" in text or "римгайк" in text:
        return "такелаж-троси-ланцюги", "такелаж"
    if "такелаж" in text:
        return "такелаж-троси-ланцюги", "такелаж"
    if "ланцюг" in text and "трос" in text:
        return "такелаж-троси-ланцюги", "троси"
    if "ланцюг" in text:
        return "такелаж-троси-ланцюги", "ланцюги"
    if "трос" in text:
        return "такелаж-троси-ланцюги", "троси"

    # --- нерж мікс ---
    if "нерж" in text and "болт" in text and ("гайка" in text or "шайба" in text):
        return "болти-гвинти-стрижні", "болти-з-шестигранною-головкою"

    # --- самонарізи / шурупи / віконні (ДО свердел і прес-шайби) ---
    if any(
        x in text
        for x in (
            "саморіз",
            "самонар",
            "сам-з",
            "віконн",
            "шуруп",
            "турбогвинт",
            "гвинт-шуруп",
            "гвинт шуруп",
        )
    ):
        if any(x in text for x in ("шуруп", "турбогвинт", "гвинт-шуруп", "гвинт шуруп")):
            return "самонарізи-шурупи", "шурупи"
        return "самонарізи-шурупи", "самонарізи"

    # --- гвинти з прес-шайбою (не саморізи) ---
    compact = text.replace(" ", "")
    if (
        "прес-шайб" in text
        or "пресшайб" in compact
        or "din967" in compact
        or "din 967" in text
    ) and "саморіз" not in text:
        return "болти-гвинти-стрижні", "гвинти-з-прес-шайбою"

    # --- гайки / шайби / гровери ---
    if "гайка" in text:
        return "гайки-шайби-гровери", "гайки"
    if "гровер" in text:
        return "гайки-шайби-гровери", "гровери" if "шайба" not in text else "шайби"
    if "шайба" in text or "шайб" in text:
        return "гайки-шайби-гровери", "шайби"
    if "кільц" in both and ("резин" in both or "гумов" in both):
        return "підшипники-сальники", "сальники"

    # --- хомути / пластини / цвяхи ---
    if "хомут" in text:
        return "хомути-пластини-цвяхи", "хомути"
    if "цвях" in text:
        return "хомути-пластини-цвяхи", "цвяхи"
    if any(x in text for x in ("кутник", "кутки", "куток", "пластин", "перфор")):
        return "хомути-пластини-цвяхи", "пластини"

    # --- підшипники ---
    if "підшипник" in text or "подшипник" in text:
        return "підшипники-сальники", "підшипники"
    if "сальник" in text:
        return "підшипники-сальники", "сальники"

    # --- витратні ---
    if any(x in text for x in ("свердл", "бур", "haisser")):
        return "витратні-матеріали", "бури-та-свердла"
    if "біта" in text or "біти" in text or "felo" in text or "suretorq" in text:
        return "витратні-матеріали", "біти"
    if "тримач біт" in text or "насадка" in text or "магнітн" in both:
        return "витратні-матеріали", "тримачі-біт"
    if "диск" in text:
        return "витратні-матеріали", "диски"
    if any(x in text for x in ("стяжк", "скоба", "органайзер", "канцеляр", "електрод")):
        return "витратні-матеріали", "стяжки"

    # --- композитна / фіксатори ---
    if "фіксатор" in text:
        return "композитна-арматура-сітка-фіксатори-клинки", "фіксатори"

    # --- меблеве ---
    if "меблев" in text or "конфірмат" in text or "з*єднан" in text:
        return "болти-гвинти-стрижні", "болти-меблеві"

    # --- болти / гвинти / шпильки ---
    if "шпильк" in text:
        return "болти-гвинти-стрижні", "стрижні"
    if any(x in text for x in ("гвинт", "din 912", "din912", "7991", "din 967")):
        l2 = resolve_bolt_screw_l2_slug(group_name or product_name, "")
        return "болти-гвинти-стрижні", l2
    if "болт" in text or "din 93" in text or "din93" in text or "din 96" in text:
        l2 = resolve_bolt_screw_l2_slug(group_name or product_name, "")
        return "болти-гвинти-стрижні", l2

    # fallback за назвою товару
    if p and p != text:
        return resolve_goods_category("", p)

    return "витратні-матеріали", "стяжки"


def infer_group_name(product_name: str) -> str:
    """Якщо в Excel немає «Група товарів» — вивести з назви."""
    p = (product_name or "").strip()
    pl = p.lower()
    if "нор." in pl or "норійн" in pl:
        return "Болт норійний"
    if "електрод" in pl:
        return "Електроди"
    if "кільц" in pl and "резин" in pl:
        return "Кільця гумові"
    if "тримач біт" in pl:
        return "Тримач біт"
    if "насадка" in pl:
        return "Насадки / тримачі біт"
    if "гіпсокартон/метал" in pl:
        return "Саморіз гіпсокартон/метал 201"
    if "гіпсокартон" in pl:
        return "Саморіз гіпсокартон/дерево 202"
    if ("прес-шайб" in pl or "прес шайб" in pl) and "саморіз" in pl:
        return "Саморіз з прес-шайбою"
    if "саморіз" in pl:
        return "Самонарізи (інше)"
    if "болт" in pl:
        return "Болт (інше)"
    return "Різне"


# L2 під L1 «Болти, гвинти, стрижні» (замість плоских Болти/Гвинти)
BOLT_SCREW_L2: list[tuple[str, str]] = [
    ("Болти з шестигранною головкою", "болти-з-шестигранною-головкою"),
    ("Болти лемішні", "болти-лемішні"),
    ("Болти норійні", "болти-норійні"),
    ("Болти меблеві", "болти-меблеві"),
    ("Гвинти з внутрішнім шестигранником", "гвинти-з-внутрішнім-шестигранником"),
    ("Гвинти потайні", "гвинти-потайні"),
    ("Гвинти з прес-шайбою", "гвинти-з-прес-шайбою"),
    ("Стрижні", "стрижні"),
]

# Старі плоскі L2 — деактивуємо після переносу
LEGACY_FLAT_L2_SLUGS = ("болти", "гвинти")
