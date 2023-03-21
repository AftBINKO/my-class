import sqlalchemy as sa
import sqlalchemy.orm as orm
from sqlalchemy.orm import Session
import sqlalchemy.ext.declarative as dec

SqlAlchemyBase = dec.declarative_base()

__factory = None


def global_init(db_file, echo=False):
    global __factory

    if __factory:
        return

    if not db_file or not db_file.strip():
        raise FileNotFoundError("You must specify the database file")

    conn_str = f'sqlite:///{db_file.strip()}?check_same_thread=False'

    if echo:
        print(f"Connecting to the database at {conn_str}")

    engine = sa.create_engine(conn_str, echo=echo)
    __factory = orm.sessionmaker(bind=engine)

    from . import __all_models

    SqlAlchemyBase.metadata.create_all(engine)


def create_session() -> Session:
    global __factory
    # noinspection PyCallingNonCallable
    return __factory()
