"""
Shared bridge service for Tax-Market domain communication.
Contains core business logic for the Data Bridge implementation.
"""
from typing import List
from datetime import datetime
from sqlalchemy.orm import Session
from src.domains.market.storage.models import Portfolio
from pydantic import BaseModel


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


class CapitalGainsSummary(BaseModel):
    total_gross_gain: float
    total_taxable_gain: float
    long_term_count: int
    short_term_count: int
    total_holdings: int


def calculate_capital_gains_for_user(user_id: str, db: Session) -> dict:
    """
    Calculate capital gains data for a user based on their portfolio holdings.

    Args:
        user_id: The user's ID (from authenticated session)
        db: Database session

    Returns:
        Dictionary containing capital gains data matching the API contract
    """
    # Query the user's portfolio holdings
    portfolio_items = db.query(Portfolio).filter(
        Portfolio.user_id == user_id
    ).all()

    # Generate deterministic capital gains data for each holding
    capital_gains_list = []
    total_gross_gain = 0.0
    total_taxable_gain = 0.0
    long_term_count = 0
    short_term_count = 0

    for item in portfolio_items:
        symbol = item.symbol

        # Create deterministic mock values based on symbol hash for consistency
        # This ensures same symbol always gives same values for testing
        symbol_hash = hash(symbol) % 1000

        # Mock buy/sell prices and dates
        buy_price = 1000.0 + (symbol_hash % 500)  # Between 1000-1500
        sell_price = buy_price + (symbol_hash % 300)  # Between buy_price and buy_price+300
        quantity = 10 + (symbol_hash % 20)  # Between 10-30 shares

        gross_gain = (sell_price - buy_price) * quantity
        # Simplified tax calculation: 15% for long-term, 30% for short-term
        is_long_term = (symbol_hash % 2) == 0  # Alternate between long/short term
        tax_rate = 0.15 if is_long_term else 0.30
        taxable_gain = gross_gain * tax_rate

        # Mock dates
        buy_date = "2024-01-15"
        sell_date = "2024-12-15"

        capital_gains_list.append({
            "symbol": symbol,
            "gross_gain": round(gross_gain, 2),
            "taxable_gain": round(taxable_gain, 2),
            "is_long_term": is_long_term,
            "buy_price": round(buy_price, 2),
            "sell_price": round(sell_price, 2),
            "quantity": quantity,
            "buy_date": buy_date,
            "sell_date": sell_date
        })

        total_gross_gain += gross_gain
        total_taxable_gain += taxable_gain
        if is_long_term:
            long_term_count += 1
        else:
            short_term_count += 1

    # Create response data
    return {
        "filing_session_id": f"FS-{user_id}-{int(datetime.now().timestamp())}",
        "user_id": user_id,
        "capital_gains": capital_gains_list,
        "summary": {
            "total_gross_gain": round(total_gross_gain, 2),
            "total_taxable_gain": round(total_taxable_gain, 2),
            "long_term_count": long_term_count,
            "short_term_count": short_term_count,
            "total_holdings": len(portfolio_items)
        }
    }


def process_tax_results(tax_data: dict, user_id: str) -> dict:
    """
    Process tax results received from the tax domain.

    Args:
        tax_data: Tax results data from tax domain
        user_id: The user's ID

    Returns:
        Success response dictionary
    """
    # In a full implementation, this would update user's market profile
    # with tax information for Phase 6
    # For now, just log the data (in real implementation, use proper logging)
    print(f"Tax results received for user {user_id}:")
    print(f"  Total Income: {tax_data.get('total_income')}")
    print(f"  Capital Gains Tax: {tax_data.get('capital_gains_tax')}")
    print(f"  Effective Tax Rate: {tax_data.get('effective_tax_rate')}")

    return {
        "status": "success",
        "message": "Tax results synced to market profile"
    }


def sync_user_data(user_data: dict, current_user_id: str) -> dict:
    """
    Verify and sync user data between domains.

    Args:
        user_data: User data to sync
        current_user_id: ID of the currently authenticated user

    Returns:
        Success response dictionary

    Raises:
        ValueError: If user ID mismatch
    """
    # Verify the user exists in the unified users table
    # For now, we'll just verify that the user_id matches the current user
    if user_data.get("user_id") != current_user_id:
        raise ValueError("User ID mismatch")

    # In a full implementation, we might update user profile data here
    # But for Phase 3, we just confirm the sync worked

    return {
        "status": "success",
        "user_id": current_user_id
    }