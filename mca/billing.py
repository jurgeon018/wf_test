import logging
from mca.exceptions import ApiClientException
from mca.utils import round_decimal
import sys
from datetime import date, timedelta
from decimal import Decimal

from mca.settings import (
    CHARGE_MAX_LIMIT_PER_DAY,
    CHARGE_MIN_LIMIT_PER_DAY,
    DATE_FORMAT,
    ZERO_AMOUNT
)
from mca.entities import Advance, ChargeForDate
from mca.databases import Database
from mca.external_api_calls import (
    get_advances_from_api,
    get_customer_revenues_for_date_from_api,
    post_charge_to_api,
    post_billing_completion_to_api,
)


logging.basicConfig(
    stream=sys.stdout,
    level=logging.INFO
)
logger = logging.getLogger(__name__)
# TODO: use sentry or ELK for logs, and grafana for metrics



def run_billing(
    *,
    today: date,
    db: Database,
) -> None:
    logger.info('Billing process for date %s has started.', today)
    # STEP 1. Retrieve advances
    try:
        advances = get_advances_from_api(today_date=today)
        logger.info('Retrieving of advances for %s succeded with result of %s advances', today, len(advances))
    except ApiClientException as error:
        # TODO: implement retrying mechanism
        logger.error(
            'Retrieving of advances for %s failed with error %s',
            today,
            error,
        )
        return
    db.create_new_advances(advances)
    # TODO: use asyncio.gather or concurrent.futures.ThreadPoolExecutor for parallel billing processes
    for advance in db.get_all_advances():
        if advance.is_completed:
            continue
        calculate_charges_amount(today=today, advance=advance)
        perform_charge(today=today, advance=advance)
        complete_billing(today=today, advance=advance)

    logger.info('Billing process for date %s has finished.', today)


def calculate_charges_amount(
    *,
    today: date,
    advance: Advance,
) -> None:
    # Important: New advances are created regularly as we sign up new customers, and give additional advances to existing customers.
    # STEP 2.1. Creates initial empty charging for previous day, only for old advances.
    # Charging amount will be calculated later, after retrieving of customer revenues.
    charge_date = today - timedelta(days=1)
    if advance.repayment_start_date <= charge_date:
        advance.charges_for_date[charge_date.strftime(DATE_FORMAT)] = ChargeForDate(
            date=charge_date,
            calculated_amount=ZERO_AMOUNT,
        )

    # Important: Due to problems with third-party systems, a customer's revenue for a given day may not be available until a later day. 
    # In this case, we should bill the customer as soon as the revenue becomes available, unless the advance has otherwise been fully repaid.
    # STEP 2.2. Calculate charges amount from customer's revenue for a specific date.
    # Retrieve all uncalculated advance's charges, including the empty one, created on the previous step. 
    # All charges that were previously calculated are skipped.
    for charge in advance.charges_for_date.values():
        if charge.calculated_amount:
            continue
        try:
            revenue = get_customer_revenues_for_date_from_api(
                today_date=today,
                revenue_date=charge.date,
                customer_id=advance.customer_id,
            )
            logger.info(
                'Revenues retrieving of customer %s succeded',
                advance.customer_id
            )
        except ApiClientException as error:
            # TODO: implement retrying mechanism
            logger.error(
                'Revenues retrieving of customer %s failed with error %s',
                advance.customer_id,
                error,
            )
            continue
        if revenue.amount:
            calculated_charge_amount = revenue.amount * Decimal(advance.repayment_percentage / 100)
            calculated_charge_amount = round_decimal(calculated_charge_amount)
            charge.calculated_amount = calculated_charge_amount


def perform_charge(
    *,
    today: date,
    advance: Advance,
) -> None:
        # Important: Due to problems with the direct debit mandate, charges on a given day may be rejected.
        # In this case, charges will be issued on subsequent days.
        # STEP 3. Issue repayment charges against a given mandate
        # All charges that were not calculated on previous step - are skipped.
        charge_max_limit_per_day = CHARGE_MAX_LIMIT_PER_DAY
        charge_min_limit_per_day = CHARGE_MIN_LIMIT_PER_DAY
        for charge in advance.charges_for_date.values():
            if not charge.calculated_amount:
                continue
            # get current charge amount
            residual_amount_for_billing = advance.get_residual_amount_for_billing()
            if charge.calculated_amount >= charge_max_limit_per_day:
                # Important: The total charges made against any advance should not exceed 10000.00 on any given day.
                # Charges greater than this should be split over multiple days.
                amount_charged = charge_max_limit_per_day
            elif charge.calculated_amount >= residual_amount_for_billing:
                amount_charged = residual_amount_for_billing
            else:
                amount_charged = charge.calculated_amount
            if next_day_is_blocked_because_of_too_small_amount_charges():
                
                amount_charged -= charge_min_limit_per_day
            try:
                if amount_charged < charge_min_limit_per_day:
                    advance.already_paid_amount -= amount_charged
                    advance.charges_for_date.pop(charge.date.strftime(DATE_FORMAT), None)
                    continue
                post_charge_to_api(
                    today_date=today,
                    mandate_id=advance.mandate_id,
                    amount=amount_charged,
                )
                logger.info(
                    'Charge for advance %s with mandate_id %s completed successfully',
                    advance.id,
                    advance.mandate_id,
                )
            except ApiClientException as error:
                # TODO: implement retrying mechanism
                logger.error(
                    'Charge for advance %s with mandate_id %s failed with error %s',
                    advance.id,
                    advance.mandate_id,
                    error,
                )
                continue

            # increases amount that customer has already paid for advance, only after successfull charging
            advance.already_paid_amount += amount_charged                
            charge_max_limit_per_day -= amount_charged
            if amount_charged == charge.calculated_amount:
                # charge for date is done, need to clear it
                advance.charges_for_date.pop(charge.date.strftime(DATE_FORMAT), None)
            else:
                charge.calculated_amount -= amount_charged

            if advance.is_completed or (not charge_max_limit_per_day):
                break


def complete_billing(
    *,
    today: date,
    advance: Advance,
) -> None:
    # Step 4. Complete billing, only if advance is fully paid
    if advance.is_completed:
        try:
            post_billing_completion_to_api(
                today_date=today,
                advance_id=advance.id
            )
            logger.info('Billing completion for advance %s completed successfully', advance.id)
        except ApiClientException as error:
            # TODO: implement retrying mechanism
            logger.error(
                'Billing completion for advance %s failed with error %s',
                advance.id,
                error,
            )
        if advance.charges_for_date: 
            # When the billing is completed and residual amount is zer - then all advance charges that are left can be deleted.
            advance.charges_for_date.clear()
