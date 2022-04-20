from __future__ import annotations
from datetime import date
from decimal import Decimal
from mca.utils import round_decimal
from mca.settings import ZERO_AMOUNT
from pydantic.dataclasses import dataclass


@dataclass
class AdvanceChargeForDateMixin:
    """
        Charges that are need to be made at specific date.
        str - ChargeForDate.date
    """
    charges_for_date: dict[str, ChargeForDate]


@dataclass
class AdvanceAlreadyPaidMixin:
    """Total amount that customer has already paid for advance"""
    already_paid_amount: Decimal


@dataclass
class ChargeForDate:
    """Charges that are need to be made at specific date"""
    date: date
    calculated_amount: Decimal


@dataclass
class Advance(AdvanceChargeForDateMixin, AdvanceAlreadyPaidMixin):
    """Advance issued to customer"""
    id: int
    """The unique identifier for each advance."""
    customer_id: int
    """The unique identifier for the customer this advance is for."""
    created: date
    """The date the advance was agreed. This may be before repayment starts."""
    total_advanced: Decimal
    """The monetary amount advanced to the customer."""
    fee: Decimal
    """The fee for this advance, to be paid back in addition to total_advanced."""
    mandate_id: int
    """The unique identifier of the direct debit mandate to charge this advance with."""
    repayment_start_date: date
    """Repayments should start on this date, and continue every day until the advance and fee have been repaid."""
    repayment_percentage: float
    """The percentage of daily revenue that should be repaid."""

    @classmethod
    def map_from_json(cls, advance_json) -> Advance:
        return Advance(
            **advance_json,
            already_paid_amount=ZERO_AMOUNT,
            charges_for_date={},
        )

    def get_residual_amount_for_billing(self):
        """Total amount that has left to charge from customer"""
        total_amount_for_billing = Decimal(self.total_advanced) + Decimal(self.fee)
        residual_amount_for_billing = total_amount_for_billing - self.already_paid_amount
        residual_amount_for_billing = round_decimal(residual_amount_for_billing)
        return residual_amount_for_billing

    @property
    def is_completed(self) -> bool:
        return self.get_residual_amount_for_billing() == ZERO_AMOUNT


@dataclass
class Revenue:
    """Revenue for a given customer for a given date."""
    id: int
    """The unique identifier for the customer."""
    for_date: date
    """The date the revenue was received by the customer."""
    amount: Decimal
    """The amount of revenue received."""
