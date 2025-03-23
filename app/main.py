"""
API for property document classification and extraction.

This module initializes the FastAPI application, sets up middleware,
and configures the Supabase client for database interactions.

Summary:
    This module serves as the entry point for the application, 
    initializing the FastAPI app, setting up CORS middleware, 
    and configuring the Supabase client. It also defines startup 
    and health check events.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from supabase import Client, create_client
from supabase.lib.client_options import ClientOptions

from .core.config import get_settings
from .core.logging import logger
from .api.endpoints import documents
from .api.endpoints import contract_templates
from .services.contract_manager import ContractManager

settings = get_settings()

try:
    # Create Supabase client with proper configuration
    options = ClientOptions(
        schema="public",
        headers={"apiKey": settings.SUPABASE_KEY},
        auto_refresh_token=False,
        persist_session=False
    )
    
    # Create Supabase client with anon key
    supabase: Client = create_client(
        settings.SUPABASE_URL,
        settings.SUPABASE_KEY,
        options
    )
except Exception as e:
    logger.error(f"Failed to initialize Supabase client: {str(e)}")
    logger.error("Supabase client initialization error details: %s", str(e))
    raise

# Create FastAPI app
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="API for property document classification and extraction"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
contract_manager = ContractManager(supabase)

# Include routers
app.include_router(
    documents.router,
    prefix=f"{settings.API_V1_STR}/documents",
    tags=["documents"]
)

app.include_router(
    contract_templates.router,
    prefix=f"{settings.API_V1_STR}",
    tags=["contract_templates"]
)

# Initialize services on startup.
# Logs the initialization process.
#
# This function is called when the application starts.
# It initializes the services and logs the process.
#
# Returns:
#     None
@app.on_event("startup")
async def startup_event():
    """
    Initialize services on startup.
    Logs the initialization process.
    
    This function is called when the application starts.
    It initializes the services and logs the process.
    
    Returns:
        None
    """
    try:
        logger.info("Initializing services...")
        # Add any additional startup logic here
        logger.info("Services initialized successfully")
    except Exception as e:
        logger.error(f"Error during startup: {str(e)}")
        logger.error("Startup error details: %s", str(e))
        raise

# Health check endpoint.
# Returns the health status of the application.
#
# This endpoint checks the health of the application and returns the status.
#
# Returns:
#     dict: Health status and version of the application.
@app.get("/health")
async def health_check():
    """
    Health check endpoint.
    Returns the health status of the application.
    
    This endpoint checks the health of the application and returns the status.
    
    Returns:
        dict: Health status and version of the application.
    """
    try:
        return {"status": "healthy", "version": settings.VERSION}
    except Exception as e:
        logger.error(f"Error during health check: {str(e)}")
        logger.error("Health check error details: %s", str(e))
        raise
if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8080))  # Default to 8080 if PORT is not set
    uvicorn.run(app, host="0.0.0.0", port=port)