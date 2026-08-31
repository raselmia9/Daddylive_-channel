import asyncio
import sys
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright
# sync_playwright এর পরিবর্তে আমরা প্লেলাইটের অ্যাসিনক্রোনাস ভার্সন দিয়েই প্রথম কাজ করব

URL = "https://dlstreams.st/24-7-channels.php"

# ধাপ ১: অ্যাসিনক্রোনাসভাবে মূল পেজ থেকে চ্যানেল এবং ওয়াচ পেজের লিংকগুলো সংগ্রহ করা
async def fetch_watch_links(browser):
    print("[1/3] DaddyLive পেজ থেকে চ্যানেল এবং ওয়াচ পেজের লিংক সংগ্রহ করা হচ্ছে...")
    channels = []
    try:
        page = await browser.new_page()
        await page.goto(URL, timeout=60000)
        await page.wait_for_timeout(4000)
        
        content = await page.content()
        await page.close()
        
        soup = BeautifulSoup(content, 'html.parser')
        cards = soup.find_all('a')
        
        for card in cards:
            href = card.get('href')
            text = card.get_text(separator="|", strip=True)
            
            if href and text:
                if href.startswith('/'):
                    href = "https://dlstreams.st" + href
                
                if "stream" in href or "watch" in href or "id=" in href:
                    parts = text.split('|')
                    channel_name = parts[0] if len(parts) > 0 else "Unknown Channel"
                    channels.append({"name": channel_name, "url": href})

    except Exception as e:
        print(f"Error fetching main page: {e}")
        return []

    unique_channels = [dict(t) for t in {tuple(d.items()) for d in channels}]
    print(f"[✔] মোট {len(unique_channels)} টি ওয়াচ পেজ পাওয়া গেছে।")
    return unique_channels

# ধাপ ২: নির্দিষ্ট ওয়াচ পেজ থেকে .m3u8 লিংক ও রেফারার বের করা
async def fetch_m3u8_stream(browser, channel_info):
    name = channel_info["name"]
    url = channel_info["url"]

    page = await browser.new_page()
    
    await page.route("**/*.{png,jpg,jpeg,gif,css,svg}", lambda route: route.abort())
    page.on("popup", lambda popup: popup.close())

    m3u8_url = None
    referer_url = "https://dlstreams.st/"

    def handle_request(request):
        nonlocal m3u8_url, referer_url
        if ".m3u8" in request.url:
            m3u8_url = request.url
            headers = request.headers
            referer_url = headers.get("referer", "https://dlstreams.st/")

    page.on("request", handle_request)

    try:
        await page.goto(url, timeout=30000, wait_until="domcontentloaded")
        
        for _ in range(10):
            if m3u8_url:
                break
            await asyncio.sleep(1)

    except Exception as e:
        print(f"Error for {name}: {e}")
    finally:
        await page.close()

    if m3u8_url:
        stream_link = f"{m3u8_url}|Referer={referer_url}"
        print(f"Success: {name}")
        return name, stream_link
    else:
        print(f"Failed: {name} (Link not found)")
        return name, None

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        
        # ১. মূল পেজ থেকে লিংকগুলো তুলে নেওয়া
        channels = await fetch_watch_links(browser)
        if not channels:
            print("কোনো চ্যানেল পাওয়া যায়নি!")
            await browser.close()
            return

        print("[2/3] মাল্টি-ট্যাব ব্যবহার করে স্ট্রিমিং পেজ থেকে .m3u8 লিংক ক্যাপচার করা হচ্ছে...")
        
        # ২. মাল্টি-ট্যাবের মাধ্যমে সব চ্যানেল প্রসেস করা
        tasks = [fetch_m3u8_stream(browser, ch) for ch in channels]
        results = await asyncio.gather(*tasks)
        
        await browser.close()

    print("[3/3] চূড়ান্ত playlist.m3u ফাইল তৈরি করা হচ্ছে...")
    
    playlist_content = "#EXTM3U\n"
    success_count = 0

    for name, stream_link in results:
        if stream_link:
            playlist_content += f'#EXTINF:-1 tvg-chno="" tvg-name="{name}" group-title="DaddyLive",{name}\n'
            playlist_content += f"{stream_link}\n"
            success_count += 1

    file_name = "playlist.m3u"
    with open(file_name, "w", encoding="utf-8") as f:
        f.write(playlist_content)

    print(f"[✔] কাজ শেষ! মোট {success_count} টি সচল স্ট্রিম নিয়ে '{file_name}' সফলভাবে তৈরি হয়েছে।")

if __name__ == "__main__":
    asyncio.run(main())
