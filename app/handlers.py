import logging
from aiogram import types, Router, F
from aiogram.filters import CommandStart
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext

from app.database.requests import set_user, add_host, get_host_info, update_host_metrics, get_user, \
    switch_user_short_format
from app.utils.ip_valid import is_valid_ip
from app.utils.send_request import send_request
from app.utils.format_host_info import format_host_info
from app.utils.message_utils import delete_and_update_message
from app.keyboards import inline_main_button, inline_cancel_button, inline_cancel_and_back_button, hosts, \
    create_send_request_button_and_inline_menu_button, inline_menu_button, inline_settings_button
from app.messages import WELCOME_MESSAGE, HOST_NAME_PROMPT, IP_PROMPT, PORT_PROMPT, INVALID_IP, INVALID_PORT, \
    HOST_ADDED, HOST_EXISTS, SETTINGS_MESSAGE, SWITCH_MESSAGE, ERROR_ADD_HOST, CANCEL_ADD_HOST, BACK_TO_MENU, \
    HOSTS_MESSAGE, NO_REQUEST_INFO, WAITING_FOR_RESPONSE, ERROR_FETCHING_DATA

router = Router()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Host(StatesGroup):
    bot_message_id = State()
    name = State()
    ip = State()
    port = State()


@router.message(CommandStart())
async def cmd_start(message: types.Message):
    logger.info(f"User {message.from_user.id} started the bot.")
    await set_user(message.from_user.id)
    await message.answer(
        text=WELCOME_MESSAGE,
        reply_markup=inline_main_button()
    )


@router.callback_query(F.data == "to_main")
async def menu(callback: types.CallbackQuery):
    await callback.answer()
    await callback.message.edit_text(
        text=WELCOME_MESSAGE,
        reply_markup=inline_main_button()
    )


@router.callback_query(F.data == "settings")
async def settings(callback: types.CallbackQuery):
    await callback.answer()
    await callback.message.edit_text(
        text=SETTINGS_MESSAGE,
        reply_markup=inline_settings_button()
    )


@router.callback_query(F.data == "switch_short")
async def settings(callback: types.CallbackQuery):
    await callback.answer()
    new_short = await switch_user_short_format(callback.from_user.id)

    format_text = "укороченный" if new_short else "полный"
    message_text = f"{SWITCH_MESSAGE} {format_text}"

    await callback.message.edit_text(
        text=message_text,
        reply_markup=inline_settings_button()
    )


