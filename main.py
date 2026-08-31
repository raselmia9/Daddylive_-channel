import asyncio
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright

URL = "https://dlstreams.st/24-7-channels.php"

async def process_single_channel(browser, channel_info):
    page = await browser.new_page()
    page.on("popup", lambda popup: popup.close())
    
    captured_data = None
    
    async def handle_request(route):
        nonlocal captured_data
        url = route.request.url
        if ".m3u8" in url:
            headers = route.request.headers
            referer = headers.get("referer", "https://dlstreams.st/")
            captured_data = f"{url}|Referer={referer}"
        await route.continue_()

    await page.route("**/*", handle_request)
    
    try:
        await page.goto(channel_info["url"], timeout=30000, wait_until="domcontentloaded")
        for _ in range(10):
            if captured_data:
                break
            await asyncio.sleep(1)
    except Exception as e:
        print(f"Error on {channel_info['title']}: {e}")
    finally:
        await page.close()
        
    return captured_data

async def main():
    print("[1/3] পেজ থেকে চ্যানেল এবং ওয়াচ লিংক সংগ্রহ করা হচ্ছে...")
    channels = []
    
    async with async_playwright() as p:
        # এখানে await যুক্ত করা হয়েছে (সংশোধিত)
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto(URL, timeout=60000)
        await page.wait_for_timeout(3000)
        
        soup = BeautifulSoup(await page.content(), 'html.parser')
        await browser.close()

    cards = soup.find_all('a')
    for card in cards:
        href = card.get('href')
        text = card.get_text(separator="|", strip=True)
        if href and text:
            if href.startswith('/'):
                href = "https://dlstreams.st" + href
            if "stream" in href or "watch" in href or "id=" in href:
                parts = text.split('|')
                name = parts[0] if len(parts) > 0 else "Unknown Channel"
                channels.append({"title": name, "url": href})

    unique_channels = [dict(t) for t in {tuple(d.items()) for d in channels}]
    print(f"[✔] মোট {len(unique_channels)} টি চ্যানেল পাওয়া গেছে। মাল্টি-ট্যাব দিয়ে লিংক ক্যাপচার শুরু হচ্ছে...")

    results = []
    async with async_playwright() as p:
        # এখানেও await যুক্ত করা হয়েছে (সংশোধিত)
        browser = await p.chromium.launch(headless=True)
        
        # প্রথম ২০টি চ্যানেল নিয়ে মাল্টি-ট্যাব টেস্ট (প্রয়োজনে সংখ্যা বাড়াতে পারেন)
        tasks = [process_single_channel(browser, ch) for ch in unique_channels[:20]]
        completed = await asyncio.gather(*tasks)
        
        for res in completed:
            if res:
                results.append(res)
                
        await browser.close()

    print(f"[2/3] মোট {len(results)} টি স্ট্রিম লিংক সফলভাবে ক্যাপচার হয়েছে।")
    
    print("[3/3] playlist.m3u ফাইল তৈরি করা হচ্ছে...")
    m3u_content = "#EXTM3U\n"
    for item in results:
        parts = item.split("|Referer=")
        stream_url = parts[0]
        referer_url = parts[1] if len(parts) > 1 else "https://dlstreams.st/"
        
        m3u_content += f"#EXTINF:-1,Channel\n"
        m3u_content += f"{stream_url}|Referer={referer_url}\n"

    with open("playlist.m3u", "w", encoding="utf-8") as f:
        f.write(m3u_content)

    print("[✔] সফলভাবে 'playlist.m3u' তৈরি হয়ে গেছে!")

if __name__ == "__main__":
    asyncio.run(main())
