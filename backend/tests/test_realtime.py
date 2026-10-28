import pytest
from starlette.websockets import WebSocketDisconnect

from tests.conftest import make_user


def token_of(headers):
    return headers["Authorization"].split()[1]


def shared_board(client):
    """Alice owns a board with one list and shares it with Bob."""
    alice = make_user(client)
    bob = make_user(client, email="bob@example.com", name="Bob")
    board = client.post("/boards", json={"name": "Team"}, headers=alice).json()
    lst = client.post(f"/boards/{board['id']}/lists", json={"title": "To do"}, headers=alice).json()
    client.post(f"/boards/{board['id']}/members", json={"email": "bob@example.com"}, headers=alice)
    return alice, bob, board, lst


def read_until(ws, msg_type):
    """Skip messages until one of the given type arrives (e.g. skip presence while waiting for board)."""
    for _ in range(10):
        msg = ws.receive_json()
        if msg["type"] == msg_type:
            return msg
    raise AssertionError(f"no {msg_type} message")


def test_rejects_bad_token(client):
    alice = make_user(client)
    board = client.post("/boards", json={"name": "B"}, headers=alice).json()
    with client.websocket_connect(f"/ws/boards/{board['id']}?token=garbage") as ws:
        with pytest.raises(WebSocketDisconnect) as e:
            ws.receive_json()
    assert e.value.code == 4401


def test_rejects_non_member(client):
    alice = make_user(client)
    eve = make_user(client, email="eve@example.com", name="Eve")
    board = client.post("/boards", json={"name": "B"}, headers=alice).json()
    with client.websocket_connect(f"/ws/boards/{board['id']}?token={token_of(eve)}") as ws:
        with pytest.raises(WebSocketDisconnect) as e:
            ws.receive_json()
    assert e.value.code == 4404


def test_initial_snapshot_and_presence(client):
    alice, bob, board, lst = shared_board(client)
    with client.websocket_connect(f"/ws/boards/{board['id']}?token={token_of(alice)}") as a:
        first = a.receive_json()
        assert first["type"] == "board" and first["board"]["lists"][0]["title"] == "To do"
        assert [u["name"] for u in read_until(a, "presence")["users"]] == ["Alice"]
        with client.websocket_connect(f"/ws/boards/{board['id']}?token={token_of(bob)}") as b:
            read_until(b, "board")
            # Alice is told Bob joined
            names = sorted(u["name"] for u in read_until(a, "presence")["users"])
            assert names == ["Alice", "Bob"]
        # Bob left: Alice sees only herself again
        assert [u["name"] for u in read_until(a, "presence")["users"]] == ["Alice"]


def test_change_by_one_user_reaches_the_other(client):
    alice, bob, board, lst = shared_board(client)
    with client.websocket_connect(f"/ws/boards/{board['id']}?token={token_of(bob)}") as b:
        read_until(b, "presence")
        # Alice adds a card over plain REST...
        client.post(f"/lists/{lst['id']}/cards", json={"title": "Live!"}, headers=alice)
        # ...and Bob's open socket receives the updated board
        update = read_until(b, "board")
        assert update["board"]["lists"][0]["cards"][0]["title"] == "Live!"


def test_board_deleted_is_broadcast(client):
    alice, bob, board, lst = shared_board(client)
    with client.websocket_connect(f"/ws/boards/{board['id']}?token={token_of(bob)}") as b:
        read_until(b, "presence")
        client.delete(f"/boards/{board['id']}", headers=alice)
        assert read_until(b, "board_deleted")["board_id"] == board["id"]
