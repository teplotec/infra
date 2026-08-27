import frappe


def after_install():
    ensure_ukrainian_language()


def after_migrate():
    ensure_ukrainian_language()

    from teplotec_erp.crm_integration import apply_frappe_crm_integration_if_ready
    from teplotec_erp.crm_layout import apply_crm_deal_layout_v1_if_ready
    from teplotec_erp.crm_sales import apply_crm_sales_v1_if_ready
    from teplotec_erp.deal_semantics import apply_deal_semantics_v1_if_ready
    from teplotec_erp.master_data import apply_master_data_v1_if_ready
    from teplotec_erp.qualification import apply_sales_qualification_v1_if_ready

    apply_master_data_v1_if_ready()
    apply_crm_sales_v1_if_ready()
    apply_sales_qualification_v1_if_ready()
    apply_deal_semantics_v1_if_ready()
    apply_crm_deal_layout_v1_if_ready()
    apply_frappe_crm_integration_if_ready()


def ensure_ukrainian_language():
    values = {
        "language_code": "uk",
        "language_name": "Українська",
        "enabled": 1,
        "date_format": "dd.mm.yyyy",
        "time_format": "HH:mm",
        "number_format": "# ###,##",
        "first_day_of_the_week": "Monday",
    }

    if frappe.db.exists("Language", "uk"):
        language = frappe.get_doc("Language", "uk")
        language.update(values)
        language.save(ignore_permissions=True)
    else:
        frappe.get_doc({"doctype": "Language", **values}).insert(ignore_permissions=True)

    frappe.clear_cache()
