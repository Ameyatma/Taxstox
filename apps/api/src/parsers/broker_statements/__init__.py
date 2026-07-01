"""Broker statement parsers — Zerodha, Groww, Upstox, Angel One, CAMS.

Each parser takes a broker trade statement (CSV or PDF) and returns
a standardized list of CGSaleEntry objects ready for classification.
"""
