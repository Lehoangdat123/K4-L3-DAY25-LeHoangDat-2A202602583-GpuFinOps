"""Pricing & purchasing economics — measure in $/1M-token, not $/GPU-hr.

Figures are June-2026 as-of snapshots from the deck's RESEARCH dossier; treat
live prices as fast-moving (re-baseline before each cohort).
"""
from __future__ import annotations


def request_cost(
    input_tok: int,
    output_tok: int,
    price_in_per_m: float,
    price_out_per_m: float,
    cached_in: int = 0,
    cache_discount: float = 0.10,   # Anthropic cached-read ~0.1x (=-90%)
    batch: bool = False,
    batch_discount: float = 0.50,   # Batch API ~ -50%
) -> float:
    """USD cost of a single request. Cached input billed at cache_discount x price."""
    cached_in = min(max(0, cached_in), input_tok)
    uncached_in = input_tok - cached_in
    cost = (
        (uncached_in / 1e6) * price_in_per_m
        + (cached_in / 1e6) * price_in_per_m * cache_discount
        + (output_tok / 1e6) * price_out_per_m
    )
    if batch:
        cost *= batch_discount
    return cost


def dollars_per_million(total_cost_usd: float, total_tokens: int) -> float:
    """Aggregate unit economics: $ per 1,000,000 tokens served."""
    if total_tokens <= 0:
        return 0.0
    return total_cost_usd / (total_tokens / 1e6)


def discount_stack(
    batch: bool = False,
    cache_hit_frac: float = 0.0,
    batch_discount: float = 0.50,
    cache_discount: float = 0.10,
) -> float:
    """Effective fraction of the naive bill after stacking discounts (input-heavy view).

    Discounts MULTIPLY: cache applies to the cached share of input, batch to the
    whole bill. batch + 100% cache-hit -> 0.5 * 0.1 = 0.05 (~95% off).
    """
    cache_mult = cache_hit_frac * cache_discount + (1.0 - cache_hit_frac)
    batch_mult = batch_discount if batch else 1.0
    return cache_mult * batch_mult


def break_even_utilization(discount_frac: float) -> float:
    """Utilization at which a commitment pays off ~= 1 - discount.

    A 45% reserved discount needs ~55% utilization (~13.2h/day) to beat on-demand.
    """
    return max(0.0, min(1.0, 1.0 - discount_frac))


def recommend_tier(hours_per_day: float, interruptible: bool, reserved_discount: float = 0.45) -> str:
    """Pick a purchasing tier from a workload's duty cycle + interruptibility.

    DOCUMENTED simple policy (instructor extension point — swap in your own):
      - interruptible & not 24/7  -> 'spot'      (checkpoint and ride the discount)
      - duty cycle >= break-even  -> 'reserved'  (steady, high utilization)
      - otherwise                 -> 'on_demand' (spiky / low duty)
    """
    duty = max(0.0, hours_per_day) / 24.0
    be = break_even_utilization(reserved_discount)
    if interruptible and hours_per_day < 24:
        return "spot"
    if duty >= be:
        return "reserved"
    return "on_demand"


def spot_checkpoint_cost(
    job_hours: float,
    spot_hr: float,
    on_demand_hr: float,
    interrupt_rate: float = 0.05,      # per-hour chance (H100 spot ~<5%)
    ckpt_overhead_frac: float = 0.03,  # steady cost of writing checkpoints
    rework_hours_per_interrupt: float = 0.5,
) -> dict:
    """Effective cost of running a checkpointable job on spot vs on-demand.

    Interruptions waste the compute since the last checkpoint (rework); checkpointing
    adds a small steady overhead. Spot still wins for interruptible jobs.
    """
    expected_interrupts = job_hours * interrupt_rate
    rework_hours = expected_interrupts * rework_hours_per_interrupt
    effective_hours = job_hours * (1.0 + ckpt_overhead_frac) + rework_hours
    spot_cost = effective_hours * spot_hr
    on_demand_cost = job_hours * on_demand_hr
    savings_pct = (1.0 - spot_cost / on_demand_cost) * 100.0 if on_demand_cost > 0 else 0.0
    return {
        "spot_effective_hours": round(effective_hours, 2),
        "spot_cost": round(spot_cost, 2),
        "on_demand_cost": round(on_demand_cost, 2),
        "savings_pct": round(savings_pct, 1),
    }


def cache_is_worth_it(
    total_input_tokens: int,
    cache_hit_frac: float,
    price_in_per_m: float,
    cache_discount: float = 0.10,
    cache_overhead_usd: float = 0.0,
) -> dict:
    """Estimate whether caching reduces input-token costs.

    cache_hit_frac is the fraction of input tokens served as cached reads.
    cache_overhead_usd is the extra cache-related cost over the same period.
    """
    total_input_tokens = max(0, total_input_tokens)
    hit_frac = max(0.0, min(1.0, cache_hit_frac))
    cache_discount = max(0.0, min(1.0, cache_discount))

    baseline_cost = (total_input_tokens / 1e6) * price_in_per_m

    effective_multiplier = (
        (1.0 - hit_frac) + hit_frac * cache_discount
    )
    cached_cost = baseline_cost * effective_multiplier + max(
        0.0, cache_overhead_usd
    )

    savings = baseline_cost - cached_cost
    worth_it = savings > 0

    return {
        "baseline_cost": round(baseline_cost, 6),
        "cached_cost": round(cached_cost, 6),
        "savings": round(savings, 6),
        "savings_pct": round(
            savings / baseline_cost * 100.0, 2
        ) if baseline_cost > 0 else 0.0,
        "worth_it": worth_it,
    }


def compare_reserved_terms(
    on_demand_hr: float,
    hours_per_month: float,
    reserved_1y_discount: float = 0.45,
    reserved_3y_discount: float = 0.60,
) -> dict:
    """Compare on-demand, 1-year reserved, and 3-year reserved costs.

    Discounts are illustrative assumptions, not live provider quotes.
    Assumes constant usage for 12 or 36 months and excludes taxes,
    upfront-payment effects, and early-termination costs.
    """
    hourly_rate = max(0.0, on_demand_hr)
    monthly_hours = max(0.0, hours_per_month)

    discount_1y = max(0.0, min(1.0, reserved_1y_discount))
    discount_3y = max(0.0, min(1.0, reserved_3y_discount))

    monthly_on_demand = hourly_rate * monthly_hours
    monthly_reserved_1y = monthly_on_demand * (1.0 - discount_1y)
    monthly_reserved_3y = monthly_on_demand * (1.0 - discount_3y)

    total_1y = monthly_reserved_1y * 12
    total_3y = monthly_reserved_3y * 36
    total_3y_on_demand = monthly_on_demand * 36

    return {
        "monthly_on_demand": round(monthly_on_demand, 2),
        "monthly_reserved_1y": round(monthly_reserved_1y, 2),
        "monthly_reserved_3y": round(monthly_reserved_3y, 2),
        "total_1y_reserved": round(total_1y, 2),
        "total_3y_reserved": round(total_3y, 2),
        "total_1y_savings": round(
            monthly_on_demand * 12 - total_1y, 2
        ),
        "total_3y_savings": round(total_3y_on_demand - total_3y, 2),
        "recommended_term": (
            "3_year" if total_3y / 3 < total_1y
            else "1_year_or_reassess"
        ),
    }
