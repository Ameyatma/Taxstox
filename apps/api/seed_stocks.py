#!/usr/bin/env python3
"""Seed the stocks table with a representative Indian equity universe.

Usage:
    export $(cat .env | xargs)
    python3 seed_stocks.py
"""

from src.domains.market.storage.database import get_db_session, engine
from src.domains.market.storage.models import Stock, Base
from sqlalchemy import text

STOCKS = [
    ("RELIANCE.NS", "Reliance Industries", "NSE", "Conglomerate", "Energy"),
    ("TCS.NS", "Tata Consultancy Services", "NSE", "IT Services", "Technology"),
    ("HDFCBANK.NS", "HDFC Bank", "NSE", "Banking", "Financial Services"),
    ("HINDUNILVR.NS", "Hindustan Unilever", "NSE", "FMCG", "Consumer Staples"),
    ("ICICIBANK.NS", "ICICI Bank", "NSE", "Banking", "Financial Services"),
    ("BHARTIARTL.NS", "Bharti Airtel", "NSE", "Telecommunication", "Communication Services"),
    ("ITC.NS", "ITC Limited", "NSE", "FMCG", "Consumer Staples"),
    ("SBIN.NS", "State Bank of India", "NSE", "Banking", "Financial Services"),
    ("LTI.NS", "Larsen & Toubro Infotech", "NSE", "IT Services", "Technology"),
    ("LTIMHLDING.NS", "Larsen & Toubro", "NSE", "Construction", "Industrials"),
    ("M&M.NS", "Mahindra & Mahindra", "NSE", "Automotive", "Consumer Discretionary"),
    ("AXISBANK.NS", "Axis Bank", "NSE", "Banking", "Financial Services"),
    ("TITAN.NS", "Titan Company", "NSE", "Consumer Goods", "Consumer Discretionary"),
    ("SUNPHARMA.NS", "Sun Pharmaceutical", "NSE", "Pharmaceuticals", "Healthcare"),
    ("NESTLEIND.NS", "Nestle India", "NSE", "FMCG", "Consumer Staples"),
    ("HCLTECH.NS", "HCL Technologies", "NSE", "IT Services", "Technology"),
    ("TECHM.NS", "Tech Mahindra", "NSE", "IT Services", "Technology"),
    ("WIPRO.NS", "Wipro", "NSE", "IT Services", "Technology"),
    ("ONGC.NS", "Oil and Natural Gas Corporation", "NSE", "Oil & Gas", "Energy"),
    ("NTPC.NS", "NTPC Limited", "NSE", "Utilities", "Utilities"),
    ("POWERGRID.NS", "Power Grid Corporation", "NSE", "Utilities", "Utilities"),
    ("TATASTEEL.NS", "Tata Steel", "NSE", "Steel", "Materials"),
    ("JSWSTEEL.NS", "JSW Steel", "NSE", "Steel", "Materials"),
    ("ULTRATECH.NS", "UltraTech Cement", "NSE", "Cement", "Materials"),
    ("MARUTI.NS", "Maruti Suzuki", "NSE", "Automotive", "Consumer Discretionary"),
    ("BAJAJFINSV.NS", "Bajaj Finserv", "NSE", "Financial Services", "Financial Services"),
    ("BAJAJ-AUTO.NS", "Bajaj Auto", "NSE", "Automotive", "Consumer Discretionary"),
    ("ASIANPAINT.NS", "Asian Paints", "NSE", "Paints", "Materials"),
    ("BRITANNIA.NS", "Britannia Industries", "NSE", "FMCG", "Consumer Staples"),
    ("DRREDDY.NS", "Dr Reddy Laboratories", "NSE", "Pharmaceuticals", "Healthcare"),
    ("CIPLA.NS", "Cipla", "NSE", "Pharmaceuticals", "Healthcare"),
    ("APOLLOHOSP.NS", "Apollo Hospitals", "NSE", "Healthcare Services", "Healthcare"),
    ("ADANIPORTS.NS", "Adani Ports", "NSE", "Infrastructure", "Industrials"),
    ("ADANIGREEN.NS", "Adani Green Energy", "NSE", "Renewable Energy", "Utilities"),
    ("GRASIM.NS", "Grasim Industries", "NSE", "Diversified", "Materials"),
    ("INDUSINDBK.NS", "IndusInd Bank", "NSE", "Banking", "Financial Services"),
    ("INFY.NS", "Infosys", "NSE", "IT Services", "Technology"),
    ("HDFCLIFE.NS", "HDFC Life Insurance", "NSE", "Insurance", "Financial Services"),
    ("SBI LIFE.NS", "SBI Life Insurance", "NSE", "Insurance", "Financial Services"),
    ("TATAMOTORS.NS", "Tata Motors", "NSE", "Automotive", "Consumer Discretionary"),
    ("COALINDIA.NS", "Coal India", "NSE", "Coal", "Energy"),
    ("VEDL.NS", "Vedanta", "NSE", "Metals & Mining", "Materials"),
    ("BPCL.NS", "Bharat Petroleum", "NSE", "Oil & Gas", "Energy"),
]


def main() -> None:
    Base.metadata.create_all(bind=engine)

    with get_db_session() as session:
        for ticker, name, exchange, sector, industry in STOCKS:
            session.execute(
                text(
                    "INSERT INTO stocks (ticker, name, exchange, sector, industry) "
                    "VALUES (:ticker, :name, :exchange, :sector, :industry) "
                    "ON CONFLICT (ticker) DO UPDATE SET "
                    "name = excluded.name, exchange = excluded.exchange, "
                    "sector = excluded.sector, industry = excluded.industry"
                ),
                {
                    "ticker": ticker,
                    "name": name,
                    "exchange": exchange,
                    "sector": sector,
                    "industry": industry,
                },
            )
        session.commit()
        print(f"Seeded {len(STOCKS)} stocks")

    with get_db_session() as session:
        count = session.execute(text("SELECT COUNT(*) FROM stocks")).scalar()
        print(f"Total stocks in DB: {count}")


if __name__ == "__main__":
    main()