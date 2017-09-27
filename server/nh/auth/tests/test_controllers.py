from datetime import datetime, timedelta

from nh.core.testutils import MockApp, initialize
from nh.core import db, config, testutils, controllers

from webob import Response
from nh.auth.models import User, UserAssociation
from nh.auth.decorators import (
    registration_required, authentication_required, permission_required)
from nh.auth.tests.fixtures import users

import os

def setup():
    global SESSION, USERS
    initialize()
    SESSION = db.Session()
    USERS = users.get_fixtures()
    users.add_fixtures(SESSION, USERS)

def teardown():
    users.delete_fixtures(SESSION, USERS)
    SESSION.commit()
        
def test_login_user():
    app = MockApp()
    response = app.get("/auth/login")
    assert response.status_int == 200
    anon_user = response.request.user
    registered_user = SESSION.query(
        User).filter_by(email=u"reg@neighborhoods.chicago.il.us").one()
    registered_user.set_password("xyzzyxyzzy")
    SESSION.commit()
    post_data = {
        'name': "",
        'password': "",
        'csrftoken': anon_user.data['csrf-token']}
    response = app.post("/auth/login", post_data)
    assert response.status_int == 200
    post_data = {
        'name': registered_user.name,
        'password': "xyzzy12345",
        'csrftoken': anon_user.data['csrf-token']}
    response = app.post("/auth/login", post_data)
    assert response.status_int == 200
    assert "Authentication failure" in response.body
    post_data = {
        'name': "finfangfong",
        'password': "xyzzyxyzzy",
        'csrftoken': anon_user.data['csrf-token']}
    response = app.post("/auth/login", post_data)
    assert response.status_int == 200
    assert "Authentication failure" in response.body
    post_data = {
        'name': registered_user.name,
        'password': "xyzzyxyzzy",
        'csrftoken': anon_user.data['csrf-token']}
    response = app.post("/auth/login", post_data)
    assert response.status_int == 302
    assert response.request.user.id == registered_user.id
    assert SESSION.query(UserAssociation).filter_by(
        from_user=anon_user, to_user=registered_user).count() > 0

def test_login_email():
    app = MockApp()
    response = app.get("/auth/login")
    assert response.status_int == 200
    anon_user = response.request.user
    registered_user = SESSION.query(
        User).filter_by(email=u"reg@neighborhoods.chicago.il.us").one()
    registered_user.set_password("xyzzyxyzzy")
    SESSION.commit()
    post_data = {
        'password': "xyzzyxyzzy",
        'csrftoken': anon_user.data['csrf-token']}
    response = app.post("/auth/login", post_data)
    assert response.status_int == 200
    assert "username or email" in response.body
    post_data = {
        'email': registered_user.email,
        'password': "xyzzyxyzzy",
        'csrftoken': anon_user.data['csrf-token']}
    response = app.post("/auth/login", post_data)
    assert response.status_int == 302
    assert response.request.user.id == registered_user.id

def test_register():
    app = MockApp()
    response = app.get("/auth/register")
    assert response.status_int == 200
    
    post_data = {
        'name': 'ver',
        'password': 'asdfgasdfg',
        'confirm': 'asdfgasdfg',
        'csrftoken': response.request.user.data['csrf-token']}
    response = app.post("/auth/register", post_data)
    assert response.status_int == 200
    assert 'user with this name already exists' in response.body
    
    post_data = {
        'name': 'flimflam',
        'password': 'qwertyqwerty',
        'confirm': 'qwertyqwerty',
        'csrftoken': response.request.user.data['csrf-token']}
    response = app.post("/auth/register", post_data)
    assert response.status_int == 302

def test_banned_username():
    app = MockApp()
    response = app.get("/auth/register")
    
    post_data = {
        'name': 'static',
        'password': 'qwertyqwerty',
        'confirm': 'qwertyqwerty',
        'csrftoken': response.request.user.data['csrf-token']}
    response = app.post("/auth/register", post_data)
    assert response.status_int == 200, "permitted username 'static'"
    assert "Choose a different username" in response.body
    
    post_data = {
        'name': 'about',
        'password': 'qwertyqwerty',
        'confirm': 'qwertyqwerty',
        'csrftoken': response.request.user.data['csrf-token']}
    response = app.post("/auth/register", post_data)
    assert response.status_int == 200, "permitted username 'about'"
    assert "Choose a different username" in response.body
    

