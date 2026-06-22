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


# ─── Strict blocklist: reject image URLs containing these words ───────────────
BLOCKED_URL_KEYWORDS = [
    # People / fashion / lifestyle
    'shirt', 'tshirt', 't-shirt', 'fashion', 'wear', 'clothing', 'apparel',
    'model', 'person', 'people', 'woman', 'man', 'girl', 'boy', 'face',
    'portrait', 'selfie', 'avatar',
    # Books / stationery / non-agri products
    'book', 'cover', 'manga', 'amazon', 'kindle', 'novel', 'magazine',
    'poster', 'wallpaper', 'icon', 'logo', 'banner', 'clipart', 'vector',
    # Generic shopping / unrelated domains
    'etsy', 'redbubble', 'pinterest', 'instagram', 'facebook', 'twitter',
    'youtube', 'tiktok', 'shutterstock', 'getty', 'istock', 'dreamstime',
    'zazzle', 'spreadshirt', 'teepublic',
]

# ─── Allowlist: image URLs MUST contain at least one of these ─────────────────
ALLOWED_URL_KEYWORDS = [
    'agri', 'farm', 'crop', 'plant', 'leaf', 'disease', 'pest',
    'fungicide', 'pesticide', 'herbicide', 'insecticide', 'chemical',
    'spray', 'blight', 'rust', 'mold', 'wilt', 'pathogen', 'seed',
    'soil', 'garden', 'horticulture', 'botany', 'mycology',
    'treatment', 'product', 'bottle', 'label', 'fertilizer',
]


def _is_agriculture_image(url: str) -> bool:
    """Returns True only if the URL looks like an agriculture/pesticide image."""
    url_lower = url.lower()
    if any(kw in url_lower for kw in BLOCKED_URL_KEYWORDS):
        return False
    return any(kw in url_lower for kw in ALLOWED_URL_KEYWORDS)


def fetch_image(chemical_name: str) -> str:
    """
    Fetches an agriculture pesticide / fungicide product image URL.
    The query is locked to the chemical name + pesticide product keywords
    so results are strictly agrochemical bottles / packaging.

    Args:
        chemical_name: e.g. "Benomyl", "Thiobendazole", "Pseudomonas fluorescens"

    Returns:
        A direct image URL string, or "" if nothing suitable is found.
    """
    SEARCH_VARIANTS = [
        f"{chemical_name} fungicide pesticide bottle agricultural product",
        f"{chemical_name} agrochemical crop spray product",
        f"{chemical_name} plant disease chemical treatment agriculture",
    ]

    for variant in SEARCH_VARIANTS:
        try:
            search_query = urllib.parse.quote(variant)
            url = (
                f"https://www.bing.com/images/search"
                f"?q={search_query}"
                f"&qft=+filterui:photo-photo+filterui:aspect-square"
                f"&form=IRFLTR"
            )

            req = urllib.request.Request(url, headers={
                'User-Agent': (
                    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                    'AppleWebKit/537.36 (KHTML, like Gecko) '
                    'Chrome/124.0.0.0 Safari/537.36'
                )
            })
            html = urllib.request.urlopen(req, timeout=8).read().decode('utf-8')

            candidates = re.findall(r'murl&quot;:&quot;(.*?)&quot;', html)

            for img_url in candidates:
                if _is_agriculture_image(img_url):
                    return img_url

        except Exception as e:
            print(f"[fetch_image] Error on variant '{variant}': {e}")
            continue

    # ── Last-resort fallback ──────────────────────────────────────────────────
    try:
        fallback_query = urllib.parse.quote(f"{chemical_name} pesticide bottle")
        url = f"https://www.bing.com/images/search?q={fallback_query}"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        html = urllib.request.urlopen(req, timeout=8).read().decode('utf-8')
        candidates = re.findall(r'murl&quot;:&quot;(.*?)&quot;', html)
        if candidates:
            return candidates[0]
    except Exception as e:
        print(f"[fetch_image] Fallback error: {e}")

    return ""


def fetch_summary(disease_name: str) -> str:
    """
    Fetches a plant disease treatment/management summary from DuckDuckGo.

    Args:
        disease_name: e.g. "Mango Anthracnose", "Rice Blast"

    Returns:
        A clean text snippet, or a fallback message.
    """
    AGRICULTURE_SNIPPET_KEYWORDS = [
        'plant', 'crop', 'disease', 'leaf', 'fungal', 'bacterial',
        'treatment', 'spray', 'pesticide', 'fungicide', 'farm',
        'agriculture', 'symptom', 'infection', 'blight', 'rust',
        'wilt', 'mold', 'control', 'management', 'harvest',
        'pathogen', 'spore', 'lesion', 'necrosis',
    ]

    try:
        query = urllib.parse.quote(
            f"{disease_name} plant disease symptoms treatment agriculture management"
        )
        url = f"https://html.duckduckgo.com/html/?q={query}"

        req = urllib.request.Request(url, headers={
            'User-Agent': (
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                'AppleWebKit/537.36 (KHTML, like Gecko) '
                'Chrome/124.0.0.0 Safari/537.36'
            )
        })
        html = urllib.request.urlopen(req, timeout=8).read().decode('utf-8')

        snippets = re.findall(
            r'<a class="result__snippet[^>]*>(.*?)</a>',
            html,
            re.IGNORECASE | re.DOTALL,
        )

        for snippet_html in snippets:
            snippet = re.sub(r'<[^>]+>', '', snippet_html)
            snippet = re.sub(r'\s+', ' ', snippet).strip()
            if any(kw in snippet.lower() for kw in AGRICULTURE_SNIPPET_KEYWORDS):
                return snippet

        if snippets:
            first = re.sub(r'<[^>]+>', '', snippets[0])
            return re.sub(r'\s+', ' ', first).strip()

        return "No agriculture summary available online."

    except Exception as e:
        print(f"[fetch_summary] Error: {e}")
        return "Could not fetch summary."
