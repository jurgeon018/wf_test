from mca.settings import START_DATE, END_DATE
from mca.databases import Database
from mca.billing import run_billing
from mca.utils import date_range


def simulate() -> None:
    db = Database()
    for today in date_range(START_DATE, END_DATE):
        run_billing(
            today=today,
            db=db,
        )


if __name__ == '__main__':
    simulate()
