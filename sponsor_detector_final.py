import pandas as pd
import re
from urllib.parse import urlparse

# --- MANUAL GROUND TRUTH / KNOWN SPONSORS ---
KNOWN_SPONSORS = {
    'sorbil': 'Sorbil',
    'gain': 'GAİN',
    'nordvpn': 'NordVPN',
    'mükellef': 'Mükellef',
    'mukellef': 'Mükellef',
    'kitapyurdu': 'Kitapyurdu',
    'kitap yurdu': 'Kitapyurdu',
    'stablex': 'Stablex',
    'goal battle': 'Goal Battle',
    'geforce now': 'GeForce NOW',
    'gaming.gen.tr': 'Gaming.Gen.TR',
    'gaming gen tr': 'Gaming.Gen.TR',
    'game garaj': 'Game Garaj',
    'gamegaraj': 'Game Garaj',
    'vatan bilgisayar': 'Vatan Bilgisayar',
    'vatanoem': 'Vatan Bilgisayar',
    'loris': 'Loris Parfüm',
    'parfüm loris': 'Loris Parfüm',
    'nocturne': 'Nocturne',
    'lunapernoctes': 'Lunapernoctes',
    'ecovacs': 'ECOVACS',
    'turkcell': 'Turkcell',
    'google cloud': 'Google Cloud',
    'nvidia': 'NVIDIA',
    'asus': 'ASUS',
    'monster': 'Monster Notebook',
    'trendyol': 'Trendyol',
    'yemeksepeti': 'Yemeksepeti',
    'getir': 'Getir',
    'amazon': 'Amazon',
    'hepsiburada': 'Hepsiburada',
    'nescafe': 'Nescafe',
    'red bull': 'Red Bull'
}

# --- CONFIGURATION ---
GENERIC_IGNORE = {
    'youtube', 'instagram', 'twitter', 'facebook', 'tiktok', 'discord', 'twitch', 'spotify',
    'abone', 'kanal', 'video', 'link', 'tıkla', 'izle', 'beğen', 'yorum', 'paylaş',
    'oyun', 'vlog', 'müzik', 'teknoloji', 'inceleme', 'film', 'dizi', 'fragman',
    'bölüm', 'part', 'seri', 'komedi', 'eğlence', 'haber', 'gündem', 'spor',
    'konser', 'tiyatro', 'sinema', 'kitap', 'yazar', 'şair', 'şiir', 'edebiyat',
    'felsefe', 'tarih', 'sanat', 'kültür', 'bilim', 'uzay', 'belgesel',
    'gta', 'minecraft', 'valorant', 'csgo', 'pubg', 'lol', 'roblox', 'fortnite',
    'playstation', 'xbox', 'nintendo', 'steam', 'epic', 'google', 'apple'
}

def normalize(text):
    if not isinstance(text, str): return ""
    return text.lower().replace('i̇', 'i').replace('ı', 'i').strip()

def extract_domain_brand(url):
    try:
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        if domain.startswith('www.'): domain = domain[4:]
        if domain in ['bit.ly', 'goo.gl', 't.co', 'go.link', 'sng.link', 'tr.ee', 'linktr.ee']: return None
        brand = domain.split('.')[0]
        if brand in ['youtu', 'instagram', 'facebook', 'twitter', 'twitch', 'discord']: return None
        return brand
    except:
        return None

# --- MANUAL BLOCKLIST FOR PEOPLE/HOSTS ---
GENERIC_PEOPLE = {
    'mesut çevik', 'mesut cevik', 'enis kirazoğlu', 'enis kirazoglu', 
    'berfu yenenler', 'eser yenenler', 'orkun işıtmak', 'orkun isitmak',
    'barış özcan', 'baris ozcan', 'duygu özaslan', 'duygu ozaslan',
    'mendebur lemur', 'tuna tavus', 'gökhan çınar', 'gokhan cinar',
    'halil ergün', 'nilgün belgün', 'murat soner', 'tolga çevik',
    'fatih altaylı', 'nevşin mengü', 'cüneyt özdemir', 'oğuzhan uğur',
    'hasan can kaya', 'zeynep bastık', 'reynmen', 'kafalar', 'delimine'
}

