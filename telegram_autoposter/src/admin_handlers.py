"""Admin commands and inline controls for bot configuration."""

from __future__ import annotations

import logging
from dataclasses import asdict

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder

from .config import Settings
from .formatter import emoji_pools, format_post
from .scheduler import PostingScheduler

LOGGER = logging.getLogger(__name__)

router = Router(name="admin")

TONES = ["мотивирующий", "экспертный", "дружеский", "вдохновляющий", "практичный"]
STYLES = ["DEFAULT", "KANDINSKY", "UHD", "ANIME"]
MOODS = ["утренний", "вечерний", "праздничный"]


class KandinskyAuthState(StatesGroup):
    """FSM states for Kandinsky auth setup."""

    wait_type = State()
    wait_api_key = State()
    wait_secret = State()
    wait_email = State()
    wait_password = State()


class OpenAIState(StatesGroup):
    """FSM states for OpenAI settings setup."""

    wait_url = State()
    wait_key = State()
    wait_text_model = State()
    wait_prompt_model = State()


def _admin_only(message: Message, settings: Settings) -> bool:
    user_id = message.from_user.id if message.from_user else 0
    return user_id in settings.admin_ids


def _build_choice_keyboard(prefix: str, values: list[str], columns: int = 2) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for value in values:
        builder.button(text=value.capitalize(), callback_data=f"{prefix}:{value}")
    builder.adjust(columns)
    return builder.as_markup()


