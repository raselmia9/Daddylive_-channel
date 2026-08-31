import asyncio
import traceback
from playwright.async_api import async_playwright

async def process_single_channel(browser, channel_info):
    context = await browser.new_context(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )
    page = await context.new_page()
    page.on("popup", lambda popup: popup.close())
    
    captured_data = None
    error_log = None
    
    async def handle_request(route):
        nonlocal captured_data
        url = route.request.url
        if ".m3u8" in url or "playlist" in url:
            headers = route.request.headers
            referer = headers.get("referer", "https://dlstreams.st/")
            captured_data = f"{url}|Referer={referer}"
        await route.continue_()

    await page.route("**/*", handle_request)
    
    try:
        print(f"Opening: {channel_info['url']}")
        # পেজ লোড করার সময় timeout বা অন্য কোনো সমস্যা হলে তা ধরার জন্য
        await page.goto(channel_info["url"], timeout=35000, wait_until="domcontentloaded")
        
        for _ in range(15):
            if captured_data:
                break
            await asyncio.sleep(1)
            
        if not captured_data:
            error_log = f"Timeout: No .m3u8 request intercepted for {channel_info['title']}"
            
    except Exception as e:
        error_log = f"Exception on {channel_info['title']}: {str(e)}"
    finally:
        await context.close()
        
    return captured_data, channel_info['title'], error_log

async def main():
    print("[1/2] প্রসেস শুরু হয়েছে...")
    
    channels_to_test = [
        {"title": "CANAL+ FAMILY POLAND", "url": "https://dlstreams.st/stream/watch.php?id=567"},
        {"title": "CANAL+ SERIALE POLAND", "url": "https://dlstreams.st/stream/watch.php?id=570"}
    ]
    
    results = []
    errors = []
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-setuid-sandbox", "--disable-dev-shm-usage"]
        )
        
        tasks = [process_single_channel(browser, ch) for ch in channels_to_test]
        completed_tasks = await asyncio.gather(*tasks)
        
        for stream_data, title, err in completed_tasks:
            if stream_data:
                results.append((stream_data, title))
            if err:
                errors.append(err)
                
        await browser.close()

    print("[2/2] প্লেলিস্ট বা ইরর লগ ফাইল তৈরি করা হচ্ছে...")
    
    m3u_content = "#EXTM3U\n"
    
    # যদি সফলভাবে লিংক পাওয়া যায়, সেগুলো যোগ হবে
    if results:
        for stream_data, title in results:
            parts = stream_data.split("|Referer=")
            stream_url = parts[0]
            referer_url = parts[1] if len(parts) > 1 else "https://dlstreams.st/"
            
            m3u_content += f"#EXTINF:-1,{title}\n"
            m3u_content += f"{stream_url}|Referer={referer_url}\n"
            
    # যদি কোনো লিংক না পাওয়া যায় বা ইরর আসে, তবে ফাইলের ভেতরেই ইরর মেসেজগুলো শো করবে
    if errors:
        m3u_content += "\n# --- DEBUG ERRORS ---\n"
        for err in errors:
            # m3u ফরম্যাট যেন ভেঙে না যায়, তাই কমেন্ট আকারে ইররগুলো লেখা হলো
            m3u_content += f"# ERROR: {err}\n"

    with open("playlist.m3u", "w", encoding="utf-8") as f:
        f.write(m3u_content)

    print("[✔] প্রসেস শেষ এবং ফাইল সেভ হয়েছে!")

if __name__ == "__main__":
    asyncio.run(main())
