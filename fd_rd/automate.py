import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        # Launch the browser
        browser = await p.chromium.launch(headless=False)  # Set headless=True for non-UI mode
        context = await browser.new_context()
        page = await context.new_page()

        # Navigate to the Fixed Deposit page
        print("Navigating to the Fixed Deposit page...")
        await page.goto("https://www.bankofbaroda.in/personal-banking/accounts/term-deposit/fixed-deposit", timeout=60000)

        # Wait for the page to load
        await page.wait_for_load_state("domcontentloaded")

        # Find all "Know More" buttons
        print("Finding all 'Know More' buttons...")
        know_more_buttons = await page.locator("text=Know More").all()

        print(f"Found {len(know_more_buttons)} 'Know More' buttons.")

        # Iterate through each "Know More" button
        for i, button in enumerate(know_more_buttons):
            print(f"Clicking on 'Know More' button {i + 1}...")
            # Click the button
            await button.click()

            # Wait for the new page to load
            await page.wait_for_load_state("domcontentloaded")

            # Extract the rates or relevant information
            print(f"Extracting rates from page {i + 1}...")
            rates = await page.locator("css=selector-for-rates").all_inner_texts()  # Replace with the correct selector
            print(f"Rates on page {i + 1}: {rates}")

            # Go back to the main page
            await page.go_back()
            await page.wait_for_load_state("domcontentloaded")

        # Close the browser
        await browser.close()

# Run the script
asyncio.run(main())