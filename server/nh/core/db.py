
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import Session as BaseSession
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql.expression import ClauseElement
from sqlalchemy import create_engine

Base = declarative_base()

ENGINE = None

class Session(BaseSession):
    def get_or_create(session, model, defaults=dict(), **kwargs):
        """
        Shortcut like django's get_or_create
        
        Returns a tuple: (instance, if_created_boolean)
        """
        instance = session.query(model).filter_by(**kwargs).first()
        found = True
        if not instance:
            found = False
            create_params = dict([
                    (x[0], x[1]) for x in kwargs.iteritems()
                    if not isinstance(x, ClauseElement)])
            create_params.update(defaults)
            instance = model(**create_params)
            session.add(instance)
        return instance, not found

Session = sessionmaker(class_=Session)

def connect(connect_info):
    """ Make and return a database engine """
    connect_url = 'postgresql+psycopg2://%(user)s:%(pass)s@%(host)s/%(db)s' \
        % connect_info
    engine = create_engine(connect_url)
    Session.configure(bind=engine)
    return engine
    
