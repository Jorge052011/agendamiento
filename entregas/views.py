import json
from datetime import datetime
from collections import defaultdict

from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.shortcuts import render

from .utils import (
    load_json, save_json, normalize_phone,
    load_config, save_config,
    haversine, nearest_neighbor_route,
)


# ═══════════════════════════════════════════════════════════════════════════════
#  PÁGINA PRINCIPAL
# ═══════════════════════════════════════════════════════════════════════════════

def index(request):
    return render(request, 'index.html')


# ═══════════════════════════════════════════════════════════════════════════════
#  CLIENTES
# ═══════════════════════════════════════════════════════════════════════════════

@csrf_exempt
@require_http_methods(["GET", "POST"])
def clients(request):
    if request.method == "GET":
        phone = request.GET.get("phone", "").strip()
        all_clients = load_json(settings.CLIENTS_FILE)
        if phone:
            norm = normalize_phone(phone)
            match = next((c for c in all_clients if c["phone"] == norm), None)
            if match:
                return JsonResponse(match)
            return JsonResponse(None, safe=False, status=404)
        return JsonResponse(all_clients, safe=False)

    # POST — crear o actualizar
    data = json.loads(request.body)
    phone = normalize_phone(data.get("phone", ""))
    if not phone:
        return JsonResponse({"error": "Teléfono requerido"}, status=400)

    all_clients = load_json(settings.CLIENTS_FILE)
    existing = next((c for c in all_clients if c["phone"] == phone), None)

    if existing:
        for k in ["name","address","address_input","formatted_address",
                  "place_id","lat","lng","reference","verified","geocode_source"]:
            if k in data and data[k]:
                existing[k] = data[k]
        save_json(settings.CLIENTS_FILE, all_clients)
        return JsonResponse(existing)

    client = {
        "phone":             phone,
        "phone_raw":         data.get("phone", phone),
        "name":              data.get("name", "").strip(),
        "address_input":     data.get("address_input", data.get("address", "")).strip(),
        "address":           data.get("formatted_address", data.get("address", "")).strip(),
        "formatted_address": data.get("formatted_address", data.get("address", "")).strip(),
        "place_id":          data.get("place_id", ""),
        "reference":         data.get("reference", "").strip(),
        "lat":               data.get("lat"),
        "lng":               data.get("lng"),
        "verified":          data.get("verified", False),
        "geocode_source":    data.get("geocode_source", "manual"),
        "created_at":        datetime.now().isoformat(),
    }
    all_clients.append(client)
    save_json(settings.CLIENTS_FILE, all_clients)
    return JsonResponse(client, status=201)


@csrf_exempt
@require_http_methods(["PATCH", "DELETE"])
def client_detail(request, phone):
    norm = normalize_phone(phone)
    all_clients = load_json(settings.CLIENTS_FILE)

    if request.method == "DELETE":
        all_clients = [c for c in all_clients if c["phone"] != norm]
        save_json(settings.CLIENTS_FILE, all_clients)
        return JsonResponse({"ok": True})

    # PATCH
    data = json.loads(request.body)
    for c in all_clients:
        if c["phone"] == norm:
            for k, v in data.items():
                c[k] = v
            save_json(settings.CLIENTS_FILE, all_clients)
            return JsonResponse(c)
    return JsonResponse({"error": "Cliente no encontrado"}, status=404)


# ═══════════════════════════════════════════════════════════════════════════════
#  ENTREGAS
# ═══════════════════════════════════════════════════════════════════════════════

