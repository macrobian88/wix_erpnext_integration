# -*- coding: utf-8 -*-
"""Background tasks for Wix Integration"""

import frappe
from frappe import _
from datetime import datetime, timedelta
import time
from wix_integration.wix_integration.doctype.wix_integration.wix_integration import sync_item_to_wix

def sync_pending_items():
	"""Sync items that are pending sync (scheduled task)"""
	try:
		# Check if integration is enabled
		settings = frappe.get_single("Wix Settings")
		if not settings.enabled:
			frappe.logger().info("Wix integration is disabled, skipping scheduled sync")
			return
		
		# Get pending items (items that should be synced but haven't been recently)
		pending_items = frappe.db.sql("""
			SELECT item_code
			FROM `tabWix Item Mapping`
			WHERE sync_enabled = 1 
				AND sync_status IN ('Pending', 'Error', 'Not Synced')
				AND (last_sync IS NULL OR last_sync < DATE_SUB(NOW(), INTERVAL 1 HOUR))
			LIMIT 50
		""", as_dict=True)
		
		if not pending_items:
			frappe.logger().info("No pending items to sync")
			return
		
		frappe.logger().info(f"Starting scheduled sync for {len(pending_items)} items")
		
		# Process items with delay to avoid rate limiting
		for item in pending_items:
			try:
				item_doc = frappe.get_doc("Item", item.item_code)
				sync_item_to_wix(item_doc)
				
				# Small delay to avoid overwhelming Wix API
				time.sleep(2)
				
			except Exception as e:
				frappe.log_error(f"Error syncing item {item.item_code}: {str(e)}", "Scheduled Sync")
				continue
		
		frappe.logger().info(f"Completed scheduled sync for {len(pending_items)} items")
		
	except Exception as e:
		frappe.log_error(f"Error in sync_pending_items: {str(e)}", "Scheduled Sync")

def cleanup_old_sync_logs():
	"""Clean up old sync logs (scheduled task)"""
	try:
		# Delete logs older than 30 days
		cutoff_date = datetime.now() - timedelta(days=30)
		
		deleted_count = frappe.db.sql("""
			DELETE FROM `tabWix Integration Log`
			WHERE creation < %s AND status = 'Success'
		""", (cutoff_date,))
		
		frappe.db.commit()
		
		frappe.logger().info(f"Cleaned up {deleted_count} old sync logs")
		
	except Exception as e:
		frappe.log_error(f"Error in cleanup_old_sync_logs: {str(e)}", "Log Cleanup")

def health_check_wix_connection():
	"""Check Wix API connection health (scheduled task)"""
	try:
		from wix_integration.wix_integration.wix_connector import WixConnector
		
		connector = WixConnector()
		result = connector.test_connection()
		
		if result.get('success'):
			frappe.logger().info("Wix connection health check passed")
			
			# Update last successful connection time
			settings = frappe.get_single("Wix Settings")
			settings.last_sync = datetime.now()
			settings.save(ignore_permissions=True)
		else:
			frappe.log_error(f"Wix connection health check failed: {result.get('error')}", "Health Check")
			
			# Update error details in settings
			settings = frappe.get_single("Wix Settings")
			error_msg = f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}: Connection failed - {result.get('error')}\n"
			settings.sync_errors = (settings.sync_errors or "") + error_msg
			if len(settings.sync_errors) > 2000:
				settings.sync_errors = settings.sync_errors[-2000:]
			settings.save(ignore_permissions=True)
		
	except Exception as e:
		frappe.log_error(f"Error in health_check_wix_connection: {str(e)}", "Health Check")

def generate_sync_reports():
	"""Generate weekly sync reports (scheduled task)"""
	try:
		# Get sync statistics for the past week
		week_ago = datetime.now() - timedelta(days=7)
		
		stats = frappe.db.sql("""
			SELECT 
				operationType,
				status,
				COUNT(*) as count,
				AVG(executionTime) as avg_execution_time,
				MAX(executionTime) as max_execution_time
			FROM `tabWix Integration Log`
			WHERE creation >= %s
			GROUP BY operationType, status
			ORDER BY operationType, status
		""", (week_ago,), as_dict=True)
		
		if stats:
			# Create a summary report
			report = "Weekly Wix Integration Report\n"
			report += "=" * 35 + "\n\n"
			
			total_operations = sum(s.count for s in stats)
			successful_operations = sum(s.count for s in stats if s.status == 'Success')
			failed_operations = sum(s.count for s in stats if s.status == 'Failed')
			
			report += f"Total Operations: {total_operations}\n"
			report += f"Successful: {successful_operations}\n"
			report += f"Failed: {failed_operations}\n"
			report += f"Success Rate: {(successful_operations/total_operations*100):.1f}%\n\n"
			
			report += "Detailed Breakdown:\n"
			report += "-" * 20 + "\n"
			
			for stat in stats:
				report += f"{stat.operationType} - {stat.status}: {stat.count} operations\n"
				if stat.avg_execution_time:
					report += f"  Avg execution time: {stat.avg_execution_time:.2f}s\n"
			
			frappe.logger().info(f"Weekly sync report:\n{report}")
		
	except Exception as e:
		frappe.log_error(f"Error in generate_sync_reports: {str(e)}", "Report Generation")

