from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ('repositories', '0005_repository_summary'),
    ]

    operations = [
        migrations.RunSQL(
            sql=(
                'CREATE INDEX IF NOT EXISTS repositories_chunkembedding_embedding_hnsw '
                'ON repositories_chunkembedding '
                'USING hnsw (embedding vector_cosine_ops)'
            ),
            reverse_sql='DROP INDEX IF EXISTS repositories_chunkembedding_embedding_hnsw',
        ),
    ]
