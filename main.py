import asyncio
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright

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
        # সরাসরি ওয়াচ পেজ বা আইডি দিয়ে লিংকে প্রবেশ
        print(f"[{channel_info['title']}] ওপেন করা হচ্ছে...")
        await page.goto(channel_info["url"], timeout=30000, wait_until="domcontentloaded")
        
        # স্ট্রিম লোড হওয়ার জন্য সময় দেওয়া
        for _ in range(10):
            if captured_data:
                break
            await asyncio.sleep(1)
            
    except Exception as e:
        print(f"Error on {channel_info['title']}: {e}")
    finally:
        await page.close()
        
    return captured_data, channel_info['title']

async def main():
    print("[1/3] হোমপেজ থেকে চ্যানেল এবং আইডি সংগ্রহ করা হচ্ছে...")
    homepage_url = "https://dlstreams.st/24-7-channels"
    
    channels_to_process = []
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        try:
            await page.goto(homepage_url, timeout=60000, wait_until="networkidle")
            await asyncio.sleep(3)
            
            content = await page.content()
            soup = BeautifulSoup(content, 'html.parser')
            
            # স্ক্রিনশটের কার্ড স্ট্রাকচার অনুযায়ী a ট্যাগ বা যেগুলোতে id আছে তা খোঁজা
            for a_tag in soup.find_all('a', href=True):
                href = a_tag['href']
                if "watch.php?id=" in href:
                    # ইউআরএল ঠিক করা
                    if href.startswith("http"):
                        watch_url = href
                    elif href.startswith("/"):
                        watch_url = f"https://dlstreams.st{href}"
                    else:
                        watch_url = f"https://dlstreams.st/{href}"
                        
                    # চ্যানেলের নাম বের করা
                    title_text = a_tag.get_text(separator=" ", strip=True)
                    # ID অংশ বা বাড়তি টেক্সট ক্লিন করা
                    if "ID:" in title_text:
                        title_text = title_text.split("ID:")[0].strip()
                    
                    if not title_text:
                        title_text = "Live Channel"
                        
                    # ডুপ্লিকেট এড়াতে চেক করে লিস্টে যোগ করা
                    if {"title": title_text, "url": watch_url} not in channels_to_process:
                        channels_to_process.append({"title": title_text, "url": watch_url})
                        
        except Exception as e:
            print(f"Error reading homepage: {e}")
            
        print(f"[2/3] মোট {len(channels_to_process)} টি চ্যানেল পাওয়া গেছে। প্যারালালি .m3u8 লিংক ক্যাপচার করা হচ্ছে...")
        
        # যদি হোমপেজ থেকে সরাসরি অটোমেটিক না পায়, তবে সেফটির জন্য টেস্ট চ্যানেলগুলো দিয়েও রান করতে পারেন।
        # আপাতত ডেমো বা রিয়েল ডাটা প্রসেস করার জন্য অ্যাসিনক্রোনাস টাস্ক চালানো হচ্ছে:
        if not channels_to_process:
            # ফলব্যাক হিসেবে আপনার দেওয়া আইডিগুলো দিয়ে টেস্ট লিস্ট
            channels_to_process = [
                {"title": "AHC (AMERICAN HEROES CHANNEL)", "url": "https://dlstreams.st/stream/watch.php?id=206"},
                {"title": "ANTENNA TV USA", "url": "https://dlstreams.st/stream/watch.php?id=283"}
            ]

        tasks = [process_single_channel(browser, ch) for ch in channels_to_process[:15]] # প্রথম ১৫টি দিয়ে টেস্ট করতে পারেন
        completed_tasks = await asyncio.gather(*tasks)
        
        results = []
        for res in completed_tasks:
            if res and res[0]:
                results.append(res)
                
        await browser.close()

    print(f"[3/3] playlist.m3u ফাইল তৈরি করা হচ্ছে...")
    
    m3u_content = "#EXTM3U\n"
    for stream_data, title in results:
        parts = stream_data.split("|Referer=")
        stream_url = parts[0]
        referer_url = parts[1] if len(parts) > 1 else "https://dlstreams.st/"
        
        m3u_content += f"#EXTINF:-1,{title}\n"
        m3u_content += f"{stream_url}|Referer={referer_url}\n"

    with open("playlist.m3u", "w", encoding="utf-8") as f:
        f.write(m3u_content)

    print("[✔] সফলভাবে 'playlist.m3u' আপডেট হয়ে গেছে!")

if __name__ == "__main__":
    asyncio.run(main())
