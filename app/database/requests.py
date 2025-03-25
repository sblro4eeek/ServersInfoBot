from typing import Tuple, Optional
from datetime import datetime
from sqlalchemy import select, insert, update, or_
from sqlalchemy.orm import joinedload
from sqlalchemy.exc import IntegrityError
from sqlalchemy.engine import ScalarResult
import logging

from .models import async_session, User, Host, Metric

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


async def set_user(tg_id: int) -> None:
    """
    Добавляет нового пользователя в базу данных, если он еще не существует.

    Args:
        tg_id (int): Telegram ID пользователя.
    """
    async with async_session() as session:
        async with session.begin():
            user = await session.scalar(select(User).where(User.tg_id == tg_id))
            if not user:
                logger.info(f"Добавление нового пользователя с tg_id={tg_id}")
                session.add(User(
                    tg_id=tg_id,
                    settings=[
                    {
                        "short": False
                    }
                ]))
                await session.commit()
                logger.info(f"Пользователь с tg_id={tg_id} успешно добавлен.")
            else:
                logger.info(f"Пользователь с tg_id={tg_id} уже существует.")


async def get_user(tg_id: int) -> Optional[User]:
    """
    Получает информацию о пользователе по его Telegram ID.

    Args:
        tg_id (int): Telegram ID пользователя.

    Returns:
        Optional[User]: Объект User или None, если пользователь не найден.
    """
    async with async_session() as session:
        user = await session.scalar(select(User).where(User.tg_id == tg_id))
        if user:
            logger.info(f"Пользователь с tg_id={tg_id} найден.")
        else:
            logger.warning(f"Пользователь с tg_id={tg_id} не найден.")
        return user


async def switch_user_short_format(tg_id: int) -> bool:
    """
    Переключает настройку формата вывода (short) для пользователя и возвращает новое значение.

    Args:
        tg_id (int): Telegram ID пользователя.

    Returns:
        bool: Новое значение настройки short после переключения.
    """
    async with async_session() as session:
        async with session.begin():
            user = await get_user(tg_id=tg_id)
            if not user:
                logger.error(f"Пользователь с tg_id={tg_id} не найден для переключения настроек.")
                return False
            current_short = user.settings[0]["short"]

            new_short = not current_short
            stmt_host = update(User).where(User.tg_id == tg_id).values(settings=[{"short": new_short}])
            await session.execute(stmt_host)
            await session.commit()
            logger.info(f"Настройка short для пользователя с tg_id={tg_id} изменена на {new_short}.")
            return new_short


async def add_host(user_id: int, name: str, ip: str, port: int) -> Tuple[bool, Optional[str]]:
    """
    Добавляет новый хост и связанные с ним метрики в базу данных.

    Args:
        user_id (int): Telegram ID пользователя.
        name (str): Имя хоста.
        ip (str): IP-адрес хоста.
        port (int): Порт хоста.

    Returns:
        Tuple[bool, Optional[str]]: Кортеж (успех, сообщение об ошибке или None).
    """
    async with async_session() as session:
        try:
            async with session.begin():
                logger.info(f"Добавление нового хоста для пользователя {user_id} с IP={ip}, порт={port}.")
                stmt = insert(Host).values(user_id=user_id, name=name, ip=ip, port=port)
                result = await session.execute(stmt)
                host_id = result.inserted_primary_key[0]

                stmt_metric = insert(Metric).values(
                    host_id=host_id,
                    last_checked=datetime.now(),
                    system_name="",
                    kernel_version="",
                    os_version="",
                    host_name="",
                    total_ram_gb=0.0,
                    total_ram_mb=0.0,
                    used_ram_gb=0.0,
                    used_ram_mb=0.0,
                    ram_percent=0.0,
                    total_swap_gb=0.0,
                    total_swap_mb=0.0,
                    used_swap_gb=0.0,
                    used_swap_mb=0.0,
                    swap_percent=0.0,
                    disks=[],
                    components=[]
                )
                await session.execute(stmt_metric)
                await session.commit()
                logger.info(f"Хост с IP={ip} успешно добавлен для пользователя {user_id}.")
            return True, None

        except IntegrityError as e:
            await session.rollback()
            logger.error(f"Ошибка при добавлении хоста с IP={ip}: {e}")
            if "unique constraint" in str(e).lower():
                return False, f"❌ Хост с IP {ip} уже существует!"
            return False, "❌ Ошибка при добавлении хоста: нарушение целостности данных."
        except Exception as e:
            await session.rollback()
            logger.error(f"Неизвестная ошибка при добавлении хоста: {str(e)}")
            return False, f"❌ Неизвестная ошибка при добавлении хоста: {str(e)}"


