import asyncio
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright

async def main():
    print("[1/2] হোমপেজ থেকে চ্যানেলের নাম এবং ওয়াচ পেজ লিংক সংগ্রহ করা হচ্ছে...")
    homepage_url = "https://dlstreams.st/24-7-channels"
    
    channels_list = []
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-setuid-sandbox", "--disable-dev-shm-usage"]
        )
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        
        try:
            # পেজ লোড করা এবং রেন্ডার হওয়ার জন্য সময় দেওয়া
            await page.goto(homepage_url, timeout=60000, wait_until="domcontentloaded")
            await asyncio.sleep(5)
            
            content = await page.content()
            soup = BeautifulSoup(content, 'html.parser')
            
            # ওয়েবসাইটের কার্ড বা লিংকগুলো খোঁজা যেগুলোতে watch.php আছে
            for a_tag in soup.find_all('a', href=True):
                href = a_tag['href']
                if "watch.php?id=" in href:
                    if href.startswith("http"):
                        watch_url = href
                    elif href.startswith("/"):
                        watch_url = f"https://dlstreams.st{href}"
                    else:
                        watch_url = f"https://dlstreams.st/{href}"
                        
                    # চ্যানেলের নাম সংগ্রহ ও পরিষ্কার করা
                    title_text = a_tag.get_text(separator=" ", strip=True)
                    if "ID:" in title_text:
                        title_text = title_text.split("ID:")[0].strip()
                    
                    if not title_text:
                        title_text = "Live Channel"
                        
                    channels_list.append({"title": title_text, "url": watch_url})
                            
        except Exception as e:
            print(f"Error fetching homepage: {e}")
        finally:
            await browser.close()
            
    # ডুপ্লিকেট রিমুভ করা
    unique_channels = []
    seen_urls = set()
    for ch in channels_list:
        if ch['url'] not in seen_urls:
            seen_urls.add(ch['url'])
            unique_channels.append(ch)

    print(f"[2/2] মোট {len(unique_channels)} টি চ্যানেল পাওয়া গেছে। playlist.m3u তৈরি হচ্ছে...")
    
    # প্লেলিস্টে ওয়াচ পেজ লিংকগুলো বসানো
    m3u_content = "#EXTM3U\n"
    if unique_channels:
        for ch in unique_channels:
            m3u_content += f"#EXTINF:-1,{ch['title']}\n"
            m3u_content += f"{ch['url']}\n"
    else:
        m3u_content += "#EXTINF:-1,Error: No watch page links captured\n"
        m3u_content += "https://dlstreams.st/\n"

    with open("playlist.m3u", "w", encoding="utf-8") as f:
        f.write(m3u_content)

    print("[✔] সফলভাবে ওয়াচ পেজ লিংক দিয়ে playlist.m3u আপডেট করা হয়েছে!")

if __name__ == "__main__":
    asyncio.run(main())
