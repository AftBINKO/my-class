from sqlalchemy import Column, String, Integer, Boolean, Text, ForeignKey, orm
from sqlalchemy_serializer import SerializerMixin

from werkzeug.security import generate_password_hash, check_password_hash
from random import choices
from string import digits, ascii_uppercase
from flask_login import UserMixin
from .db_session import SqlAlchemyBase


class User(SqlAlchemyBase, UserMixin, SerializerMixin):
    __tablename__ = 'users'

    serialize_rules = ("-user_status", "-user_class",)

    id = Column(Integer, primary_key=True, autoincrement=True)

    fullname = Column(String, nullable=False)
    class_id = Column(Integer, ForeignKey("classes.id"))

    login = Column(String, unique=True)
    hashed_password = Column(String)
    key = Column(String, unique=True)

    data = Column(Text, nullable=False, default="{}")
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


class Class(SqlAlchemyBase, SerializerMixin):
    __tablename__ = 'classes'

    serialize_rules = ("-school", "-user",)

    id = Column(Integer, primary_key=True, autoincrement=True)
    class_number = Column(Integer, nullable=False)
    letter = Column(String)
    school_id = Column(Integer, ForeignKey("schools.id"))

    school = orm.relationship('School')

    user = orm.relationship("User", back_populates="user_class")

    def __repr__(self):
        return f"<Class {self.title}>"

    def get_columns(self):
        return [column.key for column in self.__table__.columns]


class School(SqlAlchemyBase, SerializerMixin):
    __tablename__ = 'schools'

    serialize_rules = ("-school_class",)

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    fullname = Column(String)

    school_class = orm.relationship("Class", back_populates="school")

    def __repr__(self):
        return f"<School {self.title}>"

    def get_columns(self):
        return [column.key for column in self.__table__.columns]


class Status(SqlAlchemyBase, SerializerMixin):
    __tablename__ = 'statuses'

    serialize_rules = ("-user",)

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String, nullable=False)
    permissions = Column(String, nullable=False, default='{"allowed": [], "banned": []}')

    user = orm.relationship("User", back_populates="user_status")

    def __repr__(self):
        return f"<Status {self.title}>"

    def get_columns(self):
        return [column.key for column in self.__table__.columns]


class Permission(SqlAlchemyBase, SerializerMixin):
    __tablename__ = 'permissions'

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String, nullable=False)
    description = Column(String)

    def __repr__(self):
        return f"<Permission {self.title}>"

    def get_columns(self):
        return [column.key for column in self.__table__.columns]
