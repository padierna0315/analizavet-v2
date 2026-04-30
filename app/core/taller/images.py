import base64
import re
import unicodedata
from datetime import datetime
from pathlib import Path
import logfire
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.models.patient_image import PatientImage
from app.schemas.taller import ImageUploadRequest, ImageUploadResult
from app.config import settings
from app.core.taller.triage import seleccionar_mejores_imagenes


# Translation table for IMAGE parameter codes → Spanish name.
#
# Translation table: image BASE code → Spanish name.
#
# ✅ VERIFICADO contra log real del Ozelle EHVT-50
#    (log_laboratorio_17 de abril.txt — 119 segmentos OBX|ED, 12 resultados reales)
#
# El Ozelle envía el identificador completo en OBX[3]: "WBC_Main", "LYM_Part3", etc.
# Esta tabla usa SOLO el código base (sin sufijo).
# Ejemplo: "WBC_Main" → split → base="WBC" → "Leucocitos" → archivo: "Leucocitos_Main.jpg"
IMAGE_PARAMETER_TRANSLATION = {
    # Hematología — Ozelle EHVT-50 (confirmados en log real)
    "WBC": "Leucocitos",
    "RBC": "Eritrocitos",
    "PLT": "Plaquetas",
    "LYM": "Linfocitos",
    "EOS": "Eosinofilos",
    "MON": "Monocitos",
    "BAS": "Basofilos",
    "NST": "Bandas",
    "NSG": "Neutrofilos_Inmaduros",
    "NSH": "Neutrofilos_Hiperseg",
    "RET": "Reticulocitos",
    "SPH": "Esferocitos",
    "ETG": "Celulas_Diana",
    "APLT": "Plaquetas_Agregadas",
    "P-LCC": "Plaquetas_Grandes",
    "P-LCR": "Plaquetas_Critica",
    "HDW-CV": "Ancho_Distribucion_Plaquetas",
    "HDW-SD": "Desviacion_Ancho_Plaquetas",
    # Distribuciones combinadas (confirmadas en log real)
    "RBC_PLT": "Distribucion_RBC_PLT",
    # Hematología — Códigos adicionales del log (confirmados en log real)
    "NEU": "Neutrofilos",
    "HGB": "Hemoglobina",
    "HCT": "Hematocrito",
    "MCV": "Volumen_Corpuscular_Medio",
    "MCH": "Corpuscular_Medio",
    "MCHC": "Corpuscular_Medio_Cromica",
    "RDW-CV": "Ancho_Distribucion_Corpuscular",
    "RDW-SD": "Desviacion_Distribucion_Corpuscular",
    "FECES": "Heces",
    # Heces — Coproscópico (confirmados en log real — paciente Rafael)
    "BACI": "Bacterias",
    "COS": "Cocos",
    "YEA": "Levaduras",
    "ANE": "Nematodos",
    "ALE": "Anquilostomas",
    "TRE": "Trichuris",
    "DIP": "Cestodos",
    # Fujifilm NX600 (no confirmados aún — pendiente conectar máquina)
    "ALT": "ALT",
    "AST": "AST",
    "ALP": "Fosfatasa_Alcalina",
    "GGT": "GGT",
    "CPK": "CPK",
    "BUN": "Nitrogeno_Ureico",
    "CRE": "Creatinina",
    "GLU": "Glucosa",
}

# Suffixes used by Ozelle in OBX identifiers (confirmed from real log)
_KNOWN_SUFFIXES = {"Main", "Histo", "Distribution"}
_PART_PATTERN = re.compile(r"_Part(\d+)$")


