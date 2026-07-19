from django.template.loader import render_to_string

class ReportService:
    def generate_markdown(self, analysis) -> str:
        context = {
            'analysis': analysis,
            'localization': getattr(analysis, 'bug_localization', None),
            'root_cause': getattr(analysis, 'root_cause', None),
            'patch': getattr(analysis, 'patch', None),
        }
        return render_to_string('report.md', context)

    def generate_html(self, markdown: str) -> str:
        import markdown as md
        return md.markdown(markdown, extensions=['fenced_code', 'tables'])

    def generate_pdf(self, html: str) -> bytes:
        pass
