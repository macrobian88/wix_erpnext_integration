# -*- coding: utf-8 -*-
from __future__ import unicode_literals

app_name = "wix_integration"
app_title = "Wix Integration"
app_publisher = "Wix ERPNext Integration"
app_description = "Bidirectional sync between Wix website and ERPNext"
app_icon = "octicon octicon-sync"
app_color = "blue"
app_email = "support@wixerpnext.com"
app_license = "MIT"

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/wix_integration/css/wix_integration.css"
# app_include_js = "/assets/wix_integration/js/wix_integration.js"

# include js, css files in header of web template
# web_include_css = "/assets/wix_integration/css/wix_integration.css"
# web_include_js = "/assets/wix_integration/js/wix_integration.js"

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

# Website user home page (by function)
# get_website_user_home_page = "wix_integration.utils.get_home_page"

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Installation
# ------------

# before_install = "wix_integration.install.before_install"
# after_install = "wix_integration.install.after_install"
after_install = "wix_integration.install.after_install"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "wix_integration.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# Doc Events
# ----------
# Hook on document methods and events

doc_events = {
	"Item": {
		"after_insert": "wix_integration.wix_integration.doctype.wix_integration.wix_integration.sync_item_to_wix",
		"on_update": "wix_integration.wix_integration.doctype.wix_integration.wix_integration.sync_item_to_wix_on_update",
	}
}

# Scheduled Tasks
# ---------------

scheduler_events = {
	"cron": {
		"0 */4 * * *": [  # Every 4 hours
			"wix_integration.tasks.sync_pending_items",
		],
	},
	"daily": [
		"wix_integration.tasks.cleanup_old_sync_logs",
		"wix_integration.tasks.health_check_wix_connection"
	],
	"weekly": [
		"wix_integration.tasks.generate_sync_reports"
	]
}

# Testing
# -------

# before_tests = "wix_integration.install.before_tests"

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "wix_integration.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "wix_integration.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

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
# 	"wix_integration.auth.validate"
# ]