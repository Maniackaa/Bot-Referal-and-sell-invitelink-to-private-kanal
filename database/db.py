import asyncio
import datetime
import sys
from sqlite3 import Timestamp
from time import time

from sqlalchemy import create_engine, ForeignKey, Date, String, DateTime, \
    Float, UniqueConstraint, Integer, MetaData
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
    member_expire: Mapped[time] = mapped_column(DateTime(), nullable=True)
    demo_used: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    delta_num: Mapped[int] = mapped_column(Integer, nullable=True)
    delta_end: Mapped[time] = mapped_column(DateTime(), nullable=True)

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
            logger.error(f'Ошибка чтения used_delta')
            raise err






Base.metadata.create_all(engine)

# with Session() as session:
#     try:
#         user: User = session.query(User).filter(
#             User.tg_id == str(585896156)).first()
#         # Если дельта есть и не просрочилась, выдаем ее
#         now = datetime.datetime.now(tz=config.tg_bot.TIMEZONE).replace(
#             tzinfo=None)
#         if user.delta_end and now < user.delta_end:
#             print(user.delta_end)
#         # Присваиваем и возвращаем новую дельту
#         user_with_delta = session.query(User).filter(
#             User.delta_num.is_not(None)).all()
#         used_num = [x.delta_num for x in user_with_delta]
#         print(used_num)
#     except Exception as err:
#         raise err
# Заполнение пустой базы
# index, text, parent_id, is_with_children
