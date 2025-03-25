from typing import Dict, Any
import logging

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)


def _round2(value: float) -> float:
    """Округляет значение до двух знаков после запятой."""
    return round(value, 2)


def _format_memory_section(title: str, data: Dict[str, float]) -> str:
    """Форматирует секцию памяти (RAM или Swap) в текстовый вид."""
    logger.debug(f"Форматирование секции памяти: {title} с данными {data}")
    return (
        f"<b>{title}:</b>\n"
        f"<b>- Общий объём:</b> {_round2(data['total_gb'])} GB ({_round2(data['total_mb'])} MB)\n"
        f"<b>- Использовано:</b> {_round2(data['used_gb'])} GB ({_round2(data['used_mb'])} MB)\n"
        f"<b>- Загрузка:</b> {_round2(data['percent'])} %\n\n"
    )


def _format_disk(disk: Dict[str, Any]) -> str:
    """Форматирует информацию о диске в текстовый вид."""
    logger.debug(f"Форматирование информации о диске: {disk}")
    return (
        f"<b>  - Диск:</b> {disk.get('name', 'Неизвестно')}\n"
        f"<b>    Точка монтирования:</b> {disk.get('mount_point', 'Не указано')}\n"
        f"<b>    Доступно:</b> {_round2(disk.get('available_space_gb', 0))} GB "
        f"({_round2(disk.get('available_space_mb', 0))} MB)\n"
        f"<b>    Всего:</b> {_round2(disk.get('total_space_gb', 0))} GB "
        f"({_round2(disk.get('total_space_mb', 0))} MB)\n"
    )


def _format_component(component: Dict[str, Any]) -> str:
    """Форматирует информацию о компоненте в текстовый вид."""
    logger.debug(f"Форматирование информации о компоненте: {component}")
    return f"<b>  - {component.get('label', 'Неизвестно')}:</b> {component.get('temperature', 'N/A')} °C\n"


def format_host_info(info: Any, short: bool = False) -> str:
    """
    Форматирует информацию о хосте в текстовый вид для отображения в Telegram.

    Args:
        info: Объект хоста с атрибутом metric, содержащим данные о системе, памяти, дисках и компонентах.
        short (bool, optional): Если True, возвращает укороченную версию информации. По умолчанию False.

    Returns:
        str: Отформатированная строка с информацией о хосте (полная или укороченная).
    """
    logger.debug(f"Начало форматирования информации о хосте с IP {info.ip}:{info.port}, короткая версия: {short}")
    metric = info.metric
    text_parts = []

    if short:
        # Укороченная версия: IP, порт, имя хоста, загрузка RAM, CPU, Swap и время проверки
        ram_percent = _round2(metric.ram_percent)
        swap_percent = _round2(metric.swap_percent)
        last_checked = metric.last_checked.strftime('%Y-%m-%d %H:%M:%S') if metric.last_checked else "Не проверялось"

        text_parts.append(
            f"<b>🖥 {info.ip}:{info.port}</b>\n"
            f"<b>- Имя:</b> {info.name or 'Не указано'}\n"
            f"<b>- RAM:</b> {ram_percent} %\n"
            f"<b>- Swap:</b> {swap_percent} %\n"
            f"<b>- Проверено:</b> {last_checked}\n"
        )
        logger.debug(f"Отформатированная укороченная версия информации о хосте: {''.join(text_parts)}")
    else:
        # Полная версия
        text_parts.append(
            f"<b>🖥 Информация о хосте {info.ip}:{info.port}:</b>\n"
            f"<b>- Имя:</b> {info.name or 'Не указано'}\n"
            f"<b>- Системное имя:</b> {metric.system_name or 'Не указано'}\n"
            f"<b>- Версия ядра:</b> {metric.kernel_version or 'Не указано'}\n"
            f"<b>- Версия ОС:</b> {metric.os_version or 'Не указано'}\n"
            f"<b>- Имя хоста:</b> {metric.host_name or 'Не указано'}\n\n"
        )

        ram_info = {
            "total_gb": metric.total_ram_gb,
            "total_mb": metric.total_ram_mb,
            "used_gb": metric.used_ram_gb,
            "used_mb": metric.used_ram_mb,
            "percent": metric.ram_percent,
        }
        text_parts.append(_format_memory_section("💾 Память", ram_info))

        swap_info = {
            "total_gb": metric.total_swap_gb,
            "total_mb": metric.total_swap_mb,
            "used_gb": metric.used_swap_gb,
            "used_mb": metric.used_swap_mb,
            "percent": metric.swap_percent,
        }
        text_parts.append(_format_memory_section("🔄 Своп", swap_info))

        text_parts.append("<b>💻 Диски:</b>\n")
        if metric.disks:
            for disk in metric.disks:
                text_parts.append(_format_disk(disk))
        else:
            text_parts.append("Нет доступных данных о дисках.\n")

        text_parts.append("\n<b>🧩 Компоненты:</b>\n")
        if metric.components:
            for component in metric.components:
                text_parts.append(_format_component(component))
        else:
            text_parts.append("Нет доступных компонентов.\n")

        last_checked = metric.last_checked.strftime('%Y-%m-%d %H:%M:%S') if metric.last_checked else "Не проверялось"
        text_parts.append(f"\n<b>📅 Последняя проверка:</b> {last_checked}\n")

    logger.debug(f"Отформатированная полная информация о хосте: {''.join(text_parts)}")
    return "".join(text_parts)