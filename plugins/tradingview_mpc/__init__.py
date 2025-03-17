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
from typing import Optional, List, Dict, Any, Union

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
            
    # New methods for additional endpoints
    
    async def get_simple_chart(self, symbol, timeframe="D", chart_type=None):
        """Get a simple chart with customizable parameters"""
        try:
            params = {
                "symbol": symbol,
                "timeframe": timeframe
            }
            if chart_type:
                params["chartType"] = chart_type
                
            response = await self.client.get(f"{self.api_url}/simpleChart", params=params)
            return response.json()
        except Exception as e:
            logger.error(f"Error getting simple chart: {str(e)}")
            return {"error": str(e)}
    
    async def get_replay_mode(self, symbol, timeframe="D", start_from=None, steps=None):
        """Get data using replay mode"""
        try:
            params = {
                "symbol": symbol,
                "timeframe": timeframe
            }
            if start_from:
                params["startFrom"] = start_from
            if steps:
                params["steps"] = steps
                
            response = await self.client.get(f"{self.api_url}/replayMode", params=params)
            return response.json()
        except Exception as e:
            logger.error(f"Error getting replay mode data: {str(e)}")
            return {"error": str(e)}
    
    async def login(self, username, password):
        """Login to TradingView"""
        try:
            data = {
                "username": username,
                "password": password
            }
            response = await self.client.post(f"{self.api_url}/login", json=data)
            return response.json()
        except Exception as e:
            logger.error(f"Error logging in: {str(e)}")
            return {"error": str(e)}
    
    async def search(self, query, exchange=None):
        """Search for symbols"""
        try:
            params = {
                "query": query
            }
            if exchange:
                params["exchange"] = exchange
                
            response = await self.client.get(f"{self.api_url}/search", params=params)
            return response.json()
        except Exception as e:
            logger.error(f"Error searching: {str(e)}")
            return {"error": str(e)}
    
    async def get_drawings(self, symbol):
        """Get drawings for a symbol"""
        try:
            params = {
                "symbol": symbol
            }
            response = await self.client.get(f"{self.api_url}/drawings", params=params)
            return response.json()
        except Exception as e:
            logger.error(f"Error getting drawings: {str(e)}")
            return {"error": str(e)}
    
    async def get_from_to_data(self, symbol, timeframe="D", from_timestamp=None, to_timestamp=None):
        """Get data for a specific time range"""
        try:
            params = {
                "symbol": symbol,
                "timeframe": timeframe
            }
            if from_timestamp:
                params["from"] = from_timestamp
            if to_timestamp:
                params["to"] = to_timestamp
                
            response = await self.client.get(f"{self.api_url}/fromToData", params=params)
            return response.json()
        except Exception as e:
            logger.error(f"Error getting from-to data: {str(e)}")
            return {"error": str(e)}
    
    async def get_built_in_indicator(self, symbol, indicator, timeframe="D", options=None):
        """Get built-in indicator data"""
        try:
            params = {
                "symbol": symbol,
                "indicator": indicator,
                "timeframe": timeframe
            }
            if options:
                params["options"] = json.dumps(options)
                
            response = await self.client.get(f"{self.api_url}/builtInIndicator", params=params)
            return response.json()
        except Exception as e:
            logger.error(f"Error getting built-in indicator: {str(e)}")
            return {"error": str(e)}
    
    async def get_custom_timeframe(self, symbol, timeframe):
        """Get data for a custom timeframe"""
        try:
            params = {
                "symbol": symbol,
                "timeframe": timeframe
            }
            response = await self.client.get(f"{self.api_url}/customTimeframe", params=params)
            return response.json()
        except Exception as e:
            logger.error(f"Error getting custom timeframe data: {str(e)}")
            return {"error": str(e)}
    
    async def get_graphic_indicator(self, symbol, indicator, timeframe="D", options=None):
        """Get graphic indicator data"""
        try:
            params = {
                "symbol": symbol,
                "indicator": indicator,
                "timeframe": timeframe
            }
            if options:
                params["options"] = json.dumps(options)
                
            response = await self.client.get(f"{self.api_url}/graphicIndicator", params=params)
            return response.json()
        except Exception as e:
            logger.error(f"Error getting graphic indicator: {str(e)}")
            return {"error": str(e)}
    
    async def get_multiple_sync_fetch(self, symbols, timeframe="D"):
        """Get data for multiple symbols"""
        try:
            if isinstance(symbols, list):
                symbols = ",".join(symbols)
                
            params = {
                "symbols": symbols,
                "timeframe": timeframe
            }
            response = await self.client.get(f"{self.api_url}/multipleSyncFetch", params=params)
            return response.json()
        except Exception as e:
            logger.error(f"Error getting multiple sync fetch data: {str(e)}")
            return {"error": str(e)}
    
    async def get_custom_chart_type(self, symbol, chart_type, timeframe="D"):
        """Get data with a custom chart type"""
        try:
            params = {
                "symbol": symbol,
                "chartType": chart_type,
                "timeframe": timeframe
            }
            response = await self.client.get(f"{self.api_url}/customChartType", params=params)
            return response.json()
        except Exception as e:
            logger.error(f"Error getting custom chart type data: {str(e)}")
            return {"error": str(e)}
    
    async def get_fake_replay_mode(self, symbol, timeframe="D", bars=None):
        """Get data using fake replay mode"""
        try:
            params = {
                "symbol": symbol,
                "timeframe": timeframe
            }
            if bars:
                params["bars"] = bars
                
            response = await self.client.get(f"{self.api_url}/fakeReplayMode", params=params)
            return response.json()
        except Exception as e:
            logger.error(f"Error getting fake replay mode data: {str(e)}")
            return {"error": str(e)}
    
    async def get_private_indicators(self):
        """Get all private indicators"""
        try:
            response = await self.client.get(f"{self.api_url}/privateIndicators")
            return response.json()
        except Exception as e:
            logger.error(f"Error getting private indicators: {str(e)}")
            return {"error": str(e)}
    
    async def manage_pine_permission(self, username, script_id, action):
        """Manage Pine script permissions"""
        try:
            data = {
                "username": username,
                "scriptId": script_id,
                "action": action
            }
            response = await self.client.post(f"{self.api_url}/pinePermission", json=data)
            return response.json()
        except Exception as e:
            logger.error(f"Error managing pine permission: {str(e)}")
            return {"error": str(e)}
    
    async def get_error_handling(self, error_type):
        """Get error handling information"""
        try:
            params = {
                "errorType": error_type
            }
            response = await self.client.get(f"{self.api_url}/errorHandling", params=params)
            return response.json()
        except Exception as e:
            logger.error(f"Error getting error handling info: {str(e)}")
            return {"error": str(e)}

