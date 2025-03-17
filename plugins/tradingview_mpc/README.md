# TradingView MPC Plugin for Starferry

This plugin integrates TradingView API functionality into Starferry, allowing AI agents to access market data through TradingView.

## Architecture

The plugin uses a multi-process communication (MPC) approach:

1. **Starferry Core**: Python FastAPI application that loads plugins
2. **TradingView MPC Plugin**: Python plugin that provides a HTTP interface to the TradingView API
3. **TradingView API Server**: Node.js Express server that connects to the TradingView API

The communication flow is as follows:
```
Starferry Core <-> TradingView MPC Plugin <-> TradingView API Server <-> TradingView API
```

## Installation

1. Make sure the TradingView API server is running:
   ```
   cd TradingView-API
   npm install
   npm run server
   ```

2. The Starferry core will automatically load the plugin when it starts.

## API Endpoints

The plugin provides these endpoints:

- `GET /plugins/tradingview_mpc/status` - Get connection status
- `POST /plugins/tradingview_mpc/symbols` - Get available symbols
- `POST /plugins/tradingview_mpc/chart` - Get chart data

## Example Usage

```python
import httpx

# Get status
response = httpx.get("http://localhost:8008/plugins/tradingview_mpc/status")
print(response.json())

# Get symbols for NASDAQ
response = httpx.post(
    "http://localhost:8008/plugins/tradingview_mpc/symbols",
    json={"exchange": "NASDAQ"}
)
print(response.json())

# Get chart data for AAPL
response = httpx.post(
    "http://localhost:8008/plugins/tradingview_mpc/chart",
    json={
        "symbol": "NASDAQ:AAPL",
        "interval": "1D",
        "range_from": "2023-01-01",
        "range_to": "2023-01-31"
    }
)
print(response.json())
```

## Configuration

The plugin reads the following environment variables:

- `TRADINGVIEW_API_URL` - URL of the TradingView API server (default: http://localhost:3000) 