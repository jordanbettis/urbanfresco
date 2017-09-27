
from sqlalchemy import (
    Column, Integer, Unicode, Boolean,
    String, Enum, DateTime, ForeignKey,
    PickleType, Table, MetaData)

from sqlalchemy import func

from nh.auth.models import new_auth_key

meta = MetaData()

user = Table('nh_auth_user', meta,
      Column('id', Integer(), primary_key=True, nullable=False),
      Column('auth_key', String(length=64), nullable=False, default=new_auth_key),
      Column('session_key', String(length=32)),
      Column('name', Unicode(length=200), nullable=False, default=u''),
      Column('email', Unicode(length=200), nullable=False, default=u''),
      Column('password', String(length=64)),
      Column('superuser', Boolean(), nullable=False, default=False),
      Column('registered', Boolean(), nullable=False, default=False),
      Column('verified', Boolean(), nullable=False, default=False),
      Column('authenticated', Boolean(), nullable=False, default=False),
      Column('current_auth', Boolean(), nullable=False, default=False),
      Column('last_auth', DateTime()),
      Column('data', PickleType(mutable=True), nullable=False, default={}),
      Column('created', DateTime(), nullable=False, default=func.timestamp()),
      Column('changed', DateTime(), nullable=False, onupdate=func.timestamp()))

permission = Table(
    'nh_auth_permission', meta,
    Column('id', Integer(), primary_key=True, nullable=False),
    Column('user_id', Integer(), ForeignKey('nh_auth_user.id')),
    Column('service', String(length=20), nullable=False),
    Column('created', DateTime(), nullable=False, default=func.timestamp()))

user_association = Table(
    'nh_auth_userassociation', meta,
    Column('id', Integer(), primary_key=True, nullable=False),
    Column('to_user_id', Integer(), ForeignKey('nh_auth_user.id')),
    Column('why', String(length=10), nullable=False),
    Column('from_user_id', Integer(), ForeignKey('nh_auth_user.id')),
    Column('created', DateTime(), nullable=False, default=func.timestamp()))

def upgrade(migrate_engine):
    meta.bind = migrate_engine
    user.create()
    permission.create()
    user_association.create()

def downgrade(migrate_engine):
    meta.bind = migrate_engine
    user_association.drop()
    permission.drop()
    user.drop()
