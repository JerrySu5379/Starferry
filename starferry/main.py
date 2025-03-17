from fastapi import FastAPI
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import asyncio
import os
import importlib
import pkgutil
import logging

# Load environment variables first
load_dotenv(dotenv_path=os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'))

from starferry.routers import bingo
from starferry.utils.ip_tracker import cleanup_ip_tracker

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PluginManager:
    """Manages plugins for Starferry core"""
    def __init__(self):
        self.plugins = {}
        self.plugin_routers = {}
    
    async def load_plugins(self, app):
        """Load all plugins from the plugins directory"""
        plugins_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'plugins')
        if not os.path.exists(plugins_dir):
            os.makedirs(plugins_dir)
            logger.info(f"Created plugins directory at {plugins_dir}")
            return
        
        # Find all plugin modules
        for finder, name, ispkg in pkgutil.iter_modules([plugins_dir]):
            if ispkg:
                try:
                    # Import the plugin package
                    plugin_module = importlib.import_module(f"plugins.{name}")
                    
                    # Check if the plugin has a setup function
                    if hasattr(plugin_module, 'setup'):
                        # Setup the plugin
                        plugin_router = await plugin_module.setup(app)
                        if plugin_router:
                            # Add the plugin router to FastAPI
                            app.include_router(plugin_router, prefix=f"/plugins/{name}", tags=[name])
                            self.plugin_routers[name] = plugin_router
                        
                        self.plugins[name] = plugin_module
                        logger.info(f"Loaded plugin: {name}")
                except Exception as e:
                    logger.error(f"Failed to load plugin {name}: {str(e)}")

    async def shutdown_plugins(self):
        """Shutdown all plugins"""
        for name, plugin in self.plugins.items():
            if hasattr(plugin, 'shutdown'):
                try:
                    await plugin.shutdown()
                    logger.info(f"Shutdown plugin: {name}")
                except Exception as e:
                    logger.error(f"Error shutting down plugin {name}: {str(e)}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize plugin manager
    plugin_manager = PluginManager()
    app.state.plugin_manager = plugin_manager
    
    # Load plugins
    await plugin_manager.load_plugins(app)
    
    # Start background task
    cleanup_task = asyncio.create_task(cleanup_ip_tracker())
    
    yield
    
    # Shutdown plugins
    await plugin_manager.shutdown_plugins()
    
    # Cleanup
    cleanup_task.cancel()
    try:
        await cleanup_task
    except asyncio.CancelledError:
        pass

# Create FastAPI app
app = FastAPI(
    title="Starferry API",
    description="Starferry with plugin architecture for AI agents",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(bingo.router, prefix="/api", tags=["bingo"])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("starferry.main:app", host="0.0.0.0", port=8008, reload=True)