def _parse_obs_identifier(obs_id: str) -> tuple[str, str]:
    """Parse Ozelle OBX identifier into (base_code, suffix).

    Examples:
        "WBC_Main"             → ("WBC", "Main")
        "LYM_Part3"            → ("LYM", "Part3")
        "PLT_Histo"            → ("PLT", "Histo")
        "RBC_PLT_Distribution" → ("RBC_PLT", "Distribution")
        "P-LCC_Main"           → ("P-LCC", "Main")
        "FECES_Distribution"   → ("FECES", "Distribution")
    """
    # Check for _PartN suffix first
    part_match = _PART_PATTERN.search(obs_id)
    if part_match:
        suffix = f"Part{part_match.group(1)}"
        base = obs_id[:part_match.start()]
        return base, suffix

    # Check for known word suffixes (_Main, _Histo, _Distribution)
    for suffix in _KNOWN_SUFFIXES:
        if obs_id.endswith(f"_{suffix}"):
            base = obs_id[:-(len(suffix) + 1)]
            return base, suffix

    # No known suffix — return full identifier as base, no suffix
    return obs_id, ""


def _translate_base_code(base_code: str) -> str:
    """Translate image base code to Spanish name.
    Falls back to lowercase code with warning if not found.
    """
    if base_code in IMAGE_PARAMETER_TRANSLATION:
        return IMAGE_PARAMETER_TRANSLATION[base_code]
    logfire.warning(
        f"Código de imagen desconocido: '{base_code}'. "
        f"Agregar a IMAGE_PARAMETER_TRANSLATION en images.py."
    )
    return f"{base_code.lower()}_desconocido"


def _build_filename(obs_identifier: str) -> tuple[str, str]:
    """Parse OBX identifier and build Spanish filename.

    Returns (filename, parameter_name_es).

    Examples:
        "WBC_Main"             → ("Leucocitos_Main.jpg", "Leucocitos")
        "LYM_Part3"            → ("Linfocitos_Part3.jpg", "Linfocitos")
        "PLT_Histo"            → ("Plaquetas_Histo.jpg", "Plaquetas")
        "RBC_PLT_Distribution" → ("Distribucion_RBC_PLT_Distribution.jpg", "Distribucion_RBC_PLT")
        "BACI_Main"            → ("Bacterias_Main.jpg", "Bacterias")
    """
    base_code, suffix = _parse_obs_identifier(obs_identifier)
    name_es = _translate_base_code(base_code)
    if suffix:
        return f"{name_es}_{suffix}.jpg", name_es
    return f"{name_es}.jpg", name_es


def _sanitize_folder_name(text: str) -> str:
    """Remove accents and spaces for safe folder/file names.

    'Laura Cepeda'  → 'LauraCepeda'
    'niña'          → 'Nina'
    'Señora Ríos'   → 'SenoraRios'

    Better than Ozelle's approach (ni_a, Se_ora_R_os).
    """
    nfd = unicodedata.normalize("NFD", text)
    ascii_text = "".join(c for c in nfd if unicodedata.category(c) != "Mn")
    return ascii_text.replace(" ", "")


def _build_patient_folder(
    patient_name: str,
    owner_name: str,
    received_at: datetime,
    base_dir: str,
) -> Path:
    """Build the patient-specific folder path.

    Pattern: {base_dir}/{PatientName}_{OwnerName}/{YYYYMMDD}/
    Example: images/Kitty_LauraCepeda/20260424/
    """
    safe_patient = _sanitize_folder_name(patient_name)
    safe_owner = _sanitize_folder_name(owner_name)
    date_str = received_at.strftime("%Y%m%d")
    folder = Path(base_dir) / f"{safe_patient}_{safe_owner}" / date_str
    return folder


