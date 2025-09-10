"""
tollgate_prompts.py — Router for tollgate prompts endpoint.
"""

from fastapi import APIRouter
from app.services import tollgate_service

router = APIRouter(tags=["Tollgate Prompts"])

@router.get("/tollgate-prompts")
def tollgate_prompts():
    return tollgate_service.get_tollgate_prompts()