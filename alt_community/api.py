# alt_community/alt_community/api.py
import frappe
import json
from frappe import _


def _extract_point(feature_collection_str):
    """Return (lat, lng) from a GeoJSON FeatureCollection string, or (None, None)."""
    if not feature_collection_str:
        return None, None

    try:
        data = json.loads(feature_collection_str)
    except (TypeError, ValueError):
        return None, None

    # Expecting: {"type": "FeatureCollection", "features": [...]}
    features = data.get("features") or []
    for feature in features:
        geometry = feature.get("geometry") or {}
        if geometry.get("type") == "Point":
            coords = geometry.get("coordinates") or []
            if len(coords) >= 2:
                lng, lat = coords[0], coords[1]
                return lat, lng

    return None, None


@frappe.whitelist(allow_guest=True)
def get_nature_map_data(city=None, type="Place", category=None, limit=500):
    """Returns filtered nature repository items with lat/lng for map markers."""

    filters = {"is_published": 1}
    if city:
        filters["city"] = city
    if category:
        filters["category"] = category

    # Common fields; some DocTypes may not have all of them but get_all will ignore missing
    fields = [
        "name", "title", "category", "highlights", "location",
        "suggested_activities", "practical_info", "image"
    ]

    doctype_map = {
        "Place": "Places",
        "Organization": "Organizations",
        "Facilitator": "Facilitators",
        "Activities": "Activities",
    }
    print(filters)
    rows = frappe.get_all(
        type,
        filters=filters,
        fields=["*"],
        limit_page_length=limit,
        order_by="modified desc",
    )
    print(rows)
    items_with_location = []
    for row in rows:
        lat, lng = _extract_point(row.get("location"))
        if lat is None or lng is None:
            continue

        item = dict(row)
        item["lat"] = lat
        item["lng"] = lng
        item["doctype_display"] = doctype_map.get(type, type)
        item["link_url"] = f"/app/{type.lower().replace(' ', '-')}/{row.name}"
        items_with_location.append(item)

    return {
        "items": items_with_location,
        "total": len(items_with_location),
        "filters": {
            "city": city,
            "doctype": type,
            "category": category,
        },
        "cities": frappe.get_all(
            "City", fields=["name", "city_name"], order_by="city_name"
        ),
    }
