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
    """
    Fetches an agriculture-specific plant disease or pesticide image URL.
    Uses multiple targeted search terms to ensure only relevant images are returned.
    """
    try:
        # Build a highly specific agriculture query to avoid unrelated results
        # e.g. "tomato leaf blight" → "tomato leaf blight plant disease agriculture crop"
        agriculture_query = f"{query} plant disease agriculture crop field"
        search_query = urllib.parse.quote(agriculture_query)

        # Use Bing Images with a safe-search and agriculture filter
        url = f"https://www.bing.com/images/search?q={search_query}&qft=+filterui:photo-photo&form=IRFLTR"

        req = urllib.request.Request(url, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                          'AppleWebKit/537.36 (KHTML, like Gecko) '
                          'Chrome/91.0.4472.124 Safari/537.36'
        })
        html = urllib.request.urlopen(req).read().decode('utf-8')

        # Extract all image URLs from Bing's native payload
        matches = re.findall(r'murl&quot;:&quot;(.*?)&quot;', html)

        # Filter: only keep URLs that contain agriculture-related keywords
        AGRICULTURE_KEYWORDS = [
            'plant', 'crop', 'leaf', 'disease', 'farm', 'agri',
            'pest', 'fungus', 'blight', 'rust', 'mold', 'wilt',
            'soil', 'field', 'garden', 'flower', 'root', 'seed',
            'vegetable', 'fruit', 'tree', 'wheat', 'rice', 'corn',
            'tomato', 'potato', 'cotton', 'paddy', 'horticulture'
        ]

        for img_url in matches:
            img_url_lower = img_url.lower()
            if any(kw in img_url_lower for kw in AGRICULTURE_KEYWORDS):
                return img_url

        # Fallback: return the first result if no keyword match found
        if matches:
            return matches[0]

        return ""

    except Exception as e:
        print("Image Scraper Error:", e)
        return ""


def fetch_summary(query):
    """
    Fetches a treatment/management summary for a plant disease from DuckDuckGo.
    Targets agriculture-specific sources for relevant results.
    """
    try:
        # More specific query targeting agriculture/farming knowledge sources
        agriculture_summary_query = f"{query} plant disease symptoms treatment agriculture management"
        search_query = urllib.parse.quote(agriculture_summary_query)

        url = f"https://html.duckduckgo.com/html/?q={search_query}"

        req = urllib.request.Request(url, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                          'AppleWebKit/537.36 (KHTML, like Gecko) '
                          'Chrome/91.0.4472.124 Safari/537.36'
        })
        html = urllib.request.urlopen(req).read().decode('utf-8')

        # Extract all result snippets from DuckDuckGo HTML
        snippets = re.findall(
            r'<a class="result__snippet[^>]*>(.*?)</a>',
            html,
            re.IGNORECASE | re.DOTALL
        )

        AGRICULTURE_KEYWORDS = [
            'plant', 'crop', 'disease', 'leaf', 'fungal', 'bacterial',
            'treatment', 'spray', 'pesticide', 'fungicide', 'farm',
            'agriculture', 'symptom', 'infection', 'blight', 'rust',
            'wilt', 'mold', 'control', 'management', 'harvest'
        ]

        for snippet_html in snippets:
            # Clean HTML tags and whitespace
            snippet = re.sub(r'<[^>]+>', '', snippet_html)
            snippet = re.sub(r'\s+', ' ', snippet).strip()

            # Only return snippets that contain agriculture-related content
            snippet_lower = snippet.lower()
            if any(kw in snippet_lower for kw in AGRICULTURE_KEYWORDS):
                return snippet

        # Fallback: return first snippet if no keyword-matched one found
        if snippets:
            first = re.sub(r'<[^>]+>', '', snippets[0])
            return re.sub(r'\s+', ' ', first).strip()

        return "No agriculture summary available online."

    except Exception as e:
        print("Summary Scraper Error:", e)
        return "Could not fetch summary."
