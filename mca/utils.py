from datetime import timedelta, date
from decimal import Decimal, ROUND_DOWN
from urllib.parse import urljoin
from mca.settings import BASE_URL, DATE_FORMAT


def date_range(start_date: date, end_date: date) -> list[date]:
    return (
        start_date + timedelta(days=days_delta)
        for days_delta in range((end_date - start_date).days + 1)
    )


def join_urls(*urls) -> str:
    return urljoin(BASE_URL, '/'.join(urls))


def get_default_headers(today_date: date) -> dict:
    return {'Today': today_date.strftime(DATE_FORMAT)}


def round_decimal(decimal: Decimal) -> Decimal:
    return decimal.quantize(Decimal('.01'), rounding=ROUND_DOWN)
