"""
Supabase operations for benchmark system
"""
from typing import List, Optional, Dict, Any
from datetime import datetime
from decimal import Decimal
import uuid

from .supabase_client import SupabaseClient
from ..models.benchmark import (
    BenchmarkRunCreate,
    BenchmarkRunResponse,
    BenchmarkSummary,
    BenchmarkResult,
    AggregatedStats,
    BenchmarkSummaryStats
)


class BenchmarkStore(SupabaseClient):
    """
    Handles all Supabase operations for benchmark system.

    Inherits automatic retry logic from SupabaseClient for all database operations.
    """

    def __init__(self, supabase_url: str, service_role_key: str):
        """Initialize Supabase client with retry logic"""
        super().__init__(supabase_url, service_role_key)

    def create_run(self, config: BenchmarkRunCreate) -> str:
        """
        Create new benchmark run

        Returns:
            run_id (UUID as string)
        """
        data = {
            "name": config.name,
            "run_type": config.run_type,
            "question_count": config.question_count,
            "databases": config.databases,
            "status": "pending",
            "completed_count": 0,
            "failed_count": 0,
            "total_cost_usd": 0,
            "created_by": config.created_by,
            "notes": config.notes
        }

        result = self.client.table("benchmark_runs").insert(data).execute()
        return result.data[0]["id"]

    def update_run_status(
        self,
        run_id: str,
        status: str,
        status_reason: Optional[str] = None,
        error: Optional[str] = None
    ):
        """Update run status and optionally set timestamps"""
        updates = {"status": status}

        if status_reason:
            updates["status_reason"] = status_reason

        if error:
            updates["last_error"] = error

        # Set appropriate timestamp
        if status == "running" and "started_at" not in updates:
            updates["started_at"] = datetime.utcnow().isoformat()
        elif status == "completed":
            updates["completed_at"] = datetime.utcnow().isoformat()
        elif status == "cancelled":
            updates["cancelled_at"] = datetime.utcnow().isoformat()

        self.client.table("benchmark_runs").update(updates).eq("id", run_id).execute()

    def update_run_progress(
        self,
        run_id: str,
        completed: int,
        failed: int,
        current_question: Optional[str] = None
    ):
        """Update progress counters (retry logic inherited from SupabaseClient)"""
        updates = {
            "completed_count": completed,
            "failed_count": failed,
        }

        # Always update current_question (None clears it)
        updates["current_question"] = current_question

        self.client.table("benchmark_runs").update(updates).eq("id", run_id).execute()

    def update_run_cost(self, run_id: str, additional_cost: float, approach: str):
        """Add cost to running total"""
        # Get current costs
        result = (
            self.client.table("benchmark_runs")
            .select("total_cost_usd, baseline_cost_usd, enhanced_cost_usd")
            .eq("id", run_id)
            .execute()
        )

        if not result.data:
            return

        current = result.data[0]
        total = float(current["total_cost_usd"] or 0) + additional_cost

        updates = {"total_cost_usd": total}

        if approach == "baseline":
            baseline = float(current["baseline_cost_usd"] or 0) + additional_cost
            updates["baseline_cost_usd"] = baseline
        elif approach == "enhanced":
            enhanced = float(current["enhanced_cost_usd"] or 0) + additional_cost
            updates["enhanced_cost_usd"] = enhanced

        self.client.table("benchmark_runs").update(updates).eq("id", run_id).execute()

    def save_result(self, result: BenchmarkResult):
        """Save individual question result"""
        data = result.model_dump(exclude_none=False)

        # Convert Decimal to float for JSON serialization
        for key in data:
            if isinstance(data[key], Decimal):
                data[key] = float(data[key])

        self.client.table("benchmark_results").insert(data).execute()

    def get_run_status(self, run_id: str) -> Optional[BenchmarkRunResponse]:
        """Get current run status for progress monitoring"""
        result = (
            self.client.table("benchmark_runs")
            .select("*")
            .eq("id", run_id)
            .execute()
        )

        if not result.data:
            return None

        run = result.data[0]

        # Calculate progress
        completed = run["completed_count"]
        total = run["question_count"]
        progress = completed / total if total > 0 else 0.0

        # Calculate running metrics from completed results so far
        baseline_exec_match_rate = None
        baseline_correct_count = None
        enhanced_exec_match_rate = None
        enhanced_correct_count = None

        if completed > 0:
            # Use limited fetch with aggregation to avoid Supabase timeouts
            # Fetch only the match columns (small payload) with limit
            try:
                results = (
                    self.client.table("benchmark_results")
                    .select("baseline_exec_match, enhanced_exec_match")
                    .eq("run_id", run_id)
                    .limit(1000)  # Limit to most recent 1000 for performance
                    .execute()
                )

                if results.data:
                    # Calculate baseline metrics
                    baseline_results = [r for r in results.data if r.get("baseline_exec_match") is not None]
                    if baseline_results:
                        baseline_correct_count = sum(1 for r in baseline_results if r.get("baseline_exec_match") is True)
                        baseline_exec_match_rate = baseline_correct_count / len(baseline_results)

                    # Calculate enhanced metrics
                    enhanced_results = [r for r in results.data if r.get("enhanced_exec_match") is not None]
                    if enhanced_results:
                        enhanced_correct_count = sum(1 for r in enhanced_results if r.get("enhanced_exec_match") is True)
                        enhanced_exec_match_rate = enhanced_correct_count / len(enhanced_results)
            except Exception as e:
                # If status query fails, don't crash - just skip running metrics
                print(f"Warning: Failed to fetch running metrics: {e}")
                pass

        return BenchmarkRunResponse(
            id=run["id"],
            name=run["name"],
            run_type=run["run_type"],
            status=run["status"],
            progress=progress,
            completed_count=completed,
            failed_count=run["failed_count"],
            question_count=total,
            current_question=run.get("current_question"),
            total_cost_usd=Decimal(str(run.get("total_cost_usd", 0))),
            created_at=datetime.fromisoformat(run["created_at"]),
            started_at=datetime.fromisoformat(run["started_at"]) if run.get("started_at") else None,
            baseline_exec_match_rate=baseline_exec_match_rate,
            baseline_correct_count=baseline_correct_count,
            enhanced_exec_match_rate=enhanced_exec_match_rate,
            enhanced_correct_count=enhanced_correct_count
        )

    def calculate_and_save_metrics(self, run_id: str):
        """Calculate final metrics and save to benchmark_runs"""
        # Get all results for this run
        results = (
            self.client.table("benchmark_results")
            .select("*")
            .eq("run_id", run_id)
            .execute()
        )

        if not results.data:
            return

        total = len(results.data)

        # Calculate baseline metrics (count True values, handle None properly)
        baseline_exact_count = sum(1 for r in results.data if r.get("baseline_exact_match") is True)
        baseline_exact_total = sum(1 for r in results.data if r.get("baseline_exact_match") is not None)
        baseline_exec_count = sum(1 for r in results.data if r.get("baseline_exec_match") is True)
        baseline_exec_total = sum(1 for r in results.data if r.get("baseline_exec_match") is not None)

        # Calculate enhanced metrics (count True values, handle None properly)
        enhanced_exact_count = sum(1 for r in results.data if r.get("enhanced_exact_match") is True)
        enhanced_exact_total = sum(1 for r in results.data if r.get("enhanced_exact_match") is not None)
        enhanced_exec_count = sum(1 for r in results.data if r.get("enhanced_exec_match") is True)
        enhanced_exec_total = sum(1 for r in results.data if r.get("enhanced_exec_match") is not None)

        updates = {
            "baseline_exact_match": baseline_exact_count / baseline_exact_total if baseline_exact_total > 0 else None,
            "baseline_exec_match": baseline_exec_count / baseline_exec_total if baseline_exec_total > 0 else None,
            "enhanced_exact_match": enhanced_exact_count / enhanced_exact_total if enhanced_exact_total > 0 else None,
            "enhanced_exec_match": enhanced_exec_count / enhanced_exec_total if enhanced_exec_total > 0 else None,
        }

        # Debug logging
        print(f"Metrics calculation for run {run_id}:")
        print(f"  Total results: {total}")
        print(f"  Baseline exact: {baseline_exact_count}/{baseline_exact_total} = {updates['baseline_exact_match']}")
        print(f"  Baseline exec: {baseline_exec_count}/{baseline_exec_total} = {updates['baseline_exec_match']}")
        print(f"  Enhanced exact: {enhanced_exact_count}/{enhanced_exact_total} = {updates['enhanced_exact_match']}")
        print(f"  Enhanced exec: {enhanced_exec_count}/{enhanced_exec_total} = {updates['enhanced_exec_match']}")

        self.client.table("benchmark_runs").update(updates).eq("id", run_id).execute()

    def get_run_summary(self, run_id: str) -> Optional[BenchmarkSummary]:
        """Get complete summary with all metrics"""
        result = (
            self.client.table("benchmark_runs")
            .select("*")
            .eq("id", run_id)
            .execute()
        )

        if not result.data:
            return None

        run = result.data[0]

        return BenchmarkSummary(
            run_id=run["id"],
            name=run["name"],
            run_type=run["run_type"],
            status=run["status"],
            status_reason=run.get("status_reason"),
            total_questions=run["question_count"],
            completed=run["completed_count"],
            failed=run["failed_count"],
            baseline_exact_match_rate=float(run["baseline_exact_match"]) if run.get("baseline_exact_match") else None,
            baseline_exec_match_rate=float(run["baseline_exec_match"]) if run.get("baseline_exec_match") else None,
            baseline_total_cost=float(run["baseline_cost_usd"]) if run.get("baseline_cost_usd") else None,
            enhanced_exact_match_rate=float(run["enhanced_exact_match"]) if run.get("enhanced_exact_match") else None,
            enhanced_exec_match_rate=float(run["enhanced_exec_match"]) if run.get("enhanced_exec_match") else None,
            enhanced_total_cost=float(run["enhanced_cost_usd"]) if run.get("enhanced_cost_usd") else None,
            total_time_ms=run.get("total_time_ms"),
            created_at=datetime.fromisoformat(run["created_at"]),
            started_at=datetime.fromisoformat(run["started_at"]) if run.get("started_at") else None,
            completed_at=datetime.fromisoformat(run["completed_at"]) if run.get("completed_at") else None,
        )

    def get_aggregated_stats(self, run_id: str) -> BenchmarkSummaryStats:
        """Get pre-aggregated statistics for charts"""
        # This would ideally be done with SQL aggregation queries
        # For now, we'll fetch all results and aggregate in Python
        results = (
            self.client.table("benchmark_results")
            .select("*")
            .eq("run_id", run_id)
            .execute()
        )

        if not results.data:
            return BenchmarkSummaryStats(
                by_database=[],
                by_difficulty=[],
                overall=AggregatedStats(total=0)
            )

        # Aggregate by database
        db_stats: Dict[str, Dict[str, int]] = {}
        diff_stats: Dict[str, Dict[str, int]] = {}

        for r in results.data:
            db = r["database"]
            diff = r.get("difficulty", "unknown")

            # Initialize if needed
            if db not in db_stats:
                db_stats[db] = {"total": 0, "baseline": 0, "enhanced": 0}
            if diff not in diff_stats:
                diff_stats[diff] = {"total": 0, "baseline": 0, "enhanced": 0}

            # Count totals
            db_stats[db]["total"] += 1
            diff_stats[diff]["total"] += 1

            # Count correct
            if r.get("baseline_exact_match"):
                db_stats[db]["baseline"] += 1
                diff_stats[diff]["baseline"] += 1
            if r.get("enhanced_exact_match"):
                db_stats[db]["enhanced"] += 1
                diff_stats[diff]["enhanced"] += 1

        # Convert to AggregatedStats
        by_database = [
            AggregatedStats(
                database=db,
                total=stats["total"],
                baseline_correct=stats["baseline"],
                enhanced_correct=stats["enhanced"],
                baseline_accuracy=stats["baseline"] / stats["total"] if stats["total"] > 0 else 0,
                enhanced_accuracy=stats["enhanced"] / stats["total"] if stats["total"] > 0 else 0
            )
            for db, stats in db_stats.items()
        ]

        by_difficulty = [
            AggregatedStats(
                difficulty=diff,
                total=stats["total"],
                baseline_correct=stats["baseline"],
                enhanced_correct=stats["enhanced"],
                baseline_accuracy=stats["baseline"] / stats["total"] if stats["total"] > 0 else 0,
                enhanced_accuracy=stats["enhanced"] / stats["total"] if stats["total"] > 0 else 0
            )
            for diff, stats in diff_stats.items()
        ]

        # Overall stats
        total = len(results.data)
        baseline_total = sum(1 for r in results.data if r.get("baseline_exact_match"))
        enhanced_total = sum(1 for r in results.data if r.get("enhanced_exact_match"))

        overall = AggregatedStats(
            total=total,
            baseline_correct=baseline_total,
            enhanced_correct=enhanced_total,
            baseline_accuracy=baseline_total / total if total > 0 else 0,
            enhanced_accuracy=enhanced_total / total if total > 0 else 0
        )

        return BenchmarkSummaryStats(
            by_database=by_database,
            by_difficulty=by_difficulty,
            overall=overall
        )

    def get_run_results(
        self,
        run_id: str,
        database: Optional[str] = None,
        difficulty: Optional[str] = None,
        show_failures_only: bool = False,
        limit: int = 100,
        offset: int = 0
    ) -> tuple[List[BenchmarkResult], int]:
        """
        Get detailed results with filtering and pagination

        Returns:
            (results, total_count)
        """
        query = self.client.table("benchmark_results").select("*", count="exact").eq("run_id", run_id)

        # Apply filters
        if database:
            query = query.eq("database", database)
        if difficulty:
            query = query.eq("difficulty", difficulty)
        if show_failures_only:
            query = query.or_("baseline_exact_match.eq.false,enhanced_exact_match.eq.false")

        # Get total count for pagination
        count_result = query.execute()
        total = count_result.count if hasattr(count_result, 'count') else 0

        # Apply pagination
        result = query.range(offset, offset + limit - 1).execute()

        results = [BenchmarkResult(**r) for r in result.data]

        return results, total

    def list_runs(self, limit: int = 50) -> List[BenchmarkSummary]:
        """List all benchmark runs, most recent first"""
        results = (
            self.client.table("benchmark_runs")
            .select("*")
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
        )

        return [
            BenchmarkSummary(
                run_id=r["id"],
                name=r["name"],
                run_type=r["run_type"],
                status=r["status"],
                status_reason=r.get("status_reason"),
                total_questions=r["question_count"],
                completed=r["completed_count"],
                failed=r["failed_count"],
                baseline_exact_match_rate=float(r["baseline_exact_match"]) if r.get("baseline_exact_match") else None,
                baseline_exec_match_rate=float(r["baseline_exec_match"]) if r.get("baseline_exec_match") else None,
                baseline_total_cost=float(r["baseline_cost_usd"]) if r.get("baseline_cost_usd") else None,
                enhanced_exact_match_rate=float(r["enhanced_exact_match"]) if r.get("enhanced_exact_match") else None,
                enhanced_exec_match_rate=float(r["enhanced_exec_match"]) if r.get("enhanced_exec_match") else None,
                enhanced_total_cost=float(r["enhanced_cost_usd"]) if r.get("enhanced_cost_usd") else None,
                total_time_ms=r.get("total_time_ms"),
                created_at=datetime.fromisoformat(r["created_at"]),
                started_at=datetime.fromisoformat(r["started_at"]) if r.get("started_at") else None,
                completed_at=datetime.fromisoformat(r["completed_at"]) if r.get("completed_at") else None,
            )
            for r in results.data
        ]

    def delete_run(self, run_id: str) -> bool:
        """
        Delete benchmark run and all results (CASCADE)

        Returns:
            True if deleted, False if not found
        """
        result = self.client.table("benchmark_runs").delete().eq("id", run_id).execute()
        return len(result.data) > 0


# Singleton instance
_benchmark_store: Optional[BenchmarkStore] = None


def get_benchmark_store(supabase_url: str, service_role_key: str) -> BenchmarkStore:
    """Get or create benchmark store singleton"""
    global _benchmark_store
    if _benchmark_store is None:
        _benchmark_store = BenchmarkStore(supabase_url, service_role_key)
    return _benchmark_store
