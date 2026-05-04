from fastapi import APIRouter, HTTPException, status, Request
from fastapi.responses import HTMLResponse
import logfire

# Import global variables and templates locally within functions to avoid circular imports
# from app.main import _adapters, _mllp_running, templates

router = APIRouter(prefix="/api/mllp", tags=["MLLP Control"])

@router.post("/start", status_code=status.HTTP_200_OK)
async def start_mllp_adapters():
    from app.main import _adapters, _mllp_running # Local import
    global _mllp_running
    if _mllp_running:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="MLLP servers are already running."
        )

    logfire.info("Attempting to start MLLP adapters...")
    try:
        if not _adapters:
            # Re-initialize adapters if they were not started during lifespan (e.g., MLLP_ENABLED=False initially)
            logfire.info("Adapters list is empty. Initializing MLLP adapters.")
            from app.satellites.ozelle import OzelleAdapter
            from app.satellites.fujifilm import FujifilmAdapter
            from app.config import settings
            
            ozelle_port = getattr(settings, "OZELLE_PORT", 6000)
            fujifilm_port = getattr(settings, "FUJIFILM_PORT", 6001)

            _adapters.append(OzelleAdapter(port=ozelle_port))
            _adapters.append(FujifilmAdapter(port=fujifilm_port))

        for adapter in _adapters:
            if not adapter.is_running():
                logfire.info(f"Starting adapter: {adapter.get_source_name()}")
                await adapter.start()
        _mllp_running = True
        logfire.info("MLLP adapters started successfully.")
        return {"message": "MLLP servers started successfully."}
    except Exception as e:
        logfire.error(f"Failed to start MLLP adapters: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start MLLP servers: {str(e)}"
        )

@router.post("/stop", status_code=status.HTTP_200_OK)
async def stop_mllp_adapters():
    from app.main import _adapters, _mllp_running # Local import
    global _mllp_running
    if not _mllp_running:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="MLLP servers are not running."
        )

    logfire.info("Attempting to stop MLLP adapters...")
    try:
        for adapter in _adapters:
            if adapter.is_running():
                logfire.info(f"Stopping adapter: {adapter.get_source_name()}")
                await adapter.stop()
        _mllp_running = False
        logfire.info("MLLP adapters stopped successfully.")
        return {"message": "MLLP servers stopped successfully."}
    except Exception as e:
        logfire.error(f"Failed to stop MLLP adapters: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to stop MLLP servers: {str(e)}"
        )

@router.get("/status", status_code=status.HTTP_200_OK)
async def get_mllp_status():
    from app.main import _mllp_running # Local import
    return {"running": _mllp_running}

@router.get("/button", response_class=HTMLResponse)
async def get_mllp_button(request: Request): # Add request parameter for templates
    """Returns the HTMX-enabled MLLP status button."""
    from app.main import templates, _mllp_running # Local import
    return templates.TemplateResponse(
        "mllp_status_button.html", {"request": request, "mllp_running": _mllp_running}
    )


