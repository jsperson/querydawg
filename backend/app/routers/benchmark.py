"""
FastAPI router for Spider benchmark endpoints
"""
import os
from typing import List, Optional
from fastapi import APIRouter, BackgroundTasks, HTTPException, Depends, Query
from fastapi.responses import JSONResponse

from ..models.benchmark import (
    BenchmarkConfig,
    BenchmarkRunResponse,
    BenchmarkSummary,
    BenchmarkResultsResponse,
    BenchmarkSummaryStats
)
from ..database.benchmark_store import get_benchmark_store, BenchmarkStore
from ..services.benchmark_runner import BenchmarkRunner, BudgetExceededError
from ..middleware.auth import verify_api_key


router = APIRouter(prefix="/api/benchmark", tags=["benchmark"])


def get_runner_instance() -> BenchmarkRunner:
    """Get benchmark runner instance (singleton-ish)"""
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    database_url = os.getenv("DATABASE_URL")

    if not all([supabase_url, supabase_key, database_url]):
        raise HTTPException(
            status_code=500,
            detail="Server configuration error: Missing database credentials"
        )

    store = get_benchmark_store(supabase_url, supabase_key)
    return BenchmarkRunner(
        benchmark_store=store,
        budget_limit_usd=5.0,
        connection_string=database_url
    )


@router.post("/run", response_model=dict)
async def start_benchmark(
    config: BenchmarkConfig,
    background_tasks: BackgroundTasks,
    _: str = Depends(verify_api_key)
):
    """
    Start a new benchmark run in the background

    Returns immediately with run_id, while processing continues in background
    """
    try:
        runner = get_runner_instance()

        # Get question count for response
        questions = runner.load_spider_questions(
            databases=config.databases,
            limit=config.question_limit
        )
        question_count = len(questions)

        # Store config for background task
        config_copy = config

        # Run benchmark in background
        # Note: run_benchmark will create the run record itself
        def run_benchmark_task():
            try:
                run_id = runner.run_benchmark(config_copy)
                print(f"Benchmark {run_id} completed successfully")
            except BudgetExceededError as e:
                print(f"Budget exceeded: {str(e)}")
            except Exception as e:
                print(f"Benchmark failed: {str(e)}")

        # Start background task
        background_tasks.add_task(run_benchmark_task)

        return {
            "status": "started",
            "message": "Benchmark started in background. Use GET /api/benchmark/runs to see status.",
            "question_count": question_count,
            "config": {
                "name": config.name,
                "run_type": config.run_type,
                "databases": config.databases
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/runs", response_model=List[BenchmarkSummary])
async def list_runs(
    limit: int = Query(default=50, ge=1, le=100),
    _: str = Depends(verify_api_key)
):
    """List all benchmark runs, most recent first"""
    try:
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

        if not all([supabase_url, supabase_key]):
            raise HTTPException(status_code=500, detail="Server configuration error")

        store = get_benchmark_store(supabase_url, supabase_key)
        runs = store.list_runs(limit=limit)

        return runs

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/run/{run_id}/status", response_model=BenchmarkRunResponse)
async def get_run_status(
    run_id: str,
    _: str = Depends(verify_api_key)
):
    """Get current status of a running or completed benchmark"""
    try:
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

        if not all([supabase_url, supabase_key]):
            raise HTTPException(status_code=500, detail="Server configuration error")

        store = get_benchmark_store(supabase_url, supabase_key)
        status = store.get_run_status(run_id)

        if not status:
            raise HTTPException(status_code=404, detail="Run not found")

        return status

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/run/{run_id}/summary", response_model=BenchmarkSummary)
async def get_run_summary(
    run_id: str,
    _: str = Depends(verify_api_key)
):
    """Get complete summary with calculated metrics"""
    try:
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

        if not all([supabase_url, supabase_key]):
            raise HTTPException(status_code=500, detail="Server configuration error")

        store = get_benchmark_store(supabase_url, supabase_key)
        summary = store.get_run_summary(run_id)

        if not summary:
            raise HTTPException(status_code=404, detail="Run not found")

        return summary

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/run/{run_id}/stats", response_model=BenchmarkSummaryStats)
async def get_run_stats(
    run_id: str,
    _: str = Depends(verify_api_key)
):
    """Get pre-aggregated statistics for charts (by database, by difficulty, overall)"""
    try:
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

        if not all([supabase_url, supabase_key]):
            raise HTTPException(status_code=500, detail="Server configuration error")

        store = get_benchmark_store(supabase_url, supabase_key)
        stats = store.get_aggregated_stats(run_id)

        return stats

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/run/{run_id}/results", response_model=BenchmarkResultsResponse)
async def get_run_results(
    run_id: str,
    database: Optional[str] = Query(None, description="Filter by database"),
    difficulty: Optional[str] = Query(None, description="Filter by difficulty"),
    failures_only: bool = Query(False, description="Show only failed questions"),
    page: int = Query(1, ge=1),
    page_size: int = Query(100, ge=1, le=500),
    _: str = Depends(verify_api_key)
):
    """
    Get detailed results with filtering and pagination

    Filters:
    - database: Filter to specific database
    - difficulty: Filter by difficulty level
    - failures_only: Show only questions where at least one approach failed
    """
    try:
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

        if not all([supabase_url, supabase_key]):
            raise HTTPException(status_code=500, detail="Server configuration error")

        store = get_benchmark_store(supabase_url, supabase_key)

        offset = (page - 1) * page_size

        results, total = store.get_run_results(
            run_id=run_id,
            database=database,
            difficulty=difficulty,
            show_failures_only=failures_only,
            limit=page_size,
            offset=offset
        )

        # Count filtered results
        filtered = len(results)

        return BenchmarkResultsResponse(
            results=results,
            total=total,
            filtered=filtered,
            page=page,
            page_size=page_size
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/run/{run_id}")
async def delete_run(
    run_id: str,
    _: str = Depends(verify_api_key)
):
    """Delete a benchmark run and all its results"""
    try:
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

        if not all([supabase_url, supabase_key]):
            raise HTTPException(status_code=500, detail="Server configuration error")

        store = get_benchmark_store(supabase_url, supabase_key)
        deleted = store.delete_run(run_id)

        if not deleted:
            raise HTTPException(status_code=404, detail="Run not found")

        return JSONResponse(
            status_code=200,
            content={"message": "Run deleted successfully", "run_id": run_id}
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
