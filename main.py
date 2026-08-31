import sys
import asyncio
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
from playwright.async_api import async_playwright as async_p

# টার্গেট ওয়েবসাইট লিংক
URL = "https://dlstreams.st/24-7-channels.php"

def get_channels_from_website():
    print("[1/3] DaddyLive পেজ থেকে চ্যানেল এবং ওয়াচ পেজের লিংক সংগ্রহ করা হচ্ছে...")
    channels = []
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            
            # পেজে যাওয়া এবং লোড হওয়ার জন্য অপেক্ষা করা
            page.goto(URL, timeout=60000)
            page.wait_for_timeout(4000)
            
            soup = BeautifulSoup(page.content(), 'html.parser')
            browser.close()

        # চ্যানেল কার্ড বা লিংক ফিল্টার করা
        cards = soup.find_all('a')
        for card in cards:
            href = card.get('href')
            text = card.get_text(separator="|", strip=True)
            
            if href and text:
                if href.startswith('/'):
                    href = "https://dlstreams.st" + href
                
                # ওয়াচ পেজ বা স্ট্রিম লিংক ফিল্টার করা
                if "stream" in href or "watch" in href or "id=" in href:
                    parts = text.split('|')
                    channel_name = parts[0] if len(parts) > 0 else "Unknown Channel"
                    channels.append({"name": channel_name, "url": href, "logo": ""})

    except Exception as e:
        print(f"Error fetching channel list: {e}")
        sys.exit(1)

    # ডুপ্লিকেট বাদ দেওয়া
    unique_channels = [dict(t) for t in {tuple(d.items()) for d in channels}]
    print(f"[✔] মোট {len(unique_channels)} টি চ্যানেল পাওয়া গেছে।")
    return unique_channels

async def fetch_m3u8_link(channel):
    name = channel.get("name")
    url = channel.get("url")
    logo = channel.get("logo", "")

    async with async_p() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()

        # পেজের গতি বাড়ানোর জন্য ইমেজ, অ্যাডস ও সিএসএস ব্লক করা
        await page.route("**/*.{png,jpg,jpeg,gif,css,svg}", lambda route: route.abort())

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
            # পেজ ভিজিট করা
            await page.goto(url, timeout=30000)
            
            # m3u8 লিংক পাওয়ার জন্য সর্বোচ্চ ১০ সেকেন্ড অপেক্ষা করা
            for _ in range(10):
                if m3u8_url:
                    break
                await asyncio.sleep(1)

        except Exception as e:
            pass # কোনো ত্রুটি হলে স্কিপ করবে

        await browser.close()

        if m3u8_url:
            stream_link = f"{m3u8_url}|Referer={referer_url}"
            return name, logo, stream_link
        return name, logo, None

async def process_all_channels(channels):
    print("[2/3] প্রতিটি চ্যানেলের পেজ থেকে m3u8 স্ট্র্রিমিং লিংক খোঁজা হচ্ছে...")
    tasks = [fetch_m3u8_link(ch) for ch in channels]
    results = await asyncio.gather(*tasks)
    return results

def generate_playlist():
    # ধাপ ১: ওয়েবসাইট থেকে চ্যানেল লিস্ট সংগ্রহ
    channels = get_channels_from_website()
    if not channels:
        print("কোনো চ্যানেল পাওয়া যায়নি!")
        return

    # ধাপ ২: অ্যাসিনক্রোনাসভাবে প্রতিটি চ্যানেল থেকে m3u8 লিংক বের করা
    results = asyncio.run(process_all_channels(channels))

    print("[3/3] playlist.m3u ফাইল তৈরি করা হচ্ছে...")
    playlist_content = "#EXTM3U\n"
    success_count = 0

    for name, logo, stream_link in results:
        if stream_link:
            playlist_content += f'#EXTINF:-1 tvg-id="" tvg-name="{name}" tvg-logo="{logo}" group-title="DaddyLive",{name}\n'
            playlist_content += f'#EXTVLCOPT:http-referrer=https://dlstreams.st/\n'
            playlist_content += f"{stream_link}\n"
            success_count += 1
            print(f"Success: {name}")
        else:
            print(f"Failed: {name} (Link not found)")

    # ফাইল সেভ করা
    file_name = "playlist.m3u"
    with open(file_name, "w", encoding="utf-8") as f:
        f.write(playlist_content)

    print(f"\n[✔] সফলভাবে কাজ সম্পন্ন হয়েছে! মোট {success_count} টি সচল চ্যানেলের লিংক নিয়ে '{file_name}' তৈরি করা হয়েছে।")

if __name__ == "__main__":
    generate_playlist()
