"""
Calculation logic for slippage API payload.

Transforms raw slippage data for API (with A/B vs B/A handling).
"""

from typing import List, Dict, Any, Optional

from bitquery_client import PoolSlippageData


def _is_pool_reversed(
    token_a_symbol: str,
    token_b_symbol: str,
    request_token_a: Optional[str],
    request_token_b: Optional[str],
) -> bool:
    """True when pool A/B order is opposite to user request (data came from B→A query)."""
    if not request_token_a or not request_token_b:
        return False
    return (
        token_a_symbol == request_token_b and token_b_symbol == request_token_a
    )


def transform_slippage_for_api(
    slippage_data: List[PoolSlippageData],
    token_a: Optional[str] = None,
    token_b: Optional[str] = None,
    include_tokens: bool = True,
) -> List[Dict[str, Any]]:
    """
    Transform raw slippage data to API JSON format.

    When data came from B→A query, pool A=user B and pool B=user A;
    we use price_btoa and max_amount_in_btoa so numbers match user's A→B direction.

    Args:
        slippage_data: List of PoolSlippageData from bitquery.
        token_a: User's token A symbol (request).
        token_b: User's token B symbol (request).
        include_tokens: If True, include token_a/token_b in each item (for /api/data).

    Returns:
        List of dicts with bps, max_amount, price, price_btoa, protocol, and optionally token_a, token_b.
    """
    result = []
    seen_bps = set()
    for s in sorted(slippage_data, key=lambda x: x.slippage_bps):
        if s.slippage_bps in seen_bps:
            continue
        seen_bps.add(s.slippage_bps)
        pool_reversed = _is_pool_reversed(
            s.token_a.symbol, s.token_b.symbol, token_a, token_b
        )
        if pool_reversed:
            price_b_per_a = s.price_btoa if (s.price_btoa and s.price_btoa > 0) else 0
            max_amount = s.max_amount_in_btoa
        else:
            price_b_per_a = s.price_atob if (s.price_atob and s.price_atob > 0) else 0
            max_amount = s.max_amount_in_atob
        item = {
            "bps": s.slippage_bps,
            "max_amount": max_amount,
            "price": price_b_per_a,
            "price_btoa": s.price_btoa,
            "protocol": f"{s.protocol} v{s.protocol_version}",
        }
        if include_tokens:
            item["token_a"] = s.token_a.symbol
            item["token_b"] = s.token_b.symbol
        result.append(item)
    return result
