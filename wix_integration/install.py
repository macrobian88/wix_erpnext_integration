# -*- coding: utf-8 -*-
"""Installation and setup functions for Wix Integration app"""

import frappe
from frappe import _
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields
from frappe.custom.doctype.property_setter.property_setter import make_property_setter

def after_install():
	"""Run after app installation"""
	try:
		frappe.logger().info("Starting Wix Integration app installation...")
		
		# Create custom fields
		create_wix_custom_fields()
		
		# Create custom role
		create_wix_manager_role()
		
		# Set up default settings
		setup_default_settings()
		
		# Create sample data if in development
		if frappe.conf.get('developer_mode'):
			create_sample_data()
		
		frappe.db.commit()
		frappe.logger().info("Wix Integration app installed successfully!")
		
	except Exception as e:
		frappe.log_error(f"Error during Wix Integration installation: {str(e)}", "Installation Error")
		frappe.throw(_("Installation failed. Please check error logs."))

def create_wix_custom_fields():
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
		
		create_custom_fields(item_custom_fields)
		frappe.logger().info("Created custom fields for Wix integration")
		
	except Exception as e:
		frappe.log_error(f"Error creating custom fields: {str(e)}", "Installation")
		raise

def create_wix_manager_role():
	"""Create Wix Manager role with appropriate permissions"""
	try:
		if not frappe.db.exists("Role", "Wix Manager"):
			role_doc = frappe.get_doc({
				'doctype': 'Role',
				'role_name': 'Wix Manager',
				'desk_access': 1,
				'is_custom': 1
			})
			role_doc.insert(ignore_permissions=True)
			frappe.logger().info("Created Wix Manager role")
		
		# Set up role permissions for Wix Integration doctypes
		wix_doctypes = [
			'Wix Settings',
			'Wix Integration Log',
			'Wix Item Mapping',
			'Wix Integration'
		]
		
		for doctype in wix_doctypes:
			if frappe.db.exists("DocType", doctype):
				# Check if permission already exists
				existing_perm = frappe.db.exists("DocPerm", {
					"parent": doctype,
					"role": "Wix Manager"
				})
				
				if not existing_perm:
					# Add permissions for Wix Manager role
					doc = frappe.get_doc("DocType", doctype)
					doc.append("permissions", {
						"role": "Wix Manager",
						"read": 1,
						"write": 1,
						"create": 1,
						"delete": 1,
						"submit": 0,
						"cancel": 0,
						"amend": 0
					})
					doc.save(ignore_permissions=True)
					frappe.logger().info(f"Added Wix Manager permissions to {doctype}")
		
	except Exception as e:
		frappe.log_error(f"Error creating Wix Manager role: {str(e)}", "Installation")
		raise

def setup_default_settings():
	"""Set up default Wix settings"""
	try:
		# Check if Wix Settings already exists
		if not frappe.db.exists("Wix Settings", "Wix Settings"):
			settings_doc = frappe.get_doc({
				'doctype': 'Wix Settings',
				'enabled': 0,  # Disabled by default
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
		else:
			frappe.logger().info("Wix Settings already exists")
		
	except Exception as e:
		frappe.log_error(f"Error setting up default settings: {str(e)}", "Installation")
		raise

def create_sample_data():
	"""Create sample data for development/testing"""
	try:
		frappe.logger().info("Creating sample data for development...")
		
		# Create a sample item if none exist
		if not frappe.db.exists("Item", "SAMPLE-WIX-001"):
			sample_item = frappe.get_doc({
				'doctype': 'Item',
				'item_code': 'SAMPLE-WIX-001',
				'item_name': 'Sample Product for Wix Integration',
				'item_group': 'Products',
				'description': 'This is a sample product created for Wix integration testing',
				'is_stock_item': 1,
				'include_item_in_manufacturing': 0,
				'standard_rate': 99.99,
				'sync_to_wix': 1
			})
			sample_item.insert(ignore_permissions=True)
			frappe.logger().info("Created sample item for testing")
		
	except Exception as e:
		frappe.log_error(f"Error creating sample data: {str(e)}", "Installation")
		# Don't raise here as sample data is optional
		pass

def before_uninstall():
	"""Clean up before uninstalling the app"""
	try:
		frappe.logger().info("Starting Wix Integration app cleanup...")
		
		# Remove custom fields
		remove_custom_fields()
		
		# Clean up role (optional)
		# remove_wix_manager_role()
		
		frappe.db.commit()
		frappe.logger().info("Wix Integration app cleanup completed")
		
	except Exception as e:
		frappe.log_error(f"Error during cleanup: {str(e)}", "Uninstall Error")

def remove_custom_fields():
	"""Remove custom fields created by the app"""
	try:
		custom_fields_to_remove = [
			'Item-wix_sync_section',
			'Item-sync_to_wix',
			'Item-wix_product_id',
			'Item-wix_sync_status',
			'Item-wix_last_sync'
		]
		
		for field_name in custom_fields_to_remove:
			if frappe.db.exists("Custom Field", field_name):
				frappe.delete_doc("Custom Field", field_name)
				frappe.logger().info(f"Removed custom field {field_name}")
		
	except Exception as e:
		frappe.log_error(f"Error removing custom fields: {str(e)}", "Cleanup")
		pass