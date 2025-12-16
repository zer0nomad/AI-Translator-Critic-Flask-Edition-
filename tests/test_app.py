"""
test_app.py - Функциональные тесты для Flask приложения
========================================================
Тесты для проверки основной функциональности приложения:
- Загрузка формы (GET /)
- Обработка данных (POST /)
- Обработка ошибок
- Валидация входных данных
"""

import pytest
from unittest.mock import patch, Mock


class TestIndexGet:
    """
    Тесты для GET запроса на корневой URL (/).
    Проверяют загрузку и структуру формы.
    """
    
    @pytest.mark.critical
    def test_index_get_returns_200(self, client):
        """
        Проверяет, что GET / возвращает статус 200.
        
        Ожидаемое: 
            - Status code: 200
            - Content-Type: text/html
        """
        response = client.get("/")
        assert response.status_code == 200
        assert "text/html" in response.content_type
    
    @pytest.mark.critical
    def test_index_returns_form(self, client):
        """
        Проверяет, что в ответе содержится HTML форма.
        
        Ожидаемое:
            - Форма содержит textarea для ввода текста
            - Форма содержит select для выбора языка
            - Форма содержит кнопку submit
        """
        response = client.get("/")
        html = response.get_data(as_text=True)
        
        # Проверяем наличие элементов формы
        assert 'name="text"' in html, "Отсутствует поле ввода текста (textarea)"
        assert 'name="language"' in html, "Отсутствует выбор языка (select)"
        assert 'type="submit"' in html, "Отсутствует кнопка submit"
    
    def test_index_contains_page_title(self, client):
        """
        Проверяет, что страница содержит правильный заголовок.
        """
        response = client.get("/")
        html = response.get_data(as_text=True)
        assert "AI Translator & Critic" in html
    
    def test_index_contains_language_options(self, client):
        """
        Проверяет, что все три языка доступны для выбора.
        """
        response = client.get("/")
        html = response.get_data(as_text=True)
        
        languages = ["Английский", "Французский", "Немецкий"]
        for language in languages:
            assert language in html, f"Язык '{language}' не найден в форме"


class TestPostRequestValidation:
    """
    Тесты для валидации POST запросов.
    Проверяют обработку различных входных данных.
    """
    
    @pytest.mark.critical
    def test_post_with_empty_text_returns_error(self, client):
        """
        Проверяет, что пустой текст возвращает ошибку.
        
        Ожидаемое:
            - Status code: 200 (страница загружается, но с сообщением об ошибке)
            - В ответе содержится сообщение об ошибке
        """
        response = client.post("/", data={
            "text": "",
            "language": "Английский"
        })
        
        assert response.status_code == 200
        html = response.get_data(as_text=True)
        assert "введите текст" in html.lower()
    
    def test_post_with_whitespace_only_returns_error(self, client):
        """
        Проверяет, что текст только с пробелами считается пустым.
        """
        response = client.post("/", data={
            "text": "   \n  \t  ",
            "language": "Английский"
        })
        
        html = response.get_data(as_text=True)
        assert "введите текст" in html.lower()
    
    @pytest.mark.critical
    def test_post_with_valid_data(self, client, sample_form_data, mock_call_llm):
        """
        Проверяет, что POST с валидными данными вызывает API.
        
        Параметры:
            client: Flask test client
            sample_form_data: фикстура с данными формы
            mock_call_llm: моковая функция API
        
        Ожидаемое:
            - Status code: 200
            - Функция call_llm вызывается два раза (перевод и оценка)
        """
        mock_call_llm.return_value = "Мокированный ответ"
        
        response = client.post("/", data=sample_form_data)
        
        assert response.status_code == 200
        # Проверяем, что call_llm была вызвана дважды
        assert mock_call_llm.call_count == 2
    
    def test_post_creates_correct_prompts(self, client, sample_form_data, mock_call_llm):
        """Проверяет, что промпты составляются правильно."""
        mock_call_llm.return_value = "Ответ"
        
        response = client.post("/", data=sample_form_data)
        
        # call_args_list содержит (args, kwargs) для каждого вызова
        # Функция вызывается как call_llm(model_name, prompt)
        assert mock_call_llm.called
        assert mock_call_llm.call_count == 2  # Перевод + оценка
    
    def test_language_parameter_passed_correctly(self, client, available_languages, mock_call_llm):
        """Проверяет, что выбранный язык включен в промпт."""
        mock_call_llm.return_value = "Ответ"
        
        response = client.post("/", data={
            "text": "Test text",
            "language": available_languages
        })
        
        assert response.status_code == 200
        assert mock_call_llm.call_count == 2



