import psycopg2
from django.db.backends.base.creation import BaseDatabaseCreation


def _create_test_db(self, verbosity, autoclobber, keepdb=False):
    test_database_name = _orig_create_test_db(self, verbosity, autoclobber, keepdb)
    params = self.connection.settings_dict
    conn = psycopg2.connect(
        dbname=test_database_name,
        user=params['USER'],
        password=params['PASSWORD'],
        host=params['HOST'],
        port=params.get('PORT') or '5432',
    )
    conn.autocommit = True
    with conn.cursor() as cur:
        cur.execute('CREATE EXTENSION IF NOT EXISTS vector')
    conn.close()
    return test_database_name


_orig_create_test_db = BaseDatabaseCreation._create_test_db  # type: ignore[attr-defined]
BaseDatabaseCreation._create_test_db = _create_test_db  # type: ignore[attr-defined]