# Global client instance
tv_client = None

# Request models
class SymbolRequest(BaseModel):
    exchange: Optional[str] = None

class ChartDataRequest(BaseModel):
    symbol: str
    interval: str = "1D"
    range_from: Optional[str] = None
    range_to: Optional[str] = None

# New request models for additional endpoints
class SimpleChartRequest(BaseModel):
    symbol: str
    timeframe: str = "D"
    chart_type: Optional[str] = None

class ReplayModeRequest(BaseModel):
    symbol: str
    timeframe: str = "D"
    start_from: Optional[int] = None
    steps: Optional[int] = None

class LoginRequest(BaseModel):
    username: str
    password: str

class SearchRequest(BaseModel):
    query: str
    exchange: Optional[str] = None

class DrawingsRequest(BaseModel):
    symbol: str

class FromToDataRequest(BaseModel):
    symbol: str
    timeframe: str = "D"
    from_timestamp: Optional[int] = None
    to_timestamp: Optional[int] = None

class IndicatorRequest(BaseModel):
    symbol: str
    indicator: str
    timeframe: str = "D"
    options: Optional[Dict[str, Any]] = None

class CustomTimeframeRequest(BaseModel):
    symbol: str
    timeframe: str

class GraphicIndicatorRequest(BaseModel):
    symbol: str
    indicator: str
    timeframe: str = "D"
    options: Optional[Dict[str, Any]] = None

class MultipleSyncFetchRequest(BaseModel):
    symbols: Union[List[str], str]
    timeframe: str = "D"

class CustomChartTypeRequest(BaseModel):
    symbol: str
    chart_type: str
    timeframe: str = "D"

class FakeReplayModeRequest(BaseModel):
    symbol: str
    timeframe: str = "D"
    bars: Optional[int] = None

class PinePermissionRequest(BaseModel):
    username: str
    script_id: str
    action: str

class ErrorHandlingRequest(BaseModel):
    error_type: str

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

# New routes for additional endpoints
@router.post("/simpleChart")
async def simple_chart(request: SimpleChartRequest):
    """Get a simple chart with customizable parameters"""
    if not tv_client or not tv_client.connected:
        raise HTTPException(status_code=503, detail="TradingView API not connected")
    
    result = await tv_client.get_simple_chart(
        request.symbol,
        request.timeframe,
        request.chart_type
    )
    return result

@router.post("/replayMode")
async def replay_mode(request: ReplayModeRequest):
    """Get data using replay mode"""
    if not tv_client or not tv_client.connected:
        raise HTTPException(status_code=503, detail="TradingView API not connected")
    
    result = await tv_client.get_replay_mode(
        request.symbol,
        request.timeframe,
        request.start_from,
        request.steps
    )
    return result

