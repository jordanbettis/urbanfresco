from sqlalchemy import *
from migrate import *

from migrate.changeset.constraint import UniqueConstraint

def upgrade(migrate_engine):
    meta = MetaData(bind=migrate_engine)
    user = Table("nh_auth_user", meta, autoload=True)

    name_column = user.c.name
    name_column.alter(nullable=True)

    migrate_engine.execute(user.update().where(
            user.c.name=="").values(name=None))
    
    name_constraint = UniqueConstraint("name", table=user)
    name_constraint.create()

    email_column = user.c.email
    email_column.alter(nullable=True)

    migrate_engine.execute(user.update().where(
            user.c.email=="").values(email=None))

    email_constraint = UniqueConstraint("email", table=user)
    email_constraint.create()

def downgrade(migrate_engine):
    meta = MetaData(bind=migrate_engine)
    user = Table("nh_auth_user", meta, autoload=True)

    name_constraint = UniqueConstraint("name", table=user)
    name_constraint.drop()

    migrate_engine.execute(user.update().where(
            user.c.name==None).values(name=""))
        
    name_column = user.c.name
    name_column.alter(nullable=False)
    
    email_constraint = UniqueConstraint("email", table=user)
    email_constraint.drop()

    migrate_engine.execute(user.update().where(
            user.c.email==None).values(email=""))
        
    email_column = user.c.email
    email_column.alter(nullable=False)

