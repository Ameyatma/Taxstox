"""Dashboard API — filing history, stats, user overview."""

from datetime import date
from decimal import Decimal

from fastapi import APIRouter, Depends
from src.auth.jwt import get_current_user, get_optional_user
from src.db.database import get_user_filings, create_filing

router = APIRouter(prefix="/api/v1", tags=["Dashboard"])


@router.get("/dashboard")
async def get_dashboard(current_user: dict = Depends(get_current_user)):
    """Get aggregated dashboard data for the authenticated user."""
    user_id = current_user["sub"]
    filings = get_user_filings(user_id)

    # Compute stats
    total_filings = len(filings)
    total_refunds = Decimal("0")
    total_tax_saved = Decimal("0")
    filed_count = 0
    draft_count = 0

    for f in filings:
        if f.get("status") == "filed":
            filed_count += 1
        elif f.get("status") == "draft":
            draft_count += 1
        # Parse financial summaries if available
        if f.get("tax_paid"):
            try:
                total_refunds += Decimal(f["tax_paid"])
            except Exception:
                pass

    # Days until filing deadline (July 31)
    today = date.today()
    deadline = date(today.year, 7, 31)
    if today > deadline:
        deadline = date(today.year + 1, 7, 31)
    days_remaining = (deadline - today).days

    # Tax calendar events
    tax_calendar = [
        {"date": f"{today.year}-07-31", "title": "ITR Filing Deadline", "type": "deadline"},
        {"date": f"{today.year}-12-31", "title": "Belated Return Deadline", "type": "deadline"},
        {"date": f"{today.year}-03-15", "title": "Advance Tax 4th Installment", "type": "payment"},
        {"date": f"{today.year + 1}-06-15", "title": f"Advance Tax 1st Installment (AY {today.year + 1}-{(today.year + 2) % 100:02d})", "type": "payment"},
    ]

    # Quick actions
    quick_actions = [
        {"id": "file_new", "label": "File New ITR", "icon": "description", "href": "/?filing=true", "primary": True},
        {"id": "regime_compare", "label": "Regime Calculator", "icon": "calculate", "href": "/tools"},
        {"id": "download_last", "label": "Download Last JSON", "icon": "download", "href": "#"},
        {"id": "revise_return", "label": "File Revised Return", "icon": "edit_note", "href": "#"},
    ]

    return {
        "stats": {
            "total_filings": total_filings,
            "total_refunds": str(total_refunds),
            "total_tax_saved": str(total_tax_saved),
            "filed_count": filed_count,
            "draft_count": draft_count,
            "days_remaining": days_remaining,
        },
        "quick_actions": quick_actions,
        "filings": filings,
        "tax_calendar": tax_calendar,
        "user_name": current_user.get("email", ""),
    }


@router.get("/filings")
async def list_filings(current_user: dict = Depends(get_current_user)):
    """Get all filings for the authenticated user."""
    return get_user_filings(current_user["sub"])


@router.post("/filings")
async def new_filing(
    assessment_year: str = "2026-27",
    itr_type: str = "ITR-2",
    current_user: dict = Depends(get_current_user),
):
    """Create a new filing record."""
    filing_id = create_filing(current_user["sub"], assessment_year, itr_type)
    return {"filing_id": filing_id, "assessment_year": assessment_year, "itr_type": itr_type}
