"""
API endpoints router configuration.

This module configures the main API router by including all endpoint-specific routers.
It serves as the central point for organizing and exposing the application's API endpoints.
"""

from fastapi import APIRouter
from .documents import router as documents_router
from .contracts import router as contracts_router
from .contract_templates import router as contract_templates_router

router = APIRouter()
router.include_router(documents_router, tags=["documents"])
router.include_router(contracts_router, tags=["contracts"])
router.include_router(contract_templates_router, tags=["contract_templates"])