import asyncio
from playwright.async_api import async_playwright

# টেস্ট করার জন্য সুনির্দিষ্ট সিঙ্গেল ওয়াচ পেজ লিংক
TEST_URL = "https://dlstreams.st/watch.php?id=51"
CHANNEL_NAME = "ABC USA"

async def test_single_link():
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=["--disable-blink-features=AutomationControlled"]
        )
        
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            viewport={"width": 1920, "height": 1080},
            device_scale_factor=1,
            locale="en-US"
        )
        
        page = await context.new_page()

        m3u8_url = None
        referer_url = "https://dlstreams.st/"

        def handle_request(request):
            nonlocal m3u8_url, referer_url
            req_url = request.url
            if ".m3u8" in req_url:
                print(f"[Network Request]: {req_url}")
                if "index.m3u8" in req_url:
                    m3u8_url = req_url
                    referer_url = request.headers.get("referer", "https://dlstreams.st/")

        page.on("request", handle_request)

        print(f"টেস্ট করা হচ্ছে (Testing): {TEST_URL}")
        try:
            await page.goto(TEST_URL, timeout=30000, wait_until="networkidle")
            
            for i in range(10):
                if m3u8_url:
                    break
                print(f"Waiting for index.m3u8... ({i+1}s)")
                await asyncio.sleep(1)
                
        except Exception as e:
            print(f"Error loading page: {e}")

        await browser.close()

        if m3u8_url:
            stream_link = f"{m3u8_url}|Referer={referer_url}"
            print("\n[✔] সফলভাবে আসল index.m3u8 লিংক পাওয়া গেছে!")
            print(f"Final Stream Link: {stream_link}")

            # সরাসরি playlist.m3u ফাইলে আউটপুট লেখার কোড
            playlist_content = "#EXTM3U\n"
            playlist_content += f'#EXTINF:-1 tvg-id="" tvg-name="{CHANNEL_NAME}" group-title="DaddyLive",{CHANNEL_NAME}\n'
            playlist_content += f'#EXTVLCOPT:http-referrer={referer_url}\n'
            playlist_content += f"{stream_link}\n"

            with open("playlist.m3u", "w", encoding="utf-8") as f:
                f.write(playlist_content)
            
            print("[✔] সফলভাবে 'playlist.m3u' ফাইল তৈরি এবং সেভ করা হয়েছে!")
        else:
            print("\n[✘] এই লিংকে index.m3u8 পাওয়া যায়নি। ফলে ফাইল তৈরি হয়নি।")

if __name__ == "__main__":
    asyncio.run(test_single_link())
