from pathlib import Path
from dateutil.parser import parse as parse_date

from custom_types import Seconds, UsageData, UsageDataRow
from parse_usage_data import parse_usage_data_csv


def test_parse_usage_data():
    """Test parsing of usage data from a CSV file-like object into UsageData."""
    with open(Path(__file__).parent / "data/test_data.csv", "rb") as csv_file:
        usage_data = parse_usage_data_csv(csv_file)

    assert usage_data == UsageData(
        [
            UsageDataRow(
                datetime=parse_date("2023-05-01T00:00:00-05:00"),
                duration=Seconds(900),
                unit="Wh",
                consumption=2000,
                generation=0,
            ),
            UsageDataRow(
                datetime=parse_date("2023-05-01T00:15:00-05:00"),
                duration=Seconds(900),
                unit="Wh",
                consumption=2,
                generation=500,
            ),
            UsageDataRow(
                datetime=parse_date("2023-05-01T00:30:00-05:00"),
                duration=Seconds(1800),
                unit="kWh",
                consumption=0,
                generation=1,
            ),
        ]
    )