def register_handlers(bot_router: Router, settings: Settings, scheduler: PostingScheduler) -> None:
    """Register router handlers with injected runtime dependencies."""

    @router.message(Command("start"))
    async def start_handler(message: Message) -> None:
        if not _admin_only(message, settings):
            await message.answer("⛔ Доступ запрещён")
            return
        await message.answer(
            "Привет! Я автопостер. Основные команды: /settings /set_topic /set_times /set_tone /set_style "
            "/set_image_size /set_channel /toggle /post_now /stats /reset"
        )

    @router.message(Command("set_topic"))
    async def set_topic(message: Message) -> None:
        if not _admin_only(message, settings):
            await message.answer("⛔ Доступ запрещён")
            return
        topic = message.text.replace("/set_topic", "", 1).strip()
        if not topic:
            await message.answer("Использование: /set_topic <тема>")
            return
        settings.topic = topic
        await settings.save()
        await message.answer(f"✅ Тема обновлена: {topic}")

    @router.message(Command("set_times"))
    async def set_times(message: Message) -> None:
        if not _admin_only(message, settings):
            await message.answer("⛔ Доступ запрещён")
            return
        payload = message.text.replace("/set_times", "", 1).strip()
        times = [item.strip() for item in payload.split(",") if item.strip()]
        if not times:
            await message.answer("Использование: /set_times <09:00,15:00,21:00>")
            return
        settings.posting_times = times
        await settings.save()
        scheduler.reload_jobs()
        await message.answer("✅ Времена публикации обновлены")

    @router.message(Command("set_tone"))
    async def set_tone(message: Message) -> None:
        if not _admin_only(message, settings):
            await message.answer("⛔ Доступ запрещён")
            return
        await message.answer("Выберите тон:", reply_markup=_build_choice_keyboard("tone", TONES))

    @router.callback_query(F.data.startswith("tone:"))
    async def tone_callback(callback: CallbackQuery) -> None:
        tone = callback.data.split(":", 1)[1]
        settings.tone = tone
        await settings.save()
        await callback.message.answer(f"✅ Тон установлен: {tone}")
        await callback.answer()

    @router.message(Command("set_mood"))
    async def set_mood(message: Message) -> None:
        if not _admin_only(message, settings):
            await message.answer("⛔ Доступ запрещён")
            return
        await message.answer("Выберите настроение:", reply_markup=_build_choice_keyboard("mood", MOODS))

    @router.callback_query(F.data.startswith("mood:"))
    async def mood_callback(callback: CallbackQuery) -> None:
        mood = callback.data.split(":", 1)[1]
        settings.mood = mood
        await settings.save()
        await callback.message.answer(f"✅ Настроение установлено: {mood}")
        await callback.answer()

    @router.message(Command("set_style"))
    async def set_style(message: Message) -> None:
        if not _admin_only(message, settings):
            await message.answer("⛔ Доступ запрещён")
            return
        await message.answer("Выберите стиль Kandinsky:", reply_markup=_build_choice_keyboard("style", STYLES))

    @router.callback_query(F.data.startswith("style:"))
    async def style_callback(callback: CallbackQuery) -> None:
        style = callback.data.split(":", 1)[1]
        settings.kandinsky_style = style
        await settings.save()
        await callback.message.answer(f"✅ Стиль установлен: {style}")
        await callback.answer()

    @router.message(Command("set_image_size"))
    async def set_image_size(message: Message) -> None:
        if not _admin_only(message, settings):
            await message.answer("⛔ Доступ запрещён")
            return
        parts = message.text.split()
        if len(parts) != 3:
            await message.answer("Использование: /set_image_size <width> <height>")
            return
        settings.kandinsky_width = int(parts[1])
        settings.kandinsky_height = int(parts[2])
        await settings.save()
        await message.answer("✅ Размер изображения обновлён")

    @router.message(Command("set_channel"))
    async def set_channel(message: Message) -> None:
        if not _admin_only(message, settings):
            await message.answer("⛔ Доступ запрещён")
            return
        channel = message.text.replace("/set_channel", "", 1).strip()
        if not channel:
            await message.answer("Использование: /set_channel <@channel или ID>")
            return
        settings.telegram_channel = channel
        await settings.save()
        await message.answer(f"✅ Канал установлен: {channel}")

    @router.message(Command("toggle"))
    async def toggle(message: Message) -> None:
        if not _admin_only(message, settings):
            await message.answer("⛔ Доступ запрещён")
            return
        settings.is_active = not settings.is_active
        await settings.save()
        scheduler.reload_jobs()
        await message.answer(f"✅ Автопостинг: {'включён' if settings.is_active else 'выключен'}")

    @router.message(Command("post_now"))
    async def post_now(message: Message) -> None:
        if not _admin_only(message, settings):
            await message.answer("⛔ Доступ запрещён")
            return
        await scheduler.publish_post()
        await message.answer("✅ Попытка публикации выполнена, смотрите лог и канал.")

    @router.message(Command("stats"))
    async def stats(message: Message) -> None:
        if not _admin_only(message, settings):
            await message.answer("⛔ Доступ запрещён")
            return
        next_post = scheduler.get_next_run() or "не запланировано"
        await message.answer(
            f"Всего постов: {settings.stats.total_posts}\n"
            f"Последний пост: {settings.stats.last_post_time or '—'}\n"
            f"Следующий пост: {next_post}\n"
            f"Статус: {'вкл' if settings.is_active else 'выкл'}"
        )

    @router.message(Command("settings"))
    async def show_settings(message: Message) -> None:
        if not _admin_only(message, settings):
            await message.answer("⛔ Доступ запрещён")
            return
        snapshot = asdict(settings)
        snapshot.pop("openai_key", None)
        snapshot.pop("kandinsky_password", None)
        snapshot.pop("kandinsky_secret_key", None)
        snapshot.pop("kandinsky_api_key", None)
        snapshot.pop("project_root", None)
        await message.answer("Текущие настройки:\n" + "\n".join(f"{k}: {v}" for k, v in snapshot.items()))

    @router.message(Command("reset"))
    async def reset(message: Message) -> None:
        if not _admin_only(message, settings):
            await message.answer("⛔ Доступ запрещён")
            return
        await settings.reset_to_env()
        scheduler.reload_jobs()
        await message.answer("✅ Настройки сброшены к значениям .env")

    @router.message(Command("set_auth_kandinsky"))
    async def set_auth_kandinsky(message: Message, state: FSMContext) -> None:
        if not _admin_only(message, settings):
            await message.answer("⛔ Доступ запрещён")
            return
        await state.set_state(KandinskyAuthState.wait_type)
        await message.answer("Выберите тип авторизации: api или web")

    @router.message(KandinskyAuthState.wait_type)
    async def kandinsky_type(message: Message, state: FSMContext) -> None:
        value = message.text.strip().lower()
        if value not in {"api", "web"}:
            await message.answer("Введите api или web")
            return
        settings.kandinsky_auth_type = value
        if value == "api":
            await state.set_state(KandinskyAuthState.wait_api_key)
            await message.answer("Введите KANDINSKY_API_KEY")
        else:
            await state.set_state(KandinskyAuthState.wait_email)
            await message.answer("Введите email FusionBrain")

    @router.message(KandinskyAuthState.wait_api_key)
    async def kandinsky_api_key(message: Message, state: FSMContext) -> None:
        settings.kandinsky_api_key = message.text.strip()
        await state.set_state(KandinskyAuthState.wait_secret)
        await message.answer("Введите KANDINSKY_SECRET_KEY")

    @router.message(KandinskyAuthState.wait_secret)
    async def kandinsky_secret(message: Message, state: FSMContext) -> None:
        settings.kandinsky_secret_key = message.text.strip()
        await settings.save()
        await state.clear()
        await message.answer("✅ Данные Kandinsky (api) обновлены")

    @router.message(KandinskyAuthState.wait_email)
    async def kandinsky_email(message: Message, state: FSMContext) -> None:
        settings.kandinsky_email = message.text.strip()
        await state.set_state(KandinskyAuthState.wait_password)
        await message.answer("Введите пароль FusionBrain")

    @router.message(KandinskyAuthState.wait_password)
    async def kandinsky_password(message: Message, state: FSMContext) -> None:
        settings.kandinsky_password = message.text.strip()
        await settings.save()
        await state.clear()
        await message.answer("✅ Данные Kandinsky (web) обновлены")

    @router.message(Command("set_openai"))
    async def set_openai(message: Message, state: FSMContext) -> None:
        if not _admin_only(message, settings):
            await message.answer("⛔ Доступ запрещён")
            return
        await state.set_state(OpenAIState.wait_url)
        await message.answer("Введите OPENAI_URL")

    @router.message(OpenAIState.wait_url)
    async def openai_url(message: Message, state: FSMContext) -> None:
        settings.openai_url = message.text.strip()
        await state.set_state(OpenAIState.wait_key)
        await message.answer("Введите OPENAI_KEY")

    @router.message(OpenAIState.wait_key)
    async def openai_key(message: Message, state: FSMContext) -> None:
        settings.openai_key = message.text.strip()
        await state.set_state(OpenAIState.wait_text_model)
        await message.answer("Введите TEXT_MODEL")

    @router.message(OpenAIState.wait_text_model)
    async def openai_text_model(message: Message, state: FSMContext) -> None:
        settings.text_model = message.text.strip()
        await state.set_state(OpenAIState.wait_prompt_model)
        await message.answer("Введите PROMPT_MODEL")

    @router.message(OpenAIState.wait_prompt_model)
    async def openai_prompt_model(message: Message, state: FSMContext) -> None:
        settings.prompt_model = message.text.strip()
        await settings.save()
        await state.clear()
        await message.answer("✅ Настройки OpenAI обновлены")

    @router.message(Command("test_format"))
    async def test_format(message: Message) -> None:
        if not _admin_only(message, settings):
            await message.answer("⛔ Доступ запрещён")
            return
        text = message.text.replace("/test_format", "", 1).strip()
        if not text:
            await message.answer("Использование: /test_format <текст>")
            return
        await message.answer(format_post(text, tone=settings.tone, topic=settings.topic, mood=settings.mood))

    bot_router.include_router(router)
    LOGGER.info("Admin handlers registered. Emoji pools available: %s", list(emoji_pools.keys()))
