import asyncio
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright

async def get_channels_from_homepage():
    print("[1/2] হোমপেজ থেকে চ্যানেলের নাম এবং ওয়াচ পেজ লিংক সংগ্রহ করা হচ্ছে...")
    
    homepage_url = "https://dlstreams.st/24-7-channels"
    channels_list = []
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        try:
            # পেজে প্রবেশ এবং সম্পূর্ণ লোড হওয়ার জন্য অপেক্ষা
            await page.goto(homepage_url, timeout=60000, wait_until="networkidle")
            
            # পেজটি পুরোপুরি রেন্ডার হওয়ার জন্য একটু সময় দেওয়া
            await asyncio.sleep(5)
            
            content = await page.content()
            soup = BeautifulSoup(content, 'html.parser')
            
            # ওয়েবসাইটের সব <a> ট্যাগ চেক করা যেগুলোতে watch.php আছে কি না
            for a_tag in soup.find_all('a', href=True):
                href = a_tag['href']
                if "watch.php?id=" in href:
                    # পূর্ণাঙ্গ ইউআরএল তৈরি
                    if href.startswith("http"):
                        watch_url = href
                    elif href.startswith("/"):
                        watch_url = f"https://dlstreams.st{href}"
                    else:
                        watch_url = f"https://dlstreams.st/{href}"
                        
                    # চ্যানেলের নাম সংগ্রহ (ট্যাগ বা তার ভেতরের টেক্সট থেকে)
                    title_text = a_tag.get_text(separator=" ", strip=True)
                    
                    # যদি টেক্সট অনেক বড় বা ফাঁকা হয়, তবে ইউআরএল থেকে আইডি বের করে ফলব্যাক নাম দেওয়া যেতে পারে
                    if not title_text:
                        title_text = "Unknown Channel"
                        
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

    print(f"[2/2] মোট {len(unique_channels)} টি চ্যানেলের ওয়াচ পেজ পাওয়া গেছে।")
    
    # প্লেলিস্ট ফরম্যাটে বা টেক্সট আকারে সেভ করা
    # আপাতত চেক করার জন্য আমরা সরাসরি m3u ফরম্যাটেই সেভ করতে পারি বা চ্যানেলের লিস্ট রাখতে পারি।
    m3u_content = "#EXTM3U\n"
    for ch in unique_channels:
        # যেহেতু এটি প্রথম ধাপ, তাই আপাতত ওয়াচ পেজ লিংকটিই দিচ্ছি (পরের ধাপে এখানে m3u8 লিংক বসবে)
        # চ্যানেলের নাম থেকে অপ্রয়োজনীয় লাইন বা আইডি টেক্সট পরিষ্কার করে নেওয়া ভালো
        clean_title = ch['title'].split("ID:")[0].strip()
        if not clean_title:
            clean_title = "Channel"
            
        m3u_content += f"#EXTINF:-1,{clean_title}\n"
        m3u_content += f"{ch['url']}\n"

    with open("playlist.m3u", "w", encoding="utf-8") as f:
        f.write(m3u_content)

    print("[✔] সফলভাবে 'playlist.m3u' ফাইলে চ্যানেলগুলো আপডেট হয়ে গেছে!")

if __name__ == "__main__":
    asyncio.run(get_channels_from_homepage())
