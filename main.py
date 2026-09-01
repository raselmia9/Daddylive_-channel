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

        # পাওয়া সব লিংকগুলো জমা রাখার জন্য লিস্ট
        captured_links = []

        def handle_request(request):
            req_url = request.url
            # .m3u8 বা স্ট্রিম সম্পর্কিত যত লিংক নেটওয়ার্কে আসবে সব ক্যাচ করা হবে
            if ".m3u8" in req_url or "playlist" in req_url or "manifest" in req_url:
                referer = request.headers.get("referer", "https://dlstreams.st/")
                full_link = f"{req_url}|Referer={referer}"
                if full_link not in captured_links:
                    captured_links.append(full_link)
                    print(f"[Captured Link]: {full_link}")

        page.on("request", handle_request)

        print(f"টেস্ট করা হচ্ছে (Testing): {TEST_URL}")
        try:
            # পেজ লোড করা
            await page.goto(TEST_URL, timeout=30000, wait_until="networkidle")
            
            # পেজে ৩০ সেকেন্ড অপেক্ষা করা এবং প্রতি সেকেন্ডে প্রোগ্রেস দেখানো
            print("পেজ লোড হয়েছে। ৩০ সেকেন্ড অপেক্ষা করা হচ্ছে...")
            for i in range(30):
                await asyncio.sleep(1)
                if (i + 1) % 5 == 0:
                    print(f"অপেক্ষা করা হয়েছে: {i + 1} সেকেন্ড...")
                
        except Exception as e:
            print(f"Error loading page: {e}")

        await browser.close()

        # ফলাফল আউটপুট ও ফাইল তৈরি করা
        if captured_links:
            print(f"\n[✔] সফলভাবে মোট {len(captured_links)} টি লিংক পাওয়া গেছে!")
            
            playlist_content = "#EXTM3U\n"
            for idx, link in enumerate(captured_links, 1):
                custom_name = f"{CHANNEL_NAME} [{idx}]"
                playlist_content += f'#EXTINF:-1 tvg-id="" tvg-name="{custom_name}" group-title="DaddyLive",{custom_name}\n'
                playlist_content += f"{link}\n"

            with open("playlist.m3u", "w", encoding="utf-8") as f:
                f.write(playlist_content)
            
            print("[✔] সফলভাবে সব লিংক নিয়ে 'playlist.m3u' ফাইল তৈরি করা হয়েছে!")
        else:
            print("\n[✘] ৩০ সেকেন্ডের মধ্যে কোনো লিংক পাওয়া যায়নি।")

if __name__ == "__main__":
    asyncio.run(test_single_link())
