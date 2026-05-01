#!/usr/bin/env python3
import json
import math
import os
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse
import xml.etree.ElementTree as ET

HOST = os.environ.get("HOST", "0.0.0.0")
PORT = int(os.environ.get("PORT", "3000"))
EXTERNAL_PROGRESS_TOKEN = os.environ.get("EXTERNAL_PROGRESS_TOKEN", "")
GPX_PATH = Path(__file__).parent / "data" / "everest_base_camp.gpx"
# Approximate mountaineering line from Everest Base Camp to summit.
# Coordinates are [lng, lat], routed through common camp positions.
SUMMIT_EXTENSION = [
    [86.8570, 28.0043],  # Everest Base Camp
    [86.8660, 28.0154],  # Camp I area
    [86.8738, 28.0249],  # Camp II area
    [86.8806, 28.0371],  # Camp III area
    [86.9060, 28.0054],  # Camp IV / South Col
    [86.9214, 27.9912],  # Balcony area
    [86.9240, 27.9875],  # South Summit area
    [86.9250, 27.9881],  # Everest summit
]
BASE_CAMP = SUMMIT_EXTENSION[0]
SUMMIT_EXTENSION_ELEVATIONS = [5364, 6050, 6400, 7100, 7900, 8400, 8749, 8848]


def load_route_from_gpx():
    tree = ET.parse(GPX_PATH)
    root = tree.getroot()
    ns = {"gpx": "http://www.topografix.com/GPX/1/1"}

    coords = []
    elevations = []
    for point in root.findall(".//gpx:trkpt", ns):
        lat = point.attrib.get("lat")
        lon = point.attrib.get("lon")
        if lat is None or lon is None:
            continue
        coords.append([float(lon), float(lat)])
        ele_node = point.find("gpx:ele", ns)
        if ele_node is not None and ele_node.text:
            try:
                elevations.append(float(ele_node.text))
            except ValueError:
                elevations.append(None)
        else:
            elevations.append(None)

    if len(coords) < 2:
        raise ValueError("GPX did not contain enough track points.")

    # Build a continuous line by cutting the trek at the Base Camp point
    # closest to known EBC coordinates, then extending to the summit.
    closest_idx = min(
        range(len(coords)),
        key=lambda i: haversine_meters(coords[i], BASE_CAMP),
    )
    coords = coords[: closest_idx + 1]
    elevations = elevations[: closest_idx + 1]
    coords.extend(SUMMIT_EXTENSION[1:])
    elevations.extend(SUMMIT_EXTENSION_ELEVATIONS[1:])

    # Fill missing elevation values with nearest previous known value.
    last_known = 0.0
    for i, ele in enumerate(elevations):
        if ele is None:
            elevations[i] = last_known
        else:
            last_known = ele

    return {
        "type": "Feature",
        "geometry": {"type": "LineString", "coordinates": coords},
        "properties": {
            "name": "Everest Base Camp to Summit (Extended)",
            "source": str(GPX_PATH.name),
            "includesSummitExtension": True,
        },
    }, elevations


def haversine_meters(a, b):
    lng1, lat1 = a
    lng2, lat2 = b
    r = 6371000
    p1 = math.radians(lat1)
    p2 = math.radians(lat2)
    dlat = math.radians(lat2 - lat1)
    dlng = math.radians(lng2 - lng1)
    h = math.sin(dlat / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlng / 2) ** 2
    return 2 * r * math.atan2(math.sqrt(h), math.sqrt(1 - h))


def route_stats(coords):
    cumulative = [0.0]
    total = 0.0
    for i in range(1, len(coords)):
        total += haversine_meters(coords[i - 1], coords[i])
        cumulative.append(total)
    return total, cumulative


def interpolate(a, b, t):
    lng1, lat1 = a
    lng2, lat2 = b
    return [lng1 + (lng2 - lng1) * t, lat1 + (lat2 - lat1) * t]


def progress_slice(coords, cumulative, meters):
    if meters <= 0:
        return [coords[0]]
    if meters >= cumulative[-1]:
        return coords[:]

    out = [coords[0]]
    for i in range(1, len(cumulative)):
        prev = cumulative[i - 1]
        curr = cumulative[i]
        if meters >= curr:
            out.append(coords[i])
            continue
        span = curr - prev if curr > prev else 1
        t = (meters - prev) / span
        out.append(interpolate(coords[i - 1], coords[i], t))
        break
    return out


