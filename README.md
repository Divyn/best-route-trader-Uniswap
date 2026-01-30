# Best Route Trader on Uniswap

A real-time trade router and monitor for **Uniswap** and its forks. Uses [Bitquery](https://bitquery.io) to fetch pool slippage data and mempool trades so you can compare routes and see live activity by token pair.

## Features

- **Pool slippage** — Per-pool slippage (basis points), price, and max amount for a given trade size
- **Mempool trades** — Pending DEX swaps (token, amount, USD value, gas)
- **Token pair filter** — Filter by symbol or address (e.g. USDC/WETH, DAI/USDT)
- **Web UI** — Flask dashboard with auto-refresh
- **CLI** — Terminal monitor with configurable refresh interval

Supported tokens (Ethereum mainnet) include USDC, USDT, DAI, WETH, WBTC; configurable in `config.py`.

## Prerequisites

- Python 3.8+
- [Bitquery](https://bitquery.io) API token (free tier available)

## Installation

```bash
git clone https://github.com/your-username/best-route-trader.git
cd best-route-trader
pip install -r requirements.txt
```

## Configuration

Create a `.env` file in the project root:

```env
VITE_BITQUERY_TOKEN=your_bitquery_api_token
```

Optional:

```env
VITE_BITQUERY_API_URL=https://streaming.bitquery.io/graphql
```

Tuning (in `config.py` or via code):

- `DATA_REFRESH_INTERVAL` — Seconds between fetches (default: 30)
- `MEMPOOL_QUERY_LIMIT` / `SLIPPAGE_QUERY_LIMIT` — Number of records per request
- `DEFAULT_TRADE_AMOUNT` — Notional used for slippage calculations

## Usage

### Web app

```bash
python app.py
```

Then open **http://localhost:5000**. The UI refreshes at `DATA_REFRESH_INTERVAL` and supports token pair filters.

### CLI monitor

```bash
# Continuous refresh (default interval)
python main.py

# Single run, no auto-refresh
python main.py --once

# Custom refresh interval (seconds)
python main.py --interval 60
```

Press `Ctrl+C` to exit.

## API endpoints

| Endpoint       | Description |
|----------------|-------------|
| `GET /api/data`   | Slippage + mempool; optional `token_a`, `token_b` (symbol or address) |
| `GET /api/slippage` | Slippage only; optional `token_a`, `token_b` |
| `GET /api/mempool`  | Mempool trades only; optional `token_a`, `token_b` |

## Project structure

```
best-route-trader/
├── app.py              # Flask web app
├── main.py             # CLI entry (monitor / once)
├── config.py           # API URL, token, limits, token addresses
├── bitquery_client.py  # Bitquery GraphQL client (slippage, mempool)
├── data_service.py     # Refresh logic and in-memory data
├── calculation.py      # Slippage transform for API (A/B, B/A)
├── requirements.txt
├── templates/
│   └── index.html      # Dashboard UI
└── .env                # VITE_BITQUERY_TOKEN (create locally)
```

## License

MIT (or your preferred license).
