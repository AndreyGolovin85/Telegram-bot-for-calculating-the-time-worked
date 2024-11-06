from sqlalchemy import DateTime, Integer, String, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, MappedAsDataclass, mapped_column, sessionmaker

from settings import *


class Base(MappedAsDataclass, DeclarativeBase, repr=False, unsafe_hash=True, kw_only=True):
    """
    Base for SQLAlchemy dataclass
    """

    __abstract__ = True

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, init=False)


class User(Base, sessionmaker):
    __tablename__ = "users"
    user_uid: Mapped[int] = mapped_column(Integer, unique=True)
    first_name: Mapped[str] = mapped_column(String(30))
    last_name: Mapped[str] = mapped_column(String(30))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, onupdate=datetime.now())

    def __repr__(self) -> str:
        return (
            f"User=(id={self.id!s}, first_name={self.first_name!s}, last_name={self.last_name!s})"
        )


engine = create_engine(engine, echo=True)

Base.metadata.create_all(engine)
Session = sessionmaker(autoflush=False, bind=engine)
