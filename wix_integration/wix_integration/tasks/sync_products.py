# -*- coding: utf-8 -*-
"""Product Sync Tasks for Wix Integration

This module provides scheduled tasks for product synchronization
including bulk sync operations and modified product detection.
"""

import frappe
from datetime import datetime, timedelta
from frappe.utils import add_days, now_datetime
from wix_integration.wix_integration.api.product_sync import sync_product_to_wix

def bulk_sync_modified_products():
	"""Bulk sync products that have been modified since last sync"""
	try:
		settings = frappe.get_single('Wix Settings')
		if not settings.enabled or not settings.auto_sync_items:
			return
		
		# Get products modified since last bulk sync (or in last 24 hours)
		last_sync = settings.last_sync or add_days(now_datetime(), -1)
		
		modified_items = frappe.get_all(
			"Item",
			filters=[
				["modified", ">", last_sync],
				["disabled", "=", 0],
				["is_stock_item", "=", 1],
				["wix_sync_status", "in", ["", "Ready", "Error"]]  # Don't sync items already pending
			],
			fields=["name", "item_name", "modified", "wix_sync_status"],
			order_by="modified desc",
			limit=50  # Process in batches of 50
		)
		
		if not modified_items:
			frappe.logger().info("No modified items found for bulk sync")
			return
		
		frappe.logger().info(f"Starting bulk sync for {len(modified_items)} modified items")
		
		sync_results = {
			'total': len(modified_items),
			'success': 0,
			'failed': 0,
			'errors': []
		}
		
		for item_info in modified_items:
			try:
				# Get full item document
				item_doc = frappe.get_doc("Item", item_info.name)
				
				# Mark as pending before sync
				frappe.db.set_value("Item", item_info.name, "wix_sync_status", "Pending")
				frappe.db.commit()
				
				# Sync to Wix
				result = sync_product_to_wix(item_doc, "bulk")
				
				if result.get('success'):
					sync_results['success'] += 1
					frappe.logger().info(f"Successfully synced {item_info.name}")
				else:
					sync_results['failed'] += 1
					sync_results['errors'].append({
						'item': item_info.name,
						'error': result.get('error', 'Unknown error')
					})
					frappe.logger().error(f"Failed to sync {item_info.name}: {result.get('error')}")
				
			except Exception as e:
				sync_results['failed'] += 1
				sync_results['errors'].append({
					'item': item_info.name,
					'error': str(e)
				})
				frappe.log_error(f"Error syncing item {item_info.name}: {str(e)}", "Wix Bulk Sync Error")
		
		# Update last sync time
		settings.last_sync = now_datetime()
		settings.save(ignore_permissions=True)
		frappe.db.commit()
		
		# Log summary
		frappe.logger().info(
			f"Bulk sync completed: {sync_results['success']} successful, "
			f"{sync_results['failed']} failed out of {sync_results['total']} items"
		)
		
		# Create integration log
		from wix_integration.wix_integration.api.product_sync import create_integration_log
		create_integration_log(
			operation_type="Bulk Product Sync",
			reference_doctype="Item",
			reference_name="Bulk Operation",
			status="Completed",
			message=f"Bulk sync: {sync_results['success']}/{sync_results['total']} successful",
			wix_response=sync_results
		)
		
	except Exception as e:
		frappe.log_error(f"Error during bulk sync of modified products: {str(e)}", "Wix Bulk Sync Task Error")

