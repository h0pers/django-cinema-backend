from decimal import Decimal


def cents_to_money(amount: int):
    return amount / Decimal('100')
