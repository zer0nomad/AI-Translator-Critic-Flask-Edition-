"""
test_api_integration.py - Тесты интеграции с API
================================================
Тесты для проверки корректности взаимодействия с внешним API:
- Правильность построения HTTP запросов
- Обработка ответов от сервера
- Обработка ошибок сети
- Безопасность (использование API ключа)
"""

import pytest
from unittest.mock import patch, Mock
import requests


class TestAPIRequestConstruction:
    """
    Тесты для проверки правильности построения запроса к API.
    """
    
    @pytest.mark.api
    @pytest.mark.critical
    def test_call_llm_sends_post_request(self, mock_requests_post):
        """
        Проверяет, что call_llm отправляет POST запрос.
        
        Ожидаемое:
            - requests.post вызывается один раз
            - URL соответствует API endpoint
        """
        from app import call_llm
        
        result = call_llm("test_model", "test_prompt")
        
        assert mock_requests_post.called
        mock_requests_post.assert_called_once()
    
    @pytest.mark.api
    @pytest.mark.critical
    def test_api_endpoint_correct(self, mock_requests_post):
        """
        Проверяет, что используется правильный API endpoint.
        
        Ожидаемое:
            - URL = https://api.mentorpiece.org/v1/process-ai-request
        """
        from app import call_llm, API_ENDPOINT
        
        call_llm("test_model", "test_prompt")
        
        # Получаем аргументы вызова requests.post
        call_args = mock_requests_post.call_args
        assert call_args[0][0] == API_ENDPOINT
    
    @pytest.mark.api
    @pytest.mark.critical
    def test_authorization_header_present(self, mock_requests_post):
        """
        Проверяет, что заголовок Authorization присутствует.
        
        Ожидаемое:
            - headers содержит Authorization
            - Authorization имеет формат "Bearer <KEY>"
        """
        from app import call_llm
        
        call_llm("test_model", "test_prompt")
        
        call_args = mock_requests_post.call_args
        headers = call_args[1]['headers']
        
        assert 'Authorization' in headers
        assert headers['Authorization'].startswith('Bearer ')
    
    @pytest.mark.api
    def test_content_type_header_json(self, mock_requests_post):
        """
        Проверяет, что Content-Type установлен на application/json.
        """
        from app import call_llm
        
        call_llm("test_model", "test_prompt")
        
        call_args = mock_requests_post.call_args
        headers = call_args[1]['headers']
        
        assert headers['Content-Type'] == 'application/json'
    
    @pytest.mark.api
    @pytest.mark.critical
    def test_request_payload_format(self, mock_requests_post):
        """
        Проверяет формат JSON payload в запросе.
        
        Ожидаемое:
            - payload содержит поля: model_name, prompt
            - payload передается как JSON
        """
        from app import call_llm
        
        test_model = "test_model"
        test_prompt = "test_prompt"
        
        call_llm(test_model, test_prompt)
        
        call_args = mock_requests_post.call_args
        payload = call_args[1]['json']
        
        assert payload['model_name'] == test_model
        assert payload['prompt'] == test_prompt
    
    @pytest.mark.api
    def test_model_name_passed_correctly(self, mock_requests_post):
        """
        Проверяет, что имя модели правильно передается в запрос.
        """
        from app import call_llm
        
        model_names = [
            "Qwen/Qwen3-VL-30B-A3B-Instruct",
            "claude-sonnet-4-5-20250929",
            "custom_model"
        ]
        
        for model in model_names:
            mock_requests_post.reset_mock()
            call_llm(model, "prompt")
            
            call_args = mock_requests_post.call_args
            assert call_args[1]['json']['model_name'] == model
    
    @pytest.mark.api
    def test_prompt_passed_correctly(self, mock_requests_post):
        """
        Проверяет, что промпт правильно передается в запрос.
        """
        from app import call_llm
        
        prompts = [
            "Translate this text",
            "Оцени качество перевода от 1 до 10",
            "Multi-line\nprompt\nwith\nspecial chars: @#$%"
        ]
        
        for prompt in prompts:
            mock_requests_post.reset_mock()
            call_llm("model", prompt)
            
            call_args = mock_requests_post.call_args
            assert call_args[1]['json']['prompt'] == prompt


