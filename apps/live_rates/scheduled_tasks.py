import datetime
import typing
from django_q.tasks import schedule
from django_q.models import Schedule
from django.utils import timezone


def schedule_stock_rates_update(
    start_date: typing.Optional[datetime.date] = None,
    end_date: typing.Optional[datetime.date] = None,
    repeats: int = -1,
    cron: str = "*/5 * * * *",
):
    """
    Schedule the task to update stock rates data based on the provided interval.

    Deletes the existing schedule if it already exists.

    :param start_date: Start date to fetch rates from.
    :param end_date: End date to fetch rates from.
    :param repeats: Number of times to repeat the task. -1 to repeat indefinitely.
    :param cron: Cron expression defining the interval at which the task should run.
    """
    task_name = "apps.live_rates.rates.update_stock_rates"
    # Delete the schedule if it already exists
    Schedule.objects.filter(func=task_name).delete()

    schedule(
        task_name,
        start_date=start_date,
        end_date=end_date,
        q_options={
            "retry": 620,
            "save": True,
        },
        timeout=600,
        schedule_type="C",
        repeats=repeats,
        cron=cron,
        # Set the next run time to 10 seconds from now to avoid running the task immediately
        next_run=(timezone.now() + datetime.timedelta(seconds=10)),
    )