@router.post("/login")
async def login(request: LoginRequest):
    """Login to TradingView"""
    if not tv_client or not tv_client.connected:
        raise HTTPException(status_code=503, detail="TradingView API not connected")
    
    result = await tv_client.login(
        request.username,
        request.password
    )
    return result

@router.post("/search")
async def search(request: SearchRequest):
    """Search for symbols"""
    if not tv_client or not tv_client.connected:
        raise HTTPException(status_code=503, detail="TradingView API not connected")
    
    result = await tv_client.search(
        request.query,
        request.exchange
    )
    return result

@router.post("/drawings")
async def drawings(request: DrawingsRequest):
    """Get drawings for a symbol"""
    if not tv_client or not tv_client.connected:
        raise HTTPException(status_code=503, detail="TradingView API not connected")
    
    result = await tv_client.get_drawings(request.symbol)
    return result

@router.post("/fromToData")
async def from_to_data(request: FromToDataRequest):
    """Get data for a specific time range"""
    if not tv_client or not tv_client.connected:
        raise HTTPException(status_code=503, detail="TradingView API not connected")
    
    result = await tv_client.get_from_to_data(
        request.symbol,
        request.timeframe,
        request.from_timestamp,
        request.to_timestamp
    )
    return result

@router.post("/builtInIndicator")
async def built_in_indicator(request: IndicatorRequest):
    """Get built-in indicator data"""
    if not tv_client or not tv_client.connected:
        raise HTTPException(status_code=503, detail="TradingView API not connected")
    
    result = await tv_client.get_built_in_indicator(
        request.symbol,
        request.indicator,
        request.timeframe,
        request.options
    )
    return result

@router.post("/customTimeframe")
async def custom_timeframe(request: CustomTimeframeRequest):
    """Get data for a custom timeframe"""
    if not tv_client or not tv_client.connected:
        raise HTTPException(status_code=503, detail="TradingView API not connected")
    
    result = await tv_client.get_custom_timeframe(
        request.symbol,
        request.timeframe
    )
    return result

@router.post("/graphicIndicator")
async def graphic_indicator(request: GraphicIndicatorRequest):
    """Get graphic indicator data"""
    if not tv_client or not tv_client.connected:
        raise HTTPException(status_code=503, detail="TradingView API not connected")
    
    result = await tv_client.get_graphic_indicator(
        request.symbol,
        request.indicator,
        request.timeframe,
        request.options
    )
    return result

@router.post("/multipleSyncFetch") 
async def multiple_sync_fetch(request: MultipleSyncFetchRequest):
    """Get data for multiple symbols"""
    if not tv_client or not tv_client.connected:
        raise HTTPException(status_code=503, detail="TradingView API not connected")
    
    result = await tv_client.get_multiple_sync_fetch(
        request.symbols,
        request.timeframe
    )
    return result

@router.post("/customChartType")
async def custom_chart_type(request: CustomChartTypeRequest):
    """Get data with a custom chart type"""
    if not tv_client or not tv_client.connected:
        raise HTTPException(status_code=503, detail="TradingView API not connected")
    
    result = await tv_client.get_custom_chart_type(
        request.symbol,
        request.chart_type,
        request.timeframe
    )
    return result

@router.post("/fakeReplayMode")
async def fake_replay_mode(request: FakeReplayModeRequest):
    """Get data using fake replay mode"""
    if not tv_client or not tv_client.connected:
        raise HTTPException(status_code=503, detail="TradingView API not connected")
    
    result = await tv_client.get_fake_replay_mode(
        request.symbol,
        request.timeframe,
        request.bars
    )
    return result

@router.get("/privateIndicators")
async def private_indicators():
    """Get all private indicators"""
    if not tv_client or not tv_client.connected:
        raise HTTPException(status_code=503, detail="TradingView API not connected")
    
    result = await tv_client.get_private_indicators()
    return result

@router.post("/pinePermission")
async def pine_permission(request: PinePermissionRequest):
    """Manage Pine script permissions"""
    if not tv_client or not tv_client.connected:
        raise HTTPException(status_code=503, detail="TradingView API not connected")
    
    result = await tv_client.manage_pine_permission(
        request.username,
        request.script_id,
        request.action
    )
    return result

@router.post("/errorHandling")
async def error_handling(request: ErrorHandlingRequest):
    """Get error handling information"""
    if not tv_client or not tv_client.connected:
        raise HTTPException(status_code=503, detail="TradingView API not connected")
    
    result = await tv_client.get_error_handling(request.error_type)
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