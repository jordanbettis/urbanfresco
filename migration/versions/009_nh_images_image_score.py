from sqlalchemy import (
    Column, Integer, Unicode, Boolean, Table,
    DateTime, String, ForeignKey, PickleType,
    Float, MetaData)

from sqlalchemy import func
from sqlalchemy.orm import relationship

meta = MetaData()

def upgrade(migrate_engine):
    meta.bind = migrate_engine
    images = Table("nh_images_image", meta, autoload=True)

    images.c.score.drop()

    views = Column("views", Integer, default=0)
    views.create(images)

    score = Column("score", Float, default=0)
    score.create(images)

def downgrade(migrate_engine):
    meta.bind = migrate_engine
    images = Table("nh_images_image", meta, autoload=True)

    images.c.score.drop()
    images.c.views.drop()

    score = Column("score", Integer)
    score.create(images)
    
