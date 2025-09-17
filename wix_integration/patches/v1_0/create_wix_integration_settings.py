# -*- coding: utf-8 -*-
"""Create default Wix Integration settings"""

import frappe

def execute():
	"""Create Wix Settings if not exists"""
	try:
		if not frappe.db.exists("Wix Settings", "Wix Settings"):
			settings_doc = frappe.get_doc({
				'doctype': 'Wix Settings',
				'enabled': 0,
				'test_mode': 1,
				'auto_sync_items': 1,
				'sync_item_name': 1,
				'sync_item_description': 1,
				'sync_item_price': 1,
				'sync_item_images': 1,
				'sync_inventory': 1,
				'sync_categories': 1,
				'retry_attempts': 3,
				'timeout_seconds': 30,
				'log_level': 'INFO'
			})
			settings_doc.insert(ignore_permissions=True)
			frappe.logger().info("Created default Wix Settings")
		
	except Exception as e:
		frappe.log_error(f"Error creating Wix Settings: {str(e)}", "Patch")
		pass