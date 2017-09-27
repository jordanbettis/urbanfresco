from sqlalchemy import (
    Column, Integer, Unicode, Boolean, Table,
    DateTime, String, ForeignKey, PickleType,
    Float, MetaData)

from sqlalchemy import func
from sqlalchemy.orm import relationship

meta = MetaData()

def upgrade(migrate_engine):
    meta.bind = migrate_engine
    vote = Table("nh_images_vote", meta, autoload=True)

    up = Column("up", Boolean, default=True)
    up.create(vote)

def downgrade(migrate_engine):
    meta.bind = migrate_engine
    vote = Table("nh_images_vote", meta, autoload=True)

    vote.c.up.drop()
