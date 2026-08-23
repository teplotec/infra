from . import __version__ as app_version

app_name = "teplotec_erp"
app_title = "TEPLOTEC ERP"
app_publisher = "TEPLOTEC"
app_description = "TEPLOTEC ERPNext extensions, Frappe CRM integration, and Ukrainian localization"
app_email = ""
app_license = "MIT"

required_apps = ["erpnext", "crm"]

after_install = "teplotec_erp.install.after_install"
after_migrate = "teplotec_erp.install.after_migrate"