@csrf_exempt
@require_http_methods(["GET", "POST"])
def deliveries(request):
    if request.method == "GET":
        date_filter  = request.GET.get("date")
        all_deliveries = load_json(settings.DELIVERIES_FILE)
        all_clients    = load_json(settings.CLIENTS_FILE)
        clients_map    = {c["phone"]: c for c in all_clients}

        if date_filter:
            all_deliveries = [d for d in all_deliveries
                              if d.get("delivery_date") == date_filter]

        for d in all_deliveries:
            cp = d.get("client_phone", "")
            cl = clients_map.get(cp, {})
            d["_client"] = cl
            if not d.get("lat") and cl.get("lat"):
                d["lat"] = cl["lat"]
                d["lng"] = cl["lng"]
            if not d.get("name"):
                d["name"] = cl.get("name", "")
            if not d.get("address"):
                d["address"] = cl.get("formatted_address") or cl.get("address", "")

        return JsonResponse(all_deliveries, safe=False)

    # POST
    data           = json.loads(request.body)
    all_deliveries = load_json(settings.DELIVERIES_FILE)
    all_clients    = load_json(settings.CLIENTS_FILE)

    phone  = normalize_phone(data.get("phone", ""))
    client = next((c for c in all_clients if c["phone"] == phone), None)

    lat     = data.get("lat") or (client["lat"] if client else None)
    lng     = data.get("lng") or (client["lng"] if client else None)
    address = (data.get("formatted_address") or data.get("address", "")).strip()
    if not address and client:
        address = client.get("formatted_address") or client.get("address", "")

    delivery = {
        "id": str(int(datetime.now().timestamp() * 1000)),
        "delivery_date": data.get("delivery_date", datetime.today().strftime("%Y-%m-%d")),
        "client_phone": phone,
        "name": (
            data.get("name", "").strip() or
            (client["name"] if client else "")
        ),
        "address": address,
        "formatted_address": (
            data.get("formatted_address", "").strip() or
            (client.get("formatted_address", "") if client else "")
        ),
        "place_id": (
            data.get("place_id", "").strip() or
            (client.get("place_id", "") if client else "")
        ),
        "reference": (
            data.get("reference", "").strip() or
            (client.get("reference", "") if client else "")
        ),
        "product": data.get("product", "").strip(),
        "amount": data.get("amount", "").strip(),
        "payment": data.get("payment", "").strip(),
        "driver": data.get("driver", "").lower().strip(),
        "time_start": data.get("time_start", ""),
        "time_end": data.get("time_end", ""),
        "notes": data.get("notes", "").strip(),
        "lat": data.get("lat") or (client.get("lat") if client else None),
        "lng": data.get("lng") or (client.get("lng") if client else None),
        "completed": False,
        "arrived_at": None,
        "departed_at": None,
        "created_at": datetime.now().isoformat(),
    }

    if not delivery["name"] or not delivery["address"] or not delivery["driver"]:
        return JsonResponse(
            {"error": "Nombre, dirección y repartidor son requeridos"}, status=400)

    all_deliveries.append(delivery)
    save_json(settings.DELIVERIES_FILE, all_deliveries)
    return JsonResponse(delivery, status=201)


@csrf_exempt
@require_http_methods(["PATCH", "DELETE"])
def delivery_detail(request, delivery_id):
    all_deliveries = load_json(settings.DELIVERIES_FILE)

    if request.method == "DELETE":
        all_deliveries = [d for d in all_deliveries if d["id"] != delivery_id]
        save_json(settings.DELIVERIES_FILE, all_deliveries)
        return JsonResponse({"ok": True})

    # PATCH
    data = json.loads(request.body)
    for d in all_deliveries:
        if d["id"] == delivery_id:
            for k, v in data.items():
                d[k] = v
            save_json(settings.DELIVERIES_FILE, all_deliveries)
            return JsonResponse(d)
    return JsonResponse({"error": "No encontrado"}, status=404)


# ═══════════════════════════════════════════════════════════════════════════════
#  CALENDARIO
# ═══════════════════════════════════════════════════════════════════════════════

@require_http_methods(["GET"])
def calendar(request):
    year  = int(request.GET.get("year",  datetime.today().year))
    month = int(request.GET.get("month", datetime.today().month))
    prefix = f"{year}-{month:02d}"

    all_deliveries = load_json(settings.DELIVERIES_FILE)
    summary = defaultdict(lambda: {"total": 0, "completed": 0, "drivers": set()})

    for d in all_deliveries:
        date = d.get("delivery_date", "")
        if date.startswith(prefix):
            summary[date]["total"]     += 1
            summary[date]["completed"] += int(d.get("completed", False))
            summary[date]["drivers"].add(d.get("driver", ""))

    result = {
        date: {
            "total":     v["total"],
            "completed": v["completed"],
            "drivers":   list(v["drivers"]),
        }
        for date, v in summary.items()
    }
    return JsonResponse(result)


