import json
import os
import asyncio
from datetime import datetime, timedelta
from playwright.async_api import async_playwright
import httpx

TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
TELEGRAM_CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]

async def send_telegram(message: str):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    async with httpx.AsyncClient() as client:
        await client.post(url, json={
            "chat_id": TELEGRAM_CHAT_ID,
            "text": message,
            "parse_mode": "HTML"
        })

def get_dates_for_months(months: list[int], min_nights: int, max_nights: int):
    """Generate (outbound, return) date pairs for given months."""
    year = datetime.now().year
    pairs = []
    for month in months:
        # start from today or month start, whichever is later
        month_start = datetime(year, month, 1)
        start = max(month_start, datetime.now() + timedelta(days=7))
        # end of month
        if month == 12:
            month_end = datetime(year + 1, 1, 1) - timedelta(days=1)
        else:
            month_end = datetime(year, month + 1, 1) - timedelta(days=1)
        
        d = start
        while d <= month_end:
            for nights in range(min_nights, max_nights + 1):
                ret = d + timedelta(days=nights)
                if ret <= month_end:
                    pairs.append((d.strftime("%Y-%m-%d"), ret.strftime("%Y-%m-%d")))
            d += timedelta(days=1)
    return pairs

async def scrape_google_flights(page, origin: str, destination: str, date_out: str, date_ret: str) -> list[dict]:
    """Scrape Google Flights for a specific route and dates."""
    dest_param = "" if destination == "ANYWHERE" else destination
    
    # Google Flights URL format
    url = (
        f"https://www.google.com/travel/flights?"
        f"q=voli+da+{origin}+a+{dest_param if dest_param else 'ovunque'}"
        f"&curr=EUR"
    )
    
    # For structured scraping, use the direct flights URL
    if dest_param:
        url = (
            f"https://www.google.com/travel/flights/search?"
            f"tfs=CBwQAhoeEgoyMDI0LTA2LTAxagcIARIDTUlMcgcIARIDTUlM"
        )
        # Build proper URL
        url = (
            f"https://www.google.com/travel/flights?"
            f"q=flights+from+{origin}+to+{dest_param}+on+{date_out}+returning+{date_ret}"
            f"&curr=EUR&hl=it"
        )
    
    results = []
    
    try:
        await page.goto(url, wait_until="networkidle", timeout=30000)
        await page.wait_for_timeout(3000)
        
        # Accept cookies if present
        try:
            accept_btn = page.locator('button:has-text("Accetta tutto"), button:has-text("Accept all")')
            if await accept_btn.count() > 0:
                await accept_btn.first.click()
                await page.wait_for_timeout(2000)
        except:
            pass
        
        # Extract flight prices
        price_elements = page.locator('[data-gs], .YMlIz, .U3gSDe')
        count = await price_elements.count()
        
        for i in range(min(count, 10)):
            try:
                el = price_elements.nth(i)
                text = await el.inner_text()
                # Look for price patterns like "€45" or "45 €"
                import re
                prices = re.findall(r'€\s*(\d+)', text)
                if prices:
                    price = int(prices[0])
                    results.append({
                        "origin": origin,
                        "destination": dest_param or "vario",
                        "date_out": date_out,
                        "date_ret": date_ret,
                        "price": price,
                        "url": page.url
                    })
                    break
            except:
                continue
                
    except Exception as e:
        print(f"Error scraping {origin}->{destination} {date_out}: {e}")
    
    return results

async def main():
    with open("searches.json") as f:
        searches = json.load(f)
    
    found_deals = []
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-dev-shm-usage"]
        )
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            locale="it-IT",
            extra_http_headers={"Accept-Language": "it-IT,it;q=0.9"}
        )
        page = await context.new_page()
        
        for search in searches:
            origins = search["origins"]
            destination = search["destination"]
            max_price = search["max_price_eur"]
            min_nights = search["min_nights"]
            max_nights = search["max_nights"]
            months = search["months"]
            
            date_pairs = get_dates_for_months(months, min_nights, max_nights)
            print(f"Checking {len(date_pairs)} date pairs for {origins} -> {destination}")
            
            for origin in origins:
                for date_out, date_ret in date_pairs[:30]:  # limit to avoid ban
                    results = await scrape_google_flights(
                        page, origin, destination, date_out, date_ret
                    )
                    for r in results:
                        if r["price"] <= max_price:
                            found_deals.append(r)
                    
                    await asyncio.sleep(2)  # polite delay
        
        await browser.close()
    
    # Send Telegram notifications
    if found_deals:
        msg = "✈️ <b>Offerte voli trovate!</b>\n\n"
        for deal in found_deals[:10]:  # max 10 per messaggio
            msg += (
                f"🛫 <b>{deal['origin']} → {deal['destination']}</b>\n"
                f"📅 {deal['date_out']} → {deal['date_ret']}\n"
                f"💶 <b>€{deal['price']}</b>\n"
                f"🔗 <a href='{deal['url']}'>Apri Google Flights</a>\n\n"
            )
        await send_telegram(msg)
        print(f"Sent {len(found_deals)} deals to Telegram")
    else:
        print("No deals found under budget")

if __name__ == "__main__":
    asyncio.run(main())
