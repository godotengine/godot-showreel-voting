from datetime import datetime
import enum
from typing import List, Optional
from urllib.parse import parse_qs, urlparse
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Boolean, Column, DateTime, Enum, ForeignKey, Integer, MetaData, String, Table
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


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


class ShowreelStatus(enum.Enum):
    OPENED_TO_SUBMISSIONS = 'OPEN'
    VOTE = 'VOTE'
    CLOSED = 'CLOSED'


class User(DB.Model):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(KEYCLOAK_ID_SIZE), primary_key=True, autoincrement=False)
    email: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    username: Mapped[str] = mapped_column(String(150), unique=True, nullable=True)

    is_staff: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False)
    is_fund_member: Mapped[bool] = mapped_column(Boolean, default=False)
    date_joined: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    videos: Mapped[List['Video']] = relationship(back_populates="author", cascade="all, delete-orphan")
    votes: Mapped[List['Vote']] = relationship(back_populates="user", cascade="all, delete-orphan")

    def can_vote(self):
        return self.is_superuser or self.is_staff or self.is_fund_member


class Showreel(DB.Model):
    __tablename__ = "showreels"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    status: Mapped[ShowreelStatus] = mapped_column(Enum(ShowreelStatus), default=ShowreelStatus.CLOSED, nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)

    videos: Mapped[List['Video']] = relationship(back_populates="showreel", cascade="all, delete-orphan")
    

class Video(DB.Model):
    __tablename__ = "videos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    showreel_id: Mapped[int] = mapped_column(Integer, ForeignKey("showreels.id"), nullable=True)
    author_id: Mapped[str] = mapped_column(String(KEYCLOAK_ID_SIZE), ForeignKey("users.id"), nullable=False)

    game: Mapped[str] = mapped_column(String(200), nullable=False, default="")
    author_name: Mapped[str] = mapped_column(String(200), nullable=False, default="")
    video_link: Mapped[str] = mapped_column(String(200), unique=True, nullable=False)
    video_download_link: Mapped[str] = mapped_column(String(200), unique=True, nullable=False)
    contact_email: Mapped[str] = mapped_column(String(200), default="", nullable=True)
    follow_me_link: Mapped[str] = mapped_column(String(200), default="", nullable=True)
    store_link: Mapped[str] = mapped_column(String(200), default="", nullable=True)

    showreel = relationship("Showreel", back_populates="videos")
    author = relationship("User", back_populates="videos")
    votes = relationship("Vote", back_populates="video", cascade="all, delete-orphan")

    def parse_youtube_video_id(self) -> Optional[str]:
        """
            Source: https://stackoverflow.com/questions/4356538/how-can-i-extract-video-id-from-youtubes-link-in-python/7936523#7936523
            Examples:
            - http://youtu.be/SA2iWivDJiE
            - http://www.youtube.com/watch?v=_oPAwA_Udwc&feature=feedu
            - http://www.youtube.com/embed/SA2iWivDJiE
            - http://www.youtube.com/v/SA2iWivDJiE?version=3&amp;hl=en_US
        """
        query = urlparse(self.video_link)
        if query.hostname == 'youtu.be':
            return query.path[1:]
        if query.hostname in ('www.youtube.com', 'youtube.com', 'm.youtube.com'):
            if query.path == '/watch':
                p = parse_qs(query.query)
                return p['v'][0]
            if query.path[:7] == '/embed/':
                return query.path.split('/')[2]
            if query.path[:3] == '/v/':
                return query.path.split('/')[2]
        # fail?
        return None


class Vote(DB.Model):
    __tablename__ = "votes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(String(KEYCLOAK_ID_SIZE), ForeignKey("users.id"), nullable=False)
    video_id: Mapped[int] = mapped_column(Integer, ForeignKey("videos.id"), nullable=False)

    rating: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="votes")
    video = relationship("Video", back_populates="votes")
