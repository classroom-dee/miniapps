from contextlib import contextmanager

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session

from app.config import settings

engine = create_engine(settings.database_url)


def init_db():
    from app.models.base import Base, Item  # noqa

    Base.metadata.create_all(engine)


def create_session_factory(engine: Engine):
    @contextmanager
    def get_session():
        session = Session(engine)
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    return get_session


_session_context = create_session_factory(engine)


def get_db():
    with _session_context() as session:
        yield session