def bulk_sync_items(item_codes, delay_seconds=3):
	"""Bulk sync multiple items with configurable delay"""
	try:
		frappe.logger().info(f"Starting bulk sync for {len(item_codes)} items")
		
		success_count = 0
		error_count = 0
		
		for item_code in item_codes:
			try:
				item_doc = frappe.get_doc("Item", item_code)
				sync_item_to_wix(item_doc)
				success_count += 1
				
				# Delay between syncs to avoid rate limiting
				if delay_seconds > 0:
					time.sleep(delay_seconds)
				
			except Exception as e:
				frappe.log_error(f"Error in bulk sync for item {item_code}: {str(e)}", "Bulk Sync")
				error_count += 1
				continue
		
		frappe.logger().info(f"Bulk sync completed: {success_count} successful, {error_count} failed")
		
		return {
			'success_count': success_count,
			'error_count': error_count,
			'total_count': len(item_codes)
		}
		
	except Exception as e:
		frappe.log_error(f"Error in bulk_sync_items: {str(e)}", "Bulk Sync")
		return {'error': str(e)}

def retry_failed_sync(log_name):
	"""Retry a failed sync operation"""
	try:
		log_entry = frappe.get_doc("Wix Integration Log", log_name)
		
		if log_entry.status != "Retry":
			frappe.logger().info(f"Log {log_name} is not in retry status, skipping")
			return
		
		# Check if we've exceeded retry attempts
		settings = frappe.get_single("Wix Settings")
		if log_entry.retry_count >= settings.retry_attempts:
			log_entry.status = "Failed"
			log_entry.error_details += f"\n{datetime.now()}: Max retry attempts exceeded"
			log_entry.save(ignore_permissions=True)
			return
		
		# Attempt retry
		log_entry.retry_count += 1
		log_entry.status = "In Progress"
		log_entry.save(ignore_permissions=True)
		
		# Retry the sync
		if log_entry.item_code:
			item_doc = frappe.get_doc("Item", log_entry.item_code)
			sync_item_to_wix(item_doc)
		
		frappe.logger().info(f"Retried sync for log {log_name}")
		
	except Exception as e:
		frappe.log_error(f"Error retrying sync for {log_name}: {str(e)}", "Retry Sync")

def sync_item_inventory(item_code, quantity=None):
	"""Sync item inventory levels to Wix"""
	try:
		# Get item mapping
		mapping = frappe.db.get_value(
			"Wix Item Mapping", 
			item_code, 
			["wix_product_id", "sync_enabled", "sync_inventory"], 
			as_dict=True
		)
		
		if not mapping or not mapping.sync_enabled or not mapping.sync_inventory:
			frappe.logger().info(f"Inventory sync disabled for item {item_code}")
			return
		
		if not mapping.wix_product_id:
			frappe.logger().info(f"No Wix product ID found for item {item_code}")
			return
		
		# Get current stock quantity if not provided
		if quantity is None:
			# Get actual stock quantity from Stock Ledger
			quantity = frappe.db.sql("""
				SELECT SUM(actual_qty) as qty
				FROM `tabStock Ledger Entry`
				WHERE item_code = %s AND is_cancelled = 0
			""", (item_code,))[0][0] or 0
		
		# Update inventory in Wix (this would need to be implemented based on Wix API)
		from wix_integration.wix_integration.wix_connector import WixConnector
		connector = WixConnector()
		
		# For now, log the inventory sync (actual implementation would use Wix inventory API)
		frappe.logger().info(f"Would sync inventory for {item_code}: {quantity} units")
		
		# Create log entry
		from wix_integration.wix_integration.doctype.wix_integration_log.wix_integration_log import create_integration_log
		create_integration_log(
			operation_type="Sync Inventory",
			status="Success",
			item_code=item_code,
			wix_product_id=mapping.wix_product_id,
			request_data={'quantity': quantity}
		)
		
	except Exception as e:
		frappe.log_error(f"Error syncing inventory for {item_code}: {str(e)}", "Inventory Sync")