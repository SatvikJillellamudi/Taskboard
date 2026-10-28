"""Two-user end-to-end test: real browsers, real drags, real WebSockets.

Start the backend (port 8000) and frontend (port 5173) first, then:
    python -m pip install playwright
    python -m playwright install chromium
    python e2e/test_two_users.py
Use a fresh database (delete backend/taskboard.db) so the test accounts do not already exist.
"""
import sys
from playwright.sync_api import sync_playwright, expect

WEB = "http://localhost:5173"
SHOTS = sys.argv[1] if len(sys.argv) > 1 else "."

def signup(page, name, email):
    page.goto(f"{WEB}/login")
    page.get_by_role("button", name="No account? Sign up").click()
    page.get_by_placeholder("Name").fill(name)
    page.get_by_placeholder("Email").fill(email)
    page.get_by_placeholder("Password (8+ characters)").fill("password123")
    page.get_by_role("button", name="Sign up").click()
    expect(page.get_by_role("heading", name="Your boards")).to_be_visible()

def drag(page, source, target):
    """Real mouse drag in small steps (dnd-kit needs actual pointer movement)."""
    s = source.bounding_box(); t = target.bounding_box()
    page.mouse.move(s["x"] + s["width"]/2, s["y"] + s["height"]/2)
    page.mouse.down()
    page.mouse.move(s["x"] + s["width"]/2 + 10, s["y"] + s["height"]/2, steps=5)
    page.mouse.move(t["x"] + t["width"]/2, t["y"] + t["height"]/2, steps=20)
    page.wait_for_timeout(200)
    page.mouse.up()

results = []
def check(label, fn):
    fn(); results.append(label); print("PASS", label)

with sync_playwright() as p:
    browser = p.chromium.launch()
    # two separate contexts = two separate people with separate logins
    a = browser.new_context(viewport={"width": 1280, "height": 720}).new_page()
    b = browser.new_context(viewport={"width": 1280, "height": 720}).new_page()

    signup(b, "Bob", "bob@example.com")
    signup(a, "Alice", "alice@example.com")

    a.get_by_placeholder("New board name").fill("Launch Plan")
    a.get_by_role("button", name="Create board").click()
    a.get_by_role("link", name="Launch Plan").click()
    expect(a.get_by_test_id("status")).to_have_text("Live")
    board_url = a.url

    for title in ["To do", "Done"]:
        a.get_by_placeholder("+ Add a list").fill(title)
        a.get_by_placeholder("+ Add a list").press("Enter")
        expect(a.get_by_test_id(f"list-{title}")).to_be_visible()
    todo = a.get_by_test_id("list-To do")
    for card in ["Design", "Build"]:
        todo.get_by_placeholder("+ Add a card").fill(card)
        todo.get_by_placeholder("+ Add a card").press("Enter")
        expect(a.get_by_test_id(f"card-{card}")).to_be_visible()

    # share with Bob
    a.get_by_role("button", name="Share").click()
    a.get_by_placeholder("Their account email").fill("bob@example.com")
    a.get_by_role("button", name="Invite").click()
    expect(a.get_by_text("Bob can now see this board.")).to_be_visible()
    a.get_by_role("button", name="Done").click()

    # Bob opens the shared board
    b.reload()
    check("shared board appears in Bob's list", lambda: expect(b.get_by_role("link", name="Launch Plan")).to_be_visible())
    b.goto(board_url)
    expect(b.get_by_test_id("status")).to_have_text("Live")
    check("Bob sees Alice's cards", lambda: expect(b.get_by_test_id("card-Design")).to_be_visible())
    check("presence: Alice sees 2 viewers", lambda: expect(a.get_by_test_id("presence").locator(".avatar")).to_have_count(2))

    # Alice adds a card -> appears on Bob's screen with no reload
    a.get_by_test_id("list-To do").get_by_placeholder("+ Add a card").fill("Ship it")
    a.get_by_test_id("list-To do").get_by_placeholder("+ Add a card").press("Enter")
    check("live: Alice's new card appears for Bob",
          lambda: expect(b.get_by_test_id("list-To do").get_by_test_id("card-Ship it")).to_be_visible())

    # Bob drags Design into Done -> Alice sees it move live
    drag(b, b.get_by_test_id("card-Design"), b.get_by_test_id("list-Done"))
    check("drag: card lands in Done for Bob",
          lambda: expect(b.get_by_test_id("list-Done").get_by_test_id("card-Design")).to_be_visible())
    check("live: Alice sees the card move",
          lambda: expect(a.get_by_test_id("list-Done").get_by_test_id("card-Design")).to_be_visible())

    # Bob reorders within a list: drag "Ship it" above "Build"
    drag(b, b.get_by_test_id("card-Ship it"), b.get_by_test_id("card-Build"))
    def order_ok():
        expect(a.get_by_test_id("list-To do").locator("[data-testid^=card-]")).to_have_count(2)
        titles = a.get_by_test_id("list-To do").locator(".card-title").all_inner_texts()
        assert titles == ["Ship it", "Build"], titles
    a.wait_for_timeout(800)
    check("reorder persists and syncs to Alice", order_ok)

    # persisted, not just in memory: Alice reloads and the state is still there
    a.reload()
    check("state survives a reload (stored in DB)",
          lambda: expect(a.get_by_test_id("list-Done").get_by_test_id("card-Design")).to_be_visible())

    # Bob leaves -> Alice's presence drops to 1
    b.goto(WEB)
    check("presence: Bob leaving drops Alice to 1 viewer",
          lambda: expect(a.get_by_test_id("presence").locator(".avatar")).to_have_count(1))

    b.goto(board_url); expect(b.get_by_test_id("status")).to_have_text("Live")
    a.screenshot(path=f"{SHOTS}/alice.png"); b.screenshot(path=f"{SHOTS}/bob.png")
    browser.close()

print(f"\n{len(results)} end-to-end checks passed")
