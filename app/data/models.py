from datetime import datetime

from sqlalchemy import Column, String, Integer, Boolean, Text, ForeignKey, orm, DateTime, BLOB
from sqlalchemy_serializer import SerializerMixin

from werkzeug.security import generate_password_hash, check_password_hash
from random import choices
from string import digits, ascii_uppercase
from flask_login import UserMixin
from .db_session import SqlAlchemyBase


class User(SqlAlchemyBase, UserMixin, SerializerMixin):
    __tablename__ = 'users'

    serialize_rules = ("-group", "-school",)

    id = Column(Integer, primary_key=True, autoincrement=True)

    fullname = Column(String, nullable=False)
    group_id = Column(Integer, ForeignKey("groups.id"))
    school_id = Column(Integer, ForeignKey("schools.id"))

    login = Column(String, unique=True)
    hashed_password = Column(String)
    key = Column(String, unique=True)

    is_registered = Column(Boolean, nullable=False, default=False)

    qr = Column(String)

    is_arrived = Column(Boolean)
    arrival_time = Column(DateTime)
    list_times = Column(Text)

    roles = Column(String, nullable=False, default="[1]")

    home_page = Column(String, nullable=False, default="profile")

    group = orm.relationship('Group')
    school = orm.relationship('School')

    def __repr__(self):
        return f"<User {self.fullname}>"

    def arrival_time_for(self, date: datetime.date):
        if self.list_times:
            user_datetimes = list(
                map(lambda d: datetime.strptime(d, "%Y-%m-%d %H:%M:%S.%f"), self.list_times.split(", ")))

            for dt in user_datetimes:
                if date == dt.date():
                    return dt.time()

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


class Group(SqlAlchemyBase, SerializerMixin):
    __tablename__ = 'groups'

    serialize_rules = ("-school", "-user",)

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    type = Column(Integer, nullable=False, default=0)
    school_id = Column(Integer, ForeignKey("schools.id"))

    school = orm.relationship('School')
    user = orm.relationship("User", back_populates="group")

    def __repr__(self):
        return f"<Group {self.name}>"


class School(SqlAlchemyBase, SerializerMixin):
    __tablename__ = 'schools'

    serialize_rules = ("-group", "-user",)

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    fullname = Column(Text)

    types = Column(String, nullable=False, default="[]")

    group = orm.relationship("Group", back_populates="school")
    user = orm.relationship("User", back_populates="school")

    def __repr__(self):
        return f"<School {self.name}>"


class Role(SqlAlchemyBase, SerializerMixin):
    __tablename__ = 'roles'

    id = Column(Integer, primary_key=True, autoincrement=True)
    priority = Column(Integer, autoincrement=True)

    title = Column(String, nullable=False)
    inheritance = Column(Integer, ForeignKey("roles.id"))
    allowed_permissions = Column(String)
    banned_permissions = Column(String)

    def __repr__(self):
        return f"<Role {self.title}>"


class Permission(SqlAlchemyBase, SerializerMixin):
    __tablename__ = 'permissions'

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String, nullable=False)
    description = Column(String)
    is_allowed_default = Column(Boolean, nullable=False, default=False)

    def __repr__(self):
        return f"<Permission {self.title}>"
