import asyncio
from playwright.async_api import async_playwright

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

        # পাওয়াসব লিংকগুলো জমা রাখার জন্য একটি লিস্ট
        captured_links = []

        def handle_request(request):
            req_url = request.url
            # .m3u8 বা স্ট্রিম সম্পর্কিত যত লিংক পাওয়া যাবে সব ক্যাচ করা হবে
            if ".m3u8" in req_url or "playlist" in req_url:
                referer = request.headers.get("referer", "https://dlstreams.st/")
                full_link = f"{req_url}|Referer={referer}"
                if full_link not in captured_links:
                    captured_links.append(full_link)
                    print(f"[Captured Link]: {full_link}")

        page.on("request", handle_request)

        print(f"টেস্ট করা হচ্ছে (Testing): {TEST_URL}")
        try:
            await page.goto(TEST_URL, timeout=30000, wait_until="networkidle")
            
            # লিংকগুলো আসার জন্য ৮ সেকেন্ড অপেক্ষা করা
            for i in range(8):
                await asyncio.sleep(1)
                
        except Exception as e:
            print(f"Error loading page: {e}")

        await browser.close()

        if captured_links:
            print(f"\n[✔] মোট {len(captured_links)} টি লিংক পাওয়া গেছে!")
            
            # সব লিংক দিয়ে playlist.m3u তৈরি করা
            playlist_content = "#EXTM3U\n"
            for idx, link in enumerate(captured_links, 1):
                custom_name = f"{CHANNEL_NAME} [{idx}]"
                playlist_content += f'#EXTINF:-1 tvg-id="" tvg-name="{custom_name}" group-title="DaddyLive",{custom_name}\n'
                playlist_content += f"{link}\n"

            with open("playlist.m3u", "w", encoding="utf-8") as f:
                f.write(playlist_content)
            
            print("[✔] সফলভাবে সব লিংক নিয়ে 'playlist.m3u' ফাইল তৈরি করা হয়েছে!")
        else:
            print("\n[✘] কোনো লিংক পাওয়া যায়নি।")

if __name__ == "__main__":
    asyncio.run(test_single_link())
