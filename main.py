#!/usr/bin/env python3
"""
Realtime Trade Router

Main application entry point for monitoring DEX trades and slippage data.
Data refreshes every DATA_REFRESH_INTERVAL seconds (configurable in config.py).
"""

import sys
import signal
import time
from datetime import datetime

from config import DATA_REFRESH_INTERVAL, MEMPOOL_QUERY_LIMIT, SLIPPAGE_QUERY_LIMIT
from data_service import DataService, get_data_service
from bitquery_client import format_usd


def clear_screen():
    """Clear the terminal screen."""
    print("\033[2J\033[H", end="")


def print_header():
    """Print the application header."""
    print("=" * 80)
    print("  Realtime Trade Router")
    print(f"  Refresh Interval: {DATA_REFRESH_INTERVAL}s | Mempool Limit: {MEMPOOL_QUERY_LIMIT} | Slippage Limit: {SLIPPAGE_QUERY_LIMIT}")
    print("=" * 80)


def on_slippage_update(data):
    """Callback when slippage data is updated."""
    pass  # Data is printed in main loop


def on_mempool_update(data):
    """Callback when mempool data is updated."""
    pass  # Data is printed in main loop


def on_error(error):
    """Callback when an error occurs."""
    print(f"\n[ERROR] {error}")


def run_monitor():
    """Run the main monitoring loop."""
    service = get_data_service()
    service.set_on_slippage_update(on_slippage_update)
    service.set_on_mempool_update(on_mempool_update)
    service.set_on_error(on_error)

    # Handle graceful shutdown
    def signal_handler(sig, frame):
        print("\n\nShutting down...")
        service.stop()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    print("Starting Best Trade Router monitor...")
    print(f"Data will refresh every {DATA_REFRESH_INTERVAL} seconds")
    print("Press Ctrl+C to exit\n")

    # Start the data service
    service.start()

    # Initial fetch
    try:
        print("Fetching initial data...")
        service.fetch_all()
    except Exception as e:
        print(f"Error fetching initial data: {e}")

    # Main display loop
    try:
        while True:
            clear_screen()
            print_header()

            # Display block info
            latest_block = service.get_latest_block()
            if latest_block:
                print(f"\n  Latest Block: {latest_block:,}")

            # Display slippage data
            service.print_slippage_table()

            # Display mempool trades
            service.print_mempool_trades()

            # Display footer
            print("\n" + "-" * 80)
            print(f"Next refresh in {DATA_REFRESH_INTERVAL}s | Press Ctrl+C to exit")

            # Wait for next refresh cycle
            time.sleep(DATA_REFRESH_INTERVAL)

    except KeyboardInterrupt:
        pass
    finally:
        service.stop()


def run_once():
    """Fetch and display data once (no auto-refresh)."""
    service = get_data_service()

    print("Fetching data from Bitquery...")

    try:
        service.fetch_all()

        print_header()

        # Display block info
        latest_block = service.get_latest_block()
        if latest_block:
            print(f"\n  Latest Block: {latest_block:,}")

        # Display slippage data
        service.print_slippage_table()

        # Display mempool trades
        service.print_mempool_trades()

    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Realtime Trade Router"
    )
    parser.add_argument(
        '--once',
        action='store_true',
        help='Fetch data once and exit (no auto-refresh)'
    )
    parser.add_argument(
        '--interval',
        type=int,
        default=None,
        help=f'Override refresh interval in seconds (default: {DATA_REFRESH_INTERVAL})'
    )

    args = parser.parse_args()

    # Override refresh interval if specified
    if args.interval:
        service = get_data_service()
        service.refresh_interval = args.interval

    if args.once:
        run_once()
    else:
        run_monitor()


if __name__ == '__main__':
    main()
