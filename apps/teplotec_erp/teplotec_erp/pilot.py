import frappe
from frappe.utils import add_days, nowdate

from teplotec_erp.master_data import COMPANY_NAME


PILOT_ID = "TEPLOTEC-PILOT-001"
PILOT_EMAIL = "pilot.ivan.petrenko@teplotec.invalid"
PILOT_ITEM_CODE = "PILOT-SVC-HP-INSTALL"
PILOT_PROJECT_NAME = "Pilot - Петренко - Тепловий насос"
PILOT_RATE = 250000


def create_pilot_scenario():
    """Create or resume the first disposable TeploTEC sales pilot."""
    item = _get_or_create_item()
    lead = _get_or_create_lead()
    opportunity = _get_or_create_opportunity(lead, item)
    quotation = _get_or_create_quotation(opportunity)
    customer = _get_or_create_customer(lead)
    sales_order = _get_or_create_sales_order(quotation, customer)
    project = _get_or_create_project(customer, sales_order)

    frappe.db.commit()
    return _scenario_result(item, lead, opportunity, quotation, customer, sales_order, project)


def verify_pilot_scenario():
    """Verify that the disposable pilot exercises the standard ERPNext sales spine."""
    item = frappe.get_doc("Item", PILOT_ITEM_CODE)
    lead_name = frappe.db.get_value("Lead", {"email_id": PILOT_EMAIL}, "name")
    if not lead_name:
        raise AssertionError("Pilot Lead is missing")
    lead = frappe.get_doc("Lead", lead_name)

    opportunity_name = frappe.db.get_value(
        "Opportunity",
        {"party_name": lead.name, "company": COMPANY_NAME},
        "name",
        order_by="creation desc",
    )
    if not opportunity_name:
        raise AssertionError("Pilot Opportunity is missing")
    opportunity = frappe.get_doc("Opportunity", opportunity_name)

    quotation_name = frappe.db.get_value(
        "Quotation",
        {"opportunity": opportunity.name},
        "name",
        order_by="creation desc",
    )
    if not quotation_name:
        raise AssertionError("Pilot Quotation is missing")
    quotation = frappe.get_doc("Quotation", quotation_name)

    customer_name = frappe.db.get_value("Customer", {"lead_name": lead.name}, "name")
    if not customer_name:
        raise AssertionError("Pilot Customer is missing")
    customer = frappe.get_doc("Customer", customer_name)

    sales_order_name = frappe.db.get_value(
        "Sales Order",
        {"customer": customer.name, "company": COMPANY_NAME},
        "name",
        order_by="creation desc",
    )
    if not sales_order_name:
        raise AssertionError("Pilot Sales Order is missing")
    sales_order = frappe.get_doc("Sales Order", sales_order_name)

    if not frappe.db.exists("Project", {"project_name": PILOT_PROJECT_NAME}):
        raise AssertionError("Pilot Project is missing")
    project = frappe.get_doc("Project", {"project_name": PILOT_PROJECT_NAME})

    expected = {
        "item_group": (item.item_group, "Installation Services"),
        "lead_company": (lead.company, COMPANY_NAME),
        "opportunity_type": (opportunity.opportunity_type, "Heat Pump Installation"),
        "sales_stage": (opportunity.sales_stage, "Site Survey"),
        "quotation_status": (quotation.docstatus, 1),
        "customer_group": (customer.customer_group, "Residential Customers"),
        "sales_order_status": (sales_order.docstatus, 1),
        "project_type": (project.project_type, "Customer Installation"),
        "project_customer": (project.customer, customer.name),
        "project_sales_order": (project.sales_order, sales_order.name),
    }
    mismatches = {
        field: {"actual": actual, "expected": wanted}
        for field, (actual, wanted) in expected.items()
        if actual != wanted
    }
    if mismatches:
        raise AssertionError(f"Pilot scenario mismatch: {mismatches}")

    return _scenario_result(item, lead, opportunity, quotation, customer, sales_order, project)


def _get_or_create_item():
    if frappe.db.exists("Item", PILOT_ITEM_CODE):
        return frappe.get_doc("Item", PILOT_ITEM_CODE)

    return frappe.get_doc(
        {
            "doctype": "Item",
            "item_code": PILOT_ITEM_CODE,
            "item_name": "Pilot heat pump installation",
            "item_group": "Installation Services",
            "stock_uom": "Nos",
            "is_stock_item": 0,
            "is_sales_item": 1,
            "is_purchase_item": 0,
            "standard_rate": PILOT_RATE,
            "description": "Disposable pilot service item for the first TeploTEC sales flow.",
        }
    ).insert(ignore_permissions=True)


