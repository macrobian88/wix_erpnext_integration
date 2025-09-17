# -*- coding: utf-8 -*-
"""Set up custom fields for Wix Integration"""

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

def execute():
	"""Create custom fields for Wix integration"""
	try:
		# Custom fields for Item doctype
		item_custom_fields = {
			"Item": [
				{
					'fieldname': 'wix_sync_section',
					'label': 'Wix Integration',
					'fieldtype': 'Section Break',
					'insert_after': 'website_image',
					'collapsible': 1
				},
				{
					'fieldname': 'sync_to_wix',
					'label': 'Sync to Wix',
					'fieldtype': 'Check',
					'insert_after': 'wix_sync_section',
					'default': '0',
					'description': 'Enable automatic sync of this item to Wix store'
				},
				{
					'fieldname': 'wix_product_id',
					'label': 'Wix Product ID',
					'fieldtype': 'Data',
					'insert_after': 'sync_to_wix',
					'read_only': 1,
					'description': 'Wix Product ID (auto-generated)'
				},
				{
					'fieldname': 'wix_sync_status',
					'label': 'Wix Sync Status',
					'fieldtype': 'Select',
					'insert_after': 'wix_product_id',
					'options': 'Not Synced\nPending\nSynced\nError\nDisabled',
					'default': 'Not Synced',
					'read_only': 1
				},
				{
					'fieldname': 'wix_last_sync',
					'label': 'Last Wix Sync',
					'fieldtype': 'Datetime',
					'insert_after': 'wix_sync_status',
					'read_only': 1,
					'description': 'Last successful sync to Wix'
				}
			]
		}
		
		# Only create if they don't exist
		for doctype, fields in item_custom_fields.items():
			for field in fields:
				if not frappe.db.exists("Custom Field", f"{doctype}-{field['fieldname']}"):
					create_custom_fields({doctype: [field]})
		
		frappe.logger().info("Created custom fields for Wix integration")
		
	except Exception as e:
		frappe.log_error(f"Error creating custom fields: {str(e)}", "Patch")
		pass