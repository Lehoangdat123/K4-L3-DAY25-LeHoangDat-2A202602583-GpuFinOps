# NimbusAI � GPU Cost Optimization Report

**Period:** monthly  
**Baseline spend:** $27,133  
**Optimized spend:** $14,626  
**Projected savings:** $12,507  (**46%**)

## Savings by lever

| Lever | Savings (USD) |
|---|---|
| Inference (cascade/cache/batch) | $1,212 |
| Purchasing (spot/reserved) | $10,040 |
| Right-size util-lies | $655 |
| Kill idle GPUs | $600 |

## Sustainability

- Energy per query: 0.24 Wh
- Carbon per query: 0.091 gCO2e
- Cheapest+cleanest region: europe-north1

_Figures are June-2026 as-of snapshots; re-baseline before acting._

## Your Turn — Additional FinOps Optimizations

### 1. Cache Cost-Benefit Analysis

Implemented `cache_is_worth_it()` in `finops/pricing.py` to evaluate whether input-token caching is cost-effective after accounting for additional cache overhead.

**Test scenario:**
- Input tokens: 10,000,000
- Input price: $3.00 per million tokens
- Cache-hit fraction: 60%
- Cache discount: 90%

| Metric | Result |
|---|---:|
| Baseline input cost | $30.00 |
| Cost with caching | $13.80 |
| Estimated savings | $16.20 |
| Savings percentage | 54% |
| Worth using cache | Yes, before additional overhead |

The function also accounts for additional cache overhead. If this overhead exceeds the savings from cached reads, caching is no longer cost-effective under the model.

### 2. Reserved Commitment Term Comparison

Implemented `compare_reserved_terms()` in `finops/pricing.py` to compare illustrative 1-year and 3-year reserved pricing scenarios.

**Test assumptions:**
- On-demand GPU price: $2.50/hour
- Usage: 500 hours/month
- 1-year reserved discount: 45%
- 3-year reserved discount: 60%

| Metric | 1-year reserved | 3-year reserved |
|---|---:|---:|
| Monthly equivalent cost | $687.50 | $500.00 |
| Total commitment cost | $8,250.00 | $18,000.00 |
| Savings vs. on-demand over the same term | $6,750.00 | $27,000.00 |

Under these assumptions, the 3-year option has the lower monthly equivalent cost. However, it requires a longer commitment and is more exposed to changes in workload demand.

The discounts are illustrative assumptions, not live provider quotes. The calculation assumes stable monthly usage and excludes taxes, upfront-payment effects, and early-termination costs.

### Validation

- `python verify.py`: 11/11 checks passed.
- `pytest -q`: 18 tests passed, including three added tests for the new optimization functions.

The additional scenarios are evaluated independently and are not added to the M5 projected savings, avoiding double-counting or mixing separate test scenarios with the baseline report.