# Добавление хоста
@router.callback_query(F.data == "add_host")
async def add_host_name(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(Host.name)
    msg = await callback.message.edit_text(
        text=HOST_NAME_PROMPT, reply_markup=inline_cancel_button()
    )
    await state.update_data(bot_message_id=msg.message_id)


@router.message(Host.name)
async def add_host_ip(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    await state.set_state(Host.ip)
    data = await state.get_data()
    bot_message_id = data["bot_message_id"]
    await message.delete()
    msg = await message.answer(
        text=IP_PROMPT,
        reply_markup=inline_cancel_button()
    )
    await delete_and_update_message(message.bot, message.chat.id, bot_message_id, state, msg)


@router.message(Host.ip)
async def add_host_port(message: types.Message, state: FSMContext):
    ip = message.text
    data = await state.get_data()
    bot_message_id = data["bot_message_id"]
    await message.delete()
    if is_valid_ip(ip):
        await state.update_data(ip=ip)
        await state.set_state(Host.port)
        msg = await message.answer(
            text=PORT_PROMPT,
            reply_markup=inline_cancel_and_back_button("cancel_add_host", "back_to_name"))
    else:
        msg = await message.reply(
            text=INVALID_IP,
            reply_markup=inline_cancel_and_back_button("cancel_add_host", "back_to_name"))
    await delete_and_update_message(message.bot, message.chat.id, bot_message_id, state, msg)


@router.callback_query(F.data == "back_to_name")
async def back_to_name(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(Host.name)
    await callback.message.edit_text(
        text=HOST_NAME_PROMPT,
        reply_markup=inline_cancel_button()
    )
    await callback.answer()


@router.message(Host.port)
async def add_host_finally(message: types.Message, state: FSMContext):
    port = message.text
    data = await state.get_data()
    bot_message_id = data["bot_message_id"]
    await message.delete()
    try:
        port = int(port)
        if not 0 <= port <= 65535:
            raise ValueError("Port out of range")
        existing_host = await get_host_info(host_ip=data["ip"])
        if existing_host and existing_host.port == port:
            await message.answer(
                text=HOST_EXISTS,
                reply_markup=inline_main_button()
            )
            await state.clear()
            return
        await state.update_data(port=port)
        success, error_message = await add_host(
            user_id=message.from_user.id,
            name=data["name"],
            ip=data["ip"],
            port=port
        )
        if success:
            await message.answer(
                text=HOST_ADDED.format(name=data["name"], ip=data["ip"], port=port),
                reply_markup=inline_main_button()
            )
            await state.clear()
        else:
            raise RuntimeError(error_message)
    except ValueError as e:
        logger.warning(f"Invalid port input: {port}, error: {e}")
        msg = await message.answer(
            text=INVALID_PORT,
            reply_markup=inline_cancel_and_back_button("cancel_add_host", "back_to_ip"))
        await delete_and_update_message(message.bot, message.chat.id, bot_message_id, state, msg)
    except Exception as e:
        logger.error(f"Error adding host: {e}")
        await message.answer(
            text=ERROR_ADD_HOST,
            reply_markup=inline_main_button())
        await state.clear()


@router.callback_query(F.data == "back_to_ip")
async def back_to_ip(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(Host.ip)
    await callback.message.edit_text(
        text=IP_PROMPT,
        reply_markup=inline_cancel_and_back_button("cancel_add_host", "back_to_name"))
    await callback.answer()


@router.callback_query(F.data == "cancel_add_host")
async def cancel_add_host(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text(
        text=CANCEL_ADD_HOST,
        reply_markup=None
    )
    await callback.message.answer(
        text=BACK_TO_MENU,
        reply_markup=inline_main_button()
    )
    await callback.answer()


# Работа с хостами
@router.callback_query(F.data == "list_hosts")
async def list_hosts(callback: types.CallbackQuery):
    await callback.message.edit_text(
        text=HOSTS_MESSAGE,
        reply_markup=await hosts(user_id=str(callback.from_user.id), page=1))
    await callback.answer()


@router.callback_query(F.data.startswith("hosts_page_"))
async def handle_hosts_pagination(callback: types.CallbackQuery):
    page = int(callback.data.split("_")[2])
    await callback.message.edit_text(
        text=HOSTS_MESSAGE,
        reply_markup=await hosts(user_id=str(callback.from_user.id), page=page))
    await callback.answer()


@router.callback_query(F.data.startswith("host_"))
async def info_host(callback: types.CallbackQuery):
    await callback.answer()
    host_id = callback.data.split("_")[1]
    info = await get_host_info(host_id=host_id)
    if info.last_checked is None:
        await callback.message.edit_text(
            text=NO_REQUEST_INFO,
            reply_markup=create_send_request_button_and_inline_menu_button(ip=info.ip, port=info.port)
        )
        return
    _settings = await get_user(callback.from_user.id)
    short = _settings.settings[0]["short"]
    text = format_host_info(info=info, short=short)
    await callback.message.edit_text(
        text=text,
        reply_markup=create_send_request_button_and_inline_menu_button(ip=info.ip,port=info.port))


@router.callback_query(F.data.startswith("send_request_"))
async def send_request_handler(callback: types.CallbackQuery):
    await callback.answer()
    ip, port = callback.data.split("_")[2], callback.data.split("_")[3]
    msg = WAITING_FOR_RESPONSE + f"{ip}:{port} ..."
    await callback.message.edit_text(
        text=msg
    )
    metrics_data = await send_request(ip, port)
    msg = ERROR_FETCHING_DATA + f"{metrics_data}"
    if isinstance(metrics_data, str):
        text = msg
    else:
        await update_host_metrics(host_ip=ip, metrics_data=metrics_data)
        info = await get_host_info(host_ip=ip)
        _settings = await get_user(callback.from_user.id)
        short = _settings.settings[0]["short"]
        text = format_host_info(info=info, short=short)
    await callback.message.edit_text(text=text, reply_markup=inline_menu_button())