async def get_hosts(user_id: int) -> ScalarResult:
    """
    Получает список всех хостов пользователя.

    Args:
        user_id (int): Telegram ID пользователя.

    Returns:
        ScalarResult: Результат запроса с объектами Host.
    """

    async with async_session() as session:
        hosts = await session.scalars(select(Host).where(Host.user_id == user_id))
        logger.info(f"Получено {hosts.rowcount} хостов для пользователя с tg_id={user_id}.")
        return hosts


async def get_host_info(host_id: Optional[str] = None, host_ip: Optional[str] = None) -> Optional[Host]:
    """
    Получает информацию о хосте по его ID или IP-адресу, включая связанные метрики.

    Args:
        host_id (Optional[str]): ID хоста.
        host_ip (Optional[str]): IP-адрес хоста.

    Returns:
        Optional[Host]: Объект Host с метриками или None, если хост не найден.

    Raises:
        ValueError: Если не указаны ни host_id, ни host_ip.
    """
    if not host_id and not host_ip:
        logger.error("Необходимо указать host_id или host_ip.")
        raise ValueError("Необходимо указать host_id или host_ip")

    async with async_session() as session:
        query = select(Host).options(joinedload(Host.metric, innerjoin=False))

        if host_id and host_ip:
            query = query.where(or_(Host.id == int(host_id), Host.ip == host_ip))
        elif host_id:
            query = query.where(Host.id == int(host_id))
        elif host_ip:
            query = query.where(Host.ip == host_ip)

        host = await session.scalar(query)
        if host:
            logger.info(f"Хост с ID={host_id} или IP={host_ip} найден.")
        else:
            logger.warning(f"Хост с ID={host_id} или IP={host_ip} не найден.")
        return host


async def update_host_metrics(host_ip: str, metrics_data: dict) -> None:
    """
    Обновляет метрики хоста в базе данных.

    Args:
        host_ip (str): IP-адрес хоста.
        metrics_data (dict): Словарь с данными метрик.
    """
    async with async_session() as session:
        async with session.begin():
            logger.info(f"Обновление метрик для хоста с IP={host_ip}.")
            stmt_host = update(Host).where(Host.ip == host_ip).values(last_checked=datetime.now())
            await session.execute(stmt_host)

            host = await session.scalar(select(Host).where(Host.ip == host_ip))
            if not host:
                logger.error(f"Хост с IP={host_ip} не найден для обновления метрик.")
                raise ValueError(f"Хост с IP {host_ip} не найден")

            stmt_metric = update(Metric).where(Metric.host_id == host.id).values(
                last_checked=datetime.now(),
                system_name=metrics_data["system"]["name"],
                kernel_version=metrics_data["system"]["kernel_version"],
                os_version=metrics_data["system"]["os_version"],
                host_name=metrics_data["system"]["host_name"],
                total_ram_gb=metrics_data["memory"]["total_ram_gb"],
                total_ram_mb=metrics_data["memory"]["total_ram_mb"],
                used_ram_gb=metrics_data["memory"]["used_ram_gb"],
                used_ram_mb=metrics_data["memory"]["used_ram_mb"],
                ram_percent=metrics_data["memory"]["ram_percent"],
                total_swap_gb=metrics_data["memory"]["total_swap_gb"],
                total_swap_mb=metrics_data["memory"]["total_swap_mb"],
                used_swap_gb=metrics_data["memory"]["used_swap_gb"],
                used_swap_mb=metrics_data["memory"]["used_swap_mb"],
                swap_percent=metrics_data["memory"]["swap_percent"],
                disks=metrics_data["disks"],
                components=metrics_data["components"]
            )
            await session.execute(stmt_metric)
            await session.commit()
            logger.info(f"Метрики для хоста с IP={host_ip} успешно обновлены.")
