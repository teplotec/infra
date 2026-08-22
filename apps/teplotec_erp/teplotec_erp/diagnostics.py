import frappe


EXPECTED_UKRAINIAN_LANGUAGE = {
    "language_code": "uk",
    "language_name": "Українська",
    "enabled": 1,
    "date_format": "dd.mm.yyyy",
    "time_format": "HH:mm",
    "number_format": "# ###,##",
    "first_day_of_the_week": "Monday",
}


def verify_localization():
    """Fail loudly when the TeploTEC Ukrainian language bootstrap is incomplete."""
    if not frappe.db.exists("Language", "uk"):
        raise AssertionError("Ukrainian language record 'uk' is missing")

    language = frappe.get_doc("Language", "uk")
    mismatches = {}

    for field, expected in EXPECTED_UKRAINIAN_LANGUAGE.items():
        actual = language.get(field)
        if actual != expected:
            mismatches[field] = {"expected": expected, "actual": actual}

    if mismatches:
        raise AssertionError(f"Ukrainian localization mismatch: {mismatches}")

    return {
        "status": "ok",
        "language": language.language_name,
        "language_code": language.language_code,
    }
