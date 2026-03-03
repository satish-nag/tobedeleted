from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get(
    "/healthz",
    summary="Liveness/readiness probe",
    description="Minimal response for Kubernetes probes.",
)
async def healthz():
    return {"status": "ok"}