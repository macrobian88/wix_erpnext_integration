# -*- coding: utf-8 -*-
"""Add Custom Fields for Wix Integration to Item DocType

This patch adds the required custom fields to the Item DocType for Wix integration
including sync status tracking and Wix product ID storage.
"""

import frappe

def execute():
	"""Add custom fields to Item DocType for Wix integration"""
	
	# Custom fields to add to Item DocType
	custom_fields = {
		"Item": [
			{
				"fieldname": "wix_section",
				"label": "Wix Integration",
				"fieldtype": "Section Break",
				"insert_after": "item_defaults",
				"collapsible": 1,
				"collapsible_depends_on": "eval:doc.wix_product_id"
			},
			{
				"fieldname": "wix_product_id",
				"label": "Wix Product ID",
				"fieldtype": "Data",
				"insert_after": "wix_section",
				"read_only": 1,
				"description": "Wix Product ID for synced items"
			},
			{
				"fieldname": "wix_sync_status",
				"label": "Wix Sync Status",
				"fieldtype": "Select",
				"options": "\nReady\nPending\nSynced\nError",
				"insert_after": "wix_product_id",
				"default": "Ready",
				"description": "Current synchronization status with Wix"
			},
			{
				"fieldname": "wix_column_break",
				"fieldtype": "Column Break",
				"insert_after": "wix_sync_status"
			},
			{
				"fieldname": "wix_last_sync",
				"label": "Last Wix Sync",
				"fieldtype": "Datetime",
				"insert_after": "wix_column_break",
				"read_only": 1,
				"description": "Timestamp of last sync attempt with Wix"
			},
			{
				"fieldname": "wix_sync_error",
				"label": "Wix Sync Error",
				"fieldtype": "Text",
				"insert_after": "wix_last_sync",
				"read_only": 1,
				"description": "Last error message from Wix sync",
				"depends_on": "eval:doc.wix_sync_status == 'Error'"
			}
		]
	}
	
	# Create custom fields
	create_custom_fields(custom_fields)
	
	frappe.db.commit()
	print("Successfully added Wix integration custom fields to Item DocType")

def create_custom_fields(custom_fields):
	"""Create custom fields for given doctypes"""
	for doctype, fields in custom_fields.items():
		for field in fields:
			# Check if field already exists
			existing_field = frappe.db.get_value(
				"Custom Field",
				{"dt": doctype, "fieldname": field.get("fieldname")},
				"name"
			)
			
			if not existing_field:
				# Create the custom field
				custom_field = frappe.get_doc({
					"doctype": "Custom Field",
					"dt": doctype,
					"fieldname": field.get("fieldname"),
					"label": field.get("label"),
					"fieldtype": field.get("fieldtype"),
					"options": field.get("options"),
					"insert_after": field.get("insert_after"),
					"read_only": field.get("read_only", 0),
					"reqd": field.get("reqd", 0),
					"default": field.get("default"),
					"description": field.get("description"),
					"depends_on": field.get("depends_on"),
					"collapsible": field.get("collapsible", 0),
					"collapsible_depends_on": field.get("collapsible_depends_on")
				})
				
				custom_field.insert(ignore_permissions=True)
				print(f"Created custom field: {field.get('fieldname')} in {doctype}")
			else:
				print(f"Custom field {field.get('fieldname')} already exists in {doctype}")

if __name__ == "__main__":
	execute()
