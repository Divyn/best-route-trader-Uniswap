"""
Bitquery API Client

Handles all communication with the Bitquery GraphQL API.
"""

import requests
import json
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from datetime import datetime

from config import BITQUERY_API_URL, BITQUERY_TOKEN


# ===========================================
# GraphQL Queries
# ===========================================

DEX_POOL_SLIPPAGES_QUERY = """
query DEXPoolSlippages($limit: Int!) {
  EVM(network: eth) {
    DEXPoolSlippages(
      limit: { count: $limit }
      orderBy: { descending: Block_Time }
    ) {
      Price {
        BtoA {
          Price
          MinAmountOut
          MaxAmountIn
        }
        AtoB {
          Price
          MinAmountOut
          MaxAmountIn
        }
        Pool {
          PoolId
          SmartContract
          Pair {
            Decimals
            SmartContract
            Name
          }
          CurrencyB {
            Symbol
            SmartContract
            Name
            Decimals
          }
          CurrencyA {
            Symbol
            SmartContract
            Name
            Decimals
          }
        }
        Dex {
          SmartContract
          ProtocolVersion
          ProtocolName
          ProtocolFamily
        }
        SlippageBasisPoints
      }
      Block {
        Time
        Number
      }
    }
  }
}
"""

# Same query with filter by token pair (CurrencyA and CurrencyB SmartContracts)
DEX_POOL_SLIPPAGES_BY_TOKENS_QUERY = """
query DEXPoolSlippagesByTokens($limit: Int!, $tokenA: String!, $tokenB: String!) {
  EVM(network: eth) {
    DEXPoolSlippages(
      limit: { count: $limit }
      orderBy: { descending: Block_Time }
      where: {
        Price: {
          Pool: {
            CurrencyA: { SmartContract: { is: $tokenA } }
            CurrencyB: { SmartContract: { is: $tokenB } }
          }
        }
      }
    ) {
      Price {
        BtoA {
          Price
          MinAmountOut
          MaxAmountIn
        }
        AtoB {
          Price
          MinAmountOut
          MaxAmountIn
        }
        Pool {
          PoolId
          SmartContract
          Pair {
            Decimals
            SmartContract
            Name
          }
          CurrencyB {
            Symbol
            SmartContract
            Name
            Decimals
          }
          CurrencyA {
            Symbol
            SmartContract
            Name
            Decimals
          }
        }
        Dex {
          SmartContract
          ProtocolVersion
          ProtocolName
          ProtocolFamily
        }
        SlippageBasisPoints
      }
      Block {
        Time
        Number
      }
    }
  }
}
"""

MEMPOOL_DEX_TRADES_QUERY = """
query MempoolDEXTrades($limit: Int!) {
  EVM(dataset: realtime, network: eth, mempool: true) {
    DEXTradeByTokens(
      limit: { count: $limit }
      orderBy: { descending: Block_Time }
    ) {
      Block {
        Time
        Number
      }
      TransactionStatus {
        Success
      }
      Fee {
        EffectiveGasPrice
        EffectiveGasPriceInUSD
        PriorityFeePerGas
        PriorityFeePerGasInUSD
        SenderFee
        SenderFeeInUSD
      }
      Trade {
        Amount
        AmountInUSD
        Buyer
        Price
        PriceInUSD
        Seller
        Sender
        Success
        Dex {
          ProtocolName
          ProtocolFamily
        }
        Currency {
          Name
          Symbol
          SmartContract
        }
        Side {
          Amount
          AmountInUSD
          Currency {
            Name
            Symbol
            SmartContract
          }
          Type
        }
      }
      Transaction {
        Hash
        From
        To
      }
    }
  }
}
"""

