# -*- coding: utf-8 -*-
"""Create Wix Item Mappings for existing items with Wix custom fields"""

import frappe

def execute():
	"""Create mappings for items that have Wix sync enabled"""
	try:
		# Check if custom fields exist
		if not frappe.db.exists("Custom Field", "Item-sync_to_wix"):
			frappe.logger().info("Wix custom fields not found, skipping migration")
			return
		
		# Get items with Wix sync enabled
		items_with_sync = frappe.db.sql("""
			SELECT 
				item_code, 
				item_name,
				sync_to_wix,
				wix_product_id,
				wix_sync_status,
				wix_last_sync
			FROM `tabItem`
			WHERE sync_to_wix = 1
		""", as_dict=True)
		
		if not items_with_sync:
			frappe.logger().info("No items with Wix sync enabled found")
			return
		
		created_count = 0
		
		for item in items_with_sync:
			try:
				# Check if mapping already exists
				if frappe.db.exists("Wix Item Mapping", item.item_code):
					continue
				
				# Create mapping
				mapping_doc = frappe.get_doc({
					'doctype': 'Wix Item Mapping',
					'item_code': item.item_code,
					'item_name': item.item_name,
					'sync_enabled': 1,
					'wix_product_id': item.wix_product_id,
					'sync_status': item.wix_sync_status or 'Not Synced',
					'last_sync': item.wix_last_sync,
					'sync_price': 1,
					'sync_inventory': 1,
					'sync_images': 1
				})
				mapping_doc.insert(ignore_permissions=True)
				created_count += 1
				
			except Exception as e:
				frappe.log_error(f"Error creating mapping for {item.item_code}: {str(e)}", "Migration")
				continue
		
		if created_count > 0:
			frappe.logger().info(f"Created {created_count} Wix Item Mappings from existing items")
		
	except Exception as e:
		frappe.log_error(f"Error in migrate_existing_items: {str(e)}", "Patch")
		pass