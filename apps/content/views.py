from django.http import Http404
from django.shortcuts import render
from django.views import View
from django.views.generic import TemplateView

from apps.content import selectors


class HomeView(TemplateView):
    template_name = "content/home.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.update(selectors.home_context())
        return ctx


class PromoListView(TemplateView):
    template_name = "content/promo_list.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["promotions"] = selectors.active_promotions()
        return ctx


class PromoDetailView(View):
    def get(self, request, slug: str):
        promo = selectors.get_promotion(slug)
        if promo is None:
            raise Http404
        return render(request, "content/promo_detail.html", {"promo": promo})


class NewsListView(TemplateView):
    template_name = "content/news_list.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["posts"] = selectors.published_news()
        return ctx


class NewsDetailView(View):
    def get(self, request, slug: str):
        post = selectors.get_news(slug)
        if post is None:
            raise Http404
        return render(request, "content/news_detail.html", {"post": post})


class ContactsView(TemplateView):
    template_name = "content/contacts.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["branches"] = selectors.contact_branches()
        return ctx


class StaticPageView(View):
    def get(self, request, slug: str):
        page = selectors.get_static_page(slug)
        if page is None:
            raise Http404
        return render(request, "content/static_page.html", {"page": page})
