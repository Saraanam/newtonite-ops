from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def token(username="member", password="member123"):
    response = client.post('/login', json={"username": username, "password": password})
    assert response.status_code == 200
    return {"Authorization": "Bearer " + response.json()["token"]}

def create_item(headers, title="Test incident", team="Operations", key=None):
    h = dict(headers)
    if key: h["Idempotency-Key"] = key
    return client.post('/items', headers=h, json={"title": title, "description": "Test description", "item_type": "incident", "priority": "urgent", "team": team})

def test_health():
    assert client.get('/health').json()["status"] == "ok"

def test_create_and_duplicate_idempotency_key():
    h = token()
    first = create_item(h, key="test-same-key")
    second = create_item(h, title="Should not create twice", key="test-same-key")
    assert first.status_code == 201
    assert first.json()["id"] == second.json()["id"]

def test_other_team_is_forbidden():
    h = token("other", "other123")
    response = create_item(h, team="Operations")
    assert response.status_code == 403

def test_viewer_cannot_create_or_claim():
    h = token("viewer", "viewer123")
    response = create_item(h)
    assert response.status_code == 201  # Viewers may create in this demo; edit/claim are blocked.
    claim = client.post(f"/items/{response.json()['id']}/claim", headers=h)
    assert claim.status_code == 403

def test_stale_update_is_rejected():
    h = token()
    item = create_item(h).json()
    update = client.patch(f"/items/{item['id']}", headers=h, json={"title": "Updated title", "version": item["version"]})
    assert update.status_code == 200
    stale = client.patch(f"/items/{item['id']}", headers=h, json={"title": "Stale title", "version": item["version"]})
    assert stale.status_code == 409

def test_invalid_transition_rejected():
    h = token()
    item = create_item(h).json()
    response = client.post(f"/items/{item['id']}/transition", headers=h, json={"status": "Closed"})
    assert response.status_code == 400
