import logging
from aiogram import types
from aiogram.fsm.context import FSMContext

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)


async def delete_and_update_message(bot, chat_id, message_id, state: FSMContext, new_message: types.Message):
    """Удаляет старое сообщение и обновляет информацию о новом сообщении."""

    logger.debug(f"Удаление сообщения с ID {message_id} в чате {chat_id}")
    await bot.delete_message(chat_id=chat_id, message_id=message_id)
    await state.update_data(bot_message_id=new_message.message_id)

    logger.info(f"Сообщение удалено. Обновлено состояние с новым сообщением ID {new_message.message_id} в чате {chat_id}")