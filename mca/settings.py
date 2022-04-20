from datetime import date, datetime
from decimal import Decimal

DATE_FORMAT: str = '%Y-%m-%d'
START_DATE_STR: str = '2022-01-01'
END_DATE_STR: str = '2022-06-30'
START_DATE: date = datetime.strptime(START_DATE_STR, DATE_FORMAT).date()
END_DATE: date = datetime.strptime(END_DATE_STR, DATE_FORMAT).date()
BASE_URL: str = 'https://billing.eng-test.wayflyer.com'
CHARGE_MAX_LIMIT_PER_DAY: int = 10000
CHARGE_MIN_LIMIT_PER_DAY: int = 100
ZERO_AMOUNT: Decimal = Decimal('0.00')
