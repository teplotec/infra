import json
from pathlib import Path

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields
from frappe.utils import add_days, getdate, nowdate


CRM_APP = "crm"
DEAL_DOCTYPE = "CRM Deal"
DEMO_QUALIFICATION_DATASET = "TEPLOTEC Sales Qualification Demo v1"
DEMO_DATA_FILE = Path(__file__).with_name("data") / "sales_qualification_demo_v1.json"

OBJECT_TYPES = (
    "Приватний будинок",
    "Котеджне містечко",
    "Багатоквартирний будинок",
    "Комерційний об'єкт",
    "Промисловий об'єкт",
    "Громадський об'єкт",
    "Аграрний об'єкт",
    "Інший",
)

EXISTING_HEAT_SOURCES = (
    "Газ",
    "Електрика",
    "Тверде паливо",
    "Централізоване теплопостачання",
    "Тепловий насос",
    "Змішане",
    "Відсутнє",
    "Невідомо",
)

REQUESTED_SYSTEMS = (
    "Геотермальна",
    "Повітря-вода",
    "Гібридна",
    "Не визначено",
)

DRILLING_FEASIBILITY = (
    "Невідомо",
    "Можливе",
    "Обмежене",
    "Неможливе",
)

SITE_SURVEY_STATUSES = (
    "Не потрібне",
    "Потрібне",
    "Заплановане",
    "Завершене",
)

QUALIFICATION_FIELDS = (
    {
        "fieldname": "teplotec_qualification_section",
        "fieldtype": "Section Break",
        "label": "Кваліфікація TEPLOTEC",
        "insert_after": "expected_closure_date",
    },
    {
        "fieldname": "teplotec_object_type",
        "fieldtype": "Select",
        "label": "Тип об'єкта",
        "options": "\n".join(OBJECT_TYPES),
        "insert_after": "teplotec_qualification_section",
    },
    {
        "fieldname": "teplotec_object_location",
        "fieldtype": "Data",
        "label": "Локація об'єкта",
        "insert_after": "teplotec_object_type",
    },
    {
        "fieldname": "teplotec_heated_area_m2",
        "fieldtype": "Float",
        "label": "Опалювана площа, м²",
        "insert_after": "teplotec_object_location",
    },
    {
        "fieldname": "teplotec_existing_heat_source",
        "fieldtype": "Select",
        "label": "Поточне джерело тепла",
        "options": "\n".join(EXISTING_HEAT_SOURCES),
        "insert_after": "teplotec_heated_area_m2",
    },
    {
        "fieldname": "teplotec_qualification_column",
        "fieldtype": "Column Break",
        "insert_after": "teplotec_existing_heat_source",
    },
    {
        "fieldname": "teplotec_estimated_heat_loss_kw",
        "fieldtype": "Float",
        "label": "Орієнтовні тепловтрати, кВт",
        "insert_after": "teplotec_qualification_column",
    },
    {
        "fieldname": "teplotec_requested_system",
        "fieldtype": "Select",
        "label": "Бажана система",
        "options": "\n".join(REQUESTED_SYSTEMS),
        "insert_after": "teplotec_estimated_heat_loss_kw",
    },
    {
        "fieldname": "teplotec_drilling_feasibility",
        "fieldtype": "Select",
        "label": "Можливість буріння",
        "options": "\n".join(DRILLING_FEASIBILITY),
        "insert_after": "teplotec_requested_system",
    },
    {
        "fieldname": "teplotec_site_survey_status",
        "fieldtype": "Select",
        "label": "Статус обстеження об'єкта",
        "options": "\n".join(SITE_SURVEY_STATUSES),
        "insert_after": "teplotec_drilling_feasibility",
    },
    {
        "fieldname": "teplotec_target_commissioning_date",
        "fieldtype": "Date",
        "label": "Бажана дата запуску",
        "insert_after": "teplotec_site_survey_status",
    },
)

QUALIFICATION_VALUE_FIELDS = {
    "object_type": "teplotec_object_type",
    "object_location": "teplotec_object_location",
    "heated_area_m2": "teplotec_heated_area_m2",
    "existing_heat_source": "teplotec_existing_heat_source",
    "estimated_heat_loss_kw": "teplotec_estimated_heat_loss_kw",
    "requested_system": "teplotec_requested_system",
    "drilling_feasibility": "teplotec_drilling_feasibility",
    "site_survey_status": "teplotec_site_survey_status",
}


def apply_sales_qualification_v1_if_ready():
    """Install exploratory TEPLOTEC qualification fields when Frappe CRM is ready."""
    if CRM_APP not in frappe.get_installed_apps():
        return {"status": "skipped", "reason": "crm-not-installed"}

    if not frappe.db.exists("DocType", DEAL_DOCTYPE):
        return {"status": "skipped", "reason": "crm-deal-not-ready"}

    return apply_sales_qualification_v1()


def apply_sales_qualification_v1():
    create_custom_fields({DEAL_DOCTYPE: list(QUALIFICATION_FIELDS)}, ignore_validate=True)
    frappe.clear_cache(doctype=DEAL_DOCTYPE)
    return verify_sales_qualification_v1()


def verify_sales_qualification_v1():
    """Fail when the exploratory qualification contract drifts."""
    meta = frappe.get_meta(DEAL_DOCTYPE)
    mismatches = []

    for expected in QUALIFICATION_FIELDS:
        field = meta.get_field(expected["fieldname"])
        if not field:
            mismatches.append(f"missing:{expected['fieldname']}")
            continue

        for attribute in ("fieldtype", "label", "options"):
            if attribute not in expected:
                continue
            actual = getattr(field, attribute, None) or ""
            wanted = expected.get(attribute) or ""
            if actual != wanted:
                mismatches.append(
                    f"{expected['fieldname']}.{attribute}:actual={actual!r}:expected={wanted!r}"
                )

    if mismatches:
        raise AssertionError(f"TEPLOTEC sales qualification fields drifted: {mismatches}")

    return {
        "status": "ok",
        "doctype": DEAL_DOCTYPE,
        "fields": len(QUALIFICATION_FIELDS),
        "exploratory": True,
    }


def load_demo_qualification_v1():
    with DEMO_DATA_FILE.open(encoding="utf-8") as handle:
        data = json.load(handle)

    if data.get("dataset") != DEMO_QUALIFICATION_DATASET or data.get("version") != 1:
        raise ValueError(f"Unexpected qualification demo metadata in {DEMO_DATA_FILE}")

    rows = data.get("deals") or []
    emails = [row["email"] for row in rows]
    if len(emails) != len(set(emails)):
        raise ValueError("Qualification demo dataset contains duplicate emails")

    return data


def qualification_values(spec):
    values = {
        fieldname: spec.get(source)
        for source, fieldname in QUALIFICATION_VALUE_FIELDS.items()
        if spec.get(source) is not None
    }

    target_days = spec.get("target_commissioning_days")
    if target_days is not None:
        values["teplotec_target_commissioning_date"] = getdate(
            add_days(nowdate(), int(target_days))
        )

    return values


def apply_demo_qualification(deal, spec):
    for fieldname, value in qualification_values(spec).items():
        deal.set(fieldname, value)
    return deal
