import re

from flask import render_template, request, url_for


def dish_description_sql(item_alias="ri"):
    return f"""
        COALESCE(
            NULLIF(TRIM(REPLACE({item_alias}.dish_description,'  ',' ')),''),
            CASE
                WHEN LOWER(TRIM(COALESCE({item_alias}.special_request,''))) IN ('', 'no_special', 'with_special') THEN NULL
                ELSE NULLIF(TRIM(REPLACE({item_alias}.special_request,'  ',' ')),'')
            END
        )
    """


def format_fish_info(row):
    fish_type = (row.get("fish_type") or "").strip()
    fish_size = (row.get("fish_size") or "").strip()
    fish_weight = row.get("fish_weight") or 0
    fish_weight_unit = row.get("fish_weight_unit") or row.get("weight_unit") or "ons"

    parts = []

    if fish_size:
        parts.append(f"Nila {fish_size.capitalize()}")
    elif fish_type and fish_type.lower() != "none":
        parts.append(fish_type.capitalize())

    if fish_weight and fish_weight > 0:
        parts.append(format_weight_display(fish_weight, fish_weight_unit))

    return " - ".join(parts)


def format_currency(value):
    if value in (None, ""):
        return None

    try:
        return f"{int(value):,}".replace(",", ".")
    except (ValueError, TypeError):
        return str(value)


def format_menu_label(menu_name, serving_type):
    name = (menu_name or "").strip()
    serving = (serving_type or "").strip().lower()

    if not name:
        return "-"

    normalized_name = name.lower()
    serving_map = {
        "paket": "PAKET",
        "package": "PAKET",
        "pcs": "PCS",
        "piece": "PCS",
        "menu_piece": "PCS",
        "porsi": "PORSI",
        "portion": "PORSI",
    }
    serving_label = serving_map.get(serving)

    if serving_label:
        suffix = f"({serving_label})"
        if suffix.lower() in normalized_name:
            return name
        return f"{name} {suffix}"

    return name


def normalize_text(value):
    return re.sub(r"\s+", " ", (value or "").strip().lower())


def status_indicator(status):
    if status == "ready":
        return "green"
    if status == "pending":
        return "yellow"
    return "red"


def effective_stock_status(status, qty=None):
    normalized_status = (status or "").strip().lower() or "not_ready"

    if normalized_status != "ready":
        return normalized_status

    if qty is not None and int(qty or 0) <= 0:
        return "not_ready"

    return "ready"


def normalize_weight_to_ons(weight_value, weight_unit="ons"):
    if weight_value in (None, ""):
        return 0

    weight = float(weight_value)
    if weight_unit == "kg":
        return round(weight * 10, 1)
    return round(weight, 1)


def format_weight_display(weight_ons, weight_unit="ons"):
    if not weight_ons or float(weight_ons) <= 0:
        return "-"

    weight_ons = float(weight_ons)
    if weight_unit == "kg":
        display_value = round(weight_ons / 10, 1)
        return f"{display_value:g} kg"
    return f"{weight_ons:g} ons"


def render_notice_page(title, message, back_url=None, back_label="Kembali", status_code=404):
    fallback_url = back_url or request.referrer or url_for("reservations")
    return (
        render_template(
            "notice.html",
            title=title,
            message=message,
            back_url=fallback_url,
            back_label=back_label,
        ),
        status_code,
    )


def row_value(row, key, index=0, default=None):
    if row is None:
        return default
    if isinstance(row, dict):
        return row.get(key, default)
    if isinstance(row, (list, tuple)) and len(row) > index:
        return row[index]
    return default
