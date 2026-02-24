from fastapi import APIRouter

router = APIRouter(tags=["web-utils"])


@router.get("/health")
async def health_check() -> dict:
    """Health check endpoint."""
    return {"status": "healthy", "service": "CodeLeash"}
