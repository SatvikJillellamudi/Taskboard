from tests.conftest import make_user


def setup_board(client, headers):
    board = client.post("/boards", json={"name": "Sprint 1"}, headers=headers).json()
    todo = client.post(f"/boards/{board['id']}/lists", json={"title": "To do"}, headers=headers).json()
    done = client.post(f"/boards/{board['id']}/lists", json={"title": "Done"}, headers=headers).json()
    return board, todo, done


def test_full_board_flow(client):
    h = make_user(client)
    board, todo, done = setup_board(client, h)
    c1 = client.post(f"/lists/{todo['id']}/cards", json={"title": "Write API"}, headers=h).json()
    c2 = client.post(f"/lists/{todo['id']}/cards", json={"title": "Write tests"}, headers=h).json()
    assert (c1["position"], c2["position"]) == (1, 2)  # appended in order

    detail = client.get(f"/boards/{board['id']}", headers=h).json()
    assert [l["title"] for l in detail["lists"]] == ["To do", "Done"]
    assert [c["title"] for c in detail["lists"][0]["cards"]] == ["Write API", "Write tests"]


def test_move_card_between_lists(client):
    h = make_user(client)
    board, todo, done = setup_board(client, h)
    card = client.post(f"/lists/{todo['id']}/cards", json={"title": "Ship it"}, headers=h).json()
    r = client.patch(f"/cards/{card['id']}", json={"list_id": done["id"]}, headers=h)
    assert r.status_code == 200 and r.json()["list_id"] == done["id"]
    detail = client.get(f"/boards/{board['id']}", headers=h).json()
    assert detail["lists"][0]["cards"] == []
    assert detail["lists"][1]["cards"][0]["title"] == "Ship it"


def test_reorder_with_fractional_position(client):
    h = make_user(client)
    board, todo, _ = setup_board(client, h)
    a = client.post(f"/lists/{todo['id']}/cards", json={"title": "A"}, headers=h).json()
    b = client.post(f"/lists/{todo['id']}/cards", json={"title": "B"}, headers=h).json()
    # drag B above A: give it a position before A's
    client.patch(f"/cards/{b['id']}", json={"position": 0.5}, headers=h)
    cards = client.get(f"/boards/{board['id']}", headers=h).json()["lists"][0]["cards"]
    assert [c["title"] for c in cards] == ["B", "A"]


def test_other_users_cannot_see_board(client):
    alice = make_user(client)
    bob = make_user(client, email="bob@example.com", name="Bob")
    board, todo, _ = setup_board(client, alice)
    card = client.post(f"/lists/{todo['id']}/cards", json={"title": "secret"}, headers=alice).json()
    # 404, not 403: don't reveal the board exists
    assert client.get(f"/boards/{board['id']}", headers=bob).status_code == 404
    assert client.patch(f"/cards/{card['id']}", json={"title": "hacked"}, headers=bob).status_code == 404
    assert client.get("/boards", headers=bob).json() == []


def test_sharing_grants_access_but_not_ownership(client):
    alice = make_user(client)
    bob = make_user(client, email="bob@example.com", name="Bob")
    board, _, _ = setup_board(client, alice)
    r = client.post(f"/boards/{board['id']}/members", json={"email": "bob@example.com"}, headers=alice)
    assert r.status_code == 201
    assert client.get(f"/boards/{board['id']}", headers=bob).status_code == 200
    assert [b["id"] for b in client.get("/boards", headers=bob).json()] == [board["id"]]
    # members can edit but not delete the board or invite others
    assert client.delete(f"/boards/{board['id']}", headers=bob).status_code == 403
    assert client.post(f"/boards/{board['id']}/members", json={"email": "x@example.com"},
                       headers=bob).status_code == 403


def test_cannot_move_card_to_another_board(client):
    h = make_user(client)
    _, todo, _ = setup_board(client, h)
    _, other_list, _ = setup_board(client, h)
    card = client.post(f"/lists/{todo['id']}/cards", json={"title": "x"}, headers=h).json()
    r = client.patch(f"/cards/{card['id']}", json={"list_id": other_list["id"]}, headers=h)
    assert r.status_code == 400


def test_delete_board_cascades(client):
    h = make_user(client)
    board, todo, _ = setup_board(client, h)
    card = client.post(f"/lists/{todo['id']}/cards", json={"title": "x"}, headers=h).json()
    assert client.delete(f"/boards/{board['id']}", headers=h).status_code == 204
    assert client.get(f"/boards/{board['id']}", headers=h).status_code == 404
    assert client.delete(f"/cards/{card['id']}", headers=h).status_code == 404  # card gone too
