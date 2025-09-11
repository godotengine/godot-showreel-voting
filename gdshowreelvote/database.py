from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import MetaData, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


KEYCLOAK_ID_SIZE = 128  # This looks more like a config item than a constant

class Base(DeclarativeBase):
    metadata = MetaData(naming_convention={
        'ix': 'ix_%(column_0_label)s',
        'uq': 'uq_%(table_name)s_%(column_0_name)s',
        'ck': 'ck_%(table_name)s_`%(constraint_name)s`',
        'fk': 'fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s',
        'pk': 'pk_%(table_name)s'
    })

DB = SQLAlchemy(model_class=Base)
migrate = Migrate()


class User(DB.Model):
    __tablename__ = 'users'
    id: Mapped[str] = mapped_column(String(KEYCLOAK_ID_SIZE), primary_key=True, autoincrement=False)
    name: Mapped[str] = mapped_column(String(128))
    email: Mapped[str] = mapped_column(String(128))
    moderator: Mapped[bool] = mapped_column(server_default='0')
