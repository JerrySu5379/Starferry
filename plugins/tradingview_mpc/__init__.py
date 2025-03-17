"""
TradingView MPC Plugin for Starferry
This plugin allows Starferry to interact with the TradingView API
"""

import logging
import os
import httpx
import asyncio
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
import json

logger = logging.getLogger(__name__)

# Router for the plugin
router = APIRouter()

# Communication client for TradingView API
class TradingViewClient:
    def __init__(self, api_url="http://localhost:3000"):
        self.api_url = api_url
        self.client = httpx.AsyncClient(timeout=30.0)
        self.connected = False
    
    async def connect(self):
        try:
            response = await self.client.get(f"{self.api_url}/status")
            if response.status_code == 200:
                self.connected = True
                logger.info("Connected to TradingView API")
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to connect to TradingView API: {str(e)}")
            return False
    
    async def disconnect(self):
        await self.client.aclose()
        self.connected = False
        logger.info("Disconnected from TradingView API")
    
    async def get_symbols(self, exchange=None):
        try:
            params = {}
            if exchange:
                params["exchange"] = exchange
            response = await self.client.get(f"{self.api_url}/symbols", params=params)
            return response.json()
        except Exception as e:
            logger.error(f"Error getting symbols: {str(e)}")
            return {"error": str(e)}
    
    async def get_chart_data(self, symbol, interval="1D", range_from=None, range_to=None):
        try:
            params = {
                "symbol": symbol,
                "interval": interval
            }
            if range_from:
                params["from"] = range_from
            if range_to:
                params["to"] = range_to
                
            response = await self.client.get(f"{self.api_url}/chart", params=params)
            return response.json()
        except Exception as e:
            logger.error(f"Error getting chart data: {str(e)}")
            return {"error": str(e)}

# Global client instance
tv_client = None

# Request models
class SymbolRequest(BaseModel):
    exchange: str = None

class ChartDataRequest(BaseModel):
    symbol: str
    interval: str = "1D"
    range_from: str = None
    range_to: str = None

# Plugin routes
@router.get("/status")
async def get_status():
    """Get the connection status of the TradingView API"""
    if tv_client and tv_client.connected:
        return {"status": "connected"}
    return {"status": "disconnected"}

@router.post("/symbols")
async def get_symbols(request: SymbolRequest):
    """Get available symbols from TradingView"""
    if not tv_client or not tv_client.connected:
        raise HTTPException(status_code=503, detail="TradingView API not connected")
    
    result = await tv_client.get_symbols(request.exchange)
    return result

@router.post("/chart")
async def get_chart_data(request: ChartDataRequest):
    """Get chart data for a symbol"""
    if not tv_client or not tv_client.connected:
        raise HTTPException(status_code=503, detail="TradingView API not connected")
    
    result = await tv_client.get_chart_data(
        request.symbol, 
        request.interval, 
        request.range_from, 
        request.range_to
    )
    return result

async def setup(app):
    """Setup the plugin and return the router"""
    global tv_client
    
    # Initialize TradingView client
    api_url = os.environ.get("TRADINGVIEW_API_URL", "http://localhost:3000")
    tv_client = TradingViewClient(api_url)
    
    # Try to connect to the TradingView API
    connection_success = await tv_client.connect()
    if not connection_success:
        logger.warning("Could not connect to TradingView API. Plugin will be available but not operational until connection is established.")
    
    # Add a periodic connection retry task
    async def connection_monitor():
        while True:
            if not tv_client.connected:
                await tv_client.connect()
            await asyncio.sleep(60)  # Check connection every 60 seconds
    
    # Start the connection monitor
    app.state.tv_connection_task = asyncio.create_task(connection_monitor())
    
    return router

async def shutdown():
    """Shutdown the plugin"""
    global tv_client
    if tv_client:
        await tv_client.disconnect()
        tv_client = None
    logger.info("TradingView MPC plugin shutdown complete") 