"""SQLAlchemy entity definitions."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    contacts: Mapped[list[FamilyContact]] = relationship(
        back_populates="user", cascade="all, delete-orphan", passive_deletes=True
    )
    push_subscriptions: Mapped[list[PushSubscription]] = relationship(
        back_populates="user", cascade="all, delete-orphan", passive_deletes=True
    )


class FamilyContact(Base):
    __tablename__ = "family_contacts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String(120))
    email: Mapped[str] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(String(32), default="waiting")  # waiting | accepted
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: Mapped[User] = relationship(back_populates="contacts")
    invitation: Mapped[Invitation | None] = relationship(
        back_populates="contact", uselist=False, cascade="all, delete-orphan", passive_deletes=True
    )


class Invitation(Base):
    __tablename__ = "invitations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    contact_id: Mapped[int] = mapped_column(ForeignKey("family_contacts.id", ondelete="CASCADE"))
    token: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    accepted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    unsubscribe_token: Mapped[str] = mapped_column(String(64), unique=True)

    contact: Mapped[FamilyContact] = relationship(back_populates="invitation")


class DrillSession(Base):
    __tablename__ = "drill_sessions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    scenario_id: Mapped[str] = mapped_column(String(64))
    difficulty: Mapped[str] = mapped_column(String(16))
    mode: Mapped[str] = mapped_column(String(16))  # experience | helper
    status: Mapped[str] = mapped_column(String(16), default="active")  # active | finished
    turn_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    turns: Mapped[list[DrillTurn]] = relationship(back_populates="session")


class DrillTurn(Base):
    __tablename__ = "drill_turns"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    session_id: Mapped[str] = mapped_column(ForeignKey("drill_sessions.id", ondelete="CASCADE"))
    role: Mapped[str] = mapped_column(String(16))  # caller | you | victim
    content: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    session: Mapped[DrillSession] = relationship(back_populates="turns")


class Report(Base):
    __tablename__ = "reports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    scam_type: Mapped[str] = mapped_column(String(64), index=True)
    area: Mapped[str] = mapped_column(String(64), index=True)
    text: Mapped[str | None] = mapped_column(String(200), nullable=True)
    ip_hash: Mapped[str] = mapped_column(String(64), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class PushSubscription(Base):
    __tablename__ = "push_subscriptions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    endpoint: Mapped[str] = mapped_column(Text)
    p256dh: Mapped[str] = mapped_column(Text)
    auth: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: Mapped[User] = relationship(back_populates="push_subscriptions")


class AlertLog(Base):
    __tablename__ = "alert_log"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    alert_type: Mapped[str] = mapped_column(String(32))
    channel: Mapped[str] = mapped_column(String(32))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class AuthCode(Base):
    __tablename__ = "auth_codes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(255), index=True)
    code: Mapped[str] = mapped_column(String(6))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    used: Mapped[bool] = mapped_column(Boolean, default=False)
