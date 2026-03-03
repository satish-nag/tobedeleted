from .health import router as health_router
from .alerts import router as alerts_router
from .feedback import router as feedback_router

all_routers = [health_router, alerts_router, feedback_router]