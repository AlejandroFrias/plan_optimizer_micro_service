from datetime import time
from dateutil.parser import parse as parse_date
import pytest
from calc_plan_cost import calc_plan_cost
from custom_types import (
    Cents,
    CentsPerKWh,
    CostData,
    PlanConfig,
    Seconds,
    TieredRate,
    TimeOfDayPrice,
    UsageData,
    UsageDataRow,
)


def test_flat_plan_cost():
    plan_config = PlanConfig(name="Flat", base_rate_per_kwh=CentsPerKWh(15))
    usage_data = UsageData(
        [
            UsageDataRow(
                datetime=parse_date("2023-05-01T00:00:00-05:00"),
                duration=Seconds(900),
                unit="Wh",
                consumption=1000,
            ),
            UsageDataRow(
                datetime=parse_date("2023-05-01T00:15:00-05:00"),
                duration=Seconds(900),
                unit="Wh",
                consumption=2000,
            ),
        ]
    )
    # 1000 Wh * 15 cents/kWh + 2000 Wh * 15 cents/kWh = 45 cents
    assert calc_plan_cost(plan_config, usage_data) == CostData(
        plan_config=plan_config, total_cost=Cents(45), monthly_average_cost=Cents(45)
    )


def test_flat_plan_with_monthly_base_fee_cost():
    plan_config = PlanConfig(
        name="Flat with Monthly Fee",
        base_rate_per_kwh=CentsPerKWh(15),
        base_monthly_fee=Cents(500),
    )
    usage_data = UsageData(
        [
            UsageDataRow(
                datetime=parse_date("2023-05-01T00:00:00-05:00"),
                duration=Seconds(900),
                unit="Wh",
                consumption=1000,
            ),
            UsageDataRow(
                datetime=parse_date("2023-05-01T00:15:00-05:00"),
                duration=Seconds(900),
                unit="Wh",
                consumption=2000,
            ),
            UsageDataRow(
                datetime=parse_date("2023-06-01T00:00:00-05:00"),
                duration=Seconds(900),
                unit="Wh",
                consumption=1000,
            ),
            UsageDataRow(
                datetime=parse_date("2023-06-01T00:15:00-05:00"),
                duration=Seconds(900),
                unit="Wh",
                consumption=2000,
            ),
        ]
    )
    # each month usage was 1000 Wh * 15 cents/kWh + 2000 Wh * 15 cents/kWh = 45 cents
    # 2 months at $5.00 base fee = $10.00
    assert calc_plan_cost(plan_config, usage_data) == CostData(
        plan_config=plan_config,
        total_cost=Cents(1090),
        monthly_average_cost=Cents(545),
    )


def test_tiered_plan():
    plan_config = PlanConfig(
        name="Tiered with Monthly Fee",
        base_rate_per_kwh=CentsPerKWh(20),
        base_monthly_fee=Cents(500),
        tiered_rates=[
            TieredRate(usage_kwh=500, rate_cents_per_kwh=CentsPerKWh(10)),
        ],
    )
    usage_data = UsageData(
        [
            UsageDataRow(
                datetime=parse_date("2023-05-01T00:00:00-05:00"),
                duration=Seconds(900),
                unit="kWh",
                consumption=100,
            ),
            UsageDataRow(
                datetime=parse_date("2023-05-02T00:00:00-05:00"),
                duration=Seconds(900),
                unit="kWh",
                consumption=100,
            ),
            UsageDataRow(
                datetime=parse_date("2023-05-03T00:00:00-05:00"),
                duration=Seconds(900),
                unit="kWh",
                consumption=100,
            ),
            UsageDataRow(
                datetime=parse_date("2023-06-01T00:00:00-05:00"),
                duration=Seconds(900),
                unit="kWh",
                consumption=400,
            ),
            UsageDataRow(
                datetime=parse_date("2023-06-02T00:00:00-05:00"),
                duration=Seconds(900),
                unit="kWh",
                consumption=300,
            ),
        ]
    )
    # first month usage was under 500kWh, so it was charged at 10 cents/kWh
    # second month usage was 700kWh, so the first 500kWh was charged at 10 cents/kWh
    # and the remaining 200kWh was charged at 15 cents/kWh
    # Total cost = (300 kWh * 10 cents/kWh) + (500 kWh * 10 cents/kWh) + (200 kWh * 20 cents/kWh)
    # = 3,000 + 5,000 + 4,000 = 12,000 cents
    # Plus the base fee of $5.00 per month
    # Total cost = 12,000 + 1,000 = 13,000 cents
    assert calc_plan_cost(plan_config, usage_data) == CostData(
        plan_config=plan_config,
        total_cost=Cents(13_000),
        monthly_average_cost=Cents(6_500),
    )


