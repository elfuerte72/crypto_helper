#!/usr/bin/env python3
"""
Unit-тесты для новой логики расчета маржи в MarginCalculator
Проверяет корректность расчета для разных типов валютных пар
"""

import unittest
from decimal import Decimal
import sys
import os

# Добавляем путь к src для импорта модулей
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from handlers.calculation_logic import MarginCalculator, calculate_margin_rate
from handlers.currency_pairs import CURRENCY_PAIRS


class TestMarginCalculationLogic(unittest.TestCase):
    """Тесты для новой логики расчета маржи"""
    
    def setUp(self):
        """Настройка тестовых данных"""
        self.base_rate = Decimal('100.0')
        self.margin_percent = Decimal('5.0')
        self.test_amount = Decimal('1000.0')
        
        # Тестовые данные курса
        self.exchange_rate_data = {
            'rate': '100.0',
            'timestamp': '2024-01-01T12:00:00Z',
            'source': 'test'
        }
    
    def test_detect_pair_type_rub_base(self):
        """Тест определения типа пары RUB/X"""
        pair_info = {
            'base': 'RUB',
            'quote': 'USD',
            'name': 'RUB/USD'
        }
        
        pair_type = MarginCalculator.detect_pair_type(pair_info)
        self.assertEqual(pair_type, 'rub_base')
    
    def test_detect_pair_type_rub_quote(self):
        """Тест определения типа пары X/RUB"""
        pair_info = {
            'base': 'USD',
            'quote': 'RUB',
            'name': 'USD/RUB'
        }
        
        pair_type = MarginCalculator.detect_pair_type(pair_info)
        self.assertEqual(pair_type, 'rub_quote')
    
    def test_detect_pair_type_standard(self):
        """Тест определения типа пары без рубля"""
        pair_info = {
            'base': 'USD',
            'quote': 'EUR',
            'name': 'USD/EUR'
        }
        
        pair_type = MarginCalculator.detect_pair_type(pair_info)
        self.assertEqual(pair_type, 'standard')
    
    def test_calculate_rub_base_margin_positive(self):
        """Тест расчета для RUB/X с положительной маржой"""
        # RUB/X должен прибавлять процент
        # 100 * (1 + 5/100) = 100 * 1.05 = 105
        result = MarginCalculator.calculate_rub_base_margin(
            self.base_rate, self.margin_percent
        )
        expected = Decimal('105.0')
        self.assertEqual(result, expected)
    
    def test_calculate_rub_base_margin_negative(self):
        """Тест расчета для RUB/X с отрицательной маржой"""
        # RUB/X должен прибавлять процент (даже отрицательный)
        # 100 * (1 + (-5)/100) = 100 * 0.95 = 95
        negative_margin = Decimal('-5.0')
        result = MarginCalculator.calculate_rub_base_margin(
            self.base_rate, negative_margin
        )
        expected = Decimal('95.0')
        self.assertEqual(result, expected)
    
    def test_calculate_rub_quote_margin_positive(self):
        """Тест расчета для X/RUB с положительной маржой"""
        # X/RUB должен вычитать процент
        # 100 * (1 - 5/100) = 100 * 0.95 = 95
        result = MarginCalculator.calculate_rub_quote_margin(
            self.base_rate, self.margin_percent
        )
        expected = Decimal('95.0')
        self.assertEqual(result, expected)
    
    def test_calculate_rub_quote_margin_negative(self):
        """Тест расчета для X/RUB с отрицательной маржой"""
        # X/RUB должен вычитать процент (отрицательный = прибавлять)
        # 100 * (1 - (-5)/100) = 100 * 1.05 = 105
        negative_margin = Decimal('-5.0')
        result = MarginCalculator.calculate_rub_quote_margin(
            self.base_rate, negative_margin
        )
        expected = Decimal('105.0')
        self.assertEqual(result, expected)
    
    def test_calculate_final_rate_with_rub_base_pair(self):
        """Тест автоматического выбора логики для RUB/X"""
        pair_info = {
            'base': 'RUB',
            'quote': 'USD',
            'name': 'RUB/USD'
        }
        
        result = MarginCalculator.calculate_final_rate(
            self.base_rate, self.margin_percent, pair_info
        )
        expected = Decimal('105.0')  # Плюс процент
        self.assertEqual(result, expected)
    
    def test_calculate_final_rate_with_rub_quote_pair(self):
        """Тест автоматического выбора логики для X/RUB"""
        pair_info = {
            'base': 'USD',
            'quote': 'RUB',
            'name': 'USD/RUB'
        }
        
        result = MarginCalculator.calculate_final_rate(
            self.base_rate, self.margin_percent, pair_info
        )
        expected = Decimal('95.0')  # Минус процент
        self.assertEqual(result, expected)
    
    def test_calculate_final_rate_backward_compatibility(self):
        """Тест обратной совместимости без pair_info"""
        # Без pair_info должна использоваться старая логика (плюс процент)
        result = MarginCalculator.calculate_final_rate(
            self.base_rate, self.margin_percent
        )
        expected = Decimal('105.0')  # Стандартная логика
        self.assertEqual(result, expected)
    
    def test_all_currency_pairs_from_config(self):
        """Тест всех валютных пар из конфигурации"""
        test_cases = [
            # X/RUB пары - должны использовать минус процент
            ('usdtrub', 'rub_quote', Decimal('95.0')),
            ('usdrub', 'rub_quote', Decimal('95.0')),
            ('eurrub', 'rub_quote', Decimal('95.0')),
            ('aedrub', 'rub_quote', Decimal('95.0')),
            ('thbrub', 'rub_quote', Decimal('95.0')),
            ('zarrub', 'rub_quote', Decimal('95.0')),
            ('idrrub', 'rub_quote', Decimal('95.0')),
            
            # RUB/X пары - должны использовать плюс процент
            ('rubusdt', 'rub_base', Decimal('105.0')),
            ('rubusd', 'rub_base', Decimal('105.0')),
            ('rubeur', 'rub_base', Decimal('105.0')),
            ('rubaed', 'rub_base', Decimal('105.0')),
            ('rubthb', 'rub_base', Decimal('105.0')),
            ('rubzar', 'rub_base', Decimal('105.0')),
            ('rubidr', 'rub_base', Decimal('105.0')),
        ]
        
        for pair_callback, expected_type, expected_rate in test_cases:
            with self.subTest(pair=pair_callback):
                pair_info = CURRENCY_PAIRS.get(pair_callback)
                self.assertIsNotNone(pair_info, f"Pair {pair_callback} not found")
                
                # Проверяем определение типа
                pair_type = MarginCalculator.detect_pair_type(pair_info)
                self.assertEqual(pair_type, expected_type)
                
                # Проверяем расчет курса
                result = MarginCalculator.calculate_final_rate(
                    self.base_rate, self.margin_percent, pair_info
                )
                self.assertEqual(result, expected_rate)
    
    def test_integration_with_calculate_margin_rate(self):
        """Тест интеграции с основной функцией calculate_margin_rate"""
        # Тест для RUB/USD (плюс процент)
        rub_usd_pair = CURRENCY_PAIRS['rubusd']
        result_rub_usd = calculate_margin_rate(
            pair_info=rub_usd_pair,
            amount=self.test_amount,
            margin=self.margin_percent,
            exchange_rate_data=self.exchange_rate_data,
            use_banking_logic=False
        )
        
        # Должно быть 105.0 (плюс процент)
        self.assertEqual(result_rub_usd.final_rate, Decimal('105.0'))
        
        # Тест для USD/RUB (минус процент)
        usd_rub_pair = CURRENCY_PAIRS['usdrub']
        result_usd_rub = calculate_margin_rate(
            pair_info=usd_rub_pair,
            amount=self.test_amount,
            margin=self.margin_percent,
            exchange_rate_data=self.exchange_rate_data,
            use_banking_logic=False
        )
        
        # Должно быть 95.0 (минус процент)
        self.assertEqual(result_usd_rub.final_rate, Decimal('95.0'))
    
    def test_precision_and_rounding(self):
        """Тест точности и округления"""
        # Тест с дробными значениями
        base_rate = Decimal('100.123456789')
        margin = Decimal('2.5')
        
        pair_info_rub_base = {'base': 'RUB', 'quote': 'USD', 'name': 'RUB/USD'}
        pair_info_rub_quote = {'base': 'USD', 'quote': 'RUB', 'name': 'USD/RUB'}
        
        # RUB/USD: 100.123456789 * 1.025 = 102.62654570725
        result_rub_base = MarginCalculator.calculate_final_rate(
            base_rate, margin, pair_info_rub_base
        )
        expected_rub_base = Decimal('102.62654571')  # Округлено до 8 знаков
        self.assertEqual(result_rub_base, expected_rub_base)
        
        # USD/RUB: 100.123456789 * 0.975 = 97.62037037025
        result_rub_quote = MarginCalculator.calculate_final_rate(
            base_rate, margin, pair_info_rub_quote
        )
        expected_rub_quote = Decimal('97.62037037')  # Округлено до 8 знаков
        self.assertEqual(result_rub_quote, expected_rub_quote)
    
    def test_zero_margin(self):
        """Тест с нулевой маржой"""
        zero_margin = Decimal('0.0')
        
        pair_info_rub_base = {'base': 'RUB', 'quote': 'USD', 'name': 'RUB/USD'}
        pair_info_rub_quote = {'base': 'USD', 'quote': 'RUB', 'name': 'USD/RUB'}
        
        # При нулевой марже результат должен быть равен базовому курсу
        result_rub_base = MarginCalculator.calculate_final_rate(
            self.base_rate, zero_margin, pair_info_rub_base
        )
        self.assertEqual(result_rub_base, self.base_rate)
        
        result_rub_quote = MarginCalculator.calculate_final_rate(
            self.base_rate, zero_margin, pair_info_rub_quote
        )
        self.assertEqual(result_rub_quote, self.base_rate)


if __name__ == '__main__':
    unittest.main()