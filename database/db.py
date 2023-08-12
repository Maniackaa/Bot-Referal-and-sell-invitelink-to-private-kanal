import asyncio
import datetime
import sys
from sqlite3 import Timestamp
from time import time

from sqlalchemy import create_engine, ForeignKey, Date, String, DateTime, \
    Float, UniqueConstraint, Integer
from sqlalchemy.orm import DeclarativeBase, relationship
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import sessionmaker

from config_data.config import LOGGING_CONFIG, config
import logging.config

logging.config.dictConfig(LOGGING_CONFIG)
logger = logging.getLogger('bot_logger')
err_log = logging.getLogger('errors_logger')

engine = create_engine(f"postgresql+psycopg2://{config.db.db_user}:{config.db.db_password}@{config.db.db_host}:{config.db.db_port}/{config.db.database}", echo=False)


Session = sessionmaker(bind=engine)


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = 'users'
    id: Mapped[int] = mapped_column(primary_key=True,
                                    autoincrement=True,
                                    comment='Первичный ключ')
    tg_id: Mapped[str] = mapped_column(String(30))
    username: Mapped[str] = mapped_column(String(50), nullable=True)
    register_date: Mapped[time] = mapped_column(DateTime(), nullable=True)
    referral: Mapped[str] = mapped_column(String(20), nullable=True)
    referral_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    referral_buy_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    member_expire: Mapped[time] = mapped_column(DateTime(), nullable=True)

    def __repr__(self):
        return f'{self.id}. {self.tg_id} {self.username or "-"}'

    def set(self, key, value):
        _session = Session()
        try:
            with _session:
                order = _session.query(User).filter(User.id == self.id).one_or_none()
                setattr(order, key, value)
                _session.commit()
                logger.debug(f'Изменено значение {key} на {value}')
        except Exception as err:
            logger.error(f'Ошибка изменения {key} на {value}')
            raise err


Base.metadata.create_all(engine)


# Заполнение пустой базы
# index, text, parent_id, is_with_children
