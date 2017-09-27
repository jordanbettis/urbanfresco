
from sqlalchemy import (
    Column, Integer, Unicode, Boolean,
    String, Enum, DateTime, ForeignKey,
    PickleType, Table, MetaData, UnicodeText)

from sqlalchemy import func

from nh.auth.models import new_auth_key

meta = MetaData()

feedbackitem = Table('nh_feedback_feedbackitem', meta,
      Column('id', Integer(), primary_key=True, nullable=False),
      Column('user_id', Integer(), ForeignKey('nh_auth_user.id')),
      Column('can_publish', Boolean(), nullable=False, default=False),
      Column('published', Boolean(), nullable=False, default=False),
      Column('dismissed', Boolean(), nullable=False, default=False),
      Column('name', Unicode(length=200)),
      Column('email', Unicode(length=200)),
      Column('message', UnicodeText(), nullable=False),
      Column('created', DateTime(), nullable=False, default=func.timestamp()),
      Column('changed', DateTime(), nullable=False, onupdate=func.timestamp()))

def upgrade(migrate_engine):
    meta.bind = migrate_engine
    user = Table("nh_auth_user", meta, autoload=True)
    feedbackitem.create()

def downgrade(migrate_engine):
    meta.bind = migrate_engine
    feedbackitem.drop()