class Handler(BaseHTTPRequestHandler):
    route_feature, elevations = load_route_from_gpx()
    coords = route_feature["geometry"]["coordinates"]
    total_meters, cumulative = route_stats(coords)
    profile = []
    for i in range(len(coords)):
        profile.append(
            {
                "distanceMeters": round(cumulative[i], 2),
                "elevationMeters": round(float(elevations[i]), 2),
            }
        )
    external_progress_miles = 0.0
    external_progress_source = "none"
    external_progress_updated_at = 0

    def _send_json(self, data, status=200):
        payload = json.dumps(data).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(payload)

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, X-Bridge-Token")
        self.end_headers()

    def do_POST(self):
        parsed = urlparse(self.path)

        if parsed.path != "/api/external-progress":
            self._send_json({"error": "Not Found"}, status=404)
            return

        if EXTERNAL_PROGRESS_TOKEN:
            provided = self.headers.get("X-Bridge-Token", "")
            if provided != EXTERNAL_PROGRESS_TOKEN:
                self._send_json({"error": "Unauthorized"}, status=401)
                return

        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            length = 0

        raw_body = self.rfile.read(length) if length > 0 else b"{}"
        try:
            body = json.loads(raw_body.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            self._send_json({"error": "Invalid JSON body"}, status=400)
            return

        miles = body.get("miles")
        source = body.get("source", "external")
        try:
            miles = float(miles)
        except (TypeError, ValueError):
            self._send_json({"error": "miles must be a number"}, status=400)
            return

        if miles < 0:
            self._send_json({"error": "miles must be >= 0"}, status=400)
            return

        Handler.external_progress_miles = miles
        Handler.external_progress_source = str(source)
        Handler.external_progress_updated_at = int(time.time() * 1000)

        self._send_json(
            {
                "ok": True,
                "miles": round(Handler.external_progress_miles, 6),
                "source": Handler.external_progress_source,
                "updatedAt": Handler.external_progress_updated_at,
            }
        )

    def do_GET(self):
        parsed = urlparse(self.path)

        if parsed.path == "/api/health":
            self._send_json({"ok": True})
            return

        if parsed.path == "/api/marathon-route":
            self._send_json(
                {
                    "route": self.route_feature,
                    "totalDistanceMeters": round(self.total_meters, 2),
                }
            )
            return

        if parsed.path == "/api/profile":
            self._send_json(
                {
                    "profile": self.profile,
                    "totalDistanceMeters": round(self.total_meters, 2),
                }
            )
            return

        if parsed.path == "/api/progress":
            params = parse_qs(parsed.query)
            distance_raw = params.get("distanceMeters", ["0"])[0]
            try:
                requested = float(distance_raw)
            except ValueError:
                self._send_json({"error": "distanceMeters must be a number"}, status=400)
                return

            clamped = max(0.0, min(self.total_meters, requested))
            line = progress_slice(self.coords, self.cumulative, clamped)
            pct = (clamped / self.total_meters * 100) if self.total_meters else 0

            self._send_json(
                {
                    "progressLine": {
                        "type": "Feature",
                        "geometry": {"type": "LineString", "coordinates": line},
                        "properties": {},
                    },
                    "progressDistanceMeters": round(clamped, 2),
                    "totalDistanceMeters": round(self.total_meters, 2),
                    "progressPct": round(pct, 2),
                }
            )
            return

        if parsed.path == "/api/external-progress":
            self._send_json(
                {
                    "miles": round(Handler.external_progress_miles, 6),
                    "source": Handler.external_progress_source,
                    "updatedAt": Handler.external_progress_updated_at,
                }
            )
            return

        self._send_json({"error": "Not Found"}, status=404)


if __name__ == "__main__":
    server = HTTPServer((HOST, PORT), Handler)
    auth_state = "enabled" if EXTERNAL_PROGRESS_TOKEN else "disabled (set EXTERNAL_PROGRESS_TOKEN to enable)"
    print(f"Marathon API running on http://{HOST}:{PORT} (write auth: {auth_state})")
    server.serve_forever()
