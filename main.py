import asyncio
from playwright.async_api import async_playwright

# টেস্ট করার জন্য সুনির্দিষ্ট সিঙ্গেল ওয়াচ পেজ লিংক
TEST_URL = "https://dlstreams.st/watch.php?id=51"

async def test_single_link():
    async with async_playwright() as p:
        # ব্রাউজার লঞ্চ করার সময় বট সিগনেচার লুকানোর জন্য অতিরিক্ত আর্গুমেন্ট যুক্ত করা হয়েছে
        browser = await p.chromium.launch(
            headless=True,
            args=["--disable-blink-features=AutomationControlled"]
        )
        
        # একদম রিয়েল ক্রোম ব্রাউজারের মতো ইউজার-এজেন্ট, ভিউপোর্ট ও এনভায়রনমেন্ট সেট করা
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            viewport={"width": 1920, "height": 1080},
            device_scale_factor=1,
            locale="en-US"
        )
        
        page = await context.new_page()

        # কোনো রিসোর্স ব্লক করা হয়নি, সব HTML, CSS, JS স্বাভাবিকভাবে লোড হবে

        m3u8_url = None
        referer_url = "https://dlstreams.st/"

        def handle_request(request):
            nonlocal m3u8_url, referer_url
            req_url = request.url
            # পেজের নেটওয়ার্ক রিকোয়েস্ট থেকে সরাসরি index.m3u8 ফিল্টার করা
            if ".m3u8" in req_url:
                print(f"[Network Request]: {req_url}")
                if "index.m3u8" in req_url:
                    m3u8_url = req_url
                    referer_url = request.headers.get("referer", "https://dlstreams.st/")

        page.on("request", handle_request)

        print(f"테স্ট করা হচ্ছে (Testing): {TEST_URL}")
        try:
            # পেজ পুরোপুরি লোড হওয়ার জন্য networkidle ব্যবহার করা হয়েছে
            await page.goto(TEST_URL, timeout=30000, wait_until="networkidle")
            
            # লিংক ক্যাচ করার জন্য সর্বোচ্চ ১০ সেকেন্ড অপেক্ষা
            for i in range(10):
                if m3u8_url:
                    break
                print(f"Waiting for index.m3u8... ({i+1}s)")
                await asyncio.sleep(1)
                
        except Exception as e:
            print(f"Error loading page: {e}")

        await browser.close()

        if m3u8_url:
            print("\n[✔] সফলভাবে আসল index.m3u8 লিংক পাওয়া গেছে!")
            print(f"Final Stream Link: {m3u8_url}|Referer={referer_url}")
        else:
            print("\n[✘] এই লিংকে index.m3u8 পাওয়া যায়নি।")

if __name__ == "__main__":
    asyncio.run(test_single_link())
