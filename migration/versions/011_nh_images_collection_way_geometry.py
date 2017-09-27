from sqlalchemy import MetaData, Table

meta = MetaData()

def upgrade(migrate_engine):
    meta.bind = migrate_engine
    gc = Table("geometry_columns", meta, autoload=True)

    update = gc.update().where(
        gc.c.f_table_name=="nh_collections_collection").values(
        f_table_name="nh_images_collection")

    migrate_engine.execute(update)

def downgrade(migrate_engine):
    meta.bind = migrate_engine
    gc = Table("geometry_columns", meta, autoload=True)

    update = gc.update().where(
        gc.c.f_table_name=="nh_images_collection").values(
        f_table_name="nh_collections_collection")

    migrate_engine.execute(update)
