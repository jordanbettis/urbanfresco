from nh.core.testutils import initialize
from nh.core import db, config, testutils

from webob import Request
from nh.auth.models import User

from fixtures import users

def setup():
    global SESSION, APP, USERS
    initialize()
    SESSION = db.Session()
    USERS = users.get_fixtures()
    users.add_fixtures(SESSION, USERS)

def teardown():
    users.delete_fixtures(SESSION, USERS)
    SESSION.commit()

def test_data():
    sup = SESSION.query(User).filter_by(
        email=u"sup@neighborhoods.chicago.il.us").one()
    sup.data['xyzzy'] = "bin"
    SESSION.commit()
    sup2 = SESSION.query(User).filter_by(
        email=u"sup@neighborhoods.chicago.il.us").one()
    assert sup2.data['xyzzy'] == 'bin', "user data error"
    
def test_authenticated_recently():
    sup = SESSION.query(User).filter_by(name=u"sup").one()
    assert not sup.authenticated_recently, "current_auth for superuser"

    sup.current_auth = True
    assert sup.authenticated_recently, \
        "auth_recently failure for superuser"
    
def test_login():
    sup = SESSION.query(User).filter_by(name=u"sup").one()
    sup.set_password("xyzzy")
    request = Request(testutils.get_environ())
    assert sup.login(request, "xyzzy"), "login falure"

    assert request.user == sup, "request.user not assigned"

    request = Request(testutils.get_environ())
    request_anon = User()
    request.user = request_anon

    sup.login(request, "xyzzy")

    assert sup.associations[0].from_user \
        == request_anon, "association not made"
