from mca.exceptions import ApiClientException
from mca.entities import Advance, Revenue
import requests
from requests import HTTPError
from datetime import date
from decimal import Decimal

from mca.settings import DATE_FORMAT
from mca.utils import join_urls, get_default_headers


# TODO: use aiohttp instead of requests


def get_advances_from_api(*, today_date: date) -> list[Advance]:
    """
    Fetch all advances issued to customers.
    """
    try:
        response = requests.get(
            url=join_urls('advances'),
            headers=get_default_headers(today_date)
        )
        response.raise_for_status()
        return [
            Advance.map_from_json(advance_json)
            for advance_json in response.json()['advances']
        ]
    except HTTPError as error:
        raise ApiClientException(error)


def get_customer_revenues_for_date_from_api(
    *,
    today_date: date,
    revenue_date: date,
    customer_id: int,
) -> Revenue:
    """
    Retrieve the revenue for a given customer for a given date.
    """
    try:
        response = requests.get(
            url=join_urls('customers', str(customer_id), 'revenues', revenue_date.strftime(DATE_FORMAT)),
            headers=get_default_headers(today_date)
        )
        response.raise_for_status()
        return Revenue(
            id=customer_id,
            for_date=today_date,
            amount=Decimal(response.json()['amount']),
        )
    except HTTPError as error:
        raise ApiClientException(error)


def post_charge_to_api(
    *,
    today_date: date,
    mandate_id: int,
    amount: Decimal
) -> None:
    """
    Issue repayment charges against a given mandate.    
    """
    try:
        headers = get_default_headers(today_date)
        headers['Content-Type'] = 'application/json'
        response = requests.post(
            url=join_urls('mandates', str(mandate_id), 'charge'),
            # data={'amount': str(amount)},
            json={'amount': str(amount)},
            headers=headers,
        )
        response.raise_for_status()
    except HTTPError as error:
        raise ApiClientException(error)


def post_billing_completion_to_api(
    *,
    today_date: date,
    advance_id: int,
) -> None:
    """
    Indicate that billing has been completed for a given advance.
    This should be called following successful final payment.    
    """
    try:
        response = requests.post(
            url=join_urls('advances', str(advance_id), 'billing_complete'),
            headers=get_default_headers(today_date),
        )
        response.raise_for_status()
    except HTTPError as error:
        raise ApiClientException(error)
