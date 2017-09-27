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

    multiline = Column("name_multiline", Unicode)
    line_length = Column("max_line_length", Integer)
    label_out_align = Column("label_out_align", String(5))

    multiline.create(coll)
    line_length.create(coll)
    label_out_align.create(coll)

def downgrade(migrate_engine):
    meta.bind = migrate_engine
    coll = Table("nh_images_collection", meta, autoload=True)

    coll.c.name_multiline.drop()
    coll.c.max_line_length.drop()
    coll.c.label_out_align.drop()
    