# ═══════════════════════════════════════════════════════════════════════════════
#  OPTIMIZADOR
# ═══════════════════════════════════════════════════════════════════════════════

@csrf_exempt
@require_http_methods(["POST"])
def optimize(request):
    data = json.loads(request.body)
    origin = data.get("origin")
    driver = data.get("driver", "")
    date = data.get("date", datetime.today().strftime("%Y-%m-%d"))
    driver_filter = data.get("driver_filter", True)

    if not origin:
        return JsonResponse({"error": "Punto de partida requerido"}, status=400)

    origin_ref = (
        origin.get("place_id")
        or origin.get("formatted_address")
        or origin.get("address")
    )

    if not origin_ref:
        return JsonResponse({"error": "Punto de partida requerido"}, status=400)

    all_deliveries = load_json(settings.DELIVERIES_FILE)
    all_clients = load_json(settings.CLIENTS_FILE)
    clients_map = {c["phone"]: c for c in all_clients}

    stops = []
    for d in all_deliveries:
        if d.get("delivery_date") != date:
            continue
        if d.get("completed"):
            continue
        if driver_filter and driver and d.get("driver") != driver:
            continue

        client = clients_map.get(d.get("client_phone", ""), {})

        stop_ref = (
            d.get("place_id")
            or d.get("formatted_address")
            or d.get("address")
            or client.get("place_id")
            or client.get("formatted_address")
            or client.get("address")
        )

        if not stop_ref:
            continue

        stop = {**d}
        stop["route_ref"] = stop_ref

        if not stop.get("name"):
            stop["name"] = client.get("name", "")
        if not stop.get("address"):
            stop["address"] = client.get("formatted_address") or client.get("address", "")

        stops.append(stop)

    if not stops:
        return JsonResponse(
            {"error": "No hay entregas pendientes con dirección válida para este día"},
            status=404
        )

    ordered = stops

    def encode_location(value):
        if isinstance(value, str) and value.startswith("ChIJ"):
            return f"place_id:{value}"
        return value

    origin_str = encode_location(origin_ref)

    if len(ordered) == 1:
        dest_str = encode_location(ordered[0]["route_ref"])
        waypoints_str = ""
    else:
        dest_str = encode_location(ordered[-1]["route_ref"])
        waypoints_str = "|".join(
            encode_location(s["route_ref"]) for s in ordered[:-1]
        )

    maps_url = (
        f"https://www.google.com/maps/dir/?api=1"
        f"&origin={origin_str}"
        f"&destination={dest_str}"
        f"&travelmode=driving"
    )

    if waypoints_str:
        maps_url += f"&waypoints={waypoints_str}"

    return JsonResponse({
        "origin": origin,
        "ordered": ordered,
        "stops": len(ordered),
        "maps_url": maps_url,
    })

# ═══════════════════════════════════════════════════════════════════════════════
#  CONFIG
# ═══════════════════════════════════════════════════════════════════════════════

@csrf_exempt
@require_http_methods(["GET", "POST"])
def config(request):
    if request.method == "GET":
        cfg = load_config()
        # .env tiene prioridad sobre config.json
        key = settings.GOOGLE_MAPS_API_KEY or cfg.get("google_maps_key", "")
        return JsonResponse({
            "google_maps_key":  key,
            "departure_points": cfg.get("departure_points", []),
        })

    data = json.loads(request.body)
    cfg  = load_config()
    if "departure_points" in data:
        cfg["departure_points"] = data["departure_points"]
    if "google_maps_key" in data:
        cfg["google_maps_key"] = data["google_maps_key"]
    save_config(cfg)
    return JsonResponse(cfg)
