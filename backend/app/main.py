"""
DataPrism FastAPI Application
Main entry point for the backend API
"""
import os
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.auth import verify_api_key
from app.models.responses import (
    HealthResponse,
    DatabaseListResponse,
    SchemaResponse,
    ErrorResponse,
    TextToSQLRequest,
    TextToSQLResponse,
    SQLMetadata,
    ExecuteRequest,
    ExecuteResponse
)
from app.services.database import get_db_service
from app.services.schema import SchemaExtractorFactory
from app.services.text_to_sql import BaselineSQLGenerator
from app.services.executor import SQLExecutor, SQLExecutionError

# Load environment variables from .env file in project root
env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(dotenv_path=env_path)


# Application version
VERSION = "0.1.0"

# Create FastAPI application
app = FastAPI(
    title="DataPrism API",
    description="Text-to-SQL system with baseline and enhanced generation",
    version=VERSION,
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware - allow frontend to access API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://*.vercel.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get(
    "/api/health",
    response_model=HealthResponse,
    tags=["System"],
    summary="Health check",
    description="Check if the API is running. No authentication required."
)
async def health_check():
    """
    Health check endpoint - returns API status, version, and timestamp

    No API key required for this endpoint.
    """
    return HealthResponse(
        status="healthy",
        version=VERSION,
        timestamp=datetime.utcnow()
    )


@app.get(
    "/api/databases",
    response_model=DatabaseListResponse,
    responses={
        401: {"model": ErrorResponse, "description": "Missing API key"},
        403: {"model": ErrorResponse, "description": "Invalid API key"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    },
    tags=["Database"],
    summary="Get database list",
    description="Retrieve list of available Spider databases. Requires API key authentication."
)
async def get_databases(api_key: str = Depends(verify_api_key)):
    """
    Get list of available databases (schemas) from Supabase

    Requires: X-API-Key header

    Returns:
        DatabaseListResponse with list of database names and count
    """
    try:
        db_service = get_db_service()
        databases = db_service.get_databases()

        return DatabaseListResponse(
            databases=databases,
            count=len(databases)
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve databases: {str(e)}"
        )


@app.get(
    "/api/schema/{database}",
    response_model=SchemaResponse,
    responses={
        401: {"model": ErrorResponse, "description": "Missing API key"},
        403: {"model": ErrorResponse, "description": "Invalid API key"},
        404: {"model": ErrorResponse, "description": "Database not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    },
    tags=["Database"],
    summary="Get database schema",
    description="Extract complete schema for a specific database. Requires API key authentication."
)
async def get_schema(database: str, api_key: str = Depends(verify_api_key)):
    """
    Extract complete database schema including tables, columns, and foreign keys

    Args:
        database: Database name (e.g., 'world_1', 'car_1')

    Requires: X-API-Key header

    Returns:
        SchemaResponse with database schema information
    """
    try:
        # Check if database exists
        db_service = get_db_service()
        if not db_service.database_exists(database):
            raise HTTPException(
                status_code=404,
                detail=f"Database '{database}' not found"
            )

        # Extract schema using factory
        extractor = SchemaExtractorFactory.create(
            db_type='postgresql',
            connection_string=os.getenv('DATABASE_URL'),
            schema_name=database
        )

        schema = extractor.extract_full_schema()

        return SchemaResponse(**schema)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to extract schema: {str(e)}"
        )


@app.post(
    "/api/text-to-sql/baseline",
    response_model=TextToSQLResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid request"},
        401: {"model": ErrorResponse, "description": "Missing API key"},
        403: {"model": ErrorResponse, "description": "Invalid API key"},
        404: {"model": ErrorResponse, "description": "Database not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    },
    tags=["Text-to-SQL"],
    summary="Generate SQL (Baseline)",
    description="Generate SQL query from natural language using schema only (baseline approach)"
)
async def generate_baseline_sql(
    request: TextToSQLRequest,
    api_key: str = Depends(verify_api_key)
):
    """
    Generate SQL query from natural language question using baseline approach

    This endpoint uses only the database schema (no RAG, examples, or history).

    Args:
        request: TextToSQLRequest with question and database name

    Requires: X-API-Key header

    Returns:
        TextToSQLResponse with SQL, explanation, and metadata
    """
    try:
        # Validate request
        if not request.question or not request.question.strip():
            raise HTTPException(
                status_code=400,
                detail="Question cannot be empty"
            )

        if not request.database or not request.database.strip():
            raise HTTPException(
                status_code=400,
                detail="Database name cannot be empty"
            )

        # Check if database exists
        db_service = get_db_service()
        if not db_service.database_exists(request.database):
            raise HTTPException(
                status_code=404,
                detail=f"Database '{request.database}' not found"
            )

        # Generate SQL using baseline generator
        generator = BaselineSQLGenerator(
            database_url=os.getenv('DATABASE_URL'),
            database_name=request.database
        )

        result = generator.generate_sql(request.question)

        # Build response
        return TextToSQLResponse(
            sql=result["sql"],
            explanation=result["explanation"],
            metadata=SQLMetadata(**result["metadata"])
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate SQL: {str(e)}"
        )


@app.post(
    "/api/execute",
    response_model=ExecuteResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid request or dangerous SQL"},
        401: {"model": ErrorResponse, "description": "Missing API key"},
        403: {"model": ErrorResponse, "description": "Invalid API key"},
        404: {"model": ErrorResponse, "description": "Database not found"},
        500: {"model": ErrorResponse, "description": "SQL execution error"}
    },
    tags=["SQL Execution"],
    summary="Execute SQL query",
    description="Execute a SELECT query and return results. Only read-only operations are allowed."
)
async def execute_sql(
    request: ExecuteRequest,
    api_key: str = Depends(verify_api_key)
):
    """
    Execute SQL query on specified database

    Only SELECT queries are allowed. INSERT, UPDATE, DELETE, DROP, etc. are blocked.

    Args:
        request: ExecuteRequest with SQL and database name

    Requires: X-API-Key header

    Returns:
        ExecuteResponse with query results and metadata
    """
    try:
        # Validate request
        if not request.sql or not request.sql.strip():
            raise HTTPException(
                status_code=400,
                detail="SQL query cannot be empty"
            )

        if not request.database or not request.database.strip():
            raise HTTPException(
                status_code=400,
                detail="Database name cannot be empty"
            )

        # Check if database exists
        db_service = get_db_service()
        if not db_service.database_exists(request.database):
            raise HTTPException(
                status_code=404,
                detail=f"Database '{request.database}' not found"
            )

        # Execute SQL query
        executor = SQLExecutor(
            database_url=os.getenv('DATABASE_URL'),
            schema_name=request.database,
            max_rows=1000,  # Limit results to 1000 rows
            timeout_seconds=30  # 30 second timeout
        )

        result = executor.execute(request.sql)

        # Build response
        return ExecuteResponse(
            results=result["results"],
            columns=result["columns"],
            row_count=result["row_count"],
            execution_time_ms=result["execution_time_ms"],
            truncated=result["truncated"],
            database=request.database
        )

    except SQLExecutionError as e:
        # SQL execution or validation errors
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to execute query: {str(e)}"
        )


@app.get("/", tags=["System"])
async def root():
    """Root endpoint - redirect to docs"""
    return {
        "message": "DataPrism API",
        "version": VERSION,
        "docs": "/docs",
        "health": "/api/health"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
