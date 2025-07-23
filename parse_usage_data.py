from dateutil.parser import parse as parse_date
from pathlib import Path
import csv

from custom_types import Seconds, UsageData, UsageDataRow, WattHourUnit
from typing import BinaryIO
import io


def validate_watt_hour_unit(unit: str) -> WattHourUnit:
    """Validates the unit of wattage."""
    valid_units: set[WattHourUnit] = {"Wh", "kWh"}
    if unit not in valid_units:
        raise ValueError(f"Invalid unit: {unit}. Must be one of {valid_units}.")
    return unit


def parse_usage_data_csv(csv_file: BinaryIO) -> UsageData:
    """Parses a CSV file into typed and validated energy UsageData"""
    usage_data: UsageData = []
    for row in csv.DictReader(io.TextIOWrapper(csv_file, encoding="utf-8")):
        usage_data.append(
            UsageDataRow(
                datetime=parse_date(row["datetime"]),
                duration=Seconds(int(row["duration"])),
                unit=validate_watt_hour_unit(row["unit"]),
                consumption=int(row["consumption"]),
                generation=int(row["generation"]),
            )
        )

    return usage_data
