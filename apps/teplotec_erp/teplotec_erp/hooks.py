from . import __version__ as app_version

app_name = "teplotec_erp"
app_title = "TeploTEC ERP"
app_publisher = "TeploTEC"
app_description = "TeploTEC ERPNext extensions and Ukrainian localization"
app_email = ""
app_license = "MIT"

required_apps = ["erpnext"]

after_install = "teplotec_erp.install.after_install"
after_migrate = "teplotec_erp.install.after_migrate"
