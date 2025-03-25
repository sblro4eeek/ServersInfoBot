import ipaddress
import logging

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)

def is_valid_ip(ip: str) -> bool:
    """Проверяет, является ли строка допустимым IP-адресом."""
    logger.debug(f"Проверка IP-адреса: {ip}")
    try:
        ipaddress.ip_address(ip)
        logger.info(f"IP-адрес {ip} является допустимым.")
        return True
    except ValueError:
        logger.error(f"IP-адрес {ip} является недопустимым.")
        return False
