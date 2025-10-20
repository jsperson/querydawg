# Evaluation Directory

Contains evaluation results, analysis notebooks, and test data.

## Structure

```
evaluation/
├── results/               # Evaluation results
│   ├── baseline/         # Schema-only results
│   ├── enhanced_mini/    # With semantic layer + GPT-4o-mini
│   └── enhanced_4o/      # With semantic layer + GPT-4o
├── notebooks/            # Jupyter notebooks for analysis
│   ├── analysis.ipynb
│   ├── visualizations.ipynb
│   └── error_analysis.ipynb
├── reports/              # Generated reports
└── test_questions/       # Test question subsets
```

## Evaluation Process

1. **Run Evaluation:**
   ```bash
   python scripts/run_evaluation.py --test-set dev --count 200
   ```

2. **Analyze Results:**
   ```bash
   python scripts/analyze_results.py --run-id [run-id]
   ```

3. **Generate Report:**
   - Open Jupyter notebooks in `notebooks/`
   - Run analysis and visualization cells
   - Export to PDF/HTML

## Metrics Tracked

- **Execution Accuracy:** % queries returning correct results
- **Valid SQL Rate:** % queries that parse and execute
- **Exact Match Accuracy:** % queries matching gold SQL
- **Average Latency:** Time per query
- **Cost per Query:** OpenAI API cost
- **Error Types:** Categorized error analysis

## Results Format

Results are stored in Supabase `evaluation` schema:
- `evaluation.runs` - Evaluation run metadata
- `evaluation.results` - Individual query results

JSON exports are also saved in `results/` directory.

## Target Metrics

- **Baseline:** 40-50% execution accuracy (estimated)
- **Enhanced:** 60-75% execution accuracy
- **Improvement:** 15-25% absolute improvement
