#!/usr/bin/env python3
"""
Realtime Trade Router - Flask Web Application

Simple Flask web UI for monitoring DEX trades and slippage data.
"""

from flask import Flask, render_template, jsonify, request
from data_service import get_data_service
from config import DATA_REFRESH_INTERVAL
from calculation import transform_slippage_for_api

app = Flask(__name__)

# Initialize data service
service = get_data_service()


@app.route('/')
def index():
    """Main dashboard page."""
    return render_template('index.html', refresh_interval=DATA_REFRESH_INTERVAL)


@app.route('/api/data')
def get_all_data():
    """API endpoint to fetch all data. Optional query params: token_a, token_b (symbol or address) to filter slippage by pair."""
    try:
        token_a = request.args.get('token_a', '').strip() or None
        token_b = request.args.get('token_b', '').strip() or None
        service.fetch_all(token_a=token_a, token_b=token_b)

        slippage_list = transform_slippage_for_api(
            service.slippage_data,
            token_a=token_a,
            token_b=token_b,
            include_tokens=True,
        )

        # Transform mempool data for JSON
        mempool_list = []
        for t in service.mempool_data[:15]:
            mempool_list.append({
                'tx_hash': t.tx_hash,
                'protocol': t.protocol,
                'trade_token': t.trade_token.symbol,
                'trade_amount': t.trade_amount,
                'trade_amount_usd': t.trade_amount_usd,
                'side_token': t.side_token.symbol,
                'side_amount': t.side_amount,
                'side_amount_usd': t.side_amount_usd,
                'gas_fee_usd': t.gas_fee_usd,
                'sender': t.sender,
                'block_time': t.block_time.isoformat(),
            })

        summary = service.get_mempool_summary()

        return jsonify({
            'success': True,
            'slippage': slippage_list,
            'mempool': mempool_list,
            'summary': summary,
            'latest_block': service.get_latest_block(),
            'last_updated': service.last_mempool_update.isoformat() if service.last_mempool_update else None,
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/slippage')
def get_slippage():
    """API endpoint for slippage data only. Optional query params: token_a, token_b (symbol or address)."""
    try:
        token_a = request.args.get('token_a', '').strip() or None
        token_b = request.args.get('token_b', '').strip() or None
        service.fetch_slippage_data(token_a=token_a, token_b=token_b)

        slippage_list = transform_slippage_for_api(
            service.slippage_data,
            token_a=token_a,
            token_b=token_b,
            include_tokens=False,
        )

        return jsonify({
            'success': True,
            'data': slippage_list,
            'latest_block': service.get_latest_block(),
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/mempool')
def get_mempool():
    """API endpoint for mempool data only. Query params token_a and token_b (symbol or address) are required."""
    try:
        token_a = request.args.get('token_a', '').strip() or None
        token_b = request.args.get('token_b', '').strip() or None
        service.fetch_mempool_data(token_a=token_a, token_b=token_b)

        mempool_list = []
        for t in service.mempool_data[:15]:
            mempool_list.append({
                'tx_hash': t.tx_hash,
                'protocol': t.protocol,
                'trade_token': t.trade_token.symbol,
                'trade_amount': t.trade_amount,
                'trade_amount_usd': t.trade_amount_usd,
                'side_token': t.side_token.symbol,
                'side_amount': t.side_amount,
                'gas_fee_usd': t.gas_fee_usd,
                'sender': t.sender,
            })

        return jsonify({
            'success': True,
            'data': mempool_list,
            'summary': service.get_mempool_summary(),
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


if __name__ == '__main__':
    print(f"Starting Realtime Trade Router...")
    print(f"Data refresh interval: {DATA_REFRESH_INTERVAL}s")
    print(f"Open http://localhost:5000 in your browser")
    app.run(debug=True, host='0.0.0.0', port=5000)
