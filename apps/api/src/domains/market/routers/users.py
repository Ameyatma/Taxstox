from fastapi import APIRouter, Depends, HTTPException, status, Response
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import List
from datetime import timedelta
from pydantic import BaseModel
from src.auth.jwt import (
    create_access_token,
    get_current_user,
)
from src.db.database import verify_password, hash_password
from src.domains.market.storage.database import get_db
from src.domains.market.storage.models import User, Portfolio, RecommendationSignal, NewsCatalyst


router = APIRouter()


class UserRegister(BaseModel):
    email: str
    password: str


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register_user(
    user_data: UserRegister,
    db: Session = Depends(get_db)
):
    """Register a new user."""
    # Check if user already exists
    db_user = db.query(User).filter(User.email == user_data.email).first()
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    # Create new user
    hashed_password = hash_password(user_data.password)
    new_user = User(email=user_data.email, hashed_password=hashed_password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {"message": "User created successfully", "user_id": new_user.id}


@router.post("/token", response_model=dict)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
    response: Response = None
):
    """OAuth2 compatible token login, get an access token for future requests.
    Sets httpOnly cookie for dual-transport authentication."""
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=30)
    access_token = create_access_token(
        data={"sub": user.id}, expires_delta=access_token_expires
    )

    # Set httpOnly cookie for dual-transport support (if response object is provided)
    if response is not None:
        response.set_cookie(
            key="taxstox_token",  # Canonical Taxstox cookie name
            value=access_token,
            httponly=True,
            max_age=30 * 60,  # 30 minutes
            expires=30 * 60,  # 30 minutes
            path="/",
            # secure=True,  # Would be True in production with HTTPS
            samesite="lax"
        )

    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/portfolio/{symbol}", status_code=status.HTTP_201_CREATED)
async def add_to_portfolio(
    symbol: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Add a stock ticker to the authenticated user's portfolio."""
    # Check if stock exists (optional, but good practice)
    # For simplicity, we assume the stock ticker is valid
    # Check if already in portfolio
    existing = db.query(Portfolio).filter(
        Portfolio.user_id == current_user["sub"],
        Portfolio.symbol == symbol
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Symbol already in portfolio"
        )
    # Add to portfolio
    portfolio_item = Portfolio(user_id=current_user["sub"], symbol=symbol.upper())
    db.add(portfolio_item)
    db.commit()
    return {"message": f"Added {symbol} to portfolio"}


@router.get("/portfolio", response_model=List[dict])
async def get_user_portfolio(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Return the user's watchlist with latest signal and news data."""
    # Get user's portfolio items
    portfolio_items = db.query(Portfolio).filter(
        Portfolio.user_id == current_user["sub"]
    ).all()

    if not portfolio_items:
        return []

    # Extract symbols
    symbols = [item.symbol for item in portfolio_items]

    # Get latest RecommendationSignal for each symbol (most recent date)
    # We'll do a subquery to get the latest date per symbol, then join
    from sqlalchemy import desc, func
    latest_signals_subq = db.query(
        RecommendationSignal.symbol,
        func.max(RecommendationSignal.date).label('max_date')
    ).filter(
        RecommendationSignal.symbol.in_(symbols)
    ).group_by(
        RecommendationSignal.symbol
    ).subquery()

    latest_signals = db.query(RecommendationSignal).join(
        latest_signals_subq,
        (RecommendationSignal.symbol == latest_signals_subq.c.symbol) &
        (RecommendationSignal.date == latest_signals_subq.c.max_date)
    ).all()

    # Get latest NewsCatalyst for each symbol (most recent publish_timestamp)
    # Similarly, we'll get the latest news per symbol
    latest_news_subq = db.query(
        NewsCatalyst.symbol,
        func.max(NewsCatalyst.publish_timestamp).label('max_publish')
    ).filter(
        NewsCatalyst.symbol.in_(symbols)
    ).group_by(
        NewsCatalyst.symbol
    ).subquery()

    latest_news = db.query(NewsCatalyst).join(
        latest_news_subq,
        (NewsCatalyst.symbol == latest_news_subq.c.symbol) &
        (NewsCatalyst.publish_timestamp == latest_news_subq.c.max_publish)
    ).all()

    # Build a dictionary for quick lookup
    signals_dict = {signal.symbol: signal for signal in latest_signals}
    news_dict = {news.symbol: news for news in latest_news}

    # Build the response
    result = []
    for item in portfolio_items:
        symbol = item.symbol
        signal = signals_dict.get(symbol)
        news = news_dict.get(symbol)

        portfolio_entry = {
            "symbol": symbol,
            "added_at": item.added_at,
            "latest_signal": None,
            "latest_news": None
        }

        if signal:
            portfolio_entry["latest_signal"] = {
                "date": signal.date,
                "final_rating": signal.final_rating,
                "composite_score": signal.composite_score,
                "tech_score": signal.tech_score,
                "sentiment_score": signal.sentiment_score,
                "stop_loss_price": signal.stop_loss_price,
                "target_price": signal.target_price
            }

        if news:
            portfolio_entry["latest_news"] = {
                "publish_timestamp": news.publish_timestamp,
                "headline": news.headline,
                "content": news.content,
                "sentiment_score": news.sentiment_score,
                "confidence": news.confidence,
                "catalyst_type": news.catalyst_type,
                "rationale": news.rationale
            }

        result.append(portfolio_entry)

    return result


@router.delete("/portfolio/{symbol}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_from_portfolio(
    symbol: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Remove a stock ticker from the authenticated user's portfolio."""
    # Find the portfolio item
    portfolio_item = db.query(Portfolio).filter(
        Portfolio.user_id == current_user["sub"],
        Portfolio.symbol == symbol.upper()
    ).first()
    if not portfolio_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Symbol not found in portfolio"
        )
    # Delete the item
    db.delete(portfolio_item)
    db.commit()
    return None


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(response: Response):
    """Logout user by clearing the httpOnly cookie."""
    response.delete_cookie(
        key="taxstox_token",  # Canonical Taxstox cookie name
        path="/",
        # secure=True,  # Would be True in production with HTTPS
        samesite="lax"
    )
    return None