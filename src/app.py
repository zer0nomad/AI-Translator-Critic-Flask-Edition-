"""AI Translator & Critic - Веб-приложение для перевода и оценки качества."""

import os
import logging
from flask import Flask, render_template, request
import requests
from dotenv import load_dotenv
import markdown

logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

load_dotenv()
app = Flask(__name__, template_folder="templates")

API_KEY = os.getenv("MENTORPIECE_API_KEY")
API_ENDPOINT = "https://api.mentorpiece.org/v1/process-ai-request"
TRANSLATOR_MODEL = "Qwen/Qwen3-VL-30B-A3B-Instruct"
JUDGE_MODEL = "claude-sonnet-4-5-20250929"
API_TIMEOUT = 30


def call_llm(model_name, prompt):
    """Вызвать LLM API."""
    if not API_KEY:
        logger.error("API_KEY не загружен")
        return None
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}"
    }
    payload = {"model_name": model_name, "prompt": prompt}
    
    try:
        logger.info(f"Запрос к API с моделью: {model_name}")
        response = requests.post(
            API_ENDPOINT,
            json=payload,
            headers=headers,
            timeout=API_TIMEOUT
        )
        
        if response.status_code == 200:
            result = response.json().get("response", "")
            logger.info(f"Успешный ответ от модели {model_name}")
            return result
        else:
            logger.error(f"API вернул статус {response.status_code}")
            return None
    
    except (requests.exceptions.Timeout, requests.exceptions.ConnectionError):
        logger.error("Ошибка соединения с API")
        return None
    except (requests.exceptions.RequestException, ValueError) as e:
        logger.error(f"Ошибка API: {e}")
        return None


def _build_translation_prompt(text, language):
    """Построить промпт для перевода."""
    return (
        f"Переведи следующий текст на {language} язык. "
        f"Ответь только переводом, без комментариев.\n\n"
        f"Текст: {text}"
    )


def _build_evaluation_prompt(original, translated, language):
    """Построить промпт для оценки."""
    return (
        f"Оцени качество перевода от 1 до 10 баллов:\n\n"
        f"Оригинал: {original}\n\n"
        f"Перевод: {translated}\n\n"
        f"Язык: {language}\n\n"
        f"Дай оценку и обоснование."
    )


def _process_translation(text, language):
    """Получить перевод текста."""
    prompt = _build_translation_prompt(text, language)
    return call_llm(TRANSLATOR_MODEL, prompt)


def _process_evaluation(original, translated, language):
    """Получить оценку качества."""
    prompt = _build_evaluation_prompt(original, translated, language)
    evaluation = call_llm(JUDGE_MODEL, prompt)
    
    if evaluation is None:
        logger.error("Не удалось получить оценку")
        return "Не удалось получить оценку. Попробуйте позже."
    
    return markdown.markdown(evaluation)


@app.route("/", methods=["GET"])
def index():
    """Отобразить форму для ввода."""
    return render_template("index.html")


@app.route("/", methods=["POST"])
def process():
    """Обработать перевод и оценку."""
    original_text = request.form.get("text", "").strip()
    target_language = request.form.get("language", "Английский")
    
    if not original_text:
        logger.warning("Получен пустой текст")
        return render_template("index.html", error="Введите текст для перевода.")
    
    logger.info(f"Перевод на {target_language}")
    translated_text = _process_translation(original_text, target_language)
    
    if translated_text is None:
        return render_template(
            "index.html",
            error="Ошибка перевода. Проверьте соединение."
        )
    
    logger.info("Оценка качества")
    evaluation = _process_evaluation(original_text, translated_text, target_language)
    
    return render_template(
        "index.html",
        original_text=original_text,
        target_language=target_language,
        translated_text=translated_text,
        evaluation=evaluation
    )


if __name__ == "__main__":
    logger.info(f"Запуск приложения. API: {bool(API_KEY)}")
    app.run(debug=True, host="0.0.0.0", port=5000)
