from sqlalchemy import Column, String, Integer, Boolean, Text, ForeignKey, orm

from werkzeug.security import generate_password_hash, check_password_hash
from random import choices
from string import digits, ascii_uppercase
from flask_login import UserMixin
from .db_session import SqlAlchemyBase


class User(SqlAlchemyBase, UserMixin):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, autoincrement=True)

    fullname = Column(String, nullable=False)
    class_id = Column(Integer, ForeignKey("classes.id"))

    login = Column(String, unique=True)
    hashed_password = Column(String)
    key = Column(String, unique=True)

    data = Column(Text, default="{}")
    status = Column(Integer, ForeignKey("statuses.id"), default=1, nullable=False)

    user_status = orm.relationship('Status')
    user_class = orm.relationship('Class')

    def __repr__(self):
        return f"<User {self.fullname}"

    def set_password(self, password):
        self.hashed_password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.hashed_password, password)

    def generate_key(self):
        while True:
            try:
                self.key = "".join(choices(digits + ascii_uppercase, k=10))
            except Exception:
                continue
            break

    def delete_key(self):
        self.key = None

    def get_columns(self):
        return [column.key for column in self.__table__.columns]


class Class(SqlAlchemyBase):
    __tablename__ = 'classes'

    id = Column(Integer, primary_key=True, autoincrement=True)
    class_number = Column(Integer, nullable=False)
    letter = Column(String)
    school_id = Column(Integer, ForeignKey("schools.id"))

    school = orm.relationship('School')

    user = orm.relationship("User", back_populates="user_class")

    def __repr__(self):
        return f"<Status {self.title}>"

    def get_columns(self):
        return [column.key for column in self.__table__.columns]


class School(SqlAlchemyBase):
    __tablename__ = 'schools'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    fullname = Column(String)

    school_class = orm.relationship("User", back_populates="school")

    def __repr__(self):
        return f"<Status {self.title}>"

    def get_columns(self):
        return [column.key for column in self.__table__.columns]


class Status(SqlAlchemyBase):
    __tablename__ = 'statuses'

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String, nullable=False)

    user = orm.relationship("User", back_populates="user_status")

    def __repr__(self):
        return f"<Status {self.title}>"

    def get_columns(self):
        return [column.key for column in self.__table__.columns]
