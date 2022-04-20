import pytest
from unittest.mock import patch
from datetime import datetime
from mca.entities import Advance
from mca.billing import run_billing
from mca.databases import Database


advances_response_mock = [
    Advance.map_from_json({
        'id': 1,
        'customer_id': 1,
        'mandate_id': 1,
        'created': '2022-01-02',
        'total_advanced': '70000.00',
        'fee': '300.00',
        'repayment_start_date': '2022-01-03',
        'repayment_percentage': 13
    }),
]


@patch('mca.billing.get_advances_from_api', return_value=advances_response_mock)
@patch('mca.billing.calculate_charges_amount', return_value=None)
@patch('mca.billing.perform_charge', return_value=None)
@patch('mca.billing.complete_billing', return_value=None)
def test_run_billing__advances_are_saved(
    complete_billing_mock,
    perform_charge_mock,
    calculate_charges_amount_mock,
    get_advances_from_api_mock,
):
    today = datetime.strptime('2022-01-03', '%Y-%m-%d').date()
    db = Database()
    advances = db.get_all_advances()
    # zero advances before billing
    assert len(advances) == 0

    run_billing(
        today=today,
        db=db,        
    )
    advances = db.get_all_advances()
    # 1 new advance after first billing run
    assert len(advances) == 1

    run_billing(
        today=today,
        db=db,        
    )
    advances = db.get_all_advances()
    # no new advances after second billing run
    assert len(advances) == 1

# TODO: test every other step, with mocked api endpoint responses
