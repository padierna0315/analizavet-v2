import os
import sys
import subprocess
from pathlib import Path
from jinja2 import Environment, FileSystemLoader
import logfire
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.taller.service import TallerService
from app.config import settings

# Directorio raíz del proyecto (donde está app/)
_PROJECT_ROOT = Path(__file__).parent.parent.parent.parent


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

        # 2. Filtrar solo imágenes relevantes para el PDF
        # _Main = imagen principal del parámetro (morfología)
        # _Histo = histograma
        # _Distribution = distribución celular
        # Las _Part1, _Part2... son fragmentos internos — NO van en el PDF
        PDF_IMAGE_SUFFIXES = ("_Main.jpg", "_Histo.jpg", "_Distribution.jpg")
        data["images"] = [
            img for img in data["images"]
            if img.get("is_included_in_report")
            and any(img.get("file_path", "").endswith(s) for s in PDF_IMAGE_SUFFIXES)
        ]

        # 3. Add absolute paths to images for WeasyPrint to find them
        current_dir = Path.cwd().absolute()
        for img in data["images"]:
            absolute_path = (current_dir / img["file_path"]).as_uri()
            img["absolute_path"] = absolute_path

        # 3. Resolve theme path and read CSS content
        theme_name = getattr(settings, "PDF_THEME", "huellas_lab")
        theme_filepath = current_dir / "app" / "static" / "css" / "themes" / f"{theme_name}.css"
        
        try:
            with open(theme_filepath, 'r') as f:
                theme_css_content = f.read()
        except FileNotFoundError:
            logfire.error(f"Archivo CSS de tema no encontrado: {theme_filepath}")
            theme_css_content = "" # Fallback to empty CSS

        # 4. Render HTML
        template = self._jinja_env.get_template("report.html")
        rendered_html = template.render(
            patient=data["patient"],
            test_result=data["test_result"],
            lab_values=data["lab_values"],
            summary=data["summary"],
            images=data["images"],
            theme_css=theme_css_content # Pass the CSS content directly
        )

        # 5. WeasyPrint en subprocess separado — evita conflicto con uvicorn --reload
        try:
            env = os.environ.copy()
            env["PYTHONPATH"] = str(_PROJECT_ROOT)
            result = subprocess.run(
                [sys.executable, "-m", "app.domains.reports.pdf_worker"],
                input=rendered_html.encode("utf-8"),
                capture_output=True,
                timeout=60,
                cwd=str(_PROJECT_ROOT),
                env=env,
            )
            if result.returncode != 0:
                error = result.stderr.decode("utf-8", errors="ignore")
                logfire.error(f"PDF worker falló: {error}")
                raise RuntimeError(f"Error en PDF worker: {error[:200]}")
            return result.stdout
        except subprocess.TimeoutExpired:
            raise RuntimeError("Timeout generando PDF (>60s)")
        except Exception as e:
            logfire.error(f"Error generando PDF: {e}")
            raise RuntimeError(f"No se pudo generar el PDF: {e}")

    def generate_pdf_sync(self, data: dict) -> bytes | None:
        """
        Versión síncrona pura — recibe datos ya cargados, no necesita DB.
        Diseñada para ejecutarse en un ThreadPoolExecutor desde el endpoint async.
        """
        PDF_IMAGE_SUFFIXES = ("_Main.jpg", "_Histo.jpg", "_Distribution.jpg")
        images = [
            img for img in data.get("images", [])
            if img.get("is_included_in_report")
            and any(img.get("file_path", "").endswith(s) for s in PDF_IMAGE_SUFFIXES)
        ]

        current_dir = Path.cwd().absolute()
        for img in images:
            img["absolute_path"] = (current_dir / img["file_path"]).as_uri()

        theme_name = getattr(settings, "PDF_THEME", "huellas_lab")
        theme_filepath = current_dir / "app" / "static" / "css" / "themes" / f"{theme_name}.css"
        try:
            theme_css_content = theme_filepath.read_text()
        except FileNotFoundError:
            theme_css_content = ""

        template = self._jinja_env.get_template("report.html")
        rendered_html = template.render(
            patient=data["patient"],
            test_result=data["test_result"],
            lab_values=data["lab_values"],
            summary=data.get("summary", {}),
            images=images,
            theme_css=theme_css_content,
        )

        from weasyprint import HTML
        return HTML(string=rendered_html).write_pdf()