def sync_pending_items():
	"""Sync items that are marked as 'Pending' sync status"""
	try:
		settings = frappe.get_single('Wix Settings')
		if not settings.enabled:
			return
		
		# Get items with pending sync status (but not too old to avoid infinite loops)
		cutoff_time = add_days(now_datetime(), hours=-4)  # Only items pending for less than 4 hours
		
		pending_items = frappe.get_all(
			"Item",
			filters=[
				["wix_sync_status", "=", "Pending"],
				["wix_last_sync", ">=", cutoff_time],
				["disabled", "=", 0],
				["is_stock_item", "=", 1]
			],
			fields=["name", "item_name", "wix_last_sync"],
			order_by="wix_last_sync asc",
			limit=20  # Process small batches to avoid timeouts
		)
		
		if not pending_items:
			return
		
		frappe.logger().info(f"Processing {len(pending_items)} pending sync items")
		
		processed = 0
		for item_info in pending_items:
			try:
				item_doc = frappe.get_doc("Item", item_info.name)
				result = sync_product_to_wix(item_doc, "retry")
				
				if result.get('success'):
					processed += 1
					frappe.logger().info(f"Successfully processed pending item: {item_info.name}")
				else:
					# If it fails again, mark as error to prevent infinite retries
					frappe.db.set_value("Item", item_info.name, "wix_sync_status", "Error")
					frappe.logger().warning(f"Failed to process pending item {item_info.name}, marked as error")
				
			except Exception as e:
				frappe.log_error(f"Error processing pending item {item_info.name}: {str(e)}", "Wix Pending Sync Error")
				# Mark as error to prevent infinite retries
				frappe.db.set_value("Item", item_info.name, "wix_sync_status", "Error")
		
		if processed > 0:
			frappe.db.commit()
			frappe.logger().info(f"Successfully processed {processed} pending sync items")
		
	except Exception as e:
		frappe.log_error(f"Error processing pending items: {str(e)}", "Wix Pending Items Task Error")

def sync_new_items_only():
	"""Sync only newly created items that haven't been synced yet"""
	try:
		settings = frappe.get_single('Wix Settings')
		if not settings.enabled or not settings.auto_sync_items:
			return
		
		# Get items created in the last hour that haven't been synced
		recent_time = add_days(now_datetime(), hours=-1)
		
		new_items = frappe.get_all(
			"Item",
			filters=[
				["creation", ">=", recent_time],
				["disabled", "=", 0],
				["is_stock_item", "=", 1],
				["wix_sync_status", "in", ["", "Ready", None]]  # Never synced
			],
			fields=["name", "item_name", "creation"],
			order_by="creation desc",
			limit=10  # Small batch for new items
		)
		
		if not new_items:
			return
		
		frappe.logger().info(f"Syncing {len(new_items)} newly created items")
		
		for item_info in new_items:
			try:
				item_doc = frappe.get_doc("Item", item_info.name)
				result = sync_product_to_wix(item_doc, "auto_new")
				
				if result.get('success'):
					frappe.logger().info(f"Successfully synced new item: {item_info.name}")
				else:
					frappe.logger().warning(f"Failed to sync new item {item_info.name}: {result.get('error')}")
				
			except Exception as e:
				frappe.log_error(f"Error syncing new item {item_info.name}: {str(e)}", "Wix New Item Sync Error")
		
	except Exception as e:
		frappe.log_error(f"Error syncing new items: {str(e)}", "Wix New Items Task Error")

def retry_failed_syncs():
	"""Retry items that failed to sync (with exponential backoff)"""
	try:
		settings = frappe.get_single('Wix Settings')
		if not settings.enabled:
			return
		
		# Get items that failed sync more than 1 hour ago (to allow for backoff)
		cutoff_time = add_days(now_datetime(), hours=-1)
		
		failed_items = frappe.get_all(
			"Item",
			filters=[
				["wix_sync_status", "=", "Error"],
				["wix_last_sync", "<=", cutoff_time],
				["disabled", "=", 0],
				["is_stock_item", "=", 1]
			],
			fields=["name", "item_name", "wix_last_sync"],
			order_by="wix_last_sync asc",
			limit=5  # Very small batch for retries
		)
		
		if not failed_items:
			return
		
		frappe.logger().info(f"Retrying {len(failed_items)} failed sync items")
		
		retried = 0
		for item_info in failed_items:
			try:
				item_doc = frappe.get_doc("Item", item_info.name)
				
				# Mark as pending before retry
				frappe.db.set_value("Item", item_info.name, "wix_sync_status", "Pending")
				frappe.db.commit()
				
				result = sync_product_to_wix(item_doc, "retry")
				
				if result.get('success'):
					retried += 1
					frappe.logger().info(f"Successfully retried failed item: {item_info.name}")
				else:
					# Keep as error status for next retry cycle
					frappe.db.set_value("Item", item_info.name, "wix_sync_status", "Error")
					frappe.logger().warning(f"Retry failed for item {item_info.name}: {result.get('error')}")
				
			except Exception as e:
				frappe.log_error(f"Error retrying item {item_info.name}: {str(e)}", "Wix Retry Sync Error")
				frappe.db.set_value("Item", item_info.name, "wix_sync_status", "Error")
		
		if retried > 0:
			frappe.db.commit()
			frappe.logger().info(f"Successfully retried {retried} failed sync items")
		
	except Exception as e:
		frappe.log_error(f"Error retrying failed syncs: {str(e)}", "Wix Retry Task Error")

