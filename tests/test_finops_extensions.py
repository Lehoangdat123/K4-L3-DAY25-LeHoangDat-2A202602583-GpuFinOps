from finops.pricing import (
    cache_is_worth_it,
    compare_reserved_terms,
)


def test_cache_is_worth_it_with_positive_savings():
    result = cache_is_worth_it(
        total_input_tokens=10_000_000,
        cache_hit_frac=0.60,
        price_in_per_m=3.0,
    )

    assert result["baseline_cost"] == 30.0
    assert result["cached_cost"] == 13.8
    assert result["savings"] == 16.2
    assert result["savings_pct"] == 54.0
    assert result["worth_it"] is True


def test_cache_is_not_worth_it_when_overhead_is_too_high():
    result = cache_is_worth_it(
        total_input_tokens=10_000_000,
        cache_hit_frac=0.60,
        price_in_per_m=3.0,
        cache_overhead_usd=20.0,
    )

    assert result["worth_it"] is False
    assert result["savings"] < 0


def test_compare_reserved_terms():
    result = compare_reserved_terms(
        on_demand_hr=2.5,
        hours_per_month=500,
        reserved_1y_discount=0.45,
        reserved_3y_discount=0.60,
    )

    assert result["monthly_on_demand"] == 1250.0
    assert result["monthly_reserved_1y"] == 687.5
    assert result["monthly_reserved_3y"] == 500.0
    assert result["total_1y_reserved"] == 8250.0
    assert result["total_3y_reserved"] == 18000.0
    assert result["recommended_term"] == "3_year"