def detect_sponsors_scored(description, channel_name):
    if not isinstance(description, str): return None
    
    # Dynamic Blocklist for this row
    current_blocklist = GENERIC_IGNORE.copy()
    
    # Add channel name parts to blocklist
    if isinstance(channel_name, str):
        c_norm = normalize(channel_name)
        current_blocklist.add(c_norm) 
        # Add individual name parts if length > 3 (e.g. "Enis" from "Enis Kirazoglu")
        for part in c_norm.split():
            if len(part) > 3:
                current_blocklist.add(part)

    # Candidate Map: {BrandName: Score}
    candidates = {}
    
    lines = description.split('\n')
    desc_lower = normalize(description)

    # Helper to add candidate
    def add_candidate(name, score):
        norm_name = normalize(name)
        
        # Check Blocklists
        if norm_name in current_blocklist: return
        if norm_name in GENERIC_PEOPLE: return
        # Check partial match with channel name (e.g. "Mesut Çevik" -> "Mesut")
        if isinstance(channel_name, str) and normalize(channel_name) in norm_name: return
        
        if len(name) < 2: return
        
        # Check if known
        final_name = name
        is_known = False
        
        if norm_name in KNOWN_SPONSORS:
            final_name = KNOWN_SPONSORS[norm_name]
            score = 100 
            is_known = True
        else:
            for k, v in KNOWN_SPONSORS.items():
                if k in norm_name and len(norm_name) < len(k) + 5:
                    final_name = v
                    score = 100
                    is_known = True
                    break
        
        final_name = final_name.strip('.,-!?:; ').title() if not is_known else final_name
        
        if final_name in candidates:
            candidates[final_name] = max(candidates[final_name], score)
        else:
            candidates[final_name] = score

    # 1. KNOWN SPONSOR SCAN (Score: 100)
    for key, val in KNOWN_SPONSORS.items():
        if len(key) < 5:
            if re.search(r'\b' + re.escape(key) + r'\b', desc_lower):
                add_candidate(val, 100)
        else:
            if key in desc_lower:
                add_candidate(val, 100)

    # 2. REGEX EXPLICIT (Score: 90)
    regex_explicit = re.compile(r'(?:Sponsor|İşbirliği|Marka|Reklam)\s*[:|–|-]\s*([^\n\.,]+)', re.IGNORECASE)
    for line in lines:
        if 'değildir' in normalize(line) and ('işbirliği' in normalize(line) or 'reklam' in normalize(line)): continue
        m = regex_explicit.search(line)
        if m:
            cand = m.group(1).strip()
            if len(cand) > 1 and len(cand.split()) < 5:
                add_candidate(cand, 90)

    # 3. REGEX SUFFIX (Score: 85)
    regex_suffix = re.compile(r'([A-Zİ][a-zA-Z0-9ğüşıöçĞÜŞİÖÇ\s\.]+?)\s+(?:tarafından|katkılarıyla|sunar|sponsorluğunda|destekleriyle)', re.UNICODE)
    for line in lines:
        m = regex_suffix.search(line)
        if m:
            cand = m.group(1).strip()
            if cand.lower().startswith('bu video '): cand = cand[9:]
            if cand.lower().startswith('videomuz '): cand = cand[9:]
            if len(cand) > 1 and len(cand.split()) < 5:
                add_candidate(cand, 85)

    # 4. HASHTAGS (Score: 60)
    hashtag_regex = re.compile(r'#(\w+)', re.UNICODE)
    for line in lines:
        line_norm = normalize(line)
        if '#işbirliği' in line_norm or '#reklam' in line_norm or '#sponsor' in line_norm:
            tags = hashtag_regex.findall(line)
            for t in tags:
                if normalize(t) not in ['işbirliği', 'reklam', 'sponsor', 'ortaklık'] and normalize(t) not in GENERIC_IGNORE:
                    add_candidate(t, 60)

    # 5. LINKS (Score: 40)
    for line in lines:
        line_norm = normalize(line)
        if any(k in line_norm for k in ['indirim', 'fırsat', 'kod', 'hazır sistem', 'satın al', 'link']):
            urls = re.findall(r'(https?://[^\s]+)', line)
            for u in urls:
                brand = extract_domain_brand(u)
                if brand:
                    add_candidate(brand, 40)

    if not candidates: return None
        
    # Find max score
    max_score = max(candidates.values())
    
    # Winners
    winners = [name for name, score in candidates.items() if score == max_score]
    
    # If we have score 100 winners, return unique ones.
    # User preference: "Clear output". 
    # If multiple 100s, usually it's "Sorbil" and "SorbilApp" (dedupped mostly), or two real sponsors.
    # Join them.
    
    return ', '.join(sorted(list(set(winners))))

def main():
    try:
        print("Loading Excel...")
        df = pd.read_excel('youtube_videos.xlsx')
        
        print("Detecting sponsors with strict channel filtering...")
        # Note: Passing channel_name to the function now
        df['detected_sponsor'] = df.apply(lambda x: detect_sponsors_scored(x['description'], x['channel_name']), axis=1)
        
        result_df = df[df['detected_sponsor'].notna()]
        
        output_file = 'sponsored_videos_scored.xlsx'
        cols = ['video_title', 'channel_name', 'published_at', 'detected_sponsor']
        result_df[cols].to_excel(output_file, index=False)
        print(f"Done. Found {len(result_df)} sponsored videos.")
        print(f"Saved to '{output_file}'")
        
        print("\n--- Strict Filter Samples ---")
        print(result_df[cols].sample(n=min(10, len(result_df))))
        
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()
