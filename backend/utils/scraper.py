import urllib.request
import urllib.parse
import re
import os

# Optional: Still try to load db.env if needed in the future
env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "db.env")
if os.path.exists(env_path):
    with open(env_path) as f:
        for line in f:
            if '=' in line and not line.startswith('#'):
                k, v = line.strip().split('=', 1)
                os.environ[k] = v

def fetch_image(query):
    try:
        # We append 'pesticide' to get more accurate domain-specific images
        search_query = urllib.parse.quote(f"{query} pesticide")
        url = f"https://www.bing.com/images/search?q={search_query}"
        
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'})
        html = urllib.request.urlopen(req).read().decode('utf-8')
        
        # Extract the first image URL from bing's native payload format
        m = re.search(r'murl&quot;:&quot;(.*?)&quot;', html)
        if m:
            return m.group(1)
            
        return ""
    except Exception as e:
        print("Scraper Error:", e)
        return ""