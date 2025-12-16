"""conftest.py - Конфигурация pytest и фикстуры."""

import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, patch

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

from app import app as flask_app


def pytest_configure(config):
    """Добавить кастомные маркеры для тестов."""
    markers = [
        "critical: критические тесты приложения",
        "api: тесты интеграции с API",
        "security: тесты безопасности",
        "performance: тесты производительности",
        "markdown: тесты обработки markdown",
        "slow: медленные тесты"
    ]
    for marker in markers:
        config.addinivalue_line("markers", marker)


@pytest.fixture
def client():
    """Flask test client для HTTP запросов."""
    flask_app.config['TESTING'] = True
    with flask_app.test_client() as test_client:
        yield test_client


@pytest.fixture
def mock_call_llm():
    """Мок функции call_llm для изоляции от API."""
    with patch('app.call_llm') as mock:
        yield mock


@pytest.fixture
def sample_text():
    """Образец текста для перевода."""
    return "Он был слишком простодушен, чтобы задумываться о смирении."


@pytest.fixture
def sample_form_data(sample_text):
    """Готовые данные формы для POST запроса."""
    return {
        "text": sample_text,
        "language": "Английский",
        "action": "translate"
    }


@pytest.fixture
def mock_api_success_response():
    """Успешный ответ от API."""
    return {
        "response": "He was too simple-minded to ponder about humility.",
        "status": "success"
    }


@pytest.fixture
def mock_api_error_response():
    """Ошибка от API."""
    return {
        "message": "Internal Server Error",
        "status": "error"
    }


@pytest.fixture
def mock_requests_post(mock_api_success_response):
    """Мок requests.post для контроля ответов API."""
    with patch('app.requests.post') as mock_post:
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_api_success_response
        mock_post.return_value = mock_response
        yield mock_post


@pytest.fixture(params=["Английский", "Французский", "Немецкий"])
def available_languages(request):
    """Параметризованная фикстура для всех доступных языков."""
    return request.param


def create_mock_response(status_code, json_data):
    """Создать mock объект ответа от API."""
    mock_response = Mock()
    mock_response.status_code = status_code
    mock_response.json.return_value = json_data
    mock_response.text = str(json_data)
    return mock_response


def assert_form_contains_elements(html_content):
    """Проверить наличие элементов формы в HTML."""
    required = ['name="text"', 'name="language"', 'type="submit"']
    return all(elem in html_content for elem in required)


def pytest_collection_finish(session):
    """Печать информации о собранных тестах."""
    print(f"\n{'='*70}")
    print(f"Собрано {len(session.items)} тестов")
    print(f"{'='*70}\n")

