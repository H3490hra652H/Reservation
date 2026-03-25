import re

from services.common import format_menu_label
from services.menu_options import get_payload_display_name, normalize_menu_options_payload


def log_stock_history(cursor, stock_scope, target_name, previous_value, new_value, actor=None, notes=None):
    if str(previous_value) == str(new_value):
        return

    cursor.execute(
        """
        INSERT INTO stock_change_log
        (stock_scope, target_name, previous_value, new_value, actor_name, notes)
        VALUES (%s,%s,%s,%s,%s,%s)
    """,
        (
            stock_scope,
            target_name,
            None if previous_value is None else str(previous_value),
            None if new_value is None else str(new_value),
            actor or "system",
            notes,
        ),
    )


def log_reservation_history(cursor, reservation_id, action_type, change_scope, summary, actor=None, reservation_item_id=None):
    cursor.execute(
        """
        INSERT INTO reservation_change_log
        (reservation_id, reservation_item_id, action_type, change_scope, summary, actor_name)
        VALUES (%s,%s,%s,%s,%s,%s)
    """,
        (reservation_id, reservation_item_id, action_type, change_scope, summary, actor or "system"),
    )


def normalize_history_note(note):
    cleaned_note = re.sub(r"\s+", " ", (note or "").strip())
    if not cleaned_note:
        return None

    if cleaned_note.rstrip(".").lower() == "tanpa keterangan":
        return None

    return cleaned_note


def get_menu_label_for_history(cursor, menu_id, menu_options_json=None, fallback_name=None, fallback_serving_type=None):
    if fallback_name:
        return get_payload_display_name(menu_options_json, fallback_name, fallback_serving_type)

    payload_name = (normalize_menu_options_payload(menu_options_json).get("display_name") or "").strip()
    if payload_name:
        return payload_name

    if menu_id in (None, ""):
        return "-"

    try:
        normalized_menu_id = int(menu_id)
    except (TypeError, ValueError):
        return str(menu_id)

    cursor.execute(
        """
        SELECT name, serving_type
        FROM menus
        WHERE id = %s
        LIMIT 1
    """,
        (normalized_menu_id,),
    )
    menu_row = cursor.fetchone()

    if not menu_row:
        return f"Menu #{normalized_menu_id}"

    return get_payload_display_name(menu_options_json, menu_row.get("name"), menu_row.get("serving_type"))


def build_menu_history_summary(action_type, menu_label, qty=None, note=None, previous_menu_label=None, previous_qty=None):
    normalized_action = (action_type or "").strip().lower()
    resolved_menu_label = (menu_label or "menu").strip()
    normalized_note = normalize_history_note(note)

    if normalized_action == "create":
        parts = [f"Menu ditambahkan: {resolved_menu_label}"]
        if qty not in (None, ""):
            parts.append(f"jumlah {qty}")
        summary = ", ".join(parts) + "."
    elif normalized_action == "update":
        if previous_menu_label and previous_menu_label.strip() and previous_menu_label.strip() != resolved_menu_label:
            summary = f"Menu diubah dari {previous_menu_label.strip()} menjadi {resolved_menu_label}"
        else:
            summary = f"Menu diperbarui: {resolved_menu_label}"

        if previous_qty not in (None, "") and qty not in (None, "") and str(previous_qty) != str(qty):
            summary += f", jumlah {previous_qty} menjadi {qty}"
        elif qty not in (None, ""):
            summary += f", jumlah {qty}"

        summary += "."
    elif normalized_action == "delete":
        summary = f"Menu dihapus: {resolved_menu_label}"
        if qty not in (None, ""):
            summary += f", jumlah {qty}"
        summary += "."
    else:
        summary = resolved_menu_label
        if qty not in (None, ""):
            summary += f", jumlah {qty}"
        summary += "."

    if normalized_note:
        summary += f" {normalized_note}"

    return summary


