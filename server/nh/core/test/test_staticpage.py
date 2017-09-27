from nh.core.testutils import MockApp, initialize

def test_staticpage():
    app = MockApp()
    response = app.get("/about")
    assert response.status_int == 200
