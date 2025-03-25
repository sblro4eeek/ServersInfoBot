WELCOME_MESSAGE = (
    "👋 Привет! Я бот для <i>мониторинга хостов</i>!\n"
    "👾 Мониторю состояние твоих хостов: <b>память, температуру и не только</b>.\n"
    "🖥️ Могу <b>следить</b> за несколькими машинами.\n"
    "🚀 <i>Готов держать всё под контролем</i>!"
)

BACK_TO_MENU = "🏠 Вы вернулись в главное меню."

SETTINGS_MESSAGE = "⚙️ Настройки"
SWITCH_MESSAGE = "🔄 Формат переключен на "
NO_REQUEST_INFO = "❓ Вы не делали запрос на информацию!"
WAITING_FOR_RESPONSE = "⏳ Получаем ответ от "
ERROR_FETCHING_DATA = "❌ Не удалось получить данные: "
HOSTS_MESSAGE = "💻 Ваши хосты:"
HOST_NAME_PROMPT = "🔧 Введите имя для вашего хоста"
IP_PROMPT = "✅ Отлично! Теперь отправь IP твоего хоста"
PORT_PROMPT = "✅ IP адрес принят! Теперь отправь порт хоста (от 0 до 65535):"
INVALID_IP = "❌ IP не валидный! Попробуй еще раз."
INVALID_PORT = "❌ Порт должен быть числом от 0 до 65535! Попробуй еще раз."
ERROR_ADD_HOST = "❌ Произошла ошибка при добавлении хоста. Попробуй позже."
CANCEL_ADD_HOST = "❌ Добавление хоста отменено."
HOST_ADDED = (
    "✅ Отлично! Хост добавлен!\n"
    "🖥️ Название: <code>{name}</code>\n"
    "🌐 IP: <code>{ip}</code>\n"
    "🔌 Порт: <code>{port}</code>"
)
HOST_EXISTS = "❌ Хост с таким IP и портом уже существует!"
