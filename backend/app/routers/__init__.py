"""API routers package."""

from .deals import router as deals_router
from .flips import router as flips_router
from .stats import router as stats_router
from .ebay import router as ebay_router

__all__ = ["deals_router", "flips_router", "stats_router", "ebay_router"]
