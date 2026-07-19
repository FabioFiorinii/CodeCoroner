import psycopg2
from django.conf import settings
from django.test.runner import DiscoverRunner

class PgVectorTestRunner(DiscoverRunner):
    def setup_databases(self, **kwargs):
        db = settings.DATABASES['default']
        db_name = db['NAME']
        test_db_name = f'test_{db_name}'

        conn = psycopg2.connect(
            dbname='postgres',
            user=db['USER'],
            password=db['PASSWORD'],
            host=db['HOST'],
            port=db.get('PORT', '5432'),
        )
        conn.autocommit = True
        cur = conn.cursor()
        cur.execute(
            "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = %s",
            (test_db_name,),
        )
        cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (test_db_name,))
        if not cur.fetchone():
            cur.execute(f'CREATE DATABASE "{test_db_name}"')
        cur.close()
        conn.close()

        conn = psycopg2.connect(
            dbname=test_db_name,
            user=db['USER'],
            password=db['PASSWORD'],
            host=db['HOST'],
            port=db.get('PORT', '5432'),
        )
        conn.autocommit = True
        cur = conn.cursor()
        cur.execute('CREATE EXTENSION IF NOT EXISTS vector')
        cur.close()
        conn.close()

        self.keepdb = True
        return super().setup_databases(**kwargs)
