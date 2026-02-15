from __future__ import annotations

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message
from aiogram.filters import Command

from .config import SettingsManager
from .scheduler import PostingScheduler
from .utils import parse_times

TONES = ["мотивирующий", "экспертный", "дружеский", "киберпанк"]
MOODS = ["утренний", "вечерний", "ночной"]
STYLES = ["DEFAULT", "KANDINSKY", "UHD", "ANIME"]


class KandinskyAuthState(StatesGroup):
    mode = State()
    key = State()
    secret = State()
    email = State()
    password = State()


class OpenAIState(StatesGroup):
    base_url = State()
    key = State()
    model = State()


def admin_router(settings_manager: SettingsManager, scheduler: PostingScheduler) -> Router:
    router = Router()

    def allowed(message: Message) -> bool:
        return bool(message.from_user and message.from_user.id in settings_manager.settings.admin_ids)

    def cb_keyboard(prefix: str, values: list[str]) -> InlineKeyboardMarkup:
        rows = [[InlineKeyboardButton(text=v, callback_data=f"{prefix}:{v}")] for v in values]
        return InlineKeyboardMarkup(inline_keyboard=rows)

    @router.message(Command("start"))
    async def start(message: Message) -> None:
        if not allowed(message):
            return
        await message.answer(
            "Готово. Команды: /set_topic /set_times /set_tone /set_mood /set_style /set_image_size "
            "/set_auth_kandinsky /set_openai /set_keywords /set_channel /toggle /post_now /stats /settings /reset"
        )

    @router.message(Command("set_topic"))
    async def set_topic(message: Message) -> None:
        if not allowed(message):
            return
        topic = message.text.replace("/set_topic", "", 1).strip()
        if not topic:
            await message.answer("Использование: /set_topic <тема>")
            return
        await settings_manager.update(topic=topic)
        await message.answer("✅ Тема обновлена")

    @router.message(Command("set_keywords"))
    async def set_keywords(message: Message) -> None:
        if not allowed(message):
            return
        raw = message.text.replace("/set_keywords", "", 1).strip()
        if not raw:
            await message.answer("Использование: /set_keywords cve,exploit,rce")
            return
        values = [x.strip().lower() for x in raw.split(",") if x.strip()]
        await settings_manager.update(source_keywords=values)
        await message.answer("✅ Ключевые слова источника обновлены")

    @router.message(Command("set_times"))
    async def set_times(message: Message) -> None:
        if not allowed(message):
            return
        raw = message.text.replace("/set_times", "", 1).strip()
        try:
            times = parse_times(raw)
        except Exception:
            await message.answer("Формат: /set_times 09:00,15:00,21:00")
            return
        await settings_manager.update(posting_times=times)
        scheduler.reload_jobs()
        await message.answer("✅ Время публикаций обновлено")

    @router.message(Command("set_tone"))
    async def set_tone(message: Message) -> None:
        if not allowed(message):
            return
        await message.answer("Выберите тон:", reply_markup=cb_keyboard("tone", TONES))

    @router.callback_query(F.data.startswith("tone:"))
    async def tone_cb(callback: CallbackQuery) -> None:
        value = callback.data.split(":", 1)[1]
        await settings_manager.update(tone=value)
        await callback.message.answer(f"✅ Тон: {value}")
        await callback.answer()

    @router.message(Command("set_mood"))
    async def set_mood(message: Message) -> None:
        if not allowed(message):
            return
        await message.answer("Выберите настроение:", reply_markup=cb_keyboard("mood", MOODS))

    @router.callback_query(F.data.startswith("mood:"))
    async def mood_cb(callback: CallbackQuery) -> None:
        value = callback.data.split(":", 1)[1]
        await settings_manager.update(mood=value)
        await callback.message.answer(f"✅ Настроение: {value}")
        await callback.answer()

    @router.message(Command("set_style"))
    async def set_style(message: Message) -> None:
        if not allowed(message):
            return
        await message.answer("Выберите стиль:", reply_markup=cb_keyboard("style", STYLES))

    @router.callback_query(F.data.startswith("style:"))
    async def style_cb(callback: CallbackQuery) -> None:
        value = callback.data.split(":", 1)[1]
        await settings_manager.update(kandinsky_style=value)
        await callback.message.answer(f"✅ Стиль: {value}")
        await callback.answer()

    @router.message(Command("set_image_size"))
    async def set_image_size(message: Message) -> None:
        if not allowed(message):
            return
        parts = message.text.split()
        if len(parts) != 3:
            await message.answer("Использование: /set_image_size <width> <height>")
            return
        await settings_manager.update(kandinsky_width=int(parts[1]), kandinsky_height=int(parts[2]))
        await message.answer("✅ Размер обновлён")

    @router.message(Command("set_channel"))
    async def set_channel(message: Message) -> None:
        if not allowed(message):
            return
        channel = message.text.replace("/set_channel", "", 1).strip()
        if not channel:
            await message.answer("Использование: /set_channel <@channel|ID>")
            return
        try:
            me = await message.bot.get_me()
            member = await message.bot.get_chat_member(channel, me.id)
            if member.status not in {"administrator", "creator"}:
                await message.answer("Бот не администратор канала")
                return
        except Exception:
            await message.answer("Не удалось проверить права, но канал сохранён")
        await settings_manager.update(channel_id=channel)
        scheduler.reload_jobs()
        await message.answer("✅ Канал сохранён")

    @router.message(Command("toggle"))
    async def toggle(message: Message) -> None:
        if not allowed(message):
            return
        value = not settings_manager.settings.autopost_enabled
        await settings_manager.update(autopost_enabled=value)
        scheduler.reload_jobs()
        await message.answer(f"✅ Автопостинг {'включён' if value else 'выключен'}")

    @router.message(Command("post_now"))
    async def post_now(message: Message) -> None:
        if not allowed(message):
            return
        await scheduler.publish_post(force=True)
        await message.answer("✅ Запущена тестовая публикация")

    @router.message(Command("stats"))
    async def stats(message: Message) -> None:
        if not allowed(message):
            return
        stats = settings_manager.settings.stats
        await message.answer(
            f"Постов: {stats.total_posts}\nПоследний: {stats.last_post_at or '—'}\nСледующий: {scheduler.next_run() or '—'}"
        )

    @router.message(Command("settings"))
    async def show_settings(message: Message) -> None:
        if not allowed(message):
            return
        data = settings_manager.settings.model_dump()
        for secret in ["openai_api_key", "kandinsky_api_key", "kandinsky_secret_key", "kandinsky_password"]:
            data.pop(secret, None)
        await message.answer("\n".join([f"{k}: {v}" for k, v in data.items()]))

    @router.message(Command("reset"))
    async def reset(message: Message) -> None:
        if not allowed(message):
            return
        await settings_manager.reset_to_env()
        scheduler.reload_jobs()
        await message.answer("✅ Сброшено к .env")

    @router.message(Command("set_auth_kandinsky"))
    async def set_auth_kandinsky(message: Message, state: FSMContext) -> None:
        if not allowed(message):
            return
        await state.set_state(KandinskyAuthState.mode)
        await message.answer("Введите режим авторизации: api или web")

    @router.message(KandinskyAuthState.mode)
    async def k_mode(message: Message, state: FSMContext) -> None:
        mode = message.text.strip().lower()
        if mode not in {"api", "web"}:
            await message.answer("Только api или web")
            return
        await settings_manager.update(kandinsky_auth_mode=mode)
        if mode == "api":
            await state.set_state(KandinskyAuthState.key)
            await message.answer("Введите KANDINSKY_API_KEY")
        else:
            await state.set_state(KandinskyAuthState.email)
            await message.answer("Введите email")

    @router.message(KandinskyAuthState.key)
    async def k_key(message: Message, state: FSMContext) -> None:
        await settings_manager.update(kandinsky_api_key=message.text.strip())
        await state.set_state(KandinskyAuthState.secret)
        await message.answer("Введите KANDINSKY_SECRET_KEY")

    @router.message(KandinskyAuthState.secret)
    async def k_secret(message: Message, state: FSMContext) -> None:
        await settings_manager.update(kandinsky_secret_key=message.text.strip())
        await state.clear()
        await message.answer("✅ Kandinsky API auth сохранён")

    @router.message(KandinskyAuthState.email)
    async def k_email(message: Message, state: FSMContext) -> None:
        await settings_manager.update(kandinsky_email=message.text.strip())
        await state.set_state(KandinskyAuthState.password)
        await message.answer("Введите пароль")

    @router.message(KandinskyAuthState.password)
    async def k_password(message: Message, state: FSMContext) -> None:
        await settings_manager.update(kandinsky_password=message.text.strip())
        await state.clear()
        await message.answer("✅ Kandinsky WEB auth сохранён")

    @router.message(Command("set_openai"))
    async def set_openai(message: Message, state: FSMContext) -> None:
        if not allowed(message):
            return
        await state.set_state(OpenAIState.base_url)
        await message.answer("Введите OPENAI_BASE_URL")

    @router.message(OpenAIState.base_url)
    async def oa_url(message: Message, state: FSMContext) -> None:
        await settings_manager.update(openai_base_url=message.text.strip())
        await state.set_state(OpenAIState.key)
        await message.answer("Введите OPENAI_API_KEY")

    @router.message(OpenAIState.key)
    async def oa_key(message: Message, state: FSMContext) -> None:
        await settings_manager.update(openai_api_key=message.text.strip())
        await state.set_state(OpenAIState.model)
        await message.answer("Введите OPENAI_MODEL")

    @router.message(OpenAIState.model)
    async def oa_model(message: Message, state: FSMContext) -> None:
        await settings_manager.update(openai_model=message.text.strip())
        await state.clear()
        await message.answer("✅ OpenAI-совместимый API сохранён")

    return router
