import uuid
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone

from analyses.models import (
    Analysis,
    AnalysisRun,
    BugLocalization,
    FixSuggestion,
    Report,
    RootCause,
    SuspiciousFileScore,
)
from projects.models import Project, ProjectMembership
from repositories.models import Repository

from .seed_base import ADMIN_EMAIL, ADMIN_PASSWORD, ensure_base

User = get_user_model()

FIXED_NOW = timezone.now() - timedelta(hours=2)


class Command(BaseCommand):
    help = 'Seed the database with demo data for showcase'

    def handle(self, *_args, **_options):  # noqa: ARG002
        self.stdout.write('Seeding demo data...')

        admin, default_group, _ = ensure_base()
        self.stdout.write(f'  Base user: {admin.email}')

        bob, _ = User.objects.get_or_create(
            email='bob@codecoroner.dev',
            defaults={'username': 'bob'},
        )
        bob.is_superuser = True
        bob.set_password('bobpass')
        bob.save()
        bob.groups.add(default_group)
        self.stdout.write('  Test user: bob@codecoroner.dev (superuser)')

        alice, _ = User.objects.get_or_create(
            email='alice@codecoroner.dev',
            defaults={'username': 'alice'},
        )
        alice.is_superuser = False
        alice.set_password('alicepass')
        alice.save()
        alice.groups.add(default_group)
        self.stdout.write('  Test user: alice@codecoroner.dev')

        project, _ = Project.objects.get_or_create(
            name='Flask Demo',
            defaults={
                'description': 'Demo project analyzing a Flask web application for common bugs',
                'created_by': admin,
            },
        )
        ProjectMembership.objects.get_or_create(
            project=project,
            user=admin,
            defaults={'role': 'owner'},
        )
        project.groups.add(default_group)
        self.stdout.write(f'  Project: {project.name}')

        repo, _ = Repository.objects.get_or_create(
            git_url='https://github.com/pallets/flask.git',
            defaults={
                'git_branch': 'main',
                'status': Repository.Status.INDEXED,
                'file_count': 187,
                'total_bytes': 2_456_789,
            },
        )
        repo.assigned_projects.add(project)
        repo.groups.add(default_group)
        self.stdout.write(f'  Repository: {repo.git_url}')

        analysis_id = uuid.UUID('00000000-0000-4000-8000-000000000001')
        analysis, created = Analysis.objects.get_or_create(
            id=analysis_id,
            defaults={
                'user': admin,
                'project': project,
                'repository': repo,
                'title': 'TemplateNotFound on index route',
                'error_context': {
                    'error_message': 'jinja2.exceptions.TemplateNotFound: index.html',
                    'environment': 'Flask 3.1, Python 3.13, Jinja2 3.1.5',
                    'description': 'When accessing the root URL (/), the application raises a TemplateNotFound exception. The index route handler calls render_template("index.html") but the template file is placed in the wrong directory.',
                    'stacktrace': """Traceback (most recent call last):
  File "/app/venv/lib/python3.13/site-packages/flask/app.py", line 1521, in wsgi_app
    response = self.full_dispatch_request()
  File "/app/venv/lib/python3.13/site-packages/flask/app.py", line 876, in full_dispatch_request
    return self.finalize_request(rv)
  File "/app/venv/lib/python3.13/site-packages/flask/app.py", line 895, in finalize_request
    response = self.process_response(response)
  File "/app/venv/lib/python3.13/site-packages/flask/app.py", line 1200, in process_response
    response = self.after_request_funcs[request.url_rule.rule](response)
  File "/app/app.py", line 12, in index
    return render_template("index.html")
  File "/app/venv/lib/python3.13/site-packages/flask/templating.py", line 152, in render_template
    return _render(app, template, context)
  File "/app/venv/lib/python3.13/site-packages/flask/templating.py", line 120, in _render
    raise TemplateNotFound(template)
jinja2.exceptions.TemplateNotFound: TemplateNotFound: index.html""",
                    'steps_to_reproduce': '1. Start the Flask app with "python app.py"\n2. Open http://localhost:5000 in browser\n3. Observe 500 Internal Server Error\n4. Check server logs for TemplateNotFound',
                    'logs': ' * Running on http://127.0.0.1:5000\n[2026-07-28 15:23:01] GET / → 500 Internal Server Error\n',
                },
                'status': Analysis.Status.COMPLETED,
                'created_at': FIXED_NOW,
                'completed_at': FIXED_NOW + timedelta(seconds=89),
                'duration_seconds': 89,
            },
        )
        if created:
            self._create_runs(analysis)
            self._create_bug_localization(analysis)
            self._create_root_cause(analysis)
            self._create_fix_suggestion(analysis)
            self._create_report(analysis)
            self.stdout.write(f'  Analysis: {analysis.title} ({analysis.status})')
        else:
            self.stdout.write(f'  Analysis already exists: {analysis.title}')

        self.stdout.write(
            self.style.SUCCESS(
                f'\nDemo data ready! Login with: {ADMIN_EMAIL} / {ADMIN_PASSWORD} '
                '(bob@codecoroner.dev / bobpass, alice@codecoroner.dev / alicepass)'
            )
        )

    def _create_runs(self, analysis):
        steps = [
            ('ensure_repo_indexed', 'completed', 5),
            ('analyze_input', 'completed', 8),
            ('bug_localization', 'completed', 22),
            ('root_cause', 'completed', 35),
            ('generate_report', 'completed', 12),
            ('fix_suggestion', 'completed', 7),
        ]
        elapsed = 0
        for step, status, duration in steps:
            start = FIXED_NOW + timedelta(seconds=elapsed)
            elapsed += duration
            end = FIXED_NOW + timedelta(seconds=elapsed)
            AnalysisRun.objects.update_or_create(
                analysis=analysis,
                step=step,
                defaults={
                    'status': status,
                    'started_at': start,
                    'completed_at': end,
                },
            )

    def _create_bug_localization(self, analysis):
        bl, _ = BugLocalization.objects.get_or_create(
            analysis=analysis,
            defaults={
                'summary': 'The application crashes because render_template() looks for templates in Flask\'s default "templates/" directory, but the template file index.html is located at the project root instead of inside the templates/ folder.',
            },
        )
        suspicious = [
            (
                'app/app.py',
                0.92,
                'Line 12 calls render_template("index.html") — this is where the crash originates',
                1,
            ),
            (
                'app/templates/index.html',
                0.85,
                'Template file exists but is in the wrong location. Flask expects templates/template_name',
                2,
            ),
            (
                'venv/lib/python3.13/site-packages/flask/templating.py',
                0.45,
                'The _render() function raises TemplateNotFound when the template path is wrong — standard Flask behavior',
                3,
            ),
        ]
        for file_path, score, evidence, rank in suspicious:
            SuspiciousFileScore.objects.get_or_create(
                localization=bl,
                file_path=file_path,
                defaults={
                    'suspicion_score': score,
                    'evidence': evidence,
                    'rank': rank,
                    'matched_lines': [12] if rank == 1 else [],
                },
            )

    def _create_root_cause(self, analysis):
        RootCause.objects.get_or_create(
            analysis=analysis,
            defaults={
                'summary': 'Missing templates/ directory structure — index.html is at project root instead of app/templates/index.html',
                'root_file': 'app/app.py',
                'root_line': 12,
                'cause_chain': '1. User requests GET /\n2. Flask routes to index() in app.py:12\n3. index() calls render_template("index.html")\n4. Flask\'s template loader searches app/templates/ for index.html\n5. The file exists but at app/index.html (wrong directory)\n6. jinja2 raises TemplateNotFound\n7. Flask returns 500 Internal Server Error',
                'confidence': 0.94,
                'reasoning': 'The stacktrace clearly shows the crash at render_template("index.html") in app.py:12. The app follows Flask conventions but the template directory structure is incorrect. Flask by default looks for templates in a "templates/" subdirectory relative to the app package. Moving index.html into app/templates/ resolves the issue. The fix is minimal, safe, and follows Flask best practices.',
            },
        )

    def _create_fix_suggestion(self, analysis):
        FixSuggestion.objects.get_or_create(
            analysis=analysis,
            defaults={
                'diff': """--- a/app/app.py
+++ b/app/app.py
@@ -9,7 +9,7 @@ app = Flask(__name__)

 @app.route("/")
 def index():
-    return render_template("index.html")
+    return render_template("main/index.html")

--- /dev/null
+++ b/app/templates/main/index.html
@@ -0,0 +1,12 @@
+<!DOCTYPE html>
+<html>
+<head>
+    <title>Flask Demo</title>
+</head>
+<body>
+    <h1>Hello, Flask!</h1>
+    <p>Application is running correctly.</p>
+</body>
+</html>""",
                'plan': """File: app/app.py
Line 12: change render_template("index.html") → render_template("main/index.html")

File: (create new) app/templates/main/index.html
Lines 1-12: create a basic HTML template with DOCTYPE, html, head, body, h1 "Hello, Flask!" and a paragraph.

Move any existing index.html from app/ into app/templates/main/index.html.
No other files need modification.""",
                'explanation': """The bug is a directory structure mismatch. Flask's default template loader looks for templates inside a "templates/" directory under the app package. The index.html file was placed at the project root (app/index.html) instead of app/templates/index.html, causing jinja2 to raise TemplateNotFound.

The fix moves the template into the correct directory and optionally organizes it under a "main/" subdirectory for better route separation. The render_template() call is updated to reflect the new path.

No side effects are expected — this only affects the template resolution path. If other routes also use templates, verify they follow the same convention. The app logic and data flow remain unchanged.""",
            },
        )

    def _create_report(self, analysis):
        Report.objects.get_or_create(
            analysis=analysis,
            defaults={
                'format': 'markdown',
                'markdown': """# Analysis Report: TemplateNotFound on index route

## Summary
The application crashes with a `jinja2.exceptions.TemplateNotFound` when accessing the root URL. The root cause is a missing `templates/` directory structure.

## Error Context
- **Error**: jinja2.exceptions.TemplateNotFound: index.html
- **Environment**: Flask 3.1, Python 3.13, Jinja2 3.1.5
- **Endpoint**: GET /

## Bug Localization
| File | Suspicion | Evidence |
|------|-----------|----------|
| app/app.py | 92% | Line 12 calls `render_template("index.html")` — crash origin |
| app/templates/index.html | 85% | Template file exists in wrong location |
| flask/templating.py | 45% | Standard Flask exception — not a bug in Flask itself |

## Root Cause
**File**: app/app.py:12
**Confidence**: 94%

render_template() looks for templates inside a "templates/" directory (Flask default), but index.html is at the project root instead of app/templates/index.html.

## Fix Suggestion
1. Create directory `app/templates/`
2. Move `index.html` into `app/templates/`
3. No code changes required — Flask's default loader will find it automatically

## Recommendation
Always place Flask templates inside a `templates/` subdirectory within the app package. This is a Flask convention that avoids TemplateNotFound errors.
""",
            },
        )
