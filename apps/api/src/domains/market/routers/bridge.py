from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from pydantic import BaseModel
from src.auth.jwt import get_current_user
from src.domains.market.storage.database import get_db
from sqlalchemy.orm import Session
from src.domains.shared.bridge_service import (
    calculate_capital_gains_for_user,
    process_tax_results,
    sync_user_data
)

router = APIRouter()


# Response models for the bridge endpoints
class CapitalGainsItem(BaseModel):
    symbol: str
    gross_gain: float
    taxable_gain: float
    is_long_term: bool
    buy_price: float
    sell_price: float
    quantity: int
    buy_date: str
    sell_date: str


class CapitalGainsResponse(BaseModel):
    filing_session_id: str
    user_id: str
    capital_gains: List[CapitalGainsItem]
    summary: dict


class TaxResultsRequest(BaseModel):
    total_income: float
    capital_gains_tax: float
    effective_tax_rate: float


class SyncUserRequest(BaseModel):
    user_id: str
    email: str
    name: str


@router.get("/capital-gains", response_model=CapitalGainsResponse)
async def get_capital_gains(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    GET /capital-gains
    Generate capital gains data based on user's portfolio holdings.
    Delegates to shared bridge service for business logic.
    """
    user_id = current_user["sub"]
    return calculate_capital_gains_for_user(user_id, db)


@router.post("/tax-results", status_code=status.HTTP_200_OK)
async def post_tax_results(
    tax_data: TaxResultsRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    POST /tax-results
    Accept tax results from tax domain and sync to market profile.
    Delegates to shared bridge service for business logic.
    """
    return process_tax_results(tax_data.dict(), current_user["sub"])


@router.post("/sync-user", status_code=status.HTTP_200_OK)
async def sync_user(
    user_data: SyncUserRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    POST /sync-user
    Verify and sync user data between domains.
    Delegates to shared bridge service for business logic.
    """
    return sync_user_data(user_data.dict(), current_user["sub"])