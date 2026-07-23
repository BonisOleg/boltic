from django.db import transaction

from apps.catalog.models import ProductGroup
from apps.core.exceptions import ReviewError
from apps.reviews.models import Review


@transaction.atomic
def create_pending_review(*, user, group_slug: str, rating: int, body: str) -> Review:
    group = ProductGroup.objects.filter(slug=group_slug, is_active=True).first()
    if group is None:
        raise ReviewError("Товар не знайдено")
    if not user.is_authenticated:
        raise ReviewError("Потрібен вхід")
    rating = int(rating)
    if rating < 1 or rating > 5:
        raise ReviewError("Оцінка 1–5")
    body = (body or "").strip()
    if len(body) < 3:
        raise ReviewError("Занадто короткий відгук")
    return Review.objects.create(
        group=group,
        user=user,
        rating=rating,
        body=body,
        is_published=False,
    )