class TestAPIResponseHandling:
    """
    Тесты для проверки обработки ответов от API.
    """
    
    @pytest.mark.api
    @pytest.mark.critical
    def test_success_response_parsed_correctly(self, mock_requests_post, mock_api_success_response):
        """
        Проверяет, что успешный ответ правильно обработан.
        
        Ожидаемое:
            - Функция возвращает текст из поля "response"
            - Тип возвращаемого значения: str
        """
        from app import call_llm
        
        result = call_llm("model", "prompt")
        
        assert isinstance(result, str)
        assert result == mock_api_success_response['response']
    
    @pytest.mark.api
    def test_error_response_handled(self, mock_requests_post):
        """
        Проверяет обработку ошибочного ответа от API.
        
        Ожидаемое:
            - Функция возвращает None при ошибке
        """
        from app import call_llm
        
        # Мокируем ошибку 500
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.text = "Server Error"
        mock_requests_post.return_value = mock_response
        
        result = call_llm("model", "prompt")
        
        assert result is None
    
    @pytest.mark.api
    def test_json_parse_error_handled(self, mock_requests_post):
        """
        Проверяет обработку ошибки парсинга JSON.
        
        Ожидаемое:
            - Функция не падает при ошибке JSON
            - Возвращает None
        """
        from app import call_llm
        
        # Мокируем ошибку парсинга JSON
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.side_effect = ValueError("Invalid JSON")
        mock_requests_post.return_value = mock_response
        
        result = call_llm("model", "prompt")
        
        assert result is None
    
    @pytest.mark.api
    def test_empty_response_field(self, mock_requests_post):
        """
        Проверяет обработку пустого поля "response".
        
        Ожидаемое:
            - Функция возвращает пустую строку (но не None)
        """
        from app import call_llm
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"response": ""}
        mock_requests_post.return_value = mock_response
        
        result = call_llm("model", "prompt")
        
        assert result == ""
        assert result is not None


class TestAPIErrorHandling:
    """
    Тесты для обработки различных типов ошибок при работе с API.
    """
    
    @pytest.mark.api
    def test_connection_error_handled(self, mock_requests_post):
        """
        Проверяет обработку ошибки соединения (сеть недоступна).
        
        Ожидаемое:
            - Функция возвращает None
            - Приложение не падает
        """
        from app import call_llm
        
        mock_requests_post.side_effect = requests.exceptions.ConnectionError()
        
        result = call_llm("model", "prompt")
        
        assert result is None
    
    @pytest.mark.api
    def test_timeout_error_handled(self, mock_requests_post):
        """
        Проверяет обработку таймаута при обращении к API.
        
        Ожидаемое:
            - Функция возвращает None
            - Логируется сообщение об ошибке
        """
        from app import call_llm
        
        mock_requests_post.side_effect = requests.exceptions.Timeout()
        
        result = call_llm("model", "prompt")
        
        assert result is None
    
    @pytest.mark.api
    def test_http_error_400(self, mock_requests_post):
        """
        Проверяет обработку ошибки 400 (неправильный запрос).
        
        Ожидаемое:
            - Функция возвращает None
        """
        from app import call_llm
        
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.text = "Bad Request"
        mock_requests_post.return_value = mock_response
        
        result = call_llm("model", "prompt")
        
        assert result is None
    
    @pytest.mark.api
    def test_http_error_401_unauthorized(self, mock_requests_post):
        """
        Проверяет обработку ошибки 401 (неавторизованный доступ).
        Это может случиться при неправильном API ключе.
        
        Ожидаемое:
            - Функция возвращает None
        """
        from app import call_llm
        
        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.text = "Unauthorized"
        mock_requests_post.return_value = mock_response
        
        result = call_llm("model", "prompt")
        
        assert result is None
    
    @pytest.mark.api
    def test_http_error_403_forbidden(self, mock_requests_post):
        """
        Проверяет обработку ошибки 403 (доступ запрещен).
        
        Ожидаемое:
            - Функция возвращает None
        """
        from app import call_llm
        
        mock_response = Mock()
        mock_response.status_code = 403
        mock_response.text = "Forbidden"
        mock_requests_post.return_value = mock_response
        
        result = call_llm("model", "prompt")
        
        assert result is None
    
    @pytest.mark.api
    def test_http_error_500_server_error(self, mock_requests_post):
        """
        Проверяет обработку ошибки 500 (внутренняя ошибка сервера).
        
        Ожидаемое:
            - Функция возвращает None
        """
        from app import call_llm
        
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        mock_requests_post.return_value = mock_response
        
        result = call_llm("model", "prompt")
        
        assert result is None
    
    @pytest.mark.api
    def test_http_error_503_service_unavailable(self, mock_requests_post):
        """
        Проверяет обработку ошибки 503 (сервис недоступен).
        
        Ожидаемое:
            - Функция возвращает None
        """
        from app import call_llm
        
        mock_response = Mock()
        mock_response.status_code = 503
        mock_response.text = "Service Unavailable"
        mock_requests_post.return_value = mock_response
        
        result = call_llm("model", "prompt")
        
        assert result is None


