#!/usr/bin/env python3
"""
Скрипт для управления тестовыми файлами APILayer интеграции
"""

import os
import sys
import argparse

def list_test_files():
    """Показывает все созданные тестовые файлы"""
    test_files = [
        'quick_test.py',
        'check_subscriptions.py', 
        'test_apilayer_full.py',
        'run_tests.py',
        'demo.py',
        'manage_tests.py',
        'TESTING_INSTRUCTIONS.md',
        'APILAYER_INTEGRATION_STATUS.md'
    ]
    
    print("📁 Тестовые файлы APILayer интеграции:")
    print("=" * 50)
    
    for file in test_files:
        if os.path.exists(file):
            size = os.path.getsize(file)
            print(f"✅ {file:<30} ({size:,} bytes)")
        else:
            print(f"❌ {file:<30} (не найден)")
    
    print("\n💡 Основные команды:")
    print("• python quick_test.py          - Быстрая проверка")
    print("• python check_subscriptions.py - Проверка подписок")
    print("• python demo.py               - Демонстрация")
    print("• python test_apilayer_full.py - Полное тестирование")
    print("• python run_tests.py          - Автоматический запуск")

def clean_test_files():
    """Удаляет все тестовые файлы"""
    test_files = [
        'quick_test.py',
        'check_subscriptions.py',
        'test_apilayer_full.py',
        'run_tests.py',
        'demo.py',
        'TESTING_INSTRUCTIONS.md',
        'APILAYER_INTEGRATION_STATUS.md'
    ]
    
    print("🗑️  Удаление тестовых файлов...")
    print("=" * 50)
    
    for file in test_files:
        if os.path.exists(file):
            try:
                os.remove(file)
                print(f"✅ Удален: {file}")
            except Exception as e:
                print(f"❌ Ошибка при удалении {file}: {e}")
        else:
            print(f"⏭️  Пропущен: {file} (не найден)")
    
    print("\n✅ Очистка завершена!")
    print("💡 Файл manage_tests.py оставлен для повторного использования")

def backup_test_files():
    """Создает резервную копию тестовых файлов"""
    import shutil
    from datetime import datetime
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = f"tests_backup_{timestamp}"
    
    test_files = [
        'quick_test.py',
        'check_subscriptions.py',
        'test_apilayer_full.py',
        'run_tests.py',
        'demo.py',
        'TESTING_INSTRUCTIONS.md',
        'APILAYER_INTEGRATION_STATUS.md'
    ]
    
    print(f"💾 Создание резервной копии в {backup_dir}...")
    print("=" * 50)
    
    try:
        os.makedirs(backup_dir, exist_ok=True)
        
        for file in test_files:
            if os.path.exists(file):
                shutil.copy2(file, backup_dir)
                print(f"✅ Скопирован: {file}")
            else:
                print(f"⏭️  Пропущен: {file} (не найден)")
        
        print(f"\n✅ Резервная копия создана в папке: {backup_dir}")
        
    except Exception as e:
        print(f"❌ Ошибка при создании резервной копии: {e}")

def main():
    """Основная функция"""
    parser = argparse.ArgumentParser(
        description='Управление тестовыми файлами APILayer интеграции'
    )
    
    parser.add_argument(
        'action',
        choices=['list', 'clean', 'backup'],
        help='Действие: list (показать файлы), clean (удалить), backup (резервная копия)'
    )
    
    args = parser.parse_args()
    
    if args.action == 'list':
        list_test_files()
    elif args.action == 'clean':
        response = input("⚠️  Вы уверены, что хотите удалить все тестовые файлы? (y/N): ")
        if response.lower() == 'y':
            clean_test_files()
        else:
            print("❌ Отменено пользователем")
    elif args.action == 'backup':
        backup_test_files()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Прервано пользователем")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Ошибка: {e}")
        sys.exit(1)