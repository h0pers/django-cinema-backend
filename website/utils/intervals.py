from dateutil.relativedelta import relativedelta
from django.db import models
from django.utils.translation import gettext_lazy as _


class Interval(models.TextChoices):
    DAY = 'day', _('Day')
    MONTH = 'month', _('Month')
    WEEK = 'week', _('Week')
    YEAR = 'year', _('Year')


interval_delta = {
    Interval.DAY: 'days',
    Interval.MONTH: 'months',
    Interval.WEEK: 'weeks',
    Interval.YEAR: 'years',
}


def interval_to_relativedelta(interval: Interval, count: int) -> relativedelta:
    return relativedelta(**{interval_delta[interval]: count})
