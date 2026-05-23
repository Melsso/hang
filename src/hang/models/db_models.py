from sqlalchemy import (
    String,
    Boolean,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    UniqueConstraint,
    Text,
)
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column, DeclarativeBase, relationship
from datetime import datetime, timezone, date

from hang.schemas.users import Gender, InterestedIn
from hang.schemas.swipes import SwipeType


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    user_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    first_name: Mapped[str] = mapped_column(String(50))
    last_name: Mapped[str] = mapped_column(String(50))
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password: Mapped[str | None] = mapped_column(String(255), nullable=True)

    auth_provider: Mapped[str] = mapped_column(
        String(20), nullable=False, default="local"
    )
    oauth_id: Mapped[str | None] = mapped_column(String(255), nullable=True)

    country: Mapped[str] = mapped_column(String(2), default="DE")
    birthdate: Mapped[date | None] = mapped_column(Date, nullable=True)

    bio: Mapped[str] = mapped_column(String(500), default="")

    gender: Mapped[Gender] = mapped_column(Enum(Gender))
    interested_in: Mapped[InterestedIn] = mapped_column(Enum(InterestedIn))
    interests: Mapped[list[str]] = mapped_column(
        ARRAY(String), nullable=False, default=list
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

    images = relationship(
        "UserImage",
        backref="user",
        cascade="all, delete-orphan",
        order_by="UserImage.position",
    )

    conversations_as_user1 = relationship(
        "Conversation",
        foreign_keys="Conversation.user1_id",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    conversations_as_user2 = relationship(
        "Conversation",
        foreign_keys="Conversation.user2_id",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class UserBlock(Base):
    __tablename__ = "user_blocks"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    blocker_id: Mapped[int] = mapped_column(
        ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False
    )

    blocked_id: Mapped[int] = mapped_column(
        ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    __table_args__ = (
        UniqueConstraint("blocker_id", "blocked_id", name="uq_user_block"),
    )

    blocker = relationship("User", foreign_keys=[blocker_id])
    blocked = relationship("User", foreign_keys=[blocked_id])


class UserReport(Base):
    __tablename__ = "user_reports"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    reporter_id: Mapped[int] = mapped_column(
        ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False
    )
    reported_id: Mapped[int] = mapped_column(
        ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False
    )

    reason: Mapped[str] = mapped_column(String(100), nullable=False)
    message: Mapped[str | None] = mapped_column(Text, nullable=True)

    status: Mapped[str] = mapped_column(String(20), default="open")

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    reporter = relationship("User", foreign_keys=[reporter_id])
    reported = relationship("User", foreign_keys=[reported_id])


class UserImage(Base):
    __tablename__ = "user_images"

    image_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.user_id", ondelete="CASCADE"), index=True
    )

    image_key: Mapped[str] = mapped_column(String(255), nullable=False)
    position: Mapped[int] = mapped_column(default=0)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )


class Message(Base):
    __tablename__ = "messages"

    message_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    conversation_id: Mapped[int] = mapped_column(
        ForeignKey("conversations.conversation_id", ondelete="CASCADE"), index=True
    )

    sender_id: Mapped[int] = mapped_column(
        ForeignKey("users.user_id", ondelete="CASCADE"), index=True
    )

    content: Mapped[str] = mapped_column(String(1000))
    is_read: Mapped[bool] = mapped_column(default=False)

    reply_to_id: Mapped[int | None] = mapped_column(
        ForeignKey("messages.message_id", ondelete="SET NULL"), nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )


class Conversation(Base):
    __tablename__ = "conversations"

    conversation_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    user1_id: Mapped[int] = mapped_column(
        ForeignKey("users.user_id", ondelete="CASCADE")
    )

    user2_id: Mapped[int] = mapped_column(
        ForeignKey("users.user_id", ondelete="CASCADE")
    )

    last_message_id: Mapped[int | None] = mapped_column(
        ForeignKey("messages.message_id", ondelete="SET NULL"), nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    messages = relationship(
        "Message",
        foreign_keys="Message.conversation_id",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class Swipe(Base):
    __tablename__ = "swipes"

    swipe_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    from_user_id: Mapped[int] = mapped_column(
        ForeignKey("users.user_id", ondelete="CASCADE"), index=True
    )

    to_user_id: Mapped[int] = mapped_column(
        ForeignKey("users.user_id", ondelete="CASCADE"), index=True
    )

    swipe_type: Mapped[SwipeType] = mapped_column(Enum(SwipeType))

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    __table_args__ = (
        UniqueConstraint("from_user_id", "to_user_id", name="uq_swipe_pair"),
    )