class TestAPISecurity:
    """
    Тесты для проверки безопасности при работе с API.
    """
    
    @pytest.mark.api
    @pytest.mark.security
    def test_api_key_in_header_not_url(self, mock_requests_post):
        """
        Проверяет, что API ключ передается в заголовке, а не в URL.
        
        Ожидаемое:
            - API ключ только в Authorization заголовке
            - API ключ не присутствует в URL
        """
        from app import call_llm
        
        call_llm("model", "prompt")
        
        call_args = mock_requests_post.call_args
        url = call_args[0][0]
        
        # Проверяем, что ключ не в URL
        assert "MENTORPIECE_API_KEY" not in url
        assert "Bearer" not in url
    
    @pytest.mark.api
    @pytest.mark.security
    def test_api_key_format_bearer(self, mock_requests_post):
        """
        Проверяет правильный формат Authorization заголовка.
        
        Ожидаемое:
            - Format: "Bearer <KEY>"
            - Не должно быть лишних пробелов
        """
        from app import call_llm
        
        call_llm("model", "prompt")
        
        call_args = mock_requests_post.call_args
        auth_header = call_args[1]['headers']['Authorization']
        
        # Проверяем формат
        assert auth_header.startswith('Bearer ')
        parts = auth_header.split(' ')
        assert len(parts) == 2
        assert parts[0] == 'Bearer'
    
    @pytest.mark.api
    @pytest.mark.security
    def test_no_api_key_no_request(self, mock_requests_post):
        """
        Проверяет, что при отсутствии API ключа запрос не отправляется.
        
        Ожидаемое:
            - requests.post не вызывается
            - Функция возвращает None
        """
        from app import call_llm
        
        # Мокируем отсутствие API ключа напрямую
        with patch('app.API_KEY', ''):
            result = call_llm("model", "prompt")
            
            assert result is None
            assert not mock_requests_post.called


class TestAPIPerfomance:
    """
    Тесты для проверки производительности при работе с API.
    """
    
    @pytest.mark.api
    def test_request_timeout_set(self, mock_requests_post):
        """
        Проверяет, что установлен таймаут для запроса.
        
        Ожидаемое:
            - Таймаут установлен (не должен быть None)
        """
        from app import call_llm
        
        call_llm("model", "prompt")
        
        call_args = mock_requests_post.call_args
        
        # Проверяем, что таймаут передан
        assert 'timeout' in call_args[1]
        assert call_args[1]['timeout'] is not None
    
    @pytest.mark.api
    def test_large_response_handled(self, mock_requests_post):
        """
        Проверяет обработку большого ответа от API.
        
        Ожидаемое:
            - Приложение корректно обрабатывает большие ответы
        """
        from app import call_llm
        
        large_response = "Response text. " * 10000  # Очень большой ответ
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"response": large_response}
        mock_requests_post.return_value = mock_response
        
        result = call_llm("model", "prompt")
        
        assert result == large_response
        assert len(result) > 100000
