import asyncio
from playwright.async_api import async_playwright

async def process_single_channel(browser, channel_info):
    # নতুন ট্যাব ওপেন করা
    page = await browser.new_page()
    
    # অতিরিক্ত পপ-আপ বা নতুন ট্যাব ওপেন হওয়া রোধ করা
    page.on("popup", lambda popup: popup.close())
    
    captured_data = None
    
    # নেটওয়ার্ক রিকোয়েস্ট ইন্টারসেপ্ট করে .m3u8 এবং Referer খোঁজা
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
        # ওয়াচ পেজে প্রবেশ
        print(f"Fetching: {channel_info['title']}")
        await page.goto(channel_info["url"], timeout=30000, wait_until="domcontentloaded")
        
        # স্ট্রিম লোড হওয়ার জন্য অল্প সময় অপেক্ষা করা
        for _ in range(12):
            if captured_data:
                break
            await asyncio.sleep(1)
            
    except Exception as e:
        print(f"Error on {channel_info['title']}: {e}")
    finally:
        await page.close()
        
    return captured_data, channel_info['title']

async def main():
    print("[1/3] ওয়াচ পেজ থেকে মাল্টি-ট্যাবের মাধ্যমে .m3u8 লিংক ক্যাপচার করা হচ্ছে...")
    
    # আপনার সেই প্রথম স্ক্রিপ্টের মতো নির্দিষ্ট ওয়াচ পেজগুলোর লিস্ট
    channels_to_test = [
        {"title": "CANAL+ FAMILY POLAND", "url": "https://dlstreams.st/stream/watch.php?id=567"},
        {"title": "CANAL+ SERIALE POLAND", "url": "https://dlstreams.st/stream/watch.php?id=570"}
        # আপনার ইচ্ছামতো এখানে আরও চ্যানেল ও আইডি যোগ করে নিতে পারেন
    ]
    
    results = []
    async with async_playwright() as p:
        # ব্রাউজার লঞ্চ (await সহ সঠিক সিনট্যাক্স)
        browser = await p.chromium.launch(headless=True)
        
        # প্যারালাল টাস্ক চালানো
        tasks = [process_single_channel(browser, ch) for ch in channels_to_test]
        completed_tasks = await asyncio.gather(*tasks)
        
        for res in completed_tasks:
            if res and res[0]:
                results.append(res)
                
        await browser.close()

    print(f"[2/3] মোট {len(results)} টি সচল স্ট্রিম লিংক পাওয়া গেছে।")
    print("[3/3] playlist.m3u ফাইল তৈরি করা হচ্ছে...")
    
    m3u_content = "#EXTM3U\n"
    for stream_data, title in results:
        parts = stream_data.split("|Referer=")
        stream_url = parts[0]
        referer_url = parts[1] if len(parts) > 1 else "https://dlstreams.st/"
        
        # চ্যানেলের নাম এবং লিংক ফরম্যাট অনুযায়ী বসানো
        m3u_content += f"#EXTINF:-1,{title}\n"
        m3u_content += f"{stream_url}|Referer={referer_url}\n"

    with open("playlist.m3u", "w", encoding="utf-8") as f:
        f.write(m3u_content)

    print("[✔] সফলভাবে 'playlist.m3u' আপডেট হয়ে গেছে!")

if __name__ == "__main__":
    asyncio.run(main())
