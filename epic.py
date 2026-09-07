import json
import urllib.request
from datetime import datetime

API_URL = "https://store-site-backend-static.ak.epicgames.com/freeGamesPromotions?locale=en-US&country=US&allowCountries=US"

def fetch_catalog():
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    req = urllib.request.Request(API_URL, headers=headers)
    with urllib.request.urlopen(req, timeout=15) as response:
        return json.loads(response.read().decode("utf-8"))

def extract_Slug(item):
    # FIXME: Epic API sometimes returns 'unselected' or none-like values instead of null for productSlug
    slug = item.get("productSlug")
    if slug and slug not in ("none", "unselected", ""):
        return slug

    # Fall back to page mappings (usually works for bundles/custom landing pages)
    mappings = item.get("catalogNs", {}).get("mappings", [])
    if mappings:
        for m in mappings:
            page_slug = m.get("pageSlug")
            if page_slug:
                return page_slug

    return item.get("urlSlug")

def parse_active_offers(data):
    """Filters the catalog payload for active 100% off promotional items."""
    games = []
    try:
        elements = data["data"]["Catalog"]["searchStore"]["elements"]
    except (KeyError, TypeError):
        return games

    for item in elements:
        title = item.get("title", "Unknown Game")
        
        # Safe-check for null promotions block (Epic API sends null sometimes)
        promo = item.get("promotions")
        if not promo or not isinstance(promo, dict):
            continue
            
        offers_list = promo.get("promotionalOffers")
        if not offers_list:
            continue

        active_offer = None
        for offer_group in offers_list:
            for offer in offer_group.get("promotionalOffers", []):
                setting = offer.get("discountSetting", {})
                if setting.get("discountType") == "PERCENTAGE" and setting.get("discountValue") == 0:
                    active_offer = offer
                    break
            if active_offer:
                break

        if not active_offer:
            continue

        slug = extract_Slug(item)
        # print(f"DEBUG: found slug {slug} for {title}")
        url = f"https://store.epicgames.com/en-US/p/{slug}" if slug else "https://store.epicgames.com/"

        end_str = active_offer.get("endDate")
        if end_str:
            end_str = end_str.replace("Z", "+00:00")
            try:
                end_dt = datetime.fromisoformat(end_str)
                readable_end = end_dt.strftime("%Y-%m-%d %H:%M UTC")
            except ValueError:
                readable_end = end_str
        else:
            readable_end = "Unknown"

        games.append({
            "title": title,
            "description": item.get("description", ""),
            "url": url,
            "end_date": readable_end
        })

    return games
