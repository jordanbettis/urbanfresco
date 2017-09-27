from sqlalchemy import *
from migrate import *


def upgrade(migrate_engine):
    meta = MetaData(bind=migrate_engine)
    user = Table("nh_auth_user", meta, autoload=True)

    dob = Column("dob", Date())
    dob.create(user)

def downgrade(migrate_engine):
    meta = MetaData(bind=migrate_engine)
    user = Table("nh_auth_user", meta, autoload=True)

    user.c.dob.drop()
