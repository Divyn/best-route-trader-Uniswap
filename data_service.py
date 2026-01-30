"""
Data Service

Handles periodic data fetching with configurable refresh intervals.
"""

import time
import threading
from typing import Callable, Optional, List, Any
from datetime import datetime

from config import (
    DATA_REFRESH_INTERVAL,
    MEMPOOL_QUERY_LIMIT,
    SLIPPAGE_QUERY_LIMIT,
    token_to_address,
)
from bitquery_client import (
    BitqueryClient,
    PoolSlippageData,
    MempoolTradeData,
    format_usd,
    format_token_amount,
    truncate_address,
    get_relative_time
)


class DataService:
    """
    Service for fetching and managing real-time data from Bitquery.

    All data refreshes at the interval specified by DATA_REFRESH_INTERVAL in config.py
    """

    def __init__(self, refresh_interval: int = DATA_REFRESH_INTERVAL):
        """
        Initialize the data service.

        Args:
            refresh_interval: Time between data refreshes in seconds (default from config)
        """
        self.refresh_interval = refresh_interval
        self.client = BitqueryClient()

        # Data storage
        self.slippage_data: List[PoolSlippageData] = []
        self.mempool_data: List[MempoolTradeData] = []

        # Timestamps
        self.last_slippage_update: Optional[datetime] = None
        self.last_mempool_update: Optional[datetime] = None

        # Thread control
        self._running = False
        self._thread: Optional[threading.Thread] = None

        # Callbacks for data updates
        self._on_slippage_update: Optional[Callable[[List[PoolSlippageData]], None]] = None
        self._on_mempool_update: Optional[Callable[[List[MempoolTradeData]], None]] = None
        self._on_error: Optional[Callable[[Exception], None]] = None

    def set_on_slippage_update(self, callback: Callable[[List[PoolSlippageData]], None]):
        """Set callback for slippage data updates."""
        self._on_slippage_update = callback

    def set_on_mempool_update(self, callback: Callable[[List[MempoolTradeData]], None]):
        """Set callback for mempool data updates."""
        self._on_mempool_update = callback

    def set_on_error(self, callback: Callable[[Exception], None]):
        """Set callback for error handling."""
        self._on_error = callback

    def fetch_slippage_data(
        self,
        limit: int = SLIPPAGE_QUERY_LIMIT,
        token_a: Optional[str] = None,
        token_b: Optional[str] = None,
    ) -> List[PoolSlippageData]:
        """Fetch slippage data once. Optionally filter by token pair (symbol or address)."""
        try:
            addr_a = token_to_address(token_a) if token_a else None
            addr_b = token_to_address(token_b) if token_b else None
            self.slippage_data = self.client.fetch_dex_pool_slippages(
                limit, token_a_address=addr_a, token_b_address=addr_b
            )
            self.last_slippage_update = datetime.now()

            if self._on_slippage_update:
                self._on_slippage_update(self.slippage_data)

            return self.slippage_data
        except Exception as e:
            if self._on_error:
                self._on_error(e)
            raise

    def fetch_mempool_data(
        self,
        limit: int = MEMPOOL_QUERY_LIMIT,
        token_a: Optional[str] = None,
        token_b: Optional[str] = None,
    ) -> List[MempoolTradeData]:
        """Fetch mempool data once. Token pair (symbol or address) is required; otherwise returns empty."""
        try:
            addr_a = token_to_address(token_a) if token_a else None
            addr_b = token_to_address(token_b) if token_b else None
            self.mempool_data = self.client.fetch_mempool_trades(
                limit, token_a_address=addr_a, token_b_address=addr_b
            )
            self.last_mempool_update = datetime.now()

            if self._on_mempool_update:
                self._on_mempool_update(self.mempool_data)

            return self.mempool_data
        except Exception as e:
            if self._on_error:
                self._on_error(e)
            raise

    def fetch_all(
        self,
        token_a: Optional[str] = None,
        token_b: Optional[str] = None,
    ) -> dict:
        """Fetch all data at once. Token pair (symbol or address) is required; unfiltered queries return all token data."""
        return {
            'slippage': self.fetch_slippage_data(token_a=token_a, token_b=token_b),
            'mempool': self.fetch_mempool_data(token_a=token_a, token_b=token_b),
        }

    def _refresh_loop(self):
        """Internal refresh loop running in a separate thread."""
        while self._running:
            try:
                self.fetch_all()
            except Exception as e:
                print(f"Error in refresh loop: {e}")
                if self._on_error:
                    self._on_error(e)

            # Sleep for the configured interval
            time.sleep(self.refresh_interval)

    def start(self):
        """Start the automatic data refresh."""
        if self._running:
            return

        self._running = True
        self._thread = threading.Thread(target=self._refresh_loop, daemon=True)
        self._thread.start()
        print(f"Data service started with {self.refresh_interval}s refresh interval")

    def stop(self):
        """Stop the automatic data refresh."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=5)
            self._thread = None
        print("Data service stopped")

    def get_latest_block(self) -> Optional[int]:
        """Get the latest block number from available data."""
        if self.slippage_data:
            return max(s.block_number for s in self.slippage_data)
        return None

    def get_unique_protocols(self) -> List[str]:
        """Get unique protocols from slippage data."""
        if not self.slippage_data:
            return []
        return list(set(f"{s.protocol} v{s.protocol_version}" for s in self.slippage_data))

    def get_mempool_summary(self) -> dict:
        """Get summary statistics for mempool trades."""
        if not self.mempool_data:
            return {
                'count': 0,
                'total_value_usd': 0,
                'unique_protocols': 0
            }

        return {
            'count': len(self.mempool_data),
            'total_value_usd': sum(t.trade_amount_usd for t in self.mempool_data),
            'unique_protocols': len(set(t.protocol for t in self.mempool_data))
        }

    def print_slippage_table(self):
        """Print slippage data as a formatted table."""
        if not self.slippage_data:
            print("No slippage data available")
            return

        print("\n" + "=" * 80)
        print("SLIPPAGE SURFACE DATA")
        print(f"Last updated: {self.last_slippage_update}")
        print("=" * 80)
        print(f"{'BPS':<8} {'Max Size':<15} {'Price':<20} {'Protocol':<20}")
        print("-" * 80)

        # Group by unique bps
        seen_bps = set()
        for s in sorted(self.slippage_data, key=lambda x: x.slippage_bps):
            if s.slippage_bps in seen_bps:
                continue
            seen_bps.add(s.slippage_bps)

            print(f"{s.slippage_bps:<8} {format_usd(s.max_amount_in_atob):<15} {s.price_btoa:<20.6f} {s.protocol} v{s.protocol_version}")

    def print_mempool_trades(self):
        """Print mempool trades as a formatted list."""
        if not self.mempool_data:
            print("No mempool trades available")
            return

        summary = self.get_mempool_summary()

        print("\n" + "=" * 80)
        print("PENDING MEMPOOL TRADES")
        print(f"Last updated: {self.last_mempool_update}")
        print(f"Total: {summary['count']} trades | Value: {format_usd(summary['total_value_usd'])} | DEXs: {summary['unique_protocols']}")
        print("=" * 80)

        for trade in self.mempool_data[:15]:
            print(f"\n{trade.protocol} | {get_relative_time(trade.block_time)}")
            print(f"  {format_token_amount(trade.trade_amount)} {trade.trade_token.symbol} → {format_token_amount(trade.side_amount)} {trade.side_token.symbol}")
            print(f"  Value: {format_usd(trade.trade_amount_usd)} | Gas: {format_usd(trade.gas_fee_usd)}")
            if trade.sender:
                print(f"  From: {truncate_address(trade.sender)}")


# Singleton instance
_data_service: Optional[DataService] = None


def get_data_service() -> DataService:
    """Get the singleton data service instance."""
    global _data_service
    if _data_service is None:
        _data_service = DataService()
    return _data_service