def clean_sync_statuses():
	"""Clean up and normalize sync statuses"""
	try:
		# Reset any items stuck in 'Pending' status for more than 24 hours
		old_pending_cutoff = add_days(now_datetime(), -1)
		
		stuck_items = frappe.get_all(
			"Item",
			filters=[
				["wix_sync_status", "=", "Pending"],
				["wix_last_sync", "<=", old_pending_cutoff]
			],
			limit=100
		)
		
		for item in stuck_items:
			frappe.db.set_value("Item", item.name, "wix_sync_status", "Ready")
		
		if stuck_items:
			frappe.db.commit()
			frappe.logger().info(f"Reset {len(stuck_items)} stuck pending items to Ready")
		
		# Set empty sync status to 'Ready' for eligible items
		empty_status_items = frappe.get_all(
			"Item",
			filters=[
				["wix_sync_status", "in", ["", None]],
				["disabled", "=", 0],
				["is_stock_item", "=", 1]
			],
			limit=100
		)
		
		for item in empty_status_items:
			frappe.db.set_value("Item", item.name, "wix_sync_status", "Ready")
		
		if empty_status_items:
			frappe.db.commit()
			frappe.logger().info(f"Set {len(empty_status_items)} items with empty status to Ready")
		
	except Exception as e:
		frappe.log_error(f"Error cleaning sync statuses: {str(e)}", "Wix Clean Status Task Error")

@frappe.whitelist()
def manual_bulk_sync(filters=None):
	"""Manual bulk sync function that can be called from UI"""
	if not frappe.has_permission("Wix Settings", "write"):
		frappe.throw(_("Insufficient permissions for bulk sync"))
	
	try:
		# Import the function from product_sync API
		from wix_integration.wix_integration.api.product_sync import bulk_sync_items
		
		result = bulk_sync_items(filters)
		return result
		
	except Exception as e:
		frappe.log_error(f"Error in manual bulk sync: {str(e)}", "Wix Manual Bulk Sync Error")
		return {
			'status': 'error',
			'message': f'Error during bulk sync: {str(e)}'
		}

def sync_high_priority_items():
	"""Sync high priority items (e.g., items with recent price changes)"""
	try:
		settings = frappe.get_single('Wix Settings')
		if not settings.enabled:
			return
		
		# Find items with recent price changes
		recent_time = add_days(now_datetime(), hours=-2)
		
		price_changed_items = frappe.db.sql("""
			SELECT DISTINCT ip.item_code
			FROM `tabItem Price` ip
			INNER JOIN `tabItem` i ON ip.item_code = i.name
			WHERE ip.modified >= %s
			  AND i.disabled = 0
			  AND i.is_stock_item = 1
			  AND i.wix_sync_status != 'Pending'
			LIMIT 20
		""", (recent_time,), as_dict=True)
		
		if not price_changed_items:
			return
		
		frappe.logger().info(f"Syncing {len(price_changed_items)} items with recent price changes")
		
		for item_info in price_changed_items:
			try:
				item_doc = frappe.get_doc("Item", item_info.item_code)
				result = sync_product_to_wix(item_doc, "priority")
				
				if result.get('success'):
					frappe.logger().info(f"Successfully synced priority item: {item_info.item_code}")
				else:
					frappe.logger().warning(f"Failed to sync priority item {item_info.item_code}: {result.get('error')}")
				
			except Exception as e:
				frappe.log_error(f"Error syncing priority item {item_info.item_code}: {str(e)}", "Wix Priority Sync Error")
		
	except Exception as e:
		frappe.log_error(f"Error syncing high priority items: {str(e)}", "Wix Priority Items Task Error")
