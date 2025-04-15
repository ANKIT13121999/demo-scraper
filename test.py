# import asyncio
# import csv
# import string
# from playwright.async_api import async_playwright

# HEADERS = {
#     "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
# }

# BASE_URL = "https://startupmahakumbh.org/exhibitor_directory/exhi_list_pub.php?event_name=sm&event_year=2025&filter="
# LETTERS = list(string.ascii_uppercase)  # A-Z
# OUTPUT_FILE = "exhibitors.csv"

# async def scrape_letter(page, letter, writer):
#     print(f"🔍 Scraping '{letter}'...")
#     try:
#         url = f"{BASE_URL}{letter}"
#         await page.goto(url, timeout=60000, wait_until="networkidle")
#         await page.wait_for_selector(".exhibitor-list", timeout=15000)

#         # Each exhibitor block is under .details
#         detail_blocks = await page.query_selector_all(".details")

#         for block in detail_blocks:
#             name_el = await block.query_selector("h2 a")
#             name = await name_el.inner_text() if name_el else ""

#             addr_el = await block.query_selector("p:has-text('Address:')")
#             address = await addr_el.inner_text() if addr_el else ""

#             contact_person_el = await block.query_selector("p:has-text('Contact Person:')")
#             contact_person = await contact_person_el.inner_text() if contact_person_el else ""

#             designation_el = await block.query_selector("p:has-text('Designation:')")
#             designation = await designation_el.inner_text() if designation_el else ""

#             contact_details_el = await block.query_selector("p:has-text('Contact Details:')")
#             contact_details = await contact_details_el.inner_text() if contact_details_el else ""

#             profile_el = await block.query_selector("p:has-text('Profile:')")
#             profile = await profile_el.inner_text() if profile_el else ""

#             writer.writerow([
#                 letter,
#                 name.replace("Name of the Organization:", "").strip(),
#                 address.replace("Address:", "").strip(),
#                 contact_person.replace("Contact Person:", "").strip(),
#                 designation.replace("Designation:", "").strip(),
#                 contact_details.replace("Contact Details:", "").strip(),
#                 profile.replace("Profile:", "").strip()
#             ])

#         print(f"✅ Done with '{letter}' - {len(detail_blocks)} records\n")

#     except Exception as e:
#         print(f"❌ Error scraping letter '{letter}': {e}\n")

# async def main():
#     async with async_playwright() as p:
#         browser = await p.chromium.launch(headless=True)
#         context = await browser.new_context(user_agent=HEADERS["User-Agent"])
#         page = await context.new_page()

#         with open(OUTPUT_FILE, mode="w", newline="", encoding="utf-8") as f:
#             writer = csv.writer(f)
#             writer.writerow([
#                 "Letter",
#                 "Company Name",
#                 "Address",
#                 "Contact Person",
#                 "Designation",
#                 "Contact Details",
#                 "Profile"
#             ])

#             for letter in LETTERS:
#                 await scrape_letter(page, letter, writer)
#                 await asyncio.sleep(1)  # polite pause

#         await browser.close()

# asyncio.run(main())

import asyncio
import csv
import string
import re
from playwright.async_api import async_playwright

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
}

BASE_URL = "https://startupmahakumbh.org/exhibitor_directory/exhi_list_pub.php?event_name=sm&event_year=2025&filter="
LETTERS = list(string.ascii_uppercase) + ["#"]
OUTPUT_FILE = "exhibitors.csv"

async def get_total_pages(page):
    try:
        pagination_text = await page.inner_text("div.pagination7")
        match = re.search(r"of\s+(\d+)", pagination_text)
        if match:
            return int(match.group(1))
    except:
        pass
    return 1

async def scrape_current_page(page, letter, writer):
    detail_blocks = await page.query_selector_all(".details")

    for block in detail_blocks:
        name_el = await block.query_selector("h2 a")
        name = await name_el.inner_text() if name_el else ""

        addr_el = await block.query_selector("p:has-text('Address:')")
        address = await addr_el.inner_text() if addr_el else ""

        contact_person_el = await block.query_selector("p:has-text('Contact Person:')")
        contact_person = await contact_person_el.inner_text() if contact_person_el else ""

        designation_el = await block.query_selector("p:has-text('Designation:')")
        designation = await designation_el.inner_text() if designation_el else ""

        contact_details_el = await block.query_selector("p:has-text('Contact Details:')")
        contact_details = await contact_details_el.inner_text() if contact_details_el else ""

        profile_el = await block.query_selector("p:has-text('Profile:')")
        profile = await profile_el.inner_text() if profile_el else ""

        writer.writerow([
            letter,
            name.replace("Name of the Organization:", "").strip(),
            address.replace("Address:", "").strip(),
            contact_person.replace("Contact Person:", "").strip(),
            designation.replace("Designation:", "").strip(),
            contact_details.replace("Contact Details:", "").strip(),
            profile.replace("Profile:", "").strip()
        ])

    print(f"    ✅ Scraped {len(detail_blocks)} records on current page.")

async def scrape_letter(page, letter, writer):
    print(f"\n🔠 Scraping letter '{letter}'...")
    url = f"{BASE_URL}{letter}"
    try:
        await page.goto(url, timeout=60000, wait_until="networkidle")
        await page.wait_for_selector(".exhibitor-list", timeout=15000)

        total_pages = await get_total_pages(page)
        print(f"📄 Found {total_pages} pages for letter '{letter}'")

        for page_num in range(1, total_pages + 1):
            print(f"➡️  Page {page_num}/{total_pages}...")
            await scrape_current_page(page, letter, writer)

            if page_num < total_pages:
                try:
                    await page.evaluate("gotoPage('next')")
                    await page.wait_for_timeout(1500)
                except Exception as nav_err:
                    print(f"⚠️  Pagination failed on page {page_num} of '{letter}': {nav_err}")
                    break

    except Exception as e:
        print(f"❌ Error scraping letter '{letter}': {e}")

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(user_agent=HEADERS["User-Agent"])
        page = await context.new_page()

        with open(OUTPUT_FILE, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([
                "Letter",
                "Company Name",
                "Address",
                "Contact Person",
                "Designation",
                "Contact Details",
                "Profile"
            ])

            for letter in LETTERS:
                await scrape_letter(page, letter, writer)
                await asyncio.sleep(1)  # polite pause

        await browser.close()

asyncio.run(main())


