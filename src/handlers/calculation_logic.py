#!/usr/bin/env python3
"""
Calculation Logic (DEPRECATED)
Заглушка для обратной совместимости со старой логикой
Новая логика будет реализована в следующих фазах
"""

from decimal import Decimal


def calculate_margin_rate(
    base_rate: Decimal, 
    margin: Decimal, 
    direction: str = "rub_to_crypto"
) -> Decimal:
    """DEPRECATED: Расчет курса с наценкой"""
    # Заглушка для старых импортов
    if direction == "rub_to_crypto":
        return base_rate * (Decimal('1') + margin / Decimal('100'))
    else:
        return base_rate * (Decimal('1') - margin / Decimal('100')) 