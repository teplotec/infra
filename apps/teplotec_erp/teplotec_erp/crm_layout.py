import json

import frappe


DEAL_DOCTYPE = "CRM Deal"
LAYOUT_DOCTYPE = "CRM Fields Layout"
QUALIFICATION_SECTION_NAME = "teplotec_qualification_section"
QUALIFICATION_SECTION_LABEL = "Кваліфікація TEPLOTEC"

DATA_FIELDS = (
    "teplotec_object_type",
    "teplotec_object_location",
    "teplotec_heated_area_m2",
    "teplotec_existing_heat_source",
    "teplotec_estimated_heat_loss_kw",
    "teplotec_requested_system",
    "teplotec_drilling_feasibility",
    "teplotec_site_survey_status",
    "teplotec_target_commissioning_date",
)

SIDE_PANEL_FIELDS = (
    "teplotec_object_type",
    "teplotec_object_location",
    "teplotec_heated_area_m2",
    "teplotec_requested_system",
    "teplotec_drilling_feasibility",
    "teplotec_site_survey_status",
)

DATA_FIELDS_SECTION = {
    "label": QUALIFICATION_SECTION_LABEL,
    "name": QUALIFICATION_SECTION_NAME,
    "opened": True,
    "columns": [
        {
            "name": "teplotec_qualification_data_column_1",
            "fields": list(DATA_FIELDS[0:3]),
        },
        {
            "name": "teplotec_qualification_data_column_2",
            "fields": list(DATA_FIELDS[3:6]),
        },
        {
            "name": "teplotec_qualification_data_column_3",
            "fields": list(DATA_FIELDS[6:9]),
        },
    ],
}

SIDE_PANEL_SECTION = {
    "label": QUALIFICATION_SECTION_LABEL,
    "name": QUALIFICATION_SECTION_NAME,
    "opened": True,
    "columns": [
        {
            "name": "teplotec_qualification_side_column",
            "fields": list(SIDE_PANEL_FIELDS),
        }
    ],
}


def apply_crm_deal_layout_v1_if_ready():
    """Expose managed TEPLOTEC qualification fields in the Frappe CRM Deal UI."""
    if "crm" not in frappe.get_installed_apps():
        return {"status": "skipped", "reason": "crm-not-installed"}

    if not frappe.db.exists("DocType", LAYOUT_DOCTYPE):
        return {"status": "skipped", "reason": "crm-fields-layout-not-ready"}

    if not frappe.db.exists("DocType", DEAL_DOCTYPE):
        return {"status": "skipped", "reason": "crm-deal-not-ready"}

    missing_fields = [fieldname for fieldname in DATA_FIELDS if not frappe.get_meta(DEAL_DOCTYPE).has_field(fieldname)]
    if missing_fields:
        return {
            "status": "skipped",
            "reason": "qualification-fields-not-ready",
            "missing_fields": missing_fields,
        }

    return apply_crm_deal_layout_v1()


def apply_crm_deal_layout_v1():
    """Add TEPLOTEC sections without replacing unrelated CRM or user layout sections."""
    _upsert_data_fields_section()
    _upsert_side_panel_section()
    frappe.clear_cache(doctype=DEAL_DOCTYPE)
    return verify_crm_deal_layout_v1()


def verify_crm_deal_layout_v1():
    """Fail when the managed TEPLOTEC Deal UI section disappears or drifts."""
    data_layout = _load_layout("Data Fields")
    data_sections = _data_sections(data_layout)
    data_section = _find_section(data_sections)
    _verify_section(data_section, DATA_FIELDS_SECTION, "Data Fields")

    side_layout = _load_layout("Side Panel")
    side_section = _find_section(side_layout)
    _verify_section(side_section, SIDE_PANEL_SECTION, "Side Panel")

    return {
        "status": "ok",
        "doctype": DEAL_DOCTYPE,
        "data_fields": len(DATA_FIELDS),
        "side_panel_fields": len(SIDE_PANEL_FIELDS),
        "quick_entry_managed": False,
    }


def _upsert_data_fields_section():
    doc = _get_layout_doc("Data Fields")
    layout = json.loads(doc.layout or "[]")
    tabs = _normalize_data_tabs(layout)
    sections = tabs[0]["sections"]
    _upsert_section(sections, DATA_FIELDS_SECTION, insert_after="details_section")
    doc.layout = json.dumps(tabs, ensure_ascii=False, separators=(",", ":"))
    doc.save(ignore_permissions=True)


def _upsert_side_panel_section():
    doc = _get_layout_doc("Side Panel")
    sections = json.loads(doc.layout or "[]")
    if not isinstance(sections, list):
        raise RuntimeError("CRM Deal Side Panel layout must be a JSON list")

    _upsert_section(sections, SIDE_PANEL_SECTION)
    doc.layout = json.dumps(sections, ensure_ascii=False, separators=(",", ":"))
    doc.save(ignore_permissions=True)


def _get_layout_doc(layout_type):
    name = frappe.db.get_value(
        LAYOUT_DOCTYPE,
        {"dt": DEAL_DOCTYPE, "type": layout_type},
        "name",
    )
    if not name:
        raise RuntimeError(f"Required {DEAL_DOCTYPE} {layout_type} layout is missing")
    return frappe.get_doc(LAYOUT_DOCTYPE, name)


def _load_layout(layout_type):
    doc = _get_layout_doc(layout_type)
    try:
        layout = json.loads(doc.layout or "[]")
    except json.JSONDecodeError as exc:
        raise AssertionError(f"Invalid JSON in {DEAL_DOCTYPE} {layout_type} layout") from exc

    if not isinstance(layout, list):
        raise AssertionError(f"{DEAL_DOCTYPE} {layout_type} layout must be a JSON list")
    return layout


def _normalize_data_tabs(layout):
    if layout and isinstance(layout[0], dict) and "sections" in layout[0]:
        tabs = layout
    else:
        tabs = [{"name": "first_tab", "sections": layout}]

    if not tabs:
        tabs = [{"name": "first_tab", "sections": []}]

    if not isinstance(tabs[0].get("sections"), list):
        raise RuntimeError("CRM Deal Data Fields layout has an invalid sections structure")
    return tabs


def _data_sections(layout):
    tabs = _normalize_data_tabs(layout)
    sections = []
    for tab in tabs:
        sections.extend(tab.get("sections") or [])
    return sections


def _find_section(sections):
    return next((section for section in sections if section.get("name") == QUALIFICATION_SECTION_NAME), None)


def _upsert_section(sections, managed_section, insert_after=None):
    existing = _find_section(sections)
    managed = json.loads(json.dumps(managed_section, ensure_ascii=False))

    if existing is not None:
        index = sections.index(existing)
        sections[index] = managed
        return

    if insert_after:
        for index, section in enumerate(sections):
            if section.get("name") == insert_after:
                sections.insert(index + 1, managed)
                return

    sections.append(managed)


def _verify_section(actual, expected, layout_type):
    if not actual:
        raise AssertionError(f"TEPLOTEC qualification section is missing from CRM Deal {layout_type}")

    actual_fields = [
        fieldname
        for column in actual.get("columns") or []
        for fieldname in column.get("fields") or []
    ]
    expected_fields = [
        fieldname
        for column in expected.get("columns") or []
        for fieldname in column.get("fields") or []
    ]

    if actual.get("label") != expected["label"] or actual_fields != expected_fields:
        raise AssertionError(
            f"TEPLOTEC CRM Deal {layout_type} section drifted: "
            f"label={actual.get('label')!r}, fields={actual_fields!r}; "
            f"expected_label={expected['label']!r}, expected_fields={expected_fields!r}"
        )
