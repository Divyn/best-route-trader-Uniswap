"""
Application Configuration

All configurable settings for the Best Trade Router trading interface.
Modify these values to adjust refresh intervals, API limits, and other settings.
"""

import os
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# ===========================================
# API CONFIGURATION
# ===========================================

BITQUERY_API_URL = os.getenv('VITE_BITQUERY_API_URL', 'https://streaming.bitquery.io/graphql')
BITQUERY_TOKEN = os.getenv('VITE_BITQUERY_TOKEN', '')

# ===========================================
# GLOBAL REFRESH INTERVAL (in seconds)
# ===========================================

# Global data refresh interval for ALL data sources (seconds)
# This controls how often the UI calls /api/data and refetches slippage + mempool.
#
# - Lower values = more real-time data, higher API usage
# - Higher values = less API usage, less frequent refreshes
#
# Slippage data changes relatively slowly; 30–60s is usually enough.
DATA_REFRESH_INTERVAL = 30

# ===========================================
# API QUERY LIMITS
# ===========================================

# Number of mempool trades to fetch per request
# Default: 20
# Set to 1 for just the latest entry
MEMPOOL_QUERY_LIMIT = 20

# Number of slippage data points to fetch per request
# Default: 50
SLIPPAGE_QUERY_LIMIT = 50

# Number of pool data entries to fetch per request
# Default: 50
POOL_DATA_QUERY_LIMIT = 50

# ===========================================
# UI SETTINGS
# ===========================================

# Maximum number of mempool trades to display
# Default: 15
MEMPOOL_DISPLAY_LIMIT = 15

# Maximum number of pools to display
# Default: 5
POOL_DISPLAY_LIMIT = 5

# ===========================================
# BLOCK INFO SETTINGS
# ===========================================

# Default block number to show when no data is available
DEFAULT_BLOCK_NUMBER = 19842771

# Default finalized time string when no data is available
DEFAULT_FINALIZED_TIME = '0.9s ago'

# ===========================================
# TRADE CONFIGURATION DEFAULTS
# ===========================================

# Default trade amount for slippage calculations
DEFAULT_TRADE_AMOUNT = 100000

# ===========================================
# TOKEN ADDRESSES (Ethereum Mainnet)
# ===========================================
# Used to filter DEXPoolSlippages by token pair. Add or override via env if needed.
# ETH in pools is typically WETH.
TOKEN_ADDRESSES = {
    'USDC': '0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48',
    'USDT': '0xdac17f958d2ee523a2206206994597c13d831ec7',
    'DAI': '0x6b175474e89094c44da98b954eedeac495271d0f',
    'WETH': '0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2',
    'ETH': '0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2',  # WETH
    'WBTC': '0x2260fac5e5542a773aa44fbcfedf7c193bc2c599',
}


def token_to_address(symbol_or_address: Optional[str]) -> Optional[str]:
    """Resolve token symbol or raw address to normalized address, or None if unknown."""
    if not symbol_or_address or not isinstance(symbol_or_address, str):
        return None
    s = symbol_or_address.strip()
    if s.startswith('0x') and len(s) == 42:
        return s.lower()
    if len(s) == 40 and all(c in '0123456789abcdefABCDEF' for c in s):
        return '0x' + s.lower()
    return TOKEN_ADDRESSES.get(s.upper())