# Same query with filter by token pair (Trade.Currency and Trade.Side.Currency SmartContracts)
MEMPOOL_DEX_TRADES_BY_TOKENS_QUERY = """
query MempoolDEXTradesByTokens($limit: Int!, $tokenA: String!, $tokenB: String!) {
  EVM(dataset: realtime, network: eth, mempool: true) {
    DEXTradeByTokens(
      limit: { count: $limit }
      orderBy: { descending: Block_Time }
      where: {
        Trade: {
          Currency: { SmartContract: { is: $tokenA } }
          Side: { Currency: { SmartContract: { is: $tokenB } } }
        }
      }
    ) {
      Block {
        Time
        Number
      }
      TransactionStatus {
        Success
      }
      Fee {
        EffectiveGasPrice
        EffectiveGasPriceInUSD
        PriorityFeePerGas
        PriorityFeePerGasInUSD
        SenderFee
        SenderFeeInUSD
      }
      Trade {
        Amount
        AmountInUSD
        Buyer
        Price
        PriceInUSD
        Seller
        Sender
        Success
        Dex {
          ProtocolName
          ProtocolFamily
        }
        Currency {
          Name
          Symbol
          SmartContract
        }
        Side {
          Amount
          AmountInUSD
          Currency {
            Name
            Symbol
            SmartContract
          }
          Type
        }
      }
      Transaction {
        Hash
        From
        To
      }
    }
  }
}
"""


# ===========================================
# Data Classes
# ===========================================

@dataclass
class TokenInfo:
    symbol: str
    name: str
    address: str
    decimals: int = 18


@dataclass
class PoolSlippageData:
    block_number: int
    block_time: datetime
    protocol: str
    protocol_version: str
    pool_address: str
    token_a: TokenInfo
    token_b: TokenInfo
    slippage_bps: int
    price_atob: float
    price_btoa: float
    max_amount_in_atob: float
    min_amount_out_atob: float
    max_amount_in_btoa: float
    min_amount_out_btoa: float


@dataclass
class MempoolTradeData:
    tx_hash: str
    block_number: int
    block_time: datetime
    from_address: str
    to_address: str
    protocol: str
    protocol_family: str
    trade_token: TokenInfo
    side_token: TokenInfo
    trade_amount: float
    trade_amount_usd: float
    side_amount: float
    side_amount_usd: float
    price: float
    price_usd: float
    gas_fee: float
    gas_fee_usd: float
    priority_fee: float
    priority_fee_usd: float
    success: bool
    buyer: str
    seller: str
    sender: str


# ===========================================
# API Client
# ===========================================

