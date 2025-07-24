# Option 3 — Plan‑optimizer micro‑service (algorithm & API)

Loom self-review video: [Loom Video](https://www.loom.com/share/f84d7ade564f4577bc395f267a37426d?sid=ede2b3fa-25b5-48fb-acf3-a6661b94dd3a)

## The brief
Expose an endpoint POST /recommend (language + framework of your choice) that returns the cheapest of three tariffs for the supplied CSV:

1. Flat:
    * 15 ¢/kWh
    * 0 base fee
2. Tiered:
    * 11 ¢/kWH first 500 kWh, then 17 ¢kWH
    * $4.95/month base fee
3. Free Nights:
    * 0 ¢/kWH 22:00‑06:00, 19 ¢/kWH otherwise
    * $9.95/month base fee

Must‑haves:
- [x] Parse CSV, compute annual cost for each tariff, return JSON with winner + costs.
- [x] Simple README with run examples (curl, HTTPie, etc.).

Stretch goal ideas:
- [x] Config‑driven tariffs (YAML or JSON). see [plan_configs.json](plan_configs.json)
- [ ] Optional LLM endpoint: POST /explain that turns the JSON result into a plain‑English email blurb.
- [ ] Enhance memory usage and performance by streaming the file and calculating all tariffs with one read through of the usage data

## Development

### Installation


Requires Python3.9+ installed and git. I'm running Python 3.13.3

Clone this repo:
```shell
git clone git@github.com:AlejandroFrias/plan_optimizer_micro_service.git
cd plan_optimizer_micro_service
```

Install python packages:
```shell
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Run dev server
Using fastapi:
```shell
fastapi dev main.py
```

Open http://127.0.0.1:8000

Upload your usage file (examples in [/data](/data)) and submit the form.

The response will be a JSON with the winning plan, the details of the plan, the total and monthly costs for the uploaded usage data, and a listing of all the other plans for comparison.

### Modify the plan configs
The brief came with 3 different plans. They are encoded in [plan_configs.json](plan_configs.json).

Simply modify the file to add new or modify existing plans for the API service to use.

### Run the tests

Using pytest:

```shell
pytest --cov
```

## Future Improvements

Performance boost for large file handling by calculating all plan configs as you parse the usage data file. Currently the entire usage data is held in memory while calculating each plan's costs, leading to a noticeable wait time on the larger test files. Would not take long to refactor code to stream the large file and calculate all plans simultaneously.

100% test coverage on error states and the to/from json layer.