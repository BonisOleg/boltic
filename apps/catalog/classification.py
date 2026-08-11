"""Правила розфасовки ProductGroup → (L1 slug, L2 slug)."""

from __future__ import annotations


def _is_stainless(*parts: str) -> bool:
    text = " ".join(p or "" for p in parts).lower()
    return any(x in text for x in ("нерж", "а2", "a2", "stainless"))


def _is_furniture(text: str) -> bool:
    t = (text or "").lower()
    return any(
        x in t
        for x in (
            "меблев",
            "мебельн",
            "конфірмат",
            "з*єднан",
            "з'єднан",
            "зʼєднан",
            "зєднання",
        )
    )


def resolve_fastener_category(
    name: str,
    standard: str = "",
    material: str = "",
) -> tuple[str, str]:
    """
    Болт / гвинт / стрижень / меблеве → (l1_slug, l2_slug).
    """
    n = (name or "").lower()
    std = (standard or "").upper()
    stainless = _is_stainless(name, material)

    if _is_furniture(n):
        return "меблеве-кріплення", "меблеве-кріплення"

    if "шпильк" in n or "стриж" in n:
        return "стрижні", "стрижні-нержавіючі" if stainless else "стрижні"

    if (
        "прес" in n
        or "967" in n
        or "7991" in n
        or "потай" in n
        or "сегмент" in n
        or "гвинт" in n
        or "DIN 912" in std
        or "912" in std
        or "DIN 7991" in std
        or "DIN 967" in std
    ):
        return "гвинти", "гвинти-нержавіючі" if stainless else "гвинти"

    if "болт" in n or any(
        s in std for s in ("DIN 933", "DIN 931", "DIN 960", "DIN 961")
    ):
        return "болти", "болти-нержавіючі" if stainless else "болти"

    return "болти", "болти-нержавіючі" if stainless else "болти"


def resolve_bolt_screw_l2_slug(name: str, standard: str = "") -> str:
    """Сумісність: лише L2 slug з resolve_fastener_category."""
    _l1, l2 = resolve_fastener_category(name, standard)
    return l2


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
    text = g if g else p
    both = f"{g} {p}".strip()

    if not g or g in {"різне", "спец.замовлення", "спец замовлення"} or g.startswith(
        "спец"
    ):
        if g.startswith("спец") or g in {"спец.замовлення", "спец замовлення"}:
            return "витратні-матеріали", "стяжки"
        text = both or p

    # --- автокріплення ---
    if "саморіз автомоб" in text or ("автомоб" in text and "саморіз" in text):
        return "автокріплення", "саморізи"

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

    # --- мішаний нерж-комплект (група) → болти нерж; SKU розносить окрема команда ---
    if "нерж" in text and "болт" in text and ("гайка" in text or "шайба" in text):
        return "болти", "болти-нержавіючі"

    # --- саморізи / шурупи / віконні (ДО свердел і прес-шайби) ---
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
            return "саморізи-шурупи", "шурупи"
        if _is_stainless(text):
            return "саморізи-шурупи", "саморізи-нержавіючі"
        return "саморізи-шурупи", "саморізи"

    # --- гвинти з прес-шайбою (не саморізи) ---
    compact = text.replace(" ", "")
    if (
        "прес-шайб" in text
        or "пресшайб" in compact
        or "din967" in compact
        or "din 967" in text
    ) and "саморіз" not in text:
        return resolve_fastener_category(group_name or product_name, "DIN 967")

    # --- меблеве (у т.ч. гайка меблева) ДО загальних гайок ---
    if _is_furniture(text):
        return "меблеве-кріплення", "меблеве-кріплення"

    # --- гайки / шайби / гровери ---
    if "гайка" in text:
        l2 = "гайки-нержавіючі" if _is_stainless(text) else "гайки"
        return "гайки-шайби-гровери", l2
    if "гровер" in text:
        # мішана група «Шайба,гровер» лишається в шайбах
        if "шайба" in text:
            return "гайки-шайби-гровери", "шайби"
        l2 = "гровери-нержавіючі" if _is_stainless(text) else "гровери"
        return "гайки-шайби-гровери", l2
    if "шайба" in text or "шайб" in text:
        l2 = "шайби-нержавіючі" if _is_stainless(text) else "шайби"
        return "гайки-шайби-гровери", l2
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

    # --- болти / гвинти / шпильки ---
    if "шпильк" in text or "стриж" in text:
        return resolve_fastener_category(group_name or product_name, "", "")
    if any(x in text for x in ("гвинт", "din 912", "din912", "7991", "din 967", "сегмент")):
        return resolve_fastener_category(group_name or product_name, "")
    if "болт" in text or "din 93" in text or "din93" in text or "din 96" in text:
        return resolve_fastener_category(group_name or product_name, "")

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
        return "Саморізи (інше)"
    if "болт" in pl:
        return "Болт (інше)"
    return "Різне"


# Цільове дерево кріплення (для seed / міграції)
FASTENER_TREE: list[tuple[str, list[str]]] = [
    ("Болти", ["Болти", "Болти нержавіючі"]),
    ("Гвинти", ["Гвинти", "Гвинти нержавіючі"]),
    ("Стрижні", ["Стрижні", "Стрижні нержавіючі"]),
    ("Меблеве кріплення", ["Меблеве кріплення"]),
]

# Застарілий L1 і детальні L2 — деактивуємо після переносу
LEGACY_L1_SLUG = "болти-гвинти-стрижні"
LEGACY_DETAIL_L2_SLUGS = (
    "болти-з-шестигранною-головкою",
    "болти-лемішні",
    "болти-норійні",
    "болти-меблеві",
    "гвинти-з-внутрішнім-шестигранником",
    "гвинти-потайні",
    "гвинти-з-прес-шайбою",
    "стрижні",
    "болти",
    "гвинти",
)

# Сумісність зі старим імпортом
BOLT_SCREW_L2: list[tuple[str, str]] = [
    ("Болти", "болти"),
    ("Болти нержавіючі", "болти-нержавіючі"),
]
LEGACY_FLAT_L2_SLUGS = LEGACY_DETAIL_L2_SLUGS
