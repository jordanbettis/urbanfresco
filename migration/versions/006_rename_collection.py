from sqlalchemy import (
    Column, Integer, Unicode, Boolean, Table,
    DateTime, String, ForeignKey, PickleType,
    MetaData)

from sqlalchemy import func
from sqlalchemy.orm import relationship
from geoalchemy import GeometryExtensionColumn, Polygon, GeometryDDL

meta = MetaData()

def upgrade(migrate_engine):
    meta.bind = migrate_engine
    collection_image = Table("nh_collections_collectionimage", meta, autoload=True)
    collection_image.drop()
    collection = Table("nh_collections_collection", meta, autoload=True)
    collection.rename("nh_images_collection")

def downgrade(migrate_engine):
    meta.bind = migrate_engine
    collection = Table("nh_images_collection", meta, autoload=True)
    collection.rename("nh_collections_collection")

    images = Table("nh_images_image", meta, autoload=True)
    
    collection_image = Table(
        'nh_collections_collectionimage', meta,
        Column('collection_id', Integer, ForeignKey('nh_collections_collection.id')),
        Column('image_id', Integer, ForeignKey('nh_images_image.id')))
    collection_image.create()
    
