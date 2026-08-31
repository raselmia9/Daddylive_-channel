import json
import sys
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

# টার্গেট ওয়েবসাইট লিংক
URL = "https://dlstreams.st/24-7-channels.php"

def generate_json_data():
    print("[1/2] DaddyLive পেজ থেকে চ্যানেল এবং ওয়াচ পেজের লিংক সংগ্রহ করা হচ্ছে...")
    
    channels_dict = {}
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            
            # পেজে যাওয়া এবং লোড হওয়ার জন্য অপেক্ষা করা
            page.goto(URL, timeout=60000)
            page.wait_for_timeout(4000)
            
            soup = BeautifulSoup(page.content(), 'html.parser')
            browser.close()

        # চ্যানেল কার্ড বা লিংক ফিল্টার করা
        cards = soup.find_all('a')
        idx = 1
        for card in cards:
            href = card.get('href')
            text = card.get_text(separator="|", strip=True)
            
            if href and text:
                if href.startswith('/'):
                    href = "https://dlstreams.st" + href
                
                # ওয়াচ পেজ বা স্ট্রিম লিংক ফিল্টার করা
                if "stream" in href or "watch" in href or "id=" in href:
                    parts = text.split('|')
                    channel_name = parts[0] if len(parts) > 0 else "Unknown Channel"
                    
                    # আপনার দেওয়া ডেমো ফরম্যাট অনুযায়ী সংখ্যা কি ("1", "2"...) ব্যবহার করা
                    channels_dict[str(idx)] = {
                        "name": channel_name,
                        "url": href,
                        "logo": ""  # প্রয়োজনে লোগো লিংক দেওয়া যাবে
                    }
                    idx += 1

    except Exception as e:
        print(f"Error fetching data: {e}")
        sys.exit(1)

    print(f"[✔] মোট {len(channels_dict)} টি চ্যানেলের ডেটা পাওয়া গেছে।")

    print("[2/2] JSON ফাইলে ডেটা সেভ করা হচ্ছে...")
    
    # আপনার দেওয়া দ্বিতীয় স্ক্রিপ্ট যে নামে JSON ফাইল খুঁজে থাকে: "Crichd page Link.json"
    json_filename = "Crichd page Link.json"
    with open(json_filename, "w", encoding="utf-8") as f:
        json.dump(channels_dict, f, ensure_ascii=False, indent=4)

    print(f"[✔] সফলভাবে '{json_filename}' ফাইলটি আপনার কাঙ্ক্ষিত ডেমো ফরম্যাটে তৈরি করা হয়েছে!")

if __name__ == "__main__":
    generate_json_data()
