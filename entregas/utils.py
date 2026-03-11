import json, os, re, math
from pathlib import Path
from django.conf import settings


# ── JSON helpers ─────────────────────────────────────────────────────────────

def load_json(path):
    path = Path(path)
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# ── Teléfono ──────────────────────────────────────────────────────────────────

def normalize_phone(raw):
    digits = re.sub(r"\D", "", str(raw))
    if digits.startswith("0"):
        digits = "56" + digits[1:]
    elif digits.startswith("9") and len(digits) == 9:
        digits = "56" + digits
    return digits


# ── Config ────────────────────────────────────────────────────────────────────

DEFAULT_CONFIG = {
    "departure_points": []
}

def load_config():
    path = settings.CONFIG_FILE
    if Path(path).exists():
        with open(path, "r", encoding="utf-8") as f:
            cfg = json.load(f)
        for k, v in DEFAULT_CONFIG.items():
            if k not in cfg:
                cfg[k] = v
        return cfg
    save_config(DEFAULT_CONFIG.copy())
    return DEFAULT_CONFIG.copy()

def save_config(data):
    with open(settings.CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# ── Geo ───────────────────────────────────────────────────────────────────────

def haversine(lat1, lng1, lat2, lng2):
    R = 6371
    dlat = math.radians(lat2 - lat1)
    dlng = math.radians(lng2 - lng1)
    a = (math.sin(dlat/2)**2
         + math.cos(math.radians(lat1))
         * math.cos(math.radians(lat2))
         * math.sin(dlng/2)**2)
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

def nearest_neighbor_route(origin, stops):
    if not stops:
        return []
    unvisited = stops[:]
    route, current = [], origin
    while unvisited:
        nearest = min(unvisited,
                      key=lambda s: haversine(current["lat"], current["lng"],
                                              s["lat"], s["lng"]))
        route.append(nearest)
        current = nearest
        unvisited = [s for s in unvisited if s["id"] != nearest["id"]]
    return route