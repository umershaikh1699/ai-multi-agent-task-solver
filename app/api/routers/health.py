from fastapi import APIRouter

router = APIRouter(tags=["meta"])


# Health check endpoint
@router.get("/health", summary="Health check")
async def health() -> dict[str, str]:
    return {"status": "ok"}