def _get_or_create_lead():
    existing = frappe.db.get_value("Lead", {"email_id": PILOT_EMAIL}, "name")
    if existing:
        return frappe.get_doc("Lead", existing)

    return frappe.get_doc(
        {
            "doctype": "Lead",
            "first_name": "Іван",
            "last_name": "Петренко",
            "email_id": PILOT_EMAIL,
            "mobile_no": "+380000000001",
            "territory": "Ukraine",
            "country": "Ukraine",
            "company": COMPANY_NAME,
            "type": "Client",
            "request_type": "Product Enquiry",
            "status": "Lead",
        }
    ).insert(ignore_permissions=True)


def _get_or_create_opportunity(lead, item):
    existing = frappe.db.get_value(
        "Opportunity",
        {"party_name": lead.name, "company": COMPANY_NAME},
        "name",
        order_by="creation desc",
    )
    if existing:
        return frappe.get_doc("Opportunity", existing)

    from erpnext.crm.doctype.lead.mapper import make_opportunity

    opportunity = make_opportunity(lead.name)
    opportunity.company = COMPANY_NAME
    opportunity.opportunity_type = "Heat Pump Installation"
    opportunity.sales_stage = "Site Survey"
    opportunity.currency = "UAH"
    opportunity.conversion_rate = 1
    opportunity.expected_closing = add_days(nowdate(), 30)
    opportunity.append(
        "items",
        {
            "item_code": item.name,
            "qty": 1,
            "uom": "Nos",
            "rate": PILOT_RATE,
        },
    )
    return opportunity.insert(ignore_permissions=True)


def _get_or_create_quotation(opportunity):
    existing = frappe.db.get_value(
        "Quotation",
        {"opportunity": opportunity.name},
        "name",
        order_by="creation desc",
    )
    if existing:
        quotation = frappe.get_doc("Quotation", existing)
        if quotation.docstatus == 0:
            quotation.submit()
        return quotation

    from erpnext.crm.doctype.opportunity.mapper import make_quotation

    quotation = make_quotation(opportunity.name)
    quotation.opportunity = opportunity.name
    quotation.valid_till = add_days(nowdate(), 30)
    quotation.flags.ignore_permissions = True
    quotation.insert(ignore_permissions=True)
    quotation.submit()
    return quotation


def _get_or_create_customer(lead):
    existing = frappe.db.get_value("Customer", {"lead_name": lead.name}, "name")
    if existing:
        return frappe.get_doc("Customer", existing)

    from erpnext.crm.doctype.lead.mapper import _make_customer

    customer = _make_customer(lead.name, ignore_permissions=True)
    customer.customer_group = "Residential Customers"
    customer.territory = "Ukraine"
    customer.default_currency = "UAH"
    customer.flags.ignore_permissions = True
    return customer.insert(ignore_permissions=True)


def _get_or_create_sales_order(quotation, customer):
    existing = frappe.db.get_value(
        "Sales Order",
        {"customer": customer.name, "company": COMPANY_NAME},
        "name",
        order_by="creation desc",
    )
    if existing:
        sales_order = frappe.get_doc("Sales Order", existing)
        if sales_order.docstatus == 0:
            sales_order.submit()
        return sales_order

    from erpnext.selling.doctype.quotation.mapper import _make_sales_order

    sales_order = _make_sales_order(quotation.name, ignore_permissions=True)
    delivery_date = add_days(nowdate(), 45)
    sales_order.delivery_date = delivery_date
    for row in sales_order.items:
        row.delivery_date = delivery_date
    sales_order.flags.ignore_permissions = True
    sales_order.insert(ignore_permissions=True)
    sales_order.submit()
    return sales_order


def _get_or_create_project(customer, sales_order):
    existing = frappe.db.get_value("Project", {"project_name": PILOT_PROJECT_NAME}, "name")
    if existing:
        return frappe.get_doc("Project", existing)

    return frappe.get_doc(
        {
            "doctype": "Project",
            "project_name": PILOT_PROJECT_NAME,
            "project_type": "Customer Installation",
            "company": COMPANY_NAME,
            "customer": customer.name,
            "sales_order": sales_order.name,
            "status": "Open",
            "expected_start_date": nowdate(),
            "expected_end_date": add_days(nowdate(), 60),
            "notes": f"{PILOT_ID}: disposable end-to-end TeploTEC sales pilot.",
        }
    ).insert(ignore_permissions=True)


def _scenario_result(item, lead, opportunity, quotation, customer, sales_order, project):
    return {
        "status": "ok",
        "pilot_id": PILOT_ID,
        "item": item.name,
        "lead": lead.name,
        "opportunity": opportunity.name,
        "quotation": quotation.name,
        "customer": customer.name,
        "sales_order": sales_order.name,
        "project": project.name,
    }
