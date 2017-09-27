from sqlalchemy import MetaData, Table
from sqlalchemy.sql import select, and_, func
from geoalchemy import GeometryExtensionColumn, GeometryDDL, Point

meta = MetaData()

def upgrade(migrate_engine):
    meta.bind = migrate_engine

    label = func.AddGeometryColumn(
            'public', 'nh_images_collection', 'label', 900913, 'LINESTRING', 2)
    label_out = func.AddGeometryColumn(
            'public', 'nh_images_collection', 'label_out', 900913, 'POINT', 2)
    label_out_path = func.AddGeometryColumn(
            'public', 'nh_images_collection',
            'label_out_path', 900913, 'LINESTRING', 2)

    connection = migrate_engine.connect()
    connection = connection.execution_options(autocommit=True)
    connection.execute(label)
    connection.execute(label_out)
    connection.execute(label_out_path)


def downgrade(migrate_engine):
    meta.bind = migrate_engine

    label = func.DropGeometryColumn('nh_images_collection', 'label')
    label_out = func.DropGeometryColumn('nh_images_collection', 'label_out')
    label_out_path = func.DropGeometryColumn(
        'nh_images_collection', 'label_out_path')

    connection = migrate_engine.connect()
    connection = connection.execution_options(autocommit=True)
    connection.execute(label)
    connection.execute(label_out)
    connection.execute(label_out_path)
