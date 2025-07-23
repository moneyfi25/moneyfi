import os
from playwright.sync_api import Playwright, sync_playwright


def run(playwright: Playwright) -> None:
    def select_and_download(cat: str,subcat: str):

        # Create a downloads folder inside current directory
        download_dir = os.path.join(os.getcwd(), "downloads")
        os.makedirs(download_dir, exist_ok=True)

        browser = playwright.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()
        page.goto("https://www.amfiindia.com/research-information/other-data/mf-scheme-performance-details")
        page.wait_for_timeout(3000)  # Allow time for Angular to bootstrap
        page.locator("iframe").content_frame.locator(".ng-arrow-wrapper").first.click()
        page.locator("iframe").content_frame.get_by_title("Open Ended").click()



        page.locator("iframe").content_frame.locator("div:nth-child(2) > .pull-left > .ng-select-container > .ng-arrow-wrapper").click()
        page.wait_for_timeout(100)
        page.locator("iframe").content_frame.get_by_title(cat).click()
        page.wait_for_timeout(100)
        page.locator("iframe").content_frame.get_by_role("listbox").filter(has_text="Sub Category").locator("div").nth(3).click()
        page.locator("iframe").content_frame.get_by_role("option",name=subcat,exact=True).click()
        page.wait_for_timeout(100)
        page.locator("iframe").content_frame.locator("div:nth-child(4) > .pull-left > .ng-select-container > .ng-arrow-wrapper").click()
        page.locator("iframe").content_frame.get_by_role("option", name="All").click()
        page.wait_for_timeout(100)
        page.locator("iframe").content_frame.get_by_role("button", name="Go").click()


            # Download 1: Long Duration
        with page.expect_download() as download_info:
            page.locator("iframe").content_frame.locator("img").click()
            download = download_info.value
            filename = subcat.replace(" / ", "_").replace(" & ", "_").replace(" ", "_") + ".xlsx"
            path1 = os.path.join(download_dir, filename)
            download.save_as(path1)
        context.close()
        browser.close()

    def get_subcategories(cat: str):
        browser = playwright.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()
        page.goto("https://www.amfiindia.com/research-information/other-data/mf-scheme-performance-details")
        page.wait_for_timeout(2000)  # Allow time for Angular to bootstrap
        page.locator("iframe").content_frame.locator(".ng-arrow-wrapper").first.click()
        page.locator("iframe").content_frame.get_by_title("Open Ended").click()
    
# ✅ Select Asset Class: Equity
        page.locator("iframe").content_frame.locator("div:nth-child(2) > .pull-left > .ng-select-container > .ng-arrow-wrapper").click()
        page.locator("iframe").content_frame.get_by_title(cat).click()

        page.locator("iframe").content_frame.get_by_role("listbox").filter(has_text="Sub Category").locator("div").nth(3).click()
        page.wait_for_timeout(300)
        subcategories = page.locator("iframe").content_frame.locator("div.ng-option span[title]")
        count = subcategories.count()
        subcategory_names = [subcategories.nth(i).get_attribute("title") for i in range(count)]
        print(f"\n📋 Found {len(subcategory_names)} subcategories:\n", subcategory_names)
        
        context.close()
        browser.close()
        return subcategory_names
    categories = "Equity" # update this to the desired category(Equity, Debt, Hybrid,Solution Oriented, Other etc.)
    subcategories = get_subcategories(categories)
    for subcat in subcategories:
        print(f"\n🔍 Downloading data for subcategory: {subcat}")
        select_and_download(categories,subcat)
with sync_playwright() as playwright:
    run(playwright)
