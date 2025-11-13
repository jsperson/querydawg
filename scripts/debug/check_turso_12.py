#!/usr/bin/env python3
"""Quick script to check Turso 12 benchmark results"""
import sys
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

sys.path.insert(0, 'backend')

from app.database.supabase_client import SupabaseClient

# Get credentials from environment
supabase_url = os.getenv('SUPABASE_URL')
service_role_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')

if not supabase_url or not service_role_key:
    print("ERROR: Missing SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY environment variables")
    sys.exit(1)

# Initialize client
sb_client = SupabaseClient(supabase_url, service_role_key)
supabase = sb_client.client

# Get Turso 12 benchmark
result = supabase.table('benchmark_runs').select('*').eq('name', 'Full Spider 1.0 Turso 12').single().execute()

if result.data:
    bench = result.data
    print('=' * 70)
    print('TURSO 12 RESULTS')
    print('=' * 70)
    print(f'ID: {bench["id"]}')
    print(f'Name: {bench["name"]}')
    print(f'Status: {bench.get("status")}')
    print()
    print(f'Baseline Exec Match: {bench.get("baseline_exec_match", 0):.1%}')
    print(f'Enhanced Exec Match: {bench.get("enhanced_exec_match", 0):.1%}')
    print(f'Baseline Exact Match: {bench.get("baseline_exact_match", 0):.1%}')
    print(f'Enhanced Exact Match: {bench.get("enhanced_exact_match", 0):.1%}')
    print()

    # Compare with Turso 9 (before Phase 1) and Turso 11 (after Phase 1)
    turso_9 = supabase.table('benchmark_runs').select('*').eq('name', 'Full Spider 1.0 Turso 9').single().execute()
    turso_11 = supabase.table('benchmark_runs').select('*').eq('name', 'Full Spider 1.0 Turso 11').single().execute()

    print('=' * 70)
    print('PHASE 1 VALIDATION')
    print('=' * 70)
    print(f'Turso 9 (Before):  Baseline {turso_9.data["baseline_exec_match"]:.1%}, Enhanced {turso_9.data["enhanced_exec_match"]:.1%}')
    print(f'Turso 11 (After):  Baseline {turso_11.data["baseline_exec_match"]:.1%}, Enhanced {turso_11.data["enhanced_exec_match"]:.1%}')
    print(f'Turso 12 (Verify): Baseline {bench["baseline_exec_match"]:.1%}, Enhanced {bench["enhanced_exec_match"]:.1%}')
    print()

    # Calculate improvements
    baseline_improvement_9 = bench['baseline_exec_match'] - turso_9.data['baseline_exec_match']
    enhanced_improvement_9 = bench['enhanced_exec_match'] - turso_9.data['enhanced_exec_match']

    baseline_improvement_11 = bench['baseline_exec_match'] - turso_11.data['baseline_exec_match']
    enhanced_improvement_11 = bench['enhanced_exec_match'] - turso_11.data['enhanced_exec_match']

    print('=' * 70)
    print('IMPROVEMENTS')
    print('=' * 70)
    print(f'From Turso 9:')
    print(f'  Baseline: {baseline_improvement_9:+.1%}')
    print(f'  Enhanced: {enhanced_improvement_9:+.1%}')
    print()
    print(f'From Turso 11 (consistency check):')
    print(f'  Baseline: {baseline_improvement_11:+.1%}')
    print(f'  Enhanced: {enhanced_improvement_11:+.1%}')
    print()
    print(f'Enhanced advantage: +{bench["enhanced_exec_match"] - bench["baseline_exec_match"]:.1%}')
    print()

    # Check if results are consistent
    if abs(baseline_improvement_11) < 0.02 and abs(enhanced_improvement_11) < 0.02:
        print('✅ VALIDATION: Results consistent with Turso 11 (Phase 1 improvements stable)')
    else:
        print('⚠️  WARNING: Results differ from Turso 11 by more than 2%')
else:
    print('Turso 12 not found')
