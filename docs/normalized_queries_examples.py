"""
Example SQL queries demonstrating the benefits of normalized model names.

BEFORE: With raw API strings, queries are complex and error-prone:
- accounts/fireworks/models/llama-v3p3-70b-instruct
- models/gemini-2.5-flash
- meta-llama/Llama-3.3-70B-Instruct

AFTER: With normalized names, queries are clean and consistent:
- llama-3.3-70b-instruct
- gemini-2.5-flash
- llama-3.3-70b-instruct
"""

# ============================================================================
# BEFORE: Complex queries with raw model names
# ============================================================================

query_before_fireworks = """
-- Hard to compare Llama models across providers due to inconsistent naming
SELECT 
    p.name as provider,
    m.name as model,
    AVG(br.total_latency_ms) as avg_latency
FROM benchmark_results br
JOIN providers p ON br.provider_id = p.id
JOIN models m ON br.model_id = m.id
WHERE m.name LIKE '%llama%70%'  -- Unreliable pattern matching
   OR m.name LIKE '%Llama%70%'  -- Case-sensitive variations
   OR m.name LIKE '%70b%'        -- May catch unrelated models
GROUP BY p.name, m.name
ORDER BY avg_latency;
"""

query_before_gemini = """
-- Need to handle Google's "models/" prefix everywhere
SELECT 
    m.name as model,
    AVG(br.cost_usd) as avg_cost
FROM benchmark_results br
JOIN models m ON br.model_id = m.id
WHERE m.name LIKE '%gemini%'
   OR m.name LIKE 'models/gemini%'  -- Have to check prefix variations
GROUP BY m.name;
"""

# ============================================================================
# AFTER: Clean queries with normalized model names
# ============================================================================

query_after_compare_llama = """
-- Simple, reliable comparison of Llama models across providers
SELECT 
    p.name as provider,
    m.name as model,
    AVG(br.total_latency_ms) as avg_latency,
    AVG(br.cost_usd) as avg_cost,
    AVG(br.tps) as avg_tps
FROM benchmark_results br
JOIN providers p ON br.provider_id = p.id
JOIN models m ON br.model_id = m.id
WHERE m.name IN (
    'llama-3.3-70b-instruct',
    'llama-3.1-405b-instruct',
    'llama-3.1-70b-instruct'
)
GROUP BY p.name, m.name
ORDER BY avg_cost;
"""

query_after_gemini = """
-- Direct model name matching, no prefix handling needed
SELECT 
    p.name as provider,
    m.name as model,
    AVG(br.total_latency_ms) as avg_latency,
    AVG(br.ttft_ms) as avg_ttft,
    COUNT(*) as test_count
FROM benchmark_results br
JOIN providers p ON br.provider_id = p.id
JOIN models m ON br.model_id = m.id
WHERE m.name = 'gemini-2.5-flash'
  AND br.created_at >= NOW() - INTERVAL '7 days'
GROUP BY p.name, m.name;
"""

query_after_cost_analysis = """
-- Compare same model across different providers
-- (e.g., llama-3.3-70b-instruct available on Fireworks, Together, etc.)
SELECT 
    p.name as provider,
    AVG(br.cost_usd) as avg_cost,
    AVG(br.total_latency_ms) as avg_latency,
    AVG(br.tps) as avg_tps,
    COUNT(*) as runs
FROM benchmark_results br
JOIN providers p ON br.provider_id = p.id
JOIN models m ON br.model_id = m.id
WHERE m.name = 'llama-3.3-70b-instruct'
  AND br.success = true
  AND br.created_at >= NOW() - INTERVAL '30 days'
GROUP BY p.name
ORDER BY avg_cost;
"""

query_after_leaderboard = """
-- Simple leaderboard of all models by performance
SELECT 
    m.name as model,
    p.name as provider,
    AVG(br.total_latency_ms) as avg_latency,
    AVG(br.cost_usd) as avg_cost,
    AVG(br.tokens_per_dollar) as tokens_per_dollar,
    COUNT(*) as test_count
FROM benchmark_results br
JOIN providers p ON br.provider_id = p.id
JOIN models m ON br.model_id = m.id
WHERE br.success = true
  AND br.created_at >= NOW() - INTERVAL '7 days'
GROUP BY m.name, p.name
HAVING COUNT(*) >= 10  -- At least 10 successful tests
ORDER BY tokens_per_dollar DESC
LIMIT 20;
"""

# ============================================================================
# Summary of Benefits
# ============================================================================

benefits = """
BENEFITS OF NORMALIZED MODEL NAMES:

1. ✅ Consistent Naming
   - No more "llama" vs "Llama" vs "llama-v3p3" confusion
   - All model names follow the same format

2. ✅ Easy Comparisons
   - Compare same model across providers with simple WHERE clause
   - No complex LIKE patterns or ILIKE needed

3. ✅ Better Analytics
   - Clean GROUP BY results without duplicates
   - Reliable aggregations for dashboards

4. ✅ Simpler Queries
   - Direct equality comparisons: WHERE m.name = 'llama-3.3-70b-instruct'
   - Clear IN clauses for multiple models
   - No need for CASE statements to handle variations

5. ✅ Future-Proof
   - Easy to add new providers without changing query logic
   - Consistent schema regardless of provider API changes

6. ✅ Cleaner Data Exports
   - CSV/JSON exports have readable model names
   - No need to post-process exported data

EXAMPLE USE CASES:

- Cost comparison: Which provider offers llama-3.3-70b-instruct cheapest?
- Performance tracking: How has gemini-2.5-flash latency changed over time?
- Bang for buck: Best tokens per dollar across all models?
- Provider reliability: Which provider has lowest error rate for specific models?
"""

if __name__ == "__main__":
    print("=" * 80)
    print("SQL QUERY IMPROVEMENTS WITH NORMALIZED MODEL NAMES")
    print("=" * 80)
    print()
    print("BEFORE: Complex pattern matching")
    print("-" * 80)
    print(query_before_fireworks)
    print()
    print("AFTER: Simple, reliable queries")
    print("-" * 80)
    print(query_after_compare_llama)
    print()
    print("=" * 80)
    print(benefits)