class BitqueryClient:
    """Client for interacting with Bitquery GraphQL API."""

    def __init__(self, api_url: str = BITQUERY_API_URL, token: str = BITQUERY_TOKEN):
        self.api_url = api_url
        self.token = token
        self.headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.token}'
        }

    def _execute_query(self, query: str, variables: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a GraphQL query against the Bitquery API."""
        payload = {
            'query': query,
            'variables': json.dumps(variables)
        }

        response = requests.post(
            self.api_url,
            headers=self.headers,
            json=payload
        )

        if not response.ok:
            raise Exception(f"Bitquery API error: {response.status_code} {response.text}")

        data = response.json()

        if 'errors' in data:
            raise Exception(f"GraphQL error: {json.dumps(data['errors'])}")

        return data.get('data', {})

    def _normalize_token_address(self, address: str) -> str:
        """Normalize token address for Bitquery (lowercase, 0x prefix)."""
        s = address.strip().lower()
        return s if s.startswith('0x') else '0x' + s

    def fetch_dex_pool_slippages(
        self,
        limit: int = 50,
        token_a_address: Optional[str] = None,
        token_b_address: Optional[str] = None,
    ) -> List[PoolSlippageData]:
        """Fetch DEX pool slippage data. Token addresses are required; unfiltered query returns all token data."""
        if not token_a_address or not token_b_address:
            return []
        ta = self._normalize_token_address(token_a_address)
        tb = self._normalize_token_address(token_b_address)
        variables_ab = {'limit': limit, 'tokenA': ta, 'tokenB': tb}
        variables_ba = {'limit': limit, 'tokenA': tb, 'tokenB': ta}
        data_ab = self._execute_query(DEX_POOL_SLIPPAGES_BY_TOKENS_QUERY, variables_ab)
        slippages_ab = data_ab.get('EVM', {}).get('DEXPoolSlippages', [])
        if slippages_ab:
            return self._transform_slippage_data(slippages_ab[:limit])
        data_ba = self._execute_query(DEX_POOL_SLIPPAGES_BY_TOKENS_QUERY, variables_ba)
        slippages_ba = data_ba.get('EVM', {}).get('DEXPoolSlippages', [])
        return self._transform_slippage_data(slippages_ba[:limit])

    def fetch_mempool_trades(
        self,
        limit: int = 20,
        token_a_address: Optional[str] = None,
        token_b_address: Optional[str] = None,
    ) -> List[MempoolTradeData]:
        """Fetch pending mempool DEX trades. Token addresses are required; unfiltered query returns all token data."""
        if not token_a_address or not token_b_address:
            return []
        ta = self._normalize_token_address(token_a_address)
        tb = self._normalize_token_address(token_b_address)
        per_limit = max(limit // 2, 5)
        variables_ab = {'limit': per_limit, 'tokenA': ta, 'tokenB': tb}
        variables_ba = {'limit': per_limit, 'tokenA': tb, 'tokenB': ta}
        data_ab = self._execute_query(MEMPOOL_DEX_TRADES_BY_TOKENS_QUERY, variables_ab)
        data_ba = self._execute_query(MEMPOOL_DEX_TRADES_BY_TOKENS_QUERY, variables_ba)
        trades_ab = data_ab.get('EVM', {}).get('DEXTradeByTokens', [])
        trades_ba = data_ba.get('EVM', {}).get('DEXTradeByTokens', [])
        seen_hashes = set()
        merged = []
        for item in trades_ab + trades_ba:
            tx_hash = (item.get('Transaction') or {}).get('Hash')
            if tx_hash and tx_hash in seen_hashes:
                continue
            if tx_hash:
                seen_hashes.add(tx_hash)
            merged.append(item)
        return self._transform_mempool_trades(merged[:limit])

    def _transform_slippage_data(self, raw_data: List[Dict]) -> List[PoolSlippageData]:
        """Transform raw API response to PoolSlippageData objects."""
        result = []

        for item in raw_data:
            try:
                block = item.get('Block', {})
                price = item.get('Price', {})
                pool = price.get('Pool', {})
                dex = price.get('Dex', {})
                atob = price.get('AtoB', {})
                btoa = price.get('BtoA', {})
                currency_a = pool.get('CurrencyA', {})
                currency_b = pool.get('CurrencyB', {})

                slippage = PoolSlippageData(
                    block_number=int(block.get('Number', 0)),
                    block_time=datetime.fromisoformat(block.get('Time', '').replace('Z', '+00:00')) if block.get('Time') else datetime.now(),
                    protocol=dex.get('ProtocolName', 'Unknown'),
                    protocol_version=dex.get('ProtocolVersion', ''),
                    pool_address=pool.get('SmartContract', ''),
                    token_a=TokenInfo(
                        symbol=currency_a.get('Symbol', ''),
                        name=currency_a.get('Name', ''),
                        address=currency_a.get('SmartContract', ''),
                        decimals=currency_a.get('Decimals', 18)
                    ),
                    token_b=TokenInfo(
                        symbol=currency_b.get('Symbol', ''),
                        name=currency_b.get('Name', ''),
                        address=currency_b.get('SmartContract', ''),
                        decimals=currency_b.get('Decimals', 18)
                    ),
                    slippage_bps=price.get('SlippageBasisPoints', 0),
                    price_atob=atob.get('Price', 0),
                    price_btoa=btoa.get('Price', 0),
                    max_amount_in_atob=atob.get('MaxAmountIn', 0),
                    min_amount_out_atob=atob.get('MinAmountOut', 0),
                    max_amount_in_btoa=btoa.get('MaxAmountIn', 0),
                    min_amount_out_btoa=btoa.get('MinAmountOut', 0)
                )
                result.append(slippage)
            except Exception as e:
                print(f"Error parsing slippage data: {e}")
                continue

        return result

    def _transform_mempool_trades(self, raw_data: List[Dict]) -> List[MempoolTradeData]:
        """Transform raw API response to MempoolTradeData objects."""
        result = []

        for item in raw_data:
            try:
                block = item.get('Block', {})
                trade = item.get('Trade', {})
                tx = item.get('Transaction', {})
                fee = item.get('Fee', {})
                dex = trade.get('Dex', {})
                currency = trade.get('Currency', {})
                side = trade.get('Side', {})
                side_currency = side.get('Currency', {})

                def safe_float(val, default=0.0):
                    """Safely convert value to float."""
                    if val is None:
                        return default
                    try:
                        return float(val)
                    except (ValueError, TypeError):
                        return default

                def safe_str(val, default=''):
                    """Safely convert value to string."""
                    if val is None:
                        return default
                    return str(val)

                mempool_trade = MempoolTradeData(
                    tx_hash=safe_str(tx.get('Hash')),
                    block_number=int(block.get('Number', 0) or 0),
                    block_time=datetime.fromisoformat(block.get('Time', '').replace('Z', '+00:00')) if block.get('Time') else datetime.now(),
                    from_address=safe_str(tx.get('From')),
                    to_address=safe_str(tx.get('To')),
                    protocol=safe_str(dex.get('ProtocolName'), 'Unknown'),
                    protocol_family=safe_str(dex.get('ProtocolFamily'), 'Unknown'),
                    trade_token=TokenInfo(
                        symbol=safe_str(currency.get('Symbol')),
                        name=safe_str(currency.get('Name')),
                        address=safe_str(currency.get('SmartContract'))
                    ),
                    side_token=TokenInfo(
                        symbol=safe_str(side_currency.get('Symbol')),
                        name=safe_str(side_currency.get('Name')),
                        address=safe_str(side_currency.get('SmartContract'))
                    ),
                    trade_amount=safe_float(trade.get('Amount')),
                    trade_amount_usd=safe_float(trade.get('AmountInUSD')),
                    side_amount=safe_float(side.get('Amount')),
                    side_amount_usd=safe_float(side.get('AmountInUSD')),
                    price=safe_float(trade.get('Price')),
                    price_usd=safe_float(trade.get('PriceInUSD')),
                    gas_fee=safe_float(fee.get('SenderFee')),
                    gas_fee_usd=safe_float(fee.get('SenderFeeInUSD')),
                    priority_fee=safe_float(fee.get('PriorityFeePerGas')),
                    priority_fee_usd=safe_float(fee.get('PriorityFeePerGasInUSD')),
                    success=trade.get('Success', True) or True,
                    buyer=safe_str(trade.get('Buyer')),
                    seller=safe_str(trade.get('Seller')),
                    sender=safe_str(trade.get('Sender'))
                )
                result.append(mempool_trade)
            except Exception as e:
                print(f"Error parsing mempool trade: {e}")
                continue

        return result


# ===========================================
# Utility Functions
# ===========================================

def format_usd(amount: float) -> str:
    """Format amount as USD string."""
    if amount >= 1_000_000:
        return f"${amount / 1_000_000:.2f}M"
    if amount >= 1_000:
        return f"${amount / 1_000:.2f}k"
    if amount >= 1:
        return f"${amount:.2f}"
    if amount >= 0.01:
        return f"${amount:.4f}"
    return f"${amount:.6f}"


def format_token_amount(amount: float) -> str:
    """Format token amount for display."""
    if amount >= 1_000_000:
        return f"{amount / 1_000_000:.2f}M"
    if amount >= 1_000:
        return f"{amount / 1_000:.2f}k"
    if amount >= 1:
        return f"{amount:.4f}"
    if amount >= 0.0001:
        return f"{amount:.6f}"
    return f"{amount:.2e}"


def truncate_address(address: str) -> str:
    """Truncate address for display."""
    if not address or len(address) <= 13:
        return address or ''
    return f"{address[:6]}...{address[-4:]}"


def get_relative_time(dt: datetime) -> str:
    """Get relative time string from datetime."""
    diff = datetime.now(dt.tzinfo) - dt
    seconds = int(diff.total_seconds())

    if seconds < 0:
        return 'pending'
    if seconds < 60:
        return f"{seconds}s ago"
    minutes = seconds // 60
    if minutes < 60:
        return f"{minutes}m ago"
    hours = minutes // 60
    return f"{hours}h ago"
