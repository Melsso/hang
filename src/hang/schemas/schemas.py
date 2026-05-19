from sqlalchemy import String, Boolean, Date, DateTime, Enum, ForeignKey
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column, DeclarativeBase, relationship
from datetime import datetime, timezone, date
from hang.models.user import Gender, InterestedIn
from hang.models.swipe import SwipeType


class Base(DeclarativeBase):
    pass


class UserDB(Base):
    __tablename__ = "users"

    user_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    first_name: Mapped[str] = mapped_column(String(50))
    last_name: Mapped[str] = mapped_column(String(50))
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password: Mapped[str] = mapped_column(String(255))

    country: Mapped[str] = mapped_column(String(2), default="DE")
    birthdate: Mapped[date] = mapped_column(Date)

    bio: Mapped[str] = mapped_column(String(500))

    gender: Mapped[Gender] = mapped_column(Enum(Gender))
    interested_in: Mapped[InterestedIn] = mapped_column(Enum(InterestedIn))
    interests: Mapped[list[str]] = mapped_column(
        ARRAY(String), nullable=False, default=list
    )
    images = relationship(
        "UserImageDB",
        backref="user",
        cascade="all, delete-orphan",
        order_by="UserImageDB.position",
    )

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )


class UserImageDB(Base):
    __tablename__ = "user_images"

    image_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.user_id"), index=True)

    image_key: Mapped[str] = mapped_column(String(255), nullable=False)
    position: Mapped[int] = mapped_column(default=0)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )


class MessageDB(Base):
    __tablename__ = "messages"

    message_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    conversation_id: Mapped[int] = mapped_column(
        ForeignKey("conversations.conversation_id"), index=True
    )

    sender_id: Mapped[int] = mapped_column(ForeignKey("users.user_id"), index=True)

    content: Mapped[str] = mapped_column(String(1000))

    is_read: Mapped[bool] = mapped_column(default=False)

    reply_to_id: Mapped[int | None] = mapped_column(nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )


class ConversationDB(Base):
    __tablename__ = "conversations"

    conversation_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    user1_id: Mapped[int] = mapped_column(ForeignKey("users.user_id"), index=True)

    user2_id: Mapped[int] = mapped_column(ForeignKey("users.user_id"), index=True)

    last_message_id: Mapped[int | None] = mapped_column(nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )


class SwipeDB(Base):
    __tablename__ = "swipes"

    swipe_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    from_user_id: Mapped[int] = mapped_column(ForeignKey("users.user_id"), index=True)

    to_user_id: Mapped[int] = mapped_column(ForeignKey("users.user_id"), index=True)

    swipe_type: Mapped[SwipeType] = mapped_column(Enum(SwipeType))

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
