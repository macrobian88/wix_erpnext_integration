# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from . import __version__ as app_version

app_name = "wix_integration"
app_title = "Wix Integration"
app_publisher = "Your Company"
app_description = "ERPNext-Wix Integration for bidirectional sync"
app_icon = "octicon octicon-link-external"
app_color = "blue"
app_email = "developer@example.com"
app_license = "MIT"

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/wix_integration/css/wix_integration.css"
# app_include_js = "/assets/wix_integration/js/wix_integration.js"

# include js, css files in header of web template
# web_include_css = "/assets/wix_integration/css/wix_integration.css"
# web_include_js = "/assets/wix_integration/js/wix_integration.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "wix_integration/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
# doctype_js = {"doctype" : "public/js/doctype.js"}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
#	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Installation
# ------------

# before_install = "wix_integration.install.before_install"
after_install = "wix_integration.install.after_install"
after_migrate = "wix_integration.install.after_migrate"

# Uninstallation
# ---------------

# before_uninstall = "wix_integration.uninstall.before_uninstall"
# after_uninstall = "wix_integration.uninstall.after_uninstall"

# Desk Notifications
# -------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "wix_integration.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
#	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
#	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# DocType Class
# ---------------
# Override standard doctype classes

# override_doctype_class = {
#	"ToDo": "custom_app.overrides.CustomToDo"
# }

# Document Events
# ---------------
# Hook on document methods and events

doc_events = {
	"Item": {
		"after_insert": "wix_integration.wix_integration.api.product_sync.on_item_update",
		"on_update": "wix_integration.wix_integration.api.product_sync.on_item_update",
		"validate": "wix_integration.wix_integration.api.product_sync.on_item_update",
	}
}

# Scheduled Tasks
# ---------------

scheduler_events = {
	"all": [
		"wix_integration.tasks.all"
	],
	"daily": [
		"wix_integration.tasks.daily",
		"wix_integration.tasks.cleanup_logs"
	],
	"hourly": [
		"wix_integration.tasks.hourly"
	],
	"weekly": [
		"wix_integration.tasks.weekly"
	],
	"monthly": [
		"wix_integration.tasks.monthly"
	],
	"cron": {
		"0 2 * * *": [  # Daily at 2 AM
			"wix_integration.tasks.daily_sync_check"
		],
		"*/15 * * * *": [  # Every 15 minutes
			"wix_integration.tasks.process_sync_queue"
		]
	}
}

# Testing
# -------

# before_tests = "wix_integration.install.before_tests"

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
#	"frappe.desk.doctype.event.event.get_events": "wix_integration.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
#	"Task": "wix_integration.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Request Events
# ---------------
# before_request = ["wix_integration.utils.before_request"]
# after_request = ["wix_integration.utils.after_request"]

# Job Events
# ----------
# before_job = ["wix_integration.utils.before_job"]
# after_job = ["wix_integration.utils.after_job"]

# User Data Protection
# --------------------

user_data_fields = [
	{
		"doctype": "{doctype_1}",
		"filter_by": "{filter_by}",
		"redact_fields": ["{field_1}", "{field_2}"],
		"partial": 1,
	},
	{
		"doctype": "{doctype_2}",
		"filter_by": "{filter_by}",
		"partial": 1,
	},
	{
		"doctype": "{doctype_3}",
		"strict": False,
	},
	{
		"doctype": "{doctype_4}"
	}
]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
#	"wix_integration.auth.validate"
# ]

# Translation
# --------------------------------

# Make property setters available in the translation directory
# fixtures = ["Property Setter", "Custom Field"]

# Website Route Rules
# --------------------------------

# Handle webhook endpoints
website_route_rules = [
	{"from_route": "/api/wix-webhook", "to_route": "wix_integration.api.webhook.handle_wix_webhook"},
]

# Wix Integration specific configurations
# ----------------------------------------

# Custom role for Wix integration management
# This will be created during installation
wix_integration_roles = [
	{
		"role_name": "Wix Manager",
		"permissions": [
			{"doctype": "Wix Settings", "read": 1, "write": 1},
			{"doctype": "Wix Integration Log", "read": 1, "write": 1},
			{"doctype": "Wix Item Mapping", "read": 1, "write": 1, "create": 1, "delete": 1},
			{"doctype": "Wix Category Mapping", "read": 1, "write": 1, "create": 1, "delete": 1},
			{"doctype": "Item", "read": 1},
			{"doctype": "Item Group", "read": 1},
			{"doctype": "Sales Order", "read": 1, "write": 1}
		]
	}
]

# Background job queues for Wix operations
job_queues = [
	{
		"name": "wix_sync",
		"workers": 2,
		"timeout": 300
	}
]

# Patch system for updates
# -------------------------

# Required patches for installation and updates
required_apps = ["erpnext"]

# Boot information
# ----------------

# Boot session information to be sent to client
# boot_session = "wix_integration.boot.boot_session"

# Application logo
app_logo_url = "/assets/wix_integration/images/logo.png"