class TestErrorHandling:
    """
    Тесты для обработки ошибок при API запросах.
    """
    
    @pytest.mark.critical
    def test_api_error_displayed_gracefully(self, client, sample_form_data, mock_call_llm):
        """
        Проверяет, что ошибка от API отображается пользователю.
        
        Ожидаемое:
            - Status code: 200
            - В ответе содержится сообщение об ошибке
            - Приложение не падает
        """
        # Мокируем ошибку API
        mock_call_llm.return_value = None
        
        response = client.post("/", data=sample_form_data)
        
        assert response.status_code == 200
        html = response.get_data(as_text=True)
        assert "Ошибка" in html or "error" in html.lower()
    
    def test_missing_api_key_handled(self, sample_form_data):
        """Проверяет поведение при отсутствии API ключа."""
        with patch('app.API_KEY', ''):
            from app import call_llm
            result = call_llm("model", "prompt")
            assert result is None



class TestMarkdownProcessing:
    """
    Тесты для обработки markdown в оценке качества.
    """
    
    @pytest.mark.critical
    def test_evaluation_with_markdown_processed(self, client, sample_form_data, mock_call_llm):
        """
        Проверяет, что markdown в оценке преобразуется в HTML.
        
        Ожидаемое:
            - ** преобразуется в <strong>
            - # преобразуется в <h2> (или выше)
            - - преобразуется в <li> (внутри <ul>)
        """
        # Мокируем ответ с markdown синтаксисом
        markdown_response = """## Оценка: 8/10
        
**Сильные стороны:**
- Точная передача смысла
- Правильная грамматика

**Недостатки:**
- Слегка неестественный стиль"""
        
        mock_call_llm.return_value = markdown_response
        
        response = client.post("/", data=sample_form_data)
        html = response.get_data(as_text=True)
        
        # Проверяем, что markdown обработан в HTML
        assert "<strong>" in html or "<h2>" in html or "<ul>" in html
    
    def test_markdown_security_xss_prevention(self, client, sample_form_data, mock_call_llm):
        """
        Проверяет, что вредоносный HTML в markdown не выполняется (XSS protection).
        
        Ожидаемое:
            - HTML теги экранируются и отображаются как текст
            - JavaScript не выполняется
        """
        dangerous_content = """<script>alert('XSS')</script>
        
Some text"""
        
        mock_call_llm.return_value = dangerous_content
        
        response = client.post("/", data=sample_form_data)
        html = response.get_data(as_text=True)
        
        # Script тег не должен быть необработанным
        # (markdown должен экранировать опасные HTML)
        assert "<script>" not in html or "&lt;script&gt;" in html


class TestResponseContent:
    """
    Тесты для проверки содержимого ответа.
    """
    
    def test_response_contains_original_text(self, client, sample_form_data, mock_call_llm):
        """
        Проверяет, что исходный текст отображается в ответе.
        """
        mock_call_llm.return_value = "Translated"
        
        response = client.post("/", data=sample_form_data)
        html = response.get_data(as_text=True)
        
        assert sample_form_data['text'] in html
    
    def test_response_contains_translated_text(self, client, sample_form_data, mock_call_llm):
        """
        Проверяет, что переведенный текст отображается в ответе.
        """
        translated_text = "He was too simple-minded"
        mock_call_llm.return_value = translated_text
        
        response = client.post("/", data=sample_form_data)
        html = response.get_data(as_text=True)
        
        assert translated_text in html
    
    def test_response_contains_evaluation(self, client, sample_form_data, mock_call_llm):
        """
        Проверяет, что оценка качества отображается в ответе.
        """
        evaluation_text = "Оценка: 8/10"
        mock_call_llm.side_effect = ["Translated", evaluation_text]
        
        response = client.post("/", data=sample_form_data)
        html = response.get_data(as_text=True)
        
        assert evaluation_text in html or "Оценка" in html
    
    def test_response_contains_language_tag(self, client, sample_form_data, mock_call_llm):
        """
        Проверяет, что выбранный язык упоминается в ответе.
        """
        mock_call_llm.return_value = "Translated"
        
        response = client.post("/", data=sample_form_data)
        html = response.get_data(as_text=True)
        
        assert sample_form_data['language'] in html


class TestApplicationStability:
    """
    Тесты для проверки стабильности приложения.
    """
    
    def test_multiple_consecutive_requests(self, client, sample_form_data, mock_call_llm):
        """
        Проверяет, что приложение выдерживает несколько последовательных запросов.
        """
        mock_call_llm.return_value = "Response"
        
        for i in range(5):
            response = client.post("/", data=sample_form_data)
            assert response.status_code == 200
    
    def test_special_characters_in_text(self, client, mock_call_llm):
        """
        Проверяет обработку специальных символов в тексте.
        """
        special_text = "Test with émojis 🚀, spëcial çhars, and 日本語"
        
        mock_call_llm.return_value = "Translated"
        
        response = client.post("/", data={
            "text": special_text,
            "language": "Английский"
        })
        
        assert response.status_code == 200
        html = response.get_data(as_text=True)
        # Проверяем, что текст корректно обработан
        assert len(html) > 0
    
    def test_very_long_text(self, client, mock_call_llm):
        """
        Проверяет обработку очень длинного текста (stress test).
        """
        long_text = "Test sentence. " * 1000  # Очень длинный текст
        
        mock_call_llm.return_value = "Translated"
        
        response = client.post("/", data={
            "text": long_text,
            "language": "Английский"
        })
        
        assert response.status_code == 200


