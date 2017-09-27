from sqlalchemy import (
    Column, Integer, Unicode, Boolean, Table,
    DateTime, String, ForeignKey, PickleType,
    Float, MetaData)

from sqlalchemy import func
from sqlalchemy.orm import relationship

meta = MetaData()

def upgrade(migrate_engine):
    meta.bind = migrate_engine
    coll = Table("nh_images_collection", meta, autoload=True)

    label_length = Column("label_length", Integer, default=0)
    label_length.create(coll)

def downgrade(migrate_engine):
    meta.bind = migrate_engine
    coll = Table("nh_images_collection", meta, autoload=True)

    coll.c.label_length.drop()
    
