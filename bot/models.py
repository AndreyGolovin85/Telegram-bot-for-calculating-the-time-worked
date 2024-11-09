from sqlalchemy import DateTime, Integer, String, create_engine, Date, Float, ForeignKey
from sqlalchemy.orm import DeclarativeBase, Mapped, MappedAsDataclass, mapped_column, sessionmaker, relationship

from settings import *


class Base(MappedAsDataclass, DeclarativeBase, repr=False, unsafe_hash=True, kw_only=True):
    """
    Base for SQLAlchemy dataclass
    """

    __abstract__ = True

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, init=False)


class User(Base, sessionmaker):
    __tablename__ = "users"

    time_works: Mapped[list["TimeWork"]] = relationship("TimeWork", back_populates="user", init=False)
    user_uid: Mapped[int] = mapped_column(Integer, unique=True)
    first_name: Mapped[str] = mapped_column(String(30))
    last_name: Mapped[str] = mapped_column(String(30))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, onupdate=datetime.now())

    def __repr__(self) -> str:
        return (
            f"User=(id={self.id!s}, first_name={self.first_name!s}, last_name={self.last_name!s})"
        )


class TimeWork(Base, sessionmaker):
    __tablename__ = "time_works"

    user_uid: Mapped[int] = mapped_column(Integer, ForeignKey("users.user_uid"))
    user: Mapped["User"] = relationship("User", back_populates="time_works", init=False)
    work_date: Mapped[str] = mapped_column(String(12), default=None)
    work_start: Mapped[str] = mapped_column(String(10))
    work_finish: Mapped[str] = mapped_column(String(10))
    work_total: Mapped[float] = mapped_column(Float)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, onupdate=datetime.now())

    def __repr__(self) -> str:
        return (
            f"TimeWork=(id={self.id!s}, work_date={self.work_date!s}, work_start={self.work_start!s},"
            f"work_finish={self.work_finish!s}, work_total={self.work_total!s})"
        )


engine = create_engine(engine, echo=True)

Base.metadata.create_all(engine)
Session = sessionmaker(autoflush=False, bind=engine)