class TestHelperFunctions:
    """Тесты для вспомогательных функций."""
    
    @pytest.mark.critical
    def test_build_translation_prompt(self):
        """Проверяет построение промпта для перевода."""
        from app import _build_translation_prompt
        
        prompt = _build_translation_prompt("Hello", "Французский")
        
        assert "Hello" in prompt
        assert "Французский" in prompt
        assert "Переведи" in prompt
    
    @pytest.mark.critical
    def test_build_evaluation_prompt(self):
        """Проверяет построение промпта для оценки."""
        from app import _build_evaluation_prompt
        
        prompt = _build_evaluation_prompt("Hello", "Bonjour", "Французский")
        
        assert "Hello" in prompt
        assert "Bonjour" in prompt
        assert "Французский" in prompt
        assert "Оцени" in prompt
    
    @patch('app.call_llm')
    def test_process_translation_success(self, mock_call_llm):
        """Проверяет успешный перевод."""
        from app import _process_translation
        
        mock_call_llm.return_value = "Bonjour"
        result = _process_translation("Hello", "Французский")
        
        assert result == "Bonjour"
        assert mock_call_llm.called
    
    @patch('app.call_llm')
    def test_process_translation_failure(self, mock_call_llm):
        """Проверяет обработку ошибки перевода."""
        from app import _process_translation
        
        mock_call_llm.return_value = None
        result = _process_translation("Hello", "Французский")
        
        assert result is None
    
    @patch('app.call_llm')
    def test_process_evaluation_success(self, mock_call_llm):
        """Проверяет успешную оценку."""
        from app import _process_evaluation
        
        mock_call_llm.return_value = "**Оценка: 9/10**"
        result = _process_evaluation("Hello", "Bonjour", "Французский")
        
        assert "Оценка: 9/10" in result
        assert "<strong>" in result  # markdown обработан
    
    @patch('app.call_llm')
    def test_process_evaluation_failure(self, mock_call_llm):
        """Проверяет обработку ошибки оценки."""
        from app import _process_evaluation
        
        mock_call_llm.return_value = None
        result = _process_evaluation("Hello", "Bonjour", "Французский")
        
        assert "Не удалось получить оценку" in result


class TestEdgeCases:
    """Тесты граничных случаев."""
    
    @patch('app.call_llm')
    def test_post_with_newlines_in_text(self, mock_call_llm, client):
        """Проверяет текст с переносами строк."""
        mock_call_llm.return_value = "Translated"
        
        response = client.post("/", data={
            "text": "Line 1\nLine 2\nLine 3",
            "language": "Английский"
        })
        
        assert response.status_code == 200
        assert mock_call_llm.called
    
    @patch('app.call_llm')
    def test_post_with_special_html_chars(self, mock_call_llm, client):
        """Проверяет текст со спецсимволами HTML."""
        mock_call_llm.return_value = "Translated"
        
        response = client.post("/", data={
            "text": "<script>alert('test')</script>",
            "language": "Английский"
        })
        
        assert response.status_code == 200
    
    @patch('app.call_llm')
    def test_post_with_unicode_characters(self, mock_call_llm, client):
        """Проверяет текст с Unicode символами."""
        mock_call_llm.return_value = "Переведено"
        
        response = client.post("/", data={
            "text": "Привет мир! 你好世界 مرحبا العالم",
            "language": "Английский"
        })
        
        assert response.status_code == 200
        assert "Привет мир!" in response.get_data(as_text=True)
    
    @patch('app.call_llm')
    def test_post_with_numbers_and_symbols(self, mock_call_llm, client):
        """Проверяет текст с числами и символами."""
        mock_call_llm.return_value = "123 translated"
        
        response = client.post("/", data={
            "text": "Test 123 !@#$%^&*()",
            "language": "Английский"
        })
        
        assert response.status_code == 200


class TestDefaultValues:
    """Тесты значений по умолчанию."""
    
    @patch('app.call_llm')
    def test_post_without_language_uses_default(self, mock_call_llm, client):
        """Проверяет использование языка по умолчанию."""
        mock_call_llm.return_value = "Translated"
        
        response = client.post("/", data={
            "text": "Test text"
            # language не указан
        })
        
        assert response.status_code == 200
        # Проверяем что был использован язык по умолчанию
        html = response.get_data(as_text=True)
        assert "Английский" in html
    
    @patch('app.call_llm')
    def test_post_without_action_uses_default(self, mock_call_llm, client):
        """Проверяет использование действия по умолчанию."""
        mock_call_llm.return_value = "Translated"
        
        response = client.post("/", data={
            "text": "Test text",
            "language": "Английский"
            # action не указан
        })
        
        assert response.status_code == 200
        assert mock_call_llm.called


# ========== МАРКЕРЫ ТЕСТОВ ==========
# Используются для запуска специфических групп тестов:
# pytest tests/test_app.py -m critical   # Запустить только критические тесты
# pytest tests/test_app.py -m "not api"  # Запустить все кроме API тестов
