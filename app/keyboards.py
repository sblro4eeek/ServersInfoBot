from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from math import ceil

from app.database.requests import get_hosts


def inline_menu_button() -> InlineKeyboardMarkup:
    """Создаёт инлайн-кнопку 'Меню'."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="На главную", callback_data="to_main")]
        ]
    )


def inline_settings_button() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Переключить формат информации", callback_data="switch_short")],
            [InlineKeyboardButton(text="На главную", callback_data="to_main")]
        ]
    )


def inline_main_button() -> InlineKeyboardMarkup:
    """Создаёт инлайн-кнопки для меню."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Добавить хост", callback_data="add_host"),
                InlineKeyboardButton(text="Список хостов", callback_data="list_hosts"),
            ],
            [InlineKeyboardButton(text="Команды", callback_data="commands")],
            [InlineKeyboardButton(text="Разработчик", url="https://t.me/sblro4eeek")],
        ]
    )


def inline_cancel_button() -> InlineKeyboardMarkup:
    """Создаёт инлайн-кнопку 'Отмена'."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Отмена", callback_data="cancel_add_host")]
        ]
    )


def create_send_request_button(ip: str, port: int) -> InlineKeyboardMarkup:
    """Создаёт инлайн-кнопку для отправки запроса."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Отправить запрос", callback_data=f"send_request_{ip}_{port}")]
        ]
    )


def create_send_request_button_and_inline_menu_button(ip: str, port: int) -> InlineKeyboardMarkup:
    """Создаёт инлайн-клавиатуру для отправки запроса и возврата."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Отправить запрос", callback_data=f"send_request_{ip}_{port}")],
            [InlineKeyboardButton(text="На главную", callback_data="to_main")]
        ]
    )


def inline_cancel_and_back_button(callback_cancel: str, callback_back: str):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Отмена", callback_data=callback_cancel),
         InlineKeyboardButton(text="⬅️ Назад", callback_data=callback_back)]
    ])


async def hosts(user_id: str, page: int = 1) -> InlineKeyboardMarkup:
    all_hosts = list(await get_hosts(int(user_id)))
    keyboard = InlineKeyboardBuilder()

    if not all_hosts:
        keyboard.add(InlineKeyboardButton(text="Нет хостов", callback_data="no_hosts"))
    else:
        HOSTS_PER_PAGE = 8
        total_pages = ceil(len(all_hosts) / HOSTS_PER_PAGE)
        page = max(1, min(page, total_pages))

        start_idx = (page - 1) * HOSTS_PER_PAGE
        end_idx = start_idx + HOSTS_PER_PAGE
        current_hosts = all_hosts[start_idx:end_idx]

        for host in current_hosts:
            keyboard.add(InlineKeyboardButton(text=host.name, callback_data=f"host_{host.id}"))
        keyboard.adjust(2)

        nav_buttons = []
        if page > 1:
            nav_buttons.append(InlineKeyboardButton(text="⬅️ Назад", callback_data=f"hosts_page_{page - 1}"))
        if page < total_pages:
            nav_buttons.append(InlineKeyboardButton(text="Вперёд ➡️", callback_data=f"hosts_page_{page + 1}"))
        if nav_buttons:
            keyboard.row(*nav_buttons)

    keyboard.row(InlineKeyboardButton(text="На главную", callback_data="to_main"))
    return keyboard.as_markup()
