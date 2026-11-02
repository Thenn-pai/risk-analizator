"""Расчёт показателей риска и проверка чисел."""

import math


def calculate(loss, probability, after_loss, after_probability):
    return loss * probability / 100, after_loss * after_probability / 100


def number(value, name, limit=None):
    try:
        result = float(value.strip().replace(',', '.'))
    except ValueError:
        raise ValueError(f'Введите число в поле «{name}».')
    if not math.isfinite(result) or result < 0 or (limit is not None and result > limit):
        raise ValueError(f'Проверьте поле «{name}»: от 0' + (f' до {limit}.' if limit is not None else '.'))
    return result
