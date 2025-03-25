from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.ext.asyncio import AsyncAttrs, async_sessionmaker, create_async_engine, AsyncSession
from sqlalchemy import String, ForeignKey, BigInteger, DateTime, Float, JSON, Integer, CheckConstraint
from datetime import datetime
import logging

from config import DB_URL

IP_MAX_LENGTH = 50
NAME_MAX_LENGTH = 100
SYSTEM_INFO_MAX_LENGTH = 255

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

engine = create_async_engine(url=DB_URL)
async_session = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


class Base(AsyncAttrs, DeclarativeBase):
    """Базовый класс для моделей с асинхронной поддержкой."""
    pass


class User(Base):
    """Пользователь Telegram, владеющий хостами."""
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    tg_id: Mapped[BigInteger] = mapped_column(BigInteger, unique=True, index=True, nullable=False)
    settings: Mapped[list] = mapped_column(JSON, nullable=False)
    hosts: Mapped[list["Host"]] = relationship("Host", back_populates="user", lazy="select")

class Host(Base):
    __tablename__ = "hosts"
    __table_args__ = (
        CheckConstraint("port >= 0 AND port <= 65535", name="check_port_range"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    ip: Mapped[str] = mapped_column(String(IP_MAX_LENGTH), unique=True, index=True, nullable=False)
    port: Mapped[int] = mapped_column(Integer, nullable=False)
    name: Mapped[str] = mapped_column(String(NAME_MAX_LENGTH), nullable=False)
    last_checked: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    user_id: Mapped[BigInteger] = mapped_column(ForeignKey("users.tg_id"))

    metric: Mapped["Metric"] = relationship("Metric", uselist=False, lazy="joined")
    user: Mapped[User] = relationship("User", back_populates="hosts")


class Metric(Base):
    """Метрики хоста, полученные из запросов."""
    __tablename__ = "metrics"

    id: Mapped[int] = mapped_column(primary_key=True)
    host_id: Mapped[int] = mapped_column(ForeignKey("hosts.id"), unique=True)
    last_checked: Mapped[datetime | None] = mapped_column(DateTime, nullable=False)

    system_name: Mapped[str] = mapped_column(String(SYSTEM_INFO_MAX_LENGTH), nullable=False)
    kernel_version: Mapped[str] = mapped_column(String(SYSTEM_INFO_MAX_LENGTH), nullable=False)
    os_version: Mapped[str] = mapped_column(String(SYSTEM_INFO_MAX_LENGTH), nullable=False)
    host_name: Mapped[str] = mapped_column(String(SYSTEM_INFO_MAX_LENGTH), nullable=False)

    total_ram_gb: Mapped[float] = mapped_column(Float, nullable=False)
    total_ram_mb: Mapped[float] = mapped_column(Float, nullable=False)
    used_ram_gb: Mapped[float] = mapped_column(Float, nullable=False)
    used_ram_mb: Mapped[float] = mapped_column(Float, nullable=False)
    ram_percent: Mapped[float] = mapped_column(Float, nullable=False)
    total_swap_gb: Mapped[float] = mapped_column(Float, nullable=False)
    total_swap_mb: Mapped[float] = mapped_column(Float, nullable=False)
    used_swap_gb: Mapped[float] = mapped_column(Float, nullable=False)
    used_swap_mb: Mapped[float] = mapped_column(Float, nullable=False)
    swap_percent: Mapped[float] = mapped_column(Float, nullable=False)

    disks: Mapped[list] = mapped_column(JSON, nullable=False)

    components: Mapped[list] = mapped_column(JSON, nullable=False)


async def async_main():
    """Инициализация базы данных с обработкой ошибок."""
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise
