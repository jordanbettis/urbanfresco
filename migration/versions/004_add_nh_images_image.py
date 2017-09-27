from sqlalchemy import (
    Column, Integer, Unicode, Boolean,
    DateTime, String, ForeignKey, PickleType,
    MetaData, Table)

from sqlalchemy import func
from geoalchemy import GeometryExtensionColumn, GeometryDDL, Point

meta = MetaData()

def upgrade(migrate_engine):
    meta.bind = migrate_engine
    user = Table("nh_auth_user", meta, autoload=True)
    
    image = Table(
        'nh_images_image', meta,
        Column('id', Integer(), primary_key=True, nullable=False),
        Column('score', Integer()),
        Column('key', String(length=29), default=lambda: "".join(
                [choice("0123456789") for x in range(29)])),
        Column('user_id', Integer(), ForeignKey('nh_auth_user.id')),
        GeometryExtensionColumn('way', Point(srid=900913)),
        Column('available', Boolean(), nullable=False, default=False),
        Column('flagged', Boolean(), nullable=False, default=False),
        Column('cleared', Boolean(), nullable=False, default=False),
        Column('rejected', Boolean(), nullable=False, default=False),
        Column('copyright_flag', Boolean(), nullable=False, default=False),
        Column('data', PickleType(mutable=True), nullable=False, default={}),
        Column('created', DateTime(), nullable=False, default=func.timestamp()),
        Column('changed', DateTime(), nullable=False, onupdate=func.timestamp()))

    GeometryDDL(image)
    image.create()

def downgrade(migrate_engine):
    meta.bind = migrate_engine
    image = Table('nh_images_image', meta, autoload=True)
    image.drop()
