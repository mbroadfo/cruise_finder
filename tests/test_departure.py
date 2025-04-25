from playwright.sync_api import sync_playwright

def inspect_cabins(departure_url: str):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()

        print(f"Navigating to {departure_url}...")
        page.goto(departure_url, timeout=60000)

        # Try dismissing the cookie popup
        try:
            ok_button = page.locator("button[data-style='button']", has_text="Ok")
            ok_button.wait_for(state="visible", timeout=10000)
            ok_button.scroll_into_view_if_needed()
            ok_button.click(timeout=5000)
            print("✅ Dismissed cookie banner.")
        except Exception as e:
            print(f"⚠️ Cookie banner not found or already dismissed: {e}")

        category_buttons = page.locator("button:has-text('See available cabins')")
        print(f"Found {category_buttons.count()} category buttons.")

        all_cabins = []

        for i in range(category_buttons.count()):
            button = category_buttons.nth(i)
            try:
                button.scroll_into_view_if_needed()
                button.click()
                print(f"✅ Opened drawer for category {i+1}")

                page.wait_for_timeout(4000)  # Increased wait time to allow cabin cards to render
                page.wait_for_selector("[data-testid='cabin-card']", timeout=15000)

                cabin_cards = page.locator("[data-testid='cabin-card']")
                cabin_texts = cabin_cards.all_inner_texts()
                print(f"Cabin card: {cabin_texts}")
                all_cabins.append(cabin_texts)
            except Exception as e:
                print(f"⚠️ Issue loading cabin cards for category {i+1}: {e}")

            try:
                close_button = page.locator("button[data-variant='text'][data-style='link']")
                if close_button.count() > 0:
                    close_button.first.click()
                    print("🔒 Closed drawer")
                    page.wait_for_timeout(1000)
            except Exception as e:
                print(f"⚠️ Failed to close drawer for category {i+1}: {e}")

        print("\n--- Summary ---")
        for cabin in all_cabins:
            print(cabin)

        browser.close()

if __name__ == "__main__":
    inspect_cabins("https://www.expeditions.com/book/cabins?departure=DLAMAZ-250809&productType=AMAZ&c=eyJnIjoiIn0%3D")
