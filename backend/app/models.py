from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Job(Base):
    __tablename__ = "jobs"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(200))
    company: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text)
    location: Mapped[str] = mapped_column(String(200), default="")
    source_url: Mapped[str] = mapped_column(String(500), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Profile(Base):
    __tablename__ = "profiles"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200), default="")
    email: Mapped[str] = mapped_column(String(255), default="")
    education: Mapped[str] = mapped_column(String(200), default="")
    skills: Mapped[str] = mapped_column(Text, default="")  # raw comma-separated text
    interests: Mapped[str] = mapped_column(Text, default="")
    experience: Mapped[str] = mapped_column(Text, default="")
    location: Mapped[str] = mapped_column(String(200), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    shortlist_entries: Mapped[list["Shortlist"]] = relationship(
        back_populates="profile", cascade="all, delete-orphan"
    )


class Shortlist(Base):
    __tablename__ = "shortlist"

    id: Mapped[int] = mapped_column(primary_key=True)
    profile_id: Mapped[int] = mapped_column(ForeignKey("profiles.id"))
    job_id: Mapped[int] = mapped_column(ForeignKey("jobs.id"))
    status: Mapped[str] = mapped_column(String(30), default="saved")  # saved | shortlisted | not_interested
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    profile: Mapped["Profile"] = relationship(back_populates="shortlist_entries")
    job: Mapped["Job"] = relationship()
