from django.urls import path

from apps.content import views
from apps.core import urlconverters  # noqa: F401

app_name = "content"

STATIC_SLUGS = (
    "oplata-i-dostavka",
    "povernennya-ta-obmin",
    "publichnyy-dohovir",
    "polityka-konfidentsiynosti",
)

urlpatterns = [
    path("", views.HomeView.as_view(), name="home"),
    path("aktsiyi/", views.PromoListView.as_view(), name="promo_list"),
    path("aktsiyi/<uslug:slug>/", views.PromoDetailView.as_view(), name="promo_detail"),
    path("novyny/", views.NewsListView.as_view(), name="news_list"),
    path("novyny/<uslug:slug>/", views.NewsDetailView.as_view(), name="news_detail"),
    path("kontakty/", views.ContactsView.as_view(), name="contacts"),
]

for _slug in STATIC_SLUGS:
    urlpatterns.append(
        path(
            f"{_slug}/",
            views.StaticPageView.as_view(),
            {"slug": _slug},
            name=_slug.replace("-", "_"),
        )
    )
