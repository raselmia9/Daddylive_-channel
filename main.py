import asyncio
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright

async def get_channels_from_homepage():
    print("[1/2] হোমপেজ থেকে চ্যানেলের নাম এবং ওয়াচ পেজ লিংক সংগ্রহ করা হচ্ছে...")
    
    # ড্যাডি লাইভের মূল চ্যানেল লিস্ট পেজ (আপনার প্রয়োজনমতো ইউআরএল পরিবর্তন করতে পারেন)
    homepage_url = "https://dlstreams.st/24-7-channels" # অথবা মূল হোমপেজ
    
    channels_list = []
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        try:
            # পেজে প্রবেশ এবং লোড হওয়া পর্যন্ত অপেক্ষা
            await page.goto(homepage_url, timeout=30000, wait_until="domcontentloaded")
            await asyncio.sleep(3) # যদি জাভাস্ক্রিপ্ট দিয়ে কার্ডগুলো লোড হয়
            
            content = await page.content()
            soup = BeautifulSoup(content, 'html.parser')
            
            # ওয়েবসাইটের স্ট্রাকচার অনুযায়ী চ্যানেল কার্ডগুলো খুঁজে বের করা
        
            # নোট: সাধারণত এই সাইটগুলোতে কার্ডগুলো <a> ট্যাগ বা নির্দিষ্ট ক্লাসের ভেতরে থাকে। 
            # নিচে একটি জেনেরিক লজিক দেওয়া হলো যা কার্ড বা লিংকগুলো খুঁজে নেবে।
            
            cards = soup.find_all('a', href=True)
            for card in cards:
                href = card['href']
                if "watch.php?id=" in href:
                    # যদি লিংকে পূর্ণাঙ্গ ইউআরএল না থাকে
                    if not href.startswith("http"):
                        watch_url = f"https://dlstreams.st/{href}" if not href.startswith("/") else f"https://dlstreams.st{href}"
                    else:
                        watch_url = href
                        
                    # চ্যানেলের নাম খোঁজার চেষ্টা (কার্ডের ভেতরের টেক্সট থেকে)
                    title_text = card.get_text(separator=" ", strip=True)
                    if title_text:
                        # নাম থেকে আইডি অংশ আলাদা করা যেতে পারে
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
    
    # ফলাফল একটি ফাইলে সেভ করে রাখা যেন পরের ধাপে ব্যবহার করা যায়
    with open("channels_output.txt", "w", encoding="utf-8") as f:
        for ch in unique_channels:
            f.write(f"Title: {ch['title']} | URL: {ch['url']}\n")
            
    print("[✔] সফলভাবে 'channels_output.txt' ফাইলে চ্যানেলগুলোর লিস্ট সেভ হয়ে গেছে!")

if __name__ == "__main__":
    asyncio.run(get_channels_from_homepage())
