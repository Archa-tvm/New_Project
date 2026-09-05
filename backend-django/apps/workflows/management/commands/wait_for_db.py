import time
from django.core.management.base import BaseCommand
from django.db import connections
from django.db.utils import OperationalError

class Command(BaseCommand):
    """Django command that waits until database is available."""

    def handle(self, *args, **options):
        self.stdout.write('Waiting for database connection...')
        db_conn = None
        attempts = 0
        while not db_conn and attempts < 30:
            try:
                db_conn = connections['default']
                db_conn.cursor()
            except OperationalError:
                attempts += 1
                self.stdout.write(f'Database unavailable, waiting 1 second... ({attempts}/30)')
                time.sleep(1)

        if db_conn:
            self.stdout.write(self.style.SUCCESS('Database ready!'))
        else:
            self.stdout.write(self.style.ERROR('Database connection timed out.'))
