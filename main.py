import json
from datetime import time
from typing import Annotated

from fastapi import FastAPI, File, UploadFile
from fastapi.responses import HTMLResponse

from calc_plan_cost import calc_plan_cost
from custom_types import (
    Cents,
    CentsPerKWh,
    CostData,
    PlanConfig,
    TieredRate,
    TimeOfDayPrice,
)
from parse_usage_data import parse_usage_data_csv

app = FastAPI()


@app.post("/recommend/")
async def recommend(file: UploadFile):
    """returns the cheapest of three tariffs for the supplied usage data CSV"""
    usage_data = parse_usage_data_csv(file.file)
    with open("plan_configs.json", "r") as f:
        plan_configs_data = json.load(f)
    plan_configs: list[PlanConfig] = [
        PlanConfig.from_json(plan_config) for plan_config in plan_configs_data
    ]
    plan_costs: list[CostData] = [
        calc_plan_cost(usage_data=usage_data, plan_config=plan_config)
        for plan_config in plan_configs
    ]
    plan_costs.sort(key=lambda cost_data: cost_data.total_cost)

    return {
        "file_name": file.filename,
        "winner": plan_costs[0].to_api_json(),
        "all_plan_costs": [cost_data.to_api_json() for cost_data in plan_costs],
    }


@app.get("/")
async def main():
    content = """
<body>
    <form action="/recommend/" enctype="multipart/form-data" method="post">
        <input name="file" type="file" required >
        <input type="submit">
    </form>
</body>
"""
    return HTMLResponse(content=content)
