"""
site_properties.py — Router for site properties endpoint.
"""

from fastapi import APIRouter
from ..services import site_properties_service

router = APIRouter(tags=["Site Properties"])

@router.get("/site-properties")
def site_properties():
    return site_properties_service.get_site_properties()