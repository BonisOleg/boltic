from django.urls import register_converter


class UnicodeSlugConverter:
    """SEO-slug з кирилицею (українські шляхи з карти сайту)."""

    regex = r"[-\w]+"

    def to_python(self, value: str) -> str:
        return value

    def to_url(self, value: str) -> str:
        return value


register_converter(UnicodeSlugConverter, "uslug")
