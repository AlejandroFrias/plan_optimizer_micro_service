from custom_types import (
    Cents,
    CentsPerKWh,
    CostData,
    PlanConfig,
    TieredRate,
    UsageData,
    WattHourUnit,
)


def validate_plan_config(plan_config: PlanConfig) -> None:
    """Validates we have a valid plan config
    TODO: Decide how to handle tiered rates mixed with different time of day prices:
          - use the time of day price if applicable, AND still count that usage towards the tier usage amount
          - or use the time of day price, BUT do NOT count that usage towards the tier usage amount
          - or apply tiered rates first, then apply time of day prices
          - or disallow mixing tiered and time of day prices in the same place (probably create a discriminating union type on plan_type)
    For now we'll disallow mixing tiered and time of day prices in the same
    plan until requirements are gathered

    Raises:
        ValueError: tiered rates and time of day prices cannot be mixed
    """
    if plan_config.tiered_rates and plan_config.time_of_day_prices:
        raise ValueError(
            "Cannot mix tiered rates with time of day prices in the same plan."
        )


def calc_plan_cost(plan_config: PlanConfig, usage_data: UsageData) -> CostData:
    """Calculate the cost of a given plan and usage data in cents.

    Handles flat rates, tiered rates, monthly fees, and time of day prices.

    Tiered rates and time of day prices are mutually exclusive in a plan as of now;
    see validate_plan_config for more details on options.

    Power generation will be bought back at the base rate per kWh.
    If needed, could be extended to handle variable buyback rates in the future, either
    via a separate config options for buyback rates or by applying tiered rates
    and time of day prices to generation as well.
    """
    validate_plan_config(plan_config)

    total_cost_cents = 0

    if plan_config.tiered_rates:

        def calculate_monthly_tiered_cost(
            monthly_consumption_total_kwh: float,
        ) -> Cents:
            total_cost_cents = 0
            for tier in plan_config.tiered_rates:
                if monthly_consumption_total_kwh <= 0:
                    break
                total_cost_cents += (
                    min(monthly_consumption_total_kwh, tier.usage_kwh)
                    * tier.rate_cents_per_kwh
                )
                monthly_consumption_total_kwh -= tier.usage_kwh
            total_cost_cents += (
                max(0, monthly_consumption_total_kwh) * plan_config.base_rate_per_kwh
            )
            return Cents(total_cost_cents)

        monthly_consumption_total_kwh = 0
        current_month = usage_data[0].datetime.month
        for row in usage_data:
            if row.datetime.month != current_month:
                total_cost_cents += calculate_monthly_tiered_cost(
                    monthly_consumption_total_kwh
                )
                # New month, reset monthly consumption
                current_month = row.datetime.month
                monthly_consumption_total_kwh = 0

            monthly_consumption_total_kwh += row.consumption_kwh
        # Add the last month's consumption
        total_cost_cents += calculate_monthly_tiered_cost(monthly_consumption_total_kwh)
    elif plan_config.time_of_day_prices:
        for row in usage_data:
            applicable_time_of_day_prices = [
                price
                for price in plan_config.time_of_day_prices
                if row.datetime.time() >= price.start_time
                or row.datetime.time() < price.end_time
            ]
            if not applicable_time_of_day_prices:
                # If no time of day price applies, use the base rate
                total_cost_cents += row.consumption_kwh * plan_config.base_rate_per_kwh
            else:
                # Use the first applicable time of day price
                total_cost_cents += (
                    row.consumption_kwh
                    * applicable_time_of_day_prices[0].rate_cents_per_kwh
                )
    else:
        # Flat rate plan
        total_consumption_kwh = sum(row.consumption_kwh for row in usage_data)
        total_cost_cents += total_consumption_kwh * plan_config.base_rate_per_kwh

    num_of_months = len(set(row.datetime.strftime("%Y-%m") for row in usage_data))
    total_cost_cents += plan_config.base_monthly_fee * num_of_months

    # Buy back any generated power at the base rate
    # TODO: variable buyback rates
    total_generation_kwh = sum(row.generation_kwh for row in usage_data)
    total_cost_cents -= total_generation_kwh * plan_config.base_rate_per_kwh

    return CostData(
        plan_config=plan_config,
        total_cost=Cents(total_cost_cents),
        monthly_average_cost=Cents(total_cost_cents / num_of_months),
    )
