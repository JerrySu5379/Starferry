from typing import Dict, Optional, Union, List
import os
from dotenv import load_dotenv
from surrealdb import AsyncSurreal

# Load environment variables
load_dotenv()

class InsufficientGenCoinsException(Exception):
    """Exception raised when a user does not have enough Gen-Coins for an operation."""
    pass

class TokenServiceException(Exception):
    """Exception for general token service errors."""
    pass

def count_tokens(text: str) -> int:
    """Count tokens in a text string.
    
    Args:
        text: The input text to count tokens for
        
    Returns:
        Number of tokens (simple whitespace splitting)
    """
    # Simple token counting based on whitespace splitting; adjust as needed.
    return len(text.split())

# Initialize AsyncSurreal client with environment variables
surreal_client = AsyncSurreal(os.getenv("SURREAL_DB_URL"))

# Model rate configuration (Gen-Coins per token)
# This could be moved to a database or config file later
MODEL_RATES = {
    # OpenAI models
    "gpt-4o-mini": 1,
    "gpt-4o": 2,
    "o3-mini": 2,

    # Gemini models
    "gemini-2.0-pro-exp-02-05": 1.75,
    "gemini-2.0-flash": 1.25,
    "gemini-2.0-flash-lite": 1,
    "gemini-2.0-flash-thinking-exp-01-21": 1.5,
    
    # XAI models
    "grok-2": 1,
    
    # Default rate for unknown models
    "default": 1.0
}

async def initialize_database():
    """Establish connection to SurrealDB and set namespace and database."""
    try:
        await surreal_client.connect()
        await surreal_client.signin({
            "username": os.getenv("SURREAL_DB_USER"),
            "password": os.getenv("SURREAL_PASSWORD")
        })
        await surreal_client.use(
            os.getenv("SURREAL_NS"), 
            os.getenv("SURREAL_DB")
        )
        return True
    except Exception as e:
        raise TokenServiceException(f"Failed to initialize database: {str(e)}")

async def get_user_gen_coins(user_uid: str) -> int:
    """Retrieve the user's Gen-Coins balance from SurrealDB.
    
    Args:
        user_uid: User's unique identifier
        
    Returns:
        Number of Gen-Coins available
    """
    try:
        # Use parameterized query to prevent injection
        result = await surreal_client.query(
            "SELECT gen_coins FROM users WHERE id = $user", 
            {"user": f"users:{user_uid}"}
        )
        
        if result and result[0].get("result") and len(result[0]["result"]) > 0:
            user_data = result[0]["result"][0]
            return user_data.get("gen_coins", 0)
        return 0
    except Exception as e:
        raise TokenServiceException(f"Error retrieving user Gen-Coins: {str(e)}")

async def update_user_gen_coins(user_uid: str, gen_coins: int) -> None:
    """Update the user's Gen-Coins balance in SurrealDB.
    
    Args:
        user_uid: User's unique identifier
        gen_coins: Updated Gen-Coins balance
    """
    try:
        await surreal_client.query(
            "UPDATE users SET gen_coins = $gen_coins WHERE id = $user",
            {
                "gen_coins": gen_coins,
                "user": f"users:{user_uid}"
            }
        )
    except Exception as e:
        raise TokenServiceException(f"Error updating user Gen-Coins: {str(e)}")

def calculate_gen_coin_cost(model: str, tokens_used: int) -> float:
    """Calculate the Gen-Coin cost for using a specific model.
    
    Args:
        model: The model identifier (e.g., "gpt-4", "gemini-pro")
        tokens_used: Number of tokens consumed
        
    Returns:
        Gen-Coin cost as a float
    """
    rate = MODEL_RATES.get(model, MODEL_RATES["default"])
    return rate * tokens_used

async def deduct_gen_coins(user_uid: str, model: str, tokens_used: int) -> None:
    """Deduct Gen-Coins for model usage and record statistics.
    
    Args:
        user_uid: User's unique identifier
        model: Model identifier (e.g., "gpt-4", "gemini-pro")
        tokens_used: Number of tokens consumed
        
    Raises:
        InsufficientGenCoinsException: If user has insufficient Gen-Coins
    """
    # Calculate the cost in Gen-Coins
    cost = calculate_gen_coin_cost(model, tokens_used)
    
    # Get current Gen-Coins balance
    current_gen_coins = await get_user_gen_coins(user_uid)
    
    # Check if sufficient Gen-Coins available
    if current_gen_coins < cost:
        raise InsufficientGenCoinsException(
            f"Insufficient Gen-Coins. Required: {cost:.2f}, Available: {current_gen_coins:.2f}"
        )
    
    # Deduct Gen-Coins
    new_balance = current_gen_coins - cost
    await update_user_gen_coins(user_uid, new_balance)
    
    # Get the service category from the model name
    service = get_service_from_model(model)
    
    # Log usage for analytics
    await log_usage(user_uid, model, service, tokens_used, cost)
    
    return new_balance

