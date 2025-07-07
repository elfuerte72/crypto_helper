#!/usr/bin/env python3
"""
Простой скрипт для запуска тестов APILayer интеграции
"""

import subprocess
import sys
import os

def run_test(test_file, description):
    """Запускает тест и возвращает результат"""
    print(f"\n🔍 {description}")
    print("-" * 50)
    
    try:
        result = subprocess.run(
            [sys.executable, test_file],
            capture_output=True,
            text=True,
            timeout=60
        )
        
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        
        return result.returncode == 0
        
    except subprocess.TimeoutExpired:
        print("❌ Тест завершен по таймауту")
        return False
    except Exception as e:
        print(f"❌ Ошибка при запуске теста: {e}")
        return False

def main():
    """Основная функция"""
    
    print("🚀 ЗАПУСК ТЕСТОВ APILAYER ИНТЕГРАЦИИ")
    print("=" * 60)
    
    # Проверяем, что мы в правильной директории
    if not os.path.exists('src'):
        print("❌ Не найдена папка src. Убедитесь, что вы запускаете из корня проекта.")
        return False
    
    # Список тестов
    tests = [
        ("test_apilayer.py", "Базовое тестирование APILayer"),
        ("test_apilayer_full.py", "Полное тестирование APILayer интеграции"),
    ]
    
    results = []
    
    for test_file, description in tests:
        if os.path.exists(test_file):
            success = run_test(test_file, description)
            results.append((description, success))
        else:
            print(f"❌ Файл {test_file} не найден")
            results.append((description, False))
    
    # Итоговый отчет
    print("\n" + "=" * 60)
    print("📊 ИТОГОВЫЙ ОТЧЕТ")
    print("=" * 60)
    
    all_passed = True
    for description, success in results:
        status = "✅ ПРОЙДЕН" if success else "❌ ПРОВАЛЕН"
        print(f"{description}: {status}")
        all_passed = all_passed and success
    
    print("=" * 60)
    if all_passed:
        print("🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ!")
    else:
        print("❌ НЕКОТОРЫЕ ТЕСТЫ ПРОВАЛЕНЫ")
    
    return all_passed

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Тестирование прервано пользователем")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Критическая ошибка: {e}")
        sys.exit(1)