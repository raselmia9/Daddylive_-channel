import sys
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

# টার্গেট ওয়েবসাইট লিংক
URL = "https://dlstreams.st/24-7-channels.php"

def generate_m3u_playlist():
    print("[1/2] DaddyLive পেজ থেকে চ্যানেল এবং লিংক সংগ্রহ করা হচ্ছে...")
    
    channels = []
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            
            # পেজে যাওয়া এবং লোড হওয়ার জন্য অপেক্ষা করা
            page.goto(URL, timeout=60000)
            page.wait_for_timeout(4000)
            
            soup = BeautifulSoup(page.content(), 'html.parser')
            browser.close()

        # সঠিক চ্যানেল কার্ড বা লিংক ফিল্টার করা (যাতে প্রথম দিকের কোনো চ্যানেল বাদ না পড়ে)
        cards = soup.find_all('a')
        for card in cards:
            href = card.get('href')
            text = card.get_text(separator="|", strip=True)
            
            if href and text:
                if href.startswith('/'):
                    href = "https://dlstreams.st" + href
                
                # শুধুমাত্র ওয়াচ পেজ বা স্ট্রিম লিংকগুলো নিখুঁতভাবে কালেক্ট করা
                if "stream" in href or "watch" in href or "id=" in href:
                    parts = text.split('|')
                    channel_name = parts[0] if len(parts) > 0 else "Unknown Channel"
                    
                    # ফালতু বা ফাঁকা নাম বাদ দিয়ে সঠিক চ্যানেলগুলো যুক্ত করা
                    if channel_name and channel_name != "Unknown Channel":
                        channels.append({"name": channel_name, "url": href})

    except Exception as e:
        print(f"Error fetching data: {e}")
        sys.exit(1)

    # ডুপ্লিকেট বাদ দেওয়া কিন্তু সঠিক ক্রম বজায় রাখা
    seen = set()
    unique_channels = []
    for item in channels:
        identifier = (item["name"], item["url"])
        if identifier not in seen:
            seen.add(identifier)
            unique_channels.append(item)

    print(f"[✔] মোট {len(unique_channels)} টি চ্যানেল পাওয়া গেছে।")

    print("[2/2] playlist.m3u ফাইল তৈরি করা হচ্ছে...")
    
    # M3U ফাইলের কন্টেন্ট তৈরি
    m3u_content = "#EXTM3U\n"
    for item in unique_channels:
        name = item["name"]
        url = item["url"]
        
        m3u_content += f'#EXTINF:-1 tvg-chno="" tvg-name="{name}" group-title="DaddyLive",{name}\n'
        m3u_content += f'#EXTVLCOPT:http-referrer=https://dlstreams.st/\n'
        # লিংকের ঠিক আগে >Capture< লেখাটি যুক্ত রাখা হয়েছে
        m3u_content += f'>Capture<{url}\n'

    # playlist.m3u ফাইলে সেভ করা
    file_name = "playlist.m3u"
    with open(file_name, "w", encoding="utf-8") as f:
        f.write(m3u_content)

    print(f"[✔] সফলভাবে '{file_name}' তৈরি করা হয়েছে!")

if __name__ == "__main__":
    generate_m3u_playlist()