class ImageHandlingService:
    """Handles saving of histogram images from satellites.

    Images are stored on disk, NOT in the database.
    The database only stores the file path + metadata.

    Folder structure:
        images/{PatientName}_{OwnerName}/{YYYYMMDD}/{ParameterNameEs}_{Suffix}.jpg

    Examples:
        images/Kitty_LauraCepeda/20260424/Leucocitos_Main.jpg
        images/Kitty_LauraCepeda/20260424/Linfocitos_Part3.jpg
        images/Kitty_LauraCepeda/20260424/Plaquetas_Histo.jpg
        images/Rafael_Laura/20260424/Bacterias_Main.jpg  ← coproscópico
    """

    def __init__(self):
        self._base_dir = getattr(settings, "IMAGES_DIR", "./images")

    async def save_images(
        self,
        request: ImageUploadRequest,
        session: AsyncSession,
    ) -> ImageUploadResult:
        """Decode Base64 images and save to disk + DB."""

        patient_folder = _build_patient_folder(
            request.patient_name,
            request.owner_name,
            request.received_at,
            self._base_dir,
        )
        patient_folder.mkdir(parents=True, exist_ok=True)

        saved = []
        failed = []
        # Track obs_identifiers seen in this batch to detect duplicates
        seen_identifiers: set[str] = set()

        for image_item in request.images:
            # Detect duplicate obs_identifier in same batch
            if image_item.obs_identifier in seen_identifiers:
                logfire.warning(
                    f"obs_identifier duplicado en el batch: '{image_item.obs_identifier}'. "
                    f"Se omite para evitar sobrescritura silenciosa."
                )
                failed.append({
                    "obs_identifier": image_item.obs_identifier,
                    "error": f"obs_identifier duplicado en el batch: '{image_item.obs_identifier}'",
                })
                continue
            seen_identifiers.add(image_item.obs_identifier)

            try:
                filename, name_es = _build_filename(image_item.obs_identifier)
                _, suffix = _parse_obs_identifier(image_item.obs_identifier)
                base_code, _ = _parse_obs_identifier(image_item.obs_identifier)

                image_data = self._decode_base64(image_item.base64_data)
                file_path = patient_folder / filename

                # Detect if file already exists (cross-batch overwrite protection)
                if file_path.exists():
                    logfire.warning(
                        f"Archivo ya existe: {file_path}. "
                        f"Se sobrescribe — verificar si es intencional."
                    )

                file_path.write_bytes(image_data)

                db_image = PatientImage(
                    test_result_id=request.test_result_id,
                    parameter_code=image_item.obs_identifier,   # full: "WBC_Main"
                    parameter_name_es=name_es,                  # "Leucocitos"
                    file_path=str(file_path),
                    patient_folder=str(patient_folder),
                    image_type=suffix or "unknown",             # "Main", "Part3", etc.
                    file_size_bytes=len(image_data),
                )
                session.add(db_image)

                saved.append({
                    "obs_identifier": image_item.obs_identifier,
                    "parameter_name_es": name_es,
                    "file_path": str(file_path),
                })
                logfire.debug(f"Imagen guardada: {file_path}")

            except Exception as e:
                logfire.error(
                    f"Error guardando imagen para "
                    f"{image_item.obs_identifier}: {e}"
                )
                failed.append({
                    "obs_identifier": image_item.obs_identifier,
                    "error": str(e),
                })

        # Apply image triage BEFORE committing — modifies is_included_in_report in-place
        if saved:
            all_images = await session.execute(
                select(PatientImage).where(
                    PatientImage.test_result_id == request.test_result_id
                )
            )
            img_list = list(all_images.scalars().all())
            seleccionar_mejores_imagenes(img_list)
            for img in img_list:
                session.add(img)
            await session.commit()

        logfire.info(
            f"Imágenes TestResult {request.test_result_id}: "
            f"{len(saved)} guardadas, {len(failed)} fallidas"
        )

        return ImageUploadResult(
            test_result_id=request.test_result_id,
            saved=saved,
            failed=failed,
            total_saved=len(saved),
            total_failed=len(failed),
        )

    def _decode_base64(self, data: str) -> bytes:
        """Decode Base64 string to bytes. Handles padding issues."""
        data = data.strip()
        if data.startswith("data:"):
            data = data.split(",", 1)[1]
        missing_padding = len(data) % 4
        if missing_padding:
            data += "=" * (4 - missing_padding)
        try:
            return base64.b64decode(data, validate=True)
        except Exception as e:
            raise ValueError(f"Base64 inválido: {e}")