def test_multi_tiered_plan():
    plan_config = PlanConfig(
        name="Multi-Tiered Plan",
        base_rate_per_kwh=CentsPerKWh(25),
        tiered_rates=[
            TieredRate(usage_kwh=500, rate_cents_per_kwh=CentsPerKWh(10)),
            TieredRate(usage_kwh=500, rate_cents_per_kwh=CentsPerKWh(20)),
        ],
    )
    usage_data = UsageData(
        [
            UsageDataRow(
                datetime=parse_date("2023-05-01T00:00:00-05:00"),
                duration=Seconds(900),
                unit="kWh",
                consumption=500,
            ),
            UsageDataRow(
                datetime=parse_date("2023-06-01T00:00:00-05:00"),
                duration=Seconds(900),
                unit="kWh",
                consumption=1000,
            ),
            UsageDataRow(
                datetime=parse_date("2023-07-01T00:00:00-05:00"),
                duration=Seconds(900),
                unit="kWh",
                consumption=2000,
            ),
        ]
    )
    # Each month usage hit different tiers:
    # 1st month: 500 kWh at 10 cents/kWh = 5,000 cents
    # 2nd month: 500 kWh at 10 cents/kWh + 500 kWh at 20 cents/kWh = 5,000 + 10,000 = 15,000 cents
    # 3rd month: 500 kWh at 10 cents/kWh + 500 kWh at 20 cents/kWh = 10,000 + 1,000 kWh at 25 cents/kWh = 5,000 + 10,000 + 25,000 = 40,000 cents
    # total cost = 5,000 + 15,000 + 40,000 = 60,000 cents
    assert calc_plan_cost(plan_config, usage_data) == CostData(
        plan_config=plan_config,
        total_cost=Cents(60_000),
        monthly_average_cost=Cents(20_000),
    )


def test_multi_tiered_plan_under_used():
    plan_config = PlanConfig(
        name="Multi-Tiered Plan",
        base_rate_per_kwh=CentsPerKWh(25),
        tiered_rates=[
            TieredRate(usage_kwh=500, rate_cents_per_kwh=CentsPerKWh(10)),
            TieredRate(usage_kwh=1000, rate_cents_per_kwh=CentsPerKWh(20)),
        ],
    )
    usage_data = UsageData(
        [
            UsageDataRow(
                datetime=parse_date("2023-05-01T00:00:00-05:00"),
                duration=Seconds(900),
                unit="kWh",
                consumption=300,
            ),
            UsageDataRow(
                datetime=parse_date("2023-06-01T00:00:00-05:00"),
                duration=Seconds(900),
                unit="kWh",
                consumption=700,
            ),
        ]
    )
    # 1st month: 300 kWh at 10 cents/kWh = 3,000 cents
    # 2nd month: 500 kWh at 10 cents/kWh + 200 kWh at 20 cents/kWh = 5,000 + 4,000 = 9,000 cents
    # total cost = 3,000 + 9,000 = 12,000 cents
    assert calc_plan_cost(plan_config, usage_data) == CostData(
        plan_config=plan_config,
        total_cost=Cents(12000),
        monthly_average_cost=Cents(6000),
    )


def test_free_nights_plan_cost():
    plan_config = PlanConfig(
        name="Free Nights Plan",
        base_rate_per_kwh=CentsPerKWh(25),
        time_of_day_prices=[
            TimeOfDayPrice(
                start_time=time(22, 0),  # 10:00 PM
                end_time=time(6, 0),  # 6:00 AM
                rate_cents_per_kwh=CentsPerKWh(0),  # Free during these hours
            )
        ],
    )
    usage_data = UsageData(
        [
            UsageDataRow(
                datetime=parse_date("2023-05-01T00:00:00-05:00"),
                duration=Seconds(900),
                unit="Wh",
                consumption=300,
            ),
            UsageDataRow(
                datetime=parse_date("2023-05-01T06:00:00-05:00"),
                duration=Seconds(900),
                unit="Wh",
                consumption=300,
            ),
        ]
    )
    # 300 Wh at night is free, and 300 Wh during the day at 25 cents/kWh
    # Total cost = 0 + (300 Wh * ( 1 kWh / 1000 Wh) * 25 cents/kWh) = .75 cents
    assert calc_plan_cost(plan_config, usage_data) == CostData(
        plan_config=plan_config,
        total_cost=Cents(7.5),
        monthly_average_cost=Cents(7.5),
    )


def test_generation():
    plan_config = PlanConfig(
        name="Flat Solar Plan",
        base_rate_per_kwh=CentsPerKWh(25),
    )
    usage_data = UsageData(
        [
            UsageDataRow(
                datetime=parse_date("2023-05-01T00:00:00-05:00"),
                duration=Seconds(900),
                unit="Wh",
                consumption=300,
            ),
            UsageDataRow(
                datetime=parse_date("2023-05-01T06:00:00-05:00"),
                duration=Seconds(900),
                unit="Wh",
                generation=300,
            ),
        ]
    )
    # same amount of consumption and generation, so the cost is 0
    assert calc_plan_cost(plan_config, usage_data) == CostData(
        plan_config=plan_config, total_cost=Cents(0), monthly_average_cost=Cents(0)
    )


def test_invalid_plan_config():
    plan_config = PlanConfig(
        name="Invalid Plan",
        base_rate_per_kwh=CentsPerKWh(25),
        tiered_rates=[TieredRate(usage_kwh=500, rate_cents_per_kwh=CentsPerKWh(10))],
        time_of_day_prices=[
            TimeOfDayPrice(
                start_time=time(0, 0),
                end_time=time(23, 59),
                rate_cents_per_kwh=CentsPerKWh(5),
            )
        ],
    )
    with pytest.raises(
        ValueError,
        match="Cannot mix tiered rates with time of day prices in the same plan.",
    ):
        calc_plan_cost(plan_config, UsageData([]))
