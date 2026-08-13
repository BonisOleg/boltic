from django.apps import apps
from django.core.management.base import BaseCommand
from django.core.management.color import no_style
from django.db import connection


class Command(BaseCommand):
    help = "Скинути PK sequences після loaddata (PostgreSQL)"

    def handle(self, *args, **options):
        models = [m for m in apps.get_models() if m._meta.managed]
        sqls = connection.ops.sequence_reset_sql(no_style(), models)
        if not sqls:
            self.stdout.write("sequences: nothing to reset")
            return
        with connection.cursor() as cursor:
            for sql in sqls:
                cursor.execute(sql)
        self.stdout.write(self.style.SUCCESS(f"sequences reset: {len(sqls)}"))
