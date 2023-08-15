import asyncio
import datetime
import sys
from sqlite3 import Timestamp
from time import time

from sqlalchemy import create_engine, ForeignKey, Date, String, DateTime, \
    Float, UniqueConstraint, Integer, MetaData, BigInteger
from sqlalchemy.orm import DeclarativeBase, relationship
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import sessionmaker

from config_data.conf import LOGGING_CONFIG, conf
import logging.config

logging.config.dictConfig(LOGGING_CONFIG)
logger = logging.getLogger('bot_logger')
err_log = logging.getLogger('errors_logger')
metadata = MetaData()
db_url = f"postgresql+psycopg2://{conf.db.db_user}:{conf.db.db_password}@{conf.db.db_host}:{conf.db.db_port}/{conf.db.database}"
engine = create_engine(db_url, echo=False)


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
    demo_expire: Mapped[time] = mapped_column(DateTime(), nullable=True)
    demo_used: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    delta_num: Mapped[int] = mapped_column(Integer, nullable=True)
    delta_end: Mapped[time] = mapped_column(DateTime(), nullable=True)
    subscribes: Mapped[list['Subscribe']] = relationship(back_populates='user')

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
            err_log.error(f'Ошибка изменения {key} на {value}')
            raise err

    @staticmethod
    def get_new_delta():
        _session = Session()
        try:
            with _session:
                used_delta = _session.query(User.delta_num).filter(
                    User.delta_num.is_not(None)).all()
                logger.debug(f'Ипсользованные числа: {used_delta}')
                for i in range(1000):
                    if i not in used_delta:
                        return i
        except Exception as err:
            err_log.error(f'Ошибка чтения used_delta')
            raise err


class Channel(Base):
    __tablename__ = 'channels'
    id: Mapped[int] = mapped_column(primary_key=True,
                                    autoincrement=True,
                                    comment='Первичный ключ')
    channel_id: Mapped[int] = mapped_column(BigInteger())
    title: Mapped[str] = mapped_column(String(50), nullable=True)
    description: Mapped[str] = mapped_column(String(250), nullable=True)
    is_active: Mapped[int] = mapped_column(Integer(), default=1)
    subscribes: Mapped[list['Subscribe']] = relationship(back_populates='channel')

    def __repr__(self):
        return f'Канал {self.id}. {self.title}. Активен: {self.is_active} '


class Subscribe(Base):
    __tablename__ = 'subscribes'
    __table_args__ = (
        UniqueConstraint("channel_id", "user_id"),
    )
    id: Mapped[int] = mapped_column(primary_key=True,
                                    autoincrement=True)
    channel_id: Mapped[int] = mapped_column(ForeignKey('channels.id'))
    channel: Mapped['Channel'] = relationship(back_populates='subscribes')
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'))
    user: Mapped['User'] = relationship(back_populates='subscribes')
    expire: Mapped[datetime.datetime] = mapped_column(DateTime())

    def __repr__(self):
        return f'Подписка {self.id}. Канал {self.channel_id} ({self.user_id}) до {self.expire}'


Base.metadata.create_all(engine)


with Session() as session:
    try:
        channels = session.query(Channel).all()
        print('------------------', channels)
        if not channels:
            channel1: Channel = Channel(
                channel_id=-1001697211543,
                title='Тестовый канал',
                description='Описание тестового канла',
                is_active=1,
            )
    except Exception as err:
        print(err)


