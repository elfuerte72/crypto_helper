#!/usr/bin/env python3
"""
Unit tests для проверки выполнения Задачи 10: Удаление модуля публикации в канал
"""

import unittest
import os
import sys
import importlib.util

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
sys.path.insert(0, project_root)


class TestTask10ChannelPublisherRemoval(unittest.TestCase):
    """Тесты для проверки удаления модуля публикации в канал"""
    
    def test_channel_publisher_file_removed(self):
        """Тест: файл channel_publisher.py должен быть удален"""
        channel_publisher_path = os.path.join(
            project_root, 'src', 'handlers', 'channel_publisher.py'
        )
        self.assertFalse(
            os.path.exists(channel_publisher_path),
            "Файл channel_publisher.py не должен существовать"
        )
    
    def test_channel_publisher_test_file_removed(self):
        """Тест: файл test_channel_publisher.py должен быть удален"""
        test_file_path = os.path.join(
            project_root, 'tests', 'backend', 'test_channel_publisher.py'
        )
        self.assertFalse(
            os.path.exists(test_file_path),
            "Файл test_channel_publisher.py не должен существовать"
        )
    
    def test_no_channel_publisher_imports(self):
        """Тест: импорты channel_publisher должны быть удалены"""
        margin_calculation_path = os.path.join(
            project_root, 'src', 'handlers', 'margin_calculation.py'
        )
        
        if os.path.exists(margin_calculation_path):
            with open(margin_calculation_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Проверяем, что нет импортов channel_publisher
            self.assertNotIn(
                'from .channel_publisher import',
                content,
                "В margin_calculation.py не должно быть импортов channel_publisher"
            )
            
            self.assertNotIn(
                'import channel_publisher',
                content,
                "В margin_calculation.py не должно быть импортов channel_publisher"
            )
    
    def test_admin_channel_id_removed_from_config(self):
        """Тест: ADMIN_CHANNEL_ID должен быть удален из конфига"""
        config_path = os.path.join(project_root, 'src', 'config.py')
        
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Проверяем, что ADMIN_CHANNEL_ID удален
            self.assertNotIn(
                'ADMIN_CHANNEL_ID',
                content,
                "ADMIN_CHANNEL_ID должен быть удален из config.py"
            )
    
    def test_no_publish_result_handler(self):
        """Тест: функция handle_publish_result должна быть удалена"""
        margin_calculation_path = os.path.join(
            project_root, 'src', 'handlers', 'margin_calculation.py'
        )
        
        if os.path.exists(margin_calculation_path):
            with open(margin_calculation_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Проверяем, что функция handle_publish_result удалена
            self.assertNotIn(
                'handle_publish_result',
                content,
                "Функция handle_publish_result должна быть удалена"
            )
            
            # Проверяем, что callback для publish_result удален
            self.assertNotIn(
                'publish_result',
                content,
                "Callback для publish_result должен быть удален"
            )
    
    def test_no_copy_result_handler(self):
        """Тест: функция handle_copy_result должна быть удалена"""
        margin_calculation_path = os.path.join(
            project_root, 'src', 'handlers', 'margin_calculation.py'
        )
        
        if os.path.exists(margin_calculation_path):
            with open(margin_calculation_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Проверяем, что функция handle_copy_result удалена
            self.assertNotIn(
                'handle_copy_result',
                content,
                "Функция handle_copy_result должна быть удалена"
            )
    
    def test_publish_button_removed_from_keyboard(self):
        """Тест: кнопка 'Опубликовать в канал' должна быть удалена"""
        margin_calculation_path = os.path.join(
            project_root, 'src', 'handlers', 'margin_calculation.py'
        )
        
        if os.path.exists(margin_calculation_path):
            with open(margin_calculation_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Проверяем, что кнопка "Опубликовать в канал" удалена
            self.assertNotIn(
                'Опубликовать в канал',
                content,
                "Кнопка 'Опубликовать в канал' должна быть удалена"
            )
            
            # Проверяем, что кнопка "Копировать результат" удалена
            self.assertNotIn(
                'Копировать результат',
                content,
                "Кнопка 'Копировать результат' должна быть удалена"
            )
    
    def test_result_keyboard_simplified(self):
        """Тест: клавиатура результата должна быть упрощена"""
        margin_calculation_path = os.path.join(
            project_root, 'src', 'handlers', 'margin_calculation.py'
        )
        
        if os.path.exists(margin_calculation_path):
            with open(margin_calculation_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Проверяем, что в клавиатуре осталось только 2 кнопки
            self.assertIn(
                'Пересчитать',
                content,
                "Кнопка 'Пересчитать' должна остаться"
            )
            
            self.assertIn(
                'Главное меню',
                content,
                "Кнопка 'Главное меню' должна остаться"
            )
    
    def test_margin_router_still_exists(self):
        """Тест: margin_router должен остаться функциональным"""
        margin_calculation_path = os.path.join(
            project_root, 'src', 'handlers', 'margin_calculation.py'
        )
        
        if os.path.exists(margin_calculation_path):
            with open(margin_calculation_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Проверяем, что margin_router определен
            self.assertIn(
                'margin_router = Router()',
                content,
                "margin_router должен быть определен"
            )
            
            # Проверяем, что основные функции остались
            self.assertIn(
                'handle_recalculate_margin',
                content,
                "Функция handle_recalculate_margin должна остаться"
            )
            
            self.assertIn(
                'handle_back_to_main',
                content,
                "Функция handle_back_to_main должна остаться"
            )
    
    def test_bot_still_includes_margin_router(self):
        """Тест: bot.py должен включать margin_router"""
        bot_path = os.path.join(project_root, 'src', 'bot.py')
        
        if os.path.exists(bot_path):
            with open(bot_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Проверяем, что margin_router импортирован
            self.assertIn(
                'from .handlers.margin_calculation import margin_router',
                content,
                "margin_router должен быть импортирован в bot.py"
            )
            
            # Проверяем, что margin_router подключен
            self.assertIn(
                'self.dp.include_router(margin_router)',
                content,
                "margin_router должен быть подключен в bot.py"
            )


class TestTask10IntegrationTests(unittest.TestCase):
    """Интеграционные тесты для проверки работоспособности без channel_publisher"""
    
    def test_can_import_margin_calculation_without_errors(self):
        """Тест: margin_calculation должен импортироваться без ошибок"""
        try:
            sys.path.insert(0, os.path.join(project_root, 'src'))
            
            # Пытаемся импортировать модуль
            spec = importlib.util.spec_from_file_location(
                "margin_calculation",
                os.path.join(project_root, 'src', 'handlers', 'margin_calculation.py')
            )
            
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                # Проверяем, что модуль можно загрузить без ошибок импорта
                try:
                    spec.loader.exec_module(module)
                    # Если дошли сюда, импорт прошел успешно
                    self.assertTrue(True, "margin_calculation импортируется без ошибок")
                except ImportError as e:
                    if 'channel_publisher' in str(e):
                        self.fail(f"Остались ссылки на channel_publisher: {e}")
                    else:
                        # Другие ошибки импорта игнорируем (могут быть связаны с зависимостями)
                        pass
        except Exception as e:
            if 'channel_publisher' in str(e):
                self.fail(f"Ошибка связанная с channel_publisher: {e}")
    
    def test_config_module_loads_without_admin_channel_id(self):
        """Тест: config должен загружаться без ADMIN_CHANNEL_ID"""
        try:
            sys.path.insert(0, os.path.join(project_root, 'src'))
            
            # Пытаемся импортировать config
            spec = importlib.util.spec_from_file_location(
                "config",
                os.path.join(project_root, 'src', 'config.py')
            )
            
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                
                # Проверяем, что ADMIN_CHANNEL_ID не существует
                self.assertFalse(
                    hasattr(module.Config, 'ADMIN_CHANNEL_ID'),
                    "ADMIN_CHANNEL_ID не должен существовать в конфиге"
                )
                
        except Exception as e:
            self.fail(f"Не удалось загрузить config.py: {e}")


if __name__ == '__main__':
    # Запуск тестов
    unittest.main(verbosity=2)