def test_verify():
    app = MockApp()
    reg = SESSION.query(
        User).filter_by(name=u"reg").one()
    app.login(reg)
    response = app.get("/auth/verify")
    post_data = {
        "email": "sup@neighborhoods.chicago.il.us",
        "dob": "12/12/1990",
        'csrftoken': response.request.user.data['csrf-token']}
    response = app.post("/auth/verify", post_data)
    assert response.status_int == 200
    SESSION.refresh(reg)
    assert reg.under_thirteen is False
    post_data = {
        "email": "finfan@hafd.org",
        "dob": "12/12/2010",
        'csrftoken': response.request.user.data['csrf-token']}
    response = app.post("/auth/verify", post_data)
    assert response.status_int == 302
    assert "coppa" in response.location
    ## Make sure the user is now blocked from verifying
    response = app.get("/auth/verify")
    assert "coppa" in response.location
    reg.dob = None
    SESSION.commit()
    post_data = {
        "email": "finfan@hafd.org",
        "dob": "12/12/1990",
        'csrftoken': response.request.user.data['csrf-token']}
    response = app.post("/auth/verify", post_data)
    assert response.status_int == 302
    assert "reg" in response.location

def test_confirm():
    app = MockApp()
    ver = SESSION.query(User).filter_by(name=u"ver").one()
    app.login(ver)
    ver.data['verify-key'] = "123456789012"
    response = app.get("/auth/confirm/111222333444")
    assert response.status_int == 200
    assert "failed" in response.body

def test_change_password():
    app = MockApp()
    ver = SESSION.query(User).filter_by(name=u"ver").one()
    ver.set_password("asdfgasdfg")
    app.login(ver)
    SESSION.commit()
    response = app.get("/auth/edit/password")
    assert response.status_int == 200
    post_data = {
        "current_password": 'asdfgasdfg',
        "password": "qwertyqwertyasdfg",
        "confirm": "qwertyqwertyasdfg",
        "csrftoken": response.request.user.data['csrf-token']}
    response = app.post("/auth/edit/password", post_data)
    print response
    assert response.status_int == 302
    assert "ver" in response.location 

def test_edit_name():
    app = MockApp()
    ver = SESSION.query(User).filter_by(name=u"ver").one()
    app.login(ver)
    SESSION.commit()
    response = app.get("/auth/edit/name")
    assert response.status_int == 200
    post_data = {
        "full_name": "Fred Foobar",
        "csrftoken": response.request.user.data['csrf-token']}
    response = app.post("/auth/edit/name", post_data)
    assert response.status_int == 302
    assert "Fred Foobar" in ver.display_name
    assert "ver" in ver.display_name

def test_edit_profile():
    app = MockApp()
    ver = SESSION.query(User).filter_by(name=u"ver").one()
    app.login(ver)
    SESSION.commit()
    response = app.get("/auth/edit/profile")
    print response
    assert response.status_int == 200
    post_data = {
        "profile": "I must go down to the sea again",
        "csrftoken": response.request.user.data['csrf-token']}
    response = app.post("/auth/edit/profile", post_data)
    assert response.status_int == 302
    ver = SESSION.query(User).filter_by(name=u"ver").one()
    assert "I must go down to the sea again" in ver.data['profile']
    assert "ver" in ver.display_name
    
def test_put_avatar():
    app = MockApp()
    ver = SESSION.query(User).filter_by(name=u"ver").one()
    app.login(ver)
    SESSION.commit()
    filename = "%s/img/default-avatar-profile.jpg" % config.CONFIG.STATIC_DIR
    post_data = {"csrftoken": ver.data['csrf-token']}
    response = app.post("/auth/put-avatar", post_data,
                        files=[("files[]", filename),])
    print response

    SESSION.refresh(ver)

    assert "avatar-key" in ver.data
    assert "avatar-filename" in ver.data
    assert "avatar-type" in ver.data
    assert "avatar-type-options" in ver.data
    assert "avatar-ext" in ver.data

    files = [ver.avatar_upload_path]
    for size in config.CONFIG.AVATAR_SIZES:
        files.append(
            os.path.join(config.CONFIG.IMAGE_DIR, "%s-%s.jpg" % (
                    ver.data['avatar-key'], size[2])))
        
    for fname in files:
        assert os.path.exists(fname)
    
    ver.unlink_avatar()
    
    for fname in files:
        assert not os.path.exists(fname)
