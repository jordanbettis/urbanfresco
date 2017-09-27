from sqlalchemy import (
    Column, Integer, Unicode, Boolean, Table,
    DateTime, String, ForeignKey, PickleType,
    MetaData)

from sqlalchemy import func
from sqlalchemy.orm import relationship

meta = MetaData()

def upgrade(migrate_engine):
    meta.bind = migrate_engine
    image = Table("nh_images_image", meta, autoload=True)
    user = Table("nh_auth_user", meta, autoload=True)
    vote = Table(
        'nh_images_vote', meta,
        Column('id', Integer(), primary_key=True, nullable=False),
        Column('user_id', Integer(), ForeignKey('nh_auth_user.id')),
        Column('image_id', Integer(), ForeignKey('nh_images_image.id')),
        Column('created', DateTime(), nullable=False, default=func.timestamp()))
    vote.create()

def downgrade(migrate_engine):
    meta.bind = migrate_engine
    vote = Table("nh_collections_vote", meta, autoload=True)
    vote.drop()
