import pytest
from app import app, db


@pytest.fixture()
def client():
    app.config.update(
        TESTING=True,
        SQLALCHEMY_DATABASE_URI='sqlite:///:memory:',
        WTF_CSRF_ENABLED=False,
    )

    with app.app_context():
        db.drop_all()
        db.create_all()

    with app.test_client() as test_client:
        yield test_client

    with app.app_context():
        db.session.remove()
        db.drop_all()


def test_index_page_loads(client):
    response = client.get('/')
    assert response.status_code == 200
    assert b"MediQueue" in response.data
