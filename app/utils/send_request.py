import httpx
from typing import Union, Dict, Any
import logging

logger = logging.getLogger(__name__)

async def send_request(ip: str, port: str, timeout: int = 10, endpoint: str = "/get_info") -> Union[Dict[str, Any], str]:
    """
    Выполняет асинхронный HTTP-запрос к хосту для получения информации.

    Args:
        ip (str): IP-адрес хоста.
        port (str): Порт хоста.
        timeout (int, optional): Тайм-аут запроса в секундах. По умолчанию 10.
        endpoint (str, optional): Конечная точка API. По умолчанию "/get_info".

    Returns:
        Union[Dict[str, Any], str]: Словарь с данными от сервера или строка с описанием ошибки.

    Examples:
            await send_request("192.168.1.1", "8080")
        {'system': {...}, 'memory': {...}, ...}  # Успешный ответ
            await send_request("invalid_ip", "8080")
        "Не удалось выполнить запрос к invalid_ip:8080: ..."
    """
    url = f"http://{ip}:{port}{endpoint}"
    logger.debug(f"Отправка запроса к {url}")

    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(timeout)) as client:
            response = await client.get(url)
            response.raise_for_status()

            data = response.json()
            if not data:
                logger.warning(f"Пустой ответ от {ip}:{port}")
                return f"Ответ от {ip}:{port} пустой"
            logger.debug(f"Успешный ответ от {ip}:{port}: {data}")
            return data

    except httpx.TimeoutException:
        error_msg = f"Превышено время ожидания ({timeout} сек) для {ip}:{port}"
        logger.warning(error_msg)
        return error_msg
    except httpx.HTTPStatusError as e:
        error_msg = f"HTTP ошибка {e.response.status_code} при запросе к {ip}:{port}"
        logger.error(error_msg)
        return error_msg
    except httpx.RequestError as e:
        error_msg = f"Не удалось выполнить запрос к {ip}:{port}: {str(e)}"
        logger.error(error_msg)
        return error_msg
    except ValueError as e:
        error_msg = f"Ошибка разбора JSON от {ip}:{port}: {str(e)}"
        logger.error(error_msg)
        return error_msg
    except Exception as e:
        error_msg = f"Неизвестная ошибка при запросе к {ip}:{port}: {str(e)}"
        logger.error(error_msg)
        return error_msg
