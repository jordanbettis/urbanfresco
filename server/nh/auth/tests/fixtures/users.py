
from nh.auth.models import User, Permission, UserAssociation

from datetime import datetime

def get_fixtures():
    fixtures = dict()
    
    fixtures['sup'] = User(
        name=u"sup", email=u"sup@neighborhoods.chicago.il.us",
        superuser=True, registered=True, verified=True,
        authenticated=True, last_auth=datetime.now())

    ## Registered user
    fixtures['reg'] = User(
        name=u"reg", email=u"reg@neighborhoods.chicago.il.us",
        registered=True, authenticated=True, last_auth=datetime.now())
    ## Anon related to nh_test_registered
    fixtures['anon_rel_reg'] = User()
    fixtures['reg'].associations.append(UserAssociation(
            from_user=fixtures['anon_rel_reg'], why=u"login"))
    ## Permission for 'xyzzy' service for registered user
    fixtures['reg'].permissions.append(Permission(service="xyzzy"))
    ## Verified user
    fixtures['ver'] = User(
        name=u"ver", email=u"ver@neighborhoods.chicago.il.us",
        registered=True, authenticated=True, last_auth=datetime.now())

    return fixtures

def add_fixtures(session, fixtures):
    session.add_all(fixtures.values())
    session.commit()

def delete_fixtures(session, fixtures):
    for user in fixtures.values():
        for assoc in user.associations:
            session.delete(assoc)
        for perm in user.permissions:
            session.delete(perm)
        user.unlink_avatar()
        session.delete(user)
    session.commit()
