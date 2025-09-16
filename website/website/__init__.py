from .celery import app as celery_app

__all__ = ('celery_app', 'is_true', 'split_with_comma')

TRUE = ("1", "true", "True", "TRUE", "on", "yes")


def is_true(val: str | None) -> bool:
    return val in TRUE


def split_with_comma(val: str) -> list[str]:
    return list(filter(None, map(str.strip, val.split(","))))
