from sqlalchemy import (
    Column, Integer, Unicode, Boolean, Table,
    DateTime, String, ForeignKey, PickleType,
    MetaData)

from sqlalchemy import func
from sqlalchemy.orm import relationship
from geoalchemy import GeometryExtensionColumn, Polygon, GeometryDDL

meta = MetaData()

collection = Table(
    'nh_collections_collection', meta,
    Column('id', Integer(), primary_key=True, nullable=False),
    Column('name', Unicode(length=200), nullable=False),
    GeometryExtensionColumn('way', Polygon(srid=900913)),
    Column('data', PickleType(mutable=True), nullable=False, default={}),
    Column('created', DateTime(), nullable=False, default=func.timestamp()),
    Column('changed', DateTime(), nullable=False, onupdate=func.timestamp()))

GeometryDDL(collection)

def upgrade(migrate_engine):
    meta.bind = migrate_engine
    image = Table('nh_images_image', meta, autoload=True)
    
    collection_image = Table(
        'nh_collections_collectionimage', meta,
        Column('collection_id', Integer, ForeignKey('nh_collections_collection.id')),
        Column('image_id', Integer, ForeignKey('nh_images_image.id')))
    
    collection.create()
    collection_image.create()

def downgrade(migrate_engine):
    meta.bind = migrate_engine
    collection_image = Table("nh_collections_collectionimage", meta, autoload=True)
    collection_image.drop()
    collection.drop()
