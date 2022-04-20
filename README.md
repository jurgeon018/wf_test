## Wayflyer MCA - Billing System Excercise

# Setup instruction:

install python 3.9 on debian/ubuntu/mint

sudo apt-get install python3.9

sudo apt-get install python3.9-venv

python3.9 -m venv venv

source venv/bin/activate

pip install -r requirements.txt

pytest tests_functional.py

python3.9 app.py

## Project description
MCA is a system that charges customers based on their revenues over the simulated period.
It interacts with an API, fetches advances issued to customers, then retrieves the revenues for each one of them, and based on that that revenue and a agreed percentage of tax - system charges some amount of money from their revenues.

## TODOs:

cover with tests

implement retrying mechanism

use relational database

use asyncio.gather or concurrent.futures.ThreadPoolExecutor for parallel billing processes

use aiohttp instead of requests

use sentry or ELK for logs, and grafana for metrics

use docker for containerization

use linter, formatter and mypy for checking code quality 
