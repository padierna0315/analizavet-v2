import os
from pathlib import Path
from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML
import logfire
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.taller.service import TallerService
from app.config import settings


class ReportService:
    def __init__(self):
        self._taller = TallerService()

        # Setup Jinja2 explicitly for WeasyPrint
        template_dir = Path("app/templates/report")
        self._jinja_env = Environment(loader=FileSystemLoader(template_dir))

    async def generate_pdf(self, test_result_id: int, session: AsyncSession) -> bytes | None:
        """Fetch data, render HTML, and convert to PDF bytes."""

        # 1. Fetch full data
        data = await self._taller.get_test_result_full(test_result_id, session)
        if not data:
            return None

        # 2. Add absolute paths to images for WeasyPrint to find them
        # WeasyPrint requires either absolute paths, full URLs, or base URLs to load local files
        current_dir = Path.cwd().absolute()
        for img in data["images"]:
            # file_path in DB is like "images/Kitty_LauraCepeda/.../Leucocitos_Main.jpg"
            absolute_path = current_dir / img["file_path"]
            img["absolute_path"] = str(absolute_path)

        # 3. Resolve theme path
        theme_name = getattr(settings, "PDF_THEME", "huellas_lab")
        theme_path = current_dir / "app" / "static" / "css" / "themes" / f"{theme_name}.css"

        # 4. Render HTML
        template = self._jinja_env.get_template("report.html")
        rendered_html = template.render(
            patient=data["patient"],
            test_result=data["test_result"],
            lab_values=data["lab_values"],
            summary=data["summary"],
            images=data["images"],
            theme_path=str(theme_path)  # Pass the theme path!
        )

        # 5. Convert to PDF using WeasyPrint
        try:
            pdf_bytes = HTML(string=rendered_html).write_pdf()
            return pdf_bytes
        except Exception as e:
            logfire.error(f"Error generando PDF: {e}")
            raise RuntimeError(f"No se pudo generar el PDF: {e}")
