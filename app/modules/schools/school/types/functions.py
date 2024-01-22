from app.data.db_session import create_session


def delete_type(name):
    db_sess = create_session()
