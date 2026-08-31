import yaml
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

# টার্গেট ওয়েবসাইট লিংক
URL = "https://dlstreams.st/24-7-channels.php"

def generate_test_yaml():
    print("[1/2] পেজ থেকে চ্যানেলগুলোর নাম এবং ওয়াচ পেজ লিংক সংগ্রহ করা হচ্ছে...")
    
    channels = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        # মূল পেজে যাওয়া
        page.goto(URL, timeout=60000)
        page.wait_for_timeout(3000)
        
        soup = BeautifulSoup(page.content(), 'html.parser')
        browser.close()

    # কার্ড বা লিংকগুলো খুঁজে বের করা
    cards = soup.select('a')
    for card in cards:
        name = card.get_text(strip=True)
        href = card.get('href')
        
        if name and href:
            if href.startswith('/'):
                href = "https://dlstreams.st" + href
            
            # শুধুমাত্র চ্যানেল পেজ বা স্ট্রিম পেজের লিংক ফিল্টার করা
            if "stream" in href or "watch" in href or "id=" in href:
                channels.append({"name": name, "url": href})
                
    # ডুপ্লিকেট রিমুভ করা
    unique_channels = [dict(t) for t in {tuple(d.items()) for d in channels}]
    print(f"[✔] মোট {len(unique_channels)} টি চ্যানেল পাওয়া গেছে।")

    print("[2/2] YAML প্লেলিস্টে ওয়াচ পেজের লিংক দিয়ে ফাইল তৈরি করা হচ্ছে...")
    
    # টেস্টের জন্য প্রথম ১০টি চ্যানেল নিয়ে YAML ফাইল বানানো যাক (প্রয়োজনে সংখ্যা বাড়াতে বা কমাতে পারেন)
    target_channels = unique_channels[:10]

    yaml_playlist = {
        "playlist_name": "DaddyLive Test Playlist (Watch Links)",
        "total_channels": len(target_channels),
        "channels": []
    }

    for item in target_channels:
        yaml_playlist["channels"].append({
            "title": item["name"],
            "url": item["url"],  # এখানে ওয়াচ পেজের লিংক বসানো হয়েছে
            "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "http_refer_url": "https://dlstreams.st/"
        })

    # ফাইলের নাম playlist.yaml করা হয়েছে
    file_name = "playlist.yaml"
    with open(file_name, "w", encoding="utf-8") as yf:
        yaml.dump(yaml_playlist, yf, allow_unicode=True, sort_keys=False, indent=4)

    print(f"[✔] সফলভাবে '{file_name}' ফাইলটি তৈরি হয়ে গেছে!")

if __name__ == "__main__":
    generate_test_yaml()
  
