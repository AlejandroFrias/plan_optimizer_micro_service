from typing import Literal, NamedTuple, NewType
from datetime import datetime, time

CentsPerKWh = NewType("CentsPerKWh", int)
Cents = NewType("Cents", float)
Seconds = NewType("Seconds", int)
WattHourUnit = Literal["Wh", "kWh"]


class UsageDataRow(NamedTuple):
    datetime: datetime
    duration: Seconds
    unit: WattHourUnit = "Wh"
    consumption: int = 0
    generation: int = 0

    @property
    def consumption_kwh(self) -> float:
        match self.unit:
            case "kWh":
                return self.consumption
            case "Wh":
                return self.consumption / 1000.0
            case _:
                raise ValueError(f"Unsupported unit: {self.unit}")

    @property
    def generation_kwh(self) -> float:
        match self.unit:
            case "kWh":
                return self.generation
            case "Wh":
                return self.generation / 1000.0
            case _:
                raise ValueError(f"Unsupported unit: {self.unit}")


UsageData = list[UsageDataRow]


def format_currency(amount: Cents | CentsPerKWh) -> str:
    return "${:,.2f}".format(amount / 100)


class TimeOfDayPrice(NamedTuple):
    start_time: time
    end_time: time
    rate_cents_per_kwh: CentsPerKWh

    def to_api_json(self) -> dict:
        return {
            "start_time": self.start_time.strftime("%H:%M"),
            "end_time": self.end_time.strftime("%H:%M"),
            "rate_cents_per_kwh": format_currency(self.rate_cents_per_kwh),
        }


class TieredRate(NamedTuple):
    usage_kwh: int
    rate_cents_per_kwh: CentsPerKWh

    def to_api_json(self) -> dict:
        return {
            "usage_kwh": self.usage_kwh,
            "rate_cents_per_kwh": format_currency(self.rate_cents_per_kwh),
        }


class PlanConfig(NamedTuple):
    name: str
    base_rate_per_kwh: CentsPerKWh
    base_monthly_fee: Cents = Cents(0)  # Optional monthly fee
    tiered_rates: list[TieredRate] = []  # Optional ordered tiered rates
    time_of_day_prices: list[TimeOfDayPrice] = []

    def to_api_json(self) -> dict:
        return {
            "plan_name": self.name,
            "plan_base_rate": format_currency(self.base_rate_per_kwh),
            "plan_base_monthly_fee": format_currency(self.base_monthly_fee),
            "plan_tiered_rates": [
                tiered_rate.to_api_json() for tiered_rate in self.tiered_rates
            ],
            "plan_time_of_day_prices": [
                todp.to_api_json() for todp in self.time_of_day_prices
            ],
        }

    @classmethod
    def from_json(cls, data: dict) -> "PlanConfig":
        return cls(
            name=data.get("name", "No Name"),
            base_rate_per_kwh=CentsPerKWh(data.get("base_rate_per_kwh", 0)),
            base_monthly_fee=Cents(data.get("base_monthly_fee", 0)),
            tiered_rates=[
                TieredRate(
                    usage_kwh=tr["usage_kwh"],
                    rate_cents_per_kwh=CentsPerKWh(tr["rate_cents_per_kwh"]),
                )
                for tr in data.get("tiered_rates", [])
            ],
            time_of_day_prices=[
                TimeOfDayPrice(
                    start_time=time.fromisoformat(todp["start_time"]),
                    end_time=time.fromisoformat(todp["end_time"]),
                    rate_cents_per_kwh=CentsPerKWh(todp["rate_cents_per_kwh"]),
                )
                for todp in data.get("time_of_day_prices", [])
            ],
        )


class CostData(NamedTuple):
    plan_config: PlanConfig
    total_cost: Cents
    monthly_average_cost: Cents

    def to_api_json(self) -> dict:
        return {
            "plan": self.plan_config.to_api_json(),
            "total_cost": format_currency(self.total_cost),
            "monthly_average_cost": format_currency(self.monthly_average_cost),
        }