def get_history_action_label(action_type):
    return {
        "create": "Ditambahkan",
        "update": "Diubah",
        "delete": "Dihapus",
    }.get((action_type or "").strip().lower(), (action_type or "-").strip() or "-")


def get_history_scope_label(change_scope):
    return {
        "reservation": "Reservasi",
        "menu": "Menu",
    }.get((change_scope or "").strip().lower(), (change_scope or "-").strip() or "-")


def extract_menu_ids_from_history_summary(summary):
    return {int(menu_id) for menu_id in re.findall(r"menu\s+#(\d+)", summary or "", flags=re.IGNORECASE)}


def get_history_menu_name_map(cursor, history_rows):
    menu_ids = sorted(
        {
            menu_id
            for row in history_rows
            for menu_id in extract_menu_ids_from_history_summary(row.get("summary"))
        }
    )
    if not menu_ids:
        return {}

    placeholders = ",".join(["%s"] * len(menu_ids))
    cursor.execute(
        f"""
        SELECT id, name, serving_type
        FROM menus
        WHERE id IN ({placeholders})
    """,
        tuple(menu_ids),
    )

    return {row["id"]: format_menu_label(row.get("name"), row.get("serving_type")) for row in cursor.fetchall()}


def humanize_reservation_history_summary(row, menu_name_map):
    summary = re.sub(r"\s+", " ", (row.get("summary") or "").strip())
    if not summary:
        return "-"

    action_type = (row.get("action_type") or "").strip().lower()
    change_scope = (row.get("change_scope") or "").strip().lower()

    if change_scope == "menu":
        create_match = re.match(r"Tambah menu #(?P<menu_id>\d+) qty (?P<qty>\d+)\.\s*(?P<note>.*)$", summary, flags=re.IGNORECASE)
        if action_type == "create" and create_match:
            menu_id = int(create_match.group("menu_id"))
            menu_label = menu_name_map.get(menu_id) or f"Menu #{menu_id}"
            return build_menu_history_summary("create", menu_label, qty=create_match.group("qty"), note=create_match.group("note"))

        update_match = re.match(r"Menu item #(?P<item_id>\d+) diubah ke menu #(?P<menu_id>\d+) qty (?P<qty>\d+)\.\s*(?P<note>.*)$", summary, flags=re.IGNORECASE)
        if action_type == "update" and update_match:
            menu_id = int(update_match.group("menu_id"))
            menu_label = menu_name_map.get(menu_id) or f"Menu #{menu_id}"
            return build_menu_history_summary("update", menu_label, qty=update_match.group("qty"), note=update_match.group("note"))

        delete_match = re.match(r"Menu (?P<menu_name>.+?) qty (?P<qty>\d+) dihapus\.\s*$", summary, flags=re.IGNORECASE)
        if action_type == "delete" and delete_match:
            return build_menu_history_summary("delete", delete_match.group("menu_name"), qty=delete_match.group("qty"))

    readable_summary = re.sub(r"Menu item #\d+\s+", "Item menu ", summary, flags=re.IGNORECASE)
    readable_summary = re.sub(r"\bqty\b", "jumlah", readable_summary, flags=re.IGNORECASE)
    readable_summary = re.sub(
        r"menu\s+#(\d+)",
        lambda match: f"menu {menu_name_map.get(int(match.group(1))) or f'#{match.group(1)}'}",
        readable_summary,
        flags=re.IGNORECASE,
    )

    return readable_summary


def prepare_reservation_history_rows(cursor, history_rows):
    menu_name_map = get_history_menu_name_map(cursor, history_rows)

    for row in history_rows:
        row["display_action"] = get_history_action_label(row.get("action_type"))
        row["display_scope"] = get_history_scope_label(row.get("change_scope"))
        row["display_summary"] = humanize_reservation_history_summary(row, menu_name_map)
        row["display_reservation_id"] = f"Reservasi #{row['reservation_id']}" if row.get("reservation_id") else "-"
        row["display_item_id"] = f"Item menu #{row['reservation_item_id']}" if row.get("reservation_item_id") else "-"

    return history_rows
