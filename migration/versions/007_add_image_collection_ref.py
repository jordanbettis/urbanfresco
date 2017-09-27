from sqlalchemy import (
    Column, Integer, Unicode, Boolean, Table,
    DateTime, String, ForeignKey, PickleType,
    MetaData)

from sqlalchemy import func
from sqlalchemy.orm import relationship

meta = MetaData()

def upgrade(migrate_engine):
    meta.bind = migrate_engine
    collection = Table("nh_images_collection", meta, autoload=True)
    images = Table("nh_images_image", meta, autoload=True)

    collection_id = Column("collection_id", Integer,
                           ForeignKey("nh_images_collection.id"))

    collection_id.create(images)

def downgrade(migrate_engine):
    meta.bind = migrate_engine
    images = Table("nh_images_image", meta, autoload=True)

    collection_id = images.columns.collection_id

    collection_id.drop()
