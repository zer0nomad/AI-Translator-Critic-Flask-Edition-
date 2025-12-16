#!/bin/bash
# run_tests.sh - Скрипт для запуска автотестов

echo "================================================"
echo "AI Translator & Critic - Запуск Автотестов"
echo "================================================"
echo ""

# Цвета для вывода
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Проверяем, установлены ли зависимости
echo -e "${BLUE}[1] Проверка установки зависимостей...${NC}"
pip install -q pytest pytest-mock pytest-cov 2>/dev/null
echo -e "${GREEN}✓ Зависимости готовы${NC}"
echo ""

# Запускаем тесты с разными вариантами
case "${1:-all}" in
    all)
        echo -e "${BLUE}[2] Запуск всех тестов...${NC}"
        python -m pytest tests/ -v
        ;;
    fast)
        echo -e "${BLUE}[2] Запуск тестов (быстрый режим без покрытия)...${NC}"
        python -m pytest tests/ -q
        ;;
    coverage)
        echo -e "${BLUE}[2] Запуск тестов с отчетом о покрытии...${NC}"
        python -m pytest tests/ --cov=src --cov-report=html --cov-report=term-missing
        echo -e "${GREEN}✓ Отчет о покрытии сохранен в htmlcov/index.html${NC}"
        ;;
    critical)
        echo -e "${BLUE}[2] Запуск только критических тестов...${NC}"
        python -m pytest tests/ -m critical -v
        ;;
    api)
        echo -e "${BLUE}[2] Запуск только тестов API интеграции...${NC}"
        python -m pytest tests/test_api_integration.py -v
        ;;
    app)
        echo -e "${BLUE}[2] Запуск только функциональных тестов...${NC}"
        python -m pytest tests/test_app.py -v
        ;;
    security)
        echo -e "${BLUE}[2] Запуск только тестов безопасности...${NC}"
        python -m pytest tests/ -m security -v
        ;;
    *)
        echo "Использование: bash run_tests.sh [all|fast|coverage|critical|api|app|security]"
        echo ""
        echo "Варианты:"
        echo "  all       - Запуск всех тестов"
        echo "  fast      - Быстрый запуск без покрытия"
        echo "  coverage  - Запуск с отчетом о покрытии кода"
        echo "  critical  - Только критические тесты"
        echo "  api       - Только тесты API интеграции"
        echo "  app       - Только функциональные тесты"
        echo "  security  - Только тесты безопасности"
        exit 1
        ;;
esac

echo ""
echo -e "${GREEN}================================================${NC}"
echo -e "${GREEN}Тестирование завершено!${NC}"
echo -e "${GREEN}================================================${NC}"
