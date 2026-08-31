import asyncio
import json
import sys
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright

URL = "https://dlstreams.st/24-7-channels.php"

# ধাপ ১: DaddyLive পেজ থেকে চ্যানেল এবং ওয়াচ পেজের লিংক সংগ্রহ করে জেসন ফরম্যাটে সাজানো
async def fetch_watch_links(page):
    print("[1/3] DaddyLive পেজ থেকে চ্যানেল এবং ওয়াচ পেজের লিংক সংগ্রহ করা হচ্ছে...")
    channels_dict = {}
    try:
        await page.goto(URL, timeout=60000)
        await page.wait_for_timeout(4000)
        
        content = await page.content()
        soup = BeautifulSoup(content, 'html.parser')
        
        cards = soup.find_all('a')
        idx = 1
        for card in cards:
            href = card.get('href')
            text = card.get_text(separator="|", strip=True)
            
            if href and text:
                if href.startswith('/'):
                    href = "https://dlstreams.st" + href
                
                if "stream" in href or "watch" in href or "id=" in href:
                    parts = text.split('|')
                    channel_name = parts[0] if len(parts) > 0 else "Unknown Channel"
                    
                    channels_dict[str(idx)] = {
                        "name": channel_name,
                        "url": href,
                        "logo": ""
                    }
                    idx += 1

    except Exception as e:
        print(f"Error fetching main page: {e}")

    print(f"[✔] মোট {len(channels_dict)} টি ওয়াচ পেজ পাওয়া গেছে।")
    
    # জেসন ফাইল সেভ করা
    with open("Crichd page Link.json", "w", encoding="utf-8") as f:
        json.dump(channels_dict, f, ensure_ascii=False, indent=4)
        
    return channels_dict

# ধাপ ২: ওয়াচ পেজ থেকে .m3u8 এবং Referer ক্যাপচার করা
async def fetch_m3u8_stream(browser, channel_id, data):
    name = data.get("name")
    url = data.get("url")
    logo = data.get("logo", "")

    context = await browser.new_context()
    page = await context.new_page()
    
    # পেজের গতি বাড়ানোর জন্য ইমেজ, অ্যাডস ও সিএসএস ব্লক করা
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
        await page.goto(url, timeout=30000)
        
        # লিংক পাওয়ার জন্য সর্বোচ্চ ১০ সেকেন্ড অপেক্ষা করা
        for _ in range(10):
            if m3u8_url:
                break
            await asyncio.sleep(1)

    except Exception as e:
        print(f"Error for {name}: {e}")
    finally:
        await context.close()

    if m3u8_url:
        stream_link = f"{m3u8_url}|Referer={referer_url}"
        print(f"Success: {name}")
        return name, logo, stream_link
    else:
        print(f"Failed: {name} (Link not found)")
        return name, logo, None

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        main_page = await browser.new_page()
        
        # ১. লিংকগুলো তুলে নেওয়া ও জেসন ফাইল তৈরি করা
        channels = await fetch_watch_links(main_page)
        await main_page.close()
        
        if not channels:
            print("কোনো চ্যানেল পাওয়া যায়নি!")
            await browser.close()
            return

        print("[2/3] মাল্টি-ট্যাব দিয়ে .m3u8 লিংক ক্যাপচার করা হচ্ছে...")
        
        # ২. অ্যাসিনক্রোনাসভাবে সব চ্যানেল প্রসেস করা
        tasks = [fetch_m3u8_stream(browser, ch_id, ch_data) for ch_id, ch_data in channels.items()]
        results = await asyncio.gather(*tasks)
        
        await browser.close()

    print("[3/3] চূড়ান্ত playlist.m3u প্লেলিস্ট তৈরি করা হচ্ছে...")
    
    playlist_content = "#EXTM3U\n"
    success_count = 0

    for name, logo, stream_link in results:
        if stream_link:
            playlist_content += f'#EXTINF:-1 tvg-chno="" tvg-name="{name}" tvg-logo="{logo}" group-title="DaddyLive",{name}\n'
            playlist_content += f"{stream_link}\n"
            success_count += 1

    file_name = "playlist.m3u"
    with open(file_name, "w", encoding="utf-8") as f:
        f.write(playlist_content)

    print(f"[✔] কাজ শেষ! মোট {success_count} টি সচল স্ট্রিম নিয়ে '{file_name}' সফলভাবে তৈরি হয়েছে।")

if __name__ == "__main__":
    asyncio.run(main())
