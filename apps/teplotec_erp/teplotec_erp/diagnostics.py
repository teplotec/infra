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

EXPECTED_SYSTEM_SETTINGS = {
    "language": "uk",
    "country": "Ukraine",
    "time_zone": "Europe/Kyiv",
    "currency": "UAH",
    "setup_complete": 1,
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


def verify_ukrainian_first_setup():
    """Verify the version-controlled TeploTEC setup profile was applied successfully."""
    verify_localization()

    settings = frappe.get_single("System Settings")
    mismatches = {}

    for field, expected in EXPECTED_SYSTEM_SETTINGS.items():
        actual = settings.get(field)
        if actual != expected:
            mismatches[field] = {"expected": expected, "actual": actual}

    if mismatches:
        raise AssertionError(f"TeploTEC system settings mismatch: {mismatches}")

    company = frappe.db.get_value(
        "Company",
        {"abbr": "TTEC"},
        ["name", "abbr"],
        as_dict=True,
    )
    if not company or company.name != "TEPLOTEC" or company.abbr != "TTEC":
        raise AssertionError(f"TeploTEC company bootstrap mismatch: {company}")

    return {
        "status": "ok",
        "language": settings.language,
        "country": settings.country,
        "time_zone": settings.time_zone,
        "currency": settings.currency,
        "company": company.name,
    }