def get_service_from_model(model: str) -> str:
    """Determine the service category based on model name.
    
    Args:
        model: Model identifier
        
    Returns:
        Service category (openai, gemini, xai, etc.)
    """
    if model.startswith("gpt"):
        return "openai"
    elif model.startswith("gemini"):
        return "gemini"
    elif model.startswith("xai"):
        return "xai"
    else:
        return "other"

async def add_gen_coins(user_uid: str, amount: float) -> float:
    """Add Gen-Coins to a user's account.
    
    Args:
        user_uid: User's unique identifier
        amount: Number of Gen-Coins to add
        
    Returns:
        New Gen-Coins balance
    """
    current_gen_coins = await get_user_gen_coins(user_uid)
    new_balance = current_gen_coins + amount
    await update_user_gen_coins(user_uid, new_balance)
    return new_balance

async def log_usage(user_uid: str, model: str, service: str, tokens_used: int, gen_coins_cost: float) -> None:
    """Log model usage for analytics.
    
    Args:
        user_uid: User's unique identifier
        model: Model used (gpt-4, gemini-pro, etc.)
        service: Service category (openai, gemini, etc.)
        tokens_used: Number of tokens consumed
        gen_coins_cost: Cost in Gen-Coins
    """
    try:
        await surreal_client.query(
            """
            CREATE usage SET 
                user = $user, 
                model = $model,
                service = $service, 
                tokens = $tokens,
                gen_coins_cost = $cost,
                timestamp = time::now()
            """,
            {
                "user": f"users:{user_uid}",
                "model": model,
                "service": service,
                "tokens": tokens_used,
                "cost": gen_coins_cost
            }
        )
    except Exception as e:
        # Log the error but don't fail the operation
        print(f"Error logging usage: {str(e)}")

async def get_usage_statistics(user_uid: str) -> Dict:
    """Get usage statistics for a user.
    
    Args:
        user_uid: User's unique identifier
        
    Returns:
        Dictionary with usage statistics by model, service, and totals
    """
    try:
        # Get statistics by model
        model_stats = await surreal_client.query(
            """
            SELECT 
                model,
                math::sum(tokens) as total_tokens,
                math::sum(gen_coins_cost) as total_cost
            FROM usage
            WHERE user = $user
            GROUP BY model
            """,
            {"user": f"users:{user_uid}"}
        )
        
        # Get statistics by service
        service_stats = await surreal_client.query(
            """
            SELECT 
                service,
                math::sum(tokens) as total_tokens,
                math::sum(gen_coins_cost) as total_cost
            FROM usage
            WHERE user = $user
            GROUP BY service
            """,
            {"user": f"users:{user_uid}"}
        )
        
        # Get overall totals
        totals = await surreal_client.query(
            """
            SELECT 
                math::sum(tokens) as total_tokens,
                math::sum(gen_coins_cost) as total_cost
            FROM usage
            WHERE user = $user
            """,
            {"user": f"users:{user_uid}"}
        )
        
        return {
            "by_model": model_stats[0].get("result", []) if model_stats and model_stats[0].get("result") else [],
            "by_service": service_stats[0].get("result", []) if service_stats and service_stats[0].get("result") else [],
            "totals": totals[0].get("result", [{}])[0] if totals and totals[0].get("result") else {}
        }
    except Exception as e:
        raise TokenServiceException(f"Error getting usage statistics: {str(e)}")

async def check_user_exists(user_uid: str) -> bool:
    """Check if a user exists in the database.
    
    Args:
        user_uid: User's unique identifier
        
    Returns:
        True if user exists, False otherwise
    """
    try:
        result = await surreal_client.query(
            "SELECT * FROM users WHERE id = $user",
            {"user": f"users:{user_uid}"}
        )
        
        return result and result[0].get("result") and len(result[0]["result"]) > 0
    except Exception as e:
        raise TokenServiceException(f"Error checking if user exists: {str(e)}")

async def create_user(user_uid: str, initial_gen_coins: float = 0) -> None:
    """Create a new user with initial Gen-Coins.
    
    Args:
        user_uid: User's unique identifier
        initial_gen_coins: Initial Gen-Coins balance
    """
    try:
        # Check if user already exists
        if await check_user_exists(user_uid):
            raise TokenServiceException(f"User {user_uid} already exists")
            
        # Create new user
        await surreal_client.query(
            "CREATE users:$uid SET gen_coins = $gen_coins, created_at = time::now()",
            {
                "uid": user_uid,
                "gen_coins": initial_gen_coins
            }
        )
    except Exception as e:
        if "already exists" not in str(e):
            raise TokenServiceException(f"Error creating user: {str(e)}")

async def get_model_rates() -> Dict[str, float]:
    """Get the current rate configuration for all models.
    
    Returns:
        Dictionary mapping model names to Gen-Coin rates
    """
    return MODEL_RATES.copy()