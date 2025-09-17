# -*- coding: utf-8 -*-
"""Scheduled Tasks for Wix Integration

This module contains all scheduled tasks for the Wix integration including
sync monitoring, cleanup operations, and background processing.
"""

import frappe
from frappe.utils import now, add_days, add_hours
from frappe import _

def all():
	"""Task that runs every few minutes"""
	# Health check - ensure integration is functioning
	pass

def daily():
	"""Daily maintenance tasks"""
	try:
		cleanup_old_logs()
		sync_health_check()
	except Exception as e:
		frappe.log_error(f"Daily task error: {str(e)}", "Wix Integration Daily Task")

def hourly():
	"""Hourly tasks"""
	try:
		process_failed_syncs()
	except Exception as e:
		frappe.log_error(f"Hourly task error: {str(e)}", "Wix Integration Hourly Task")

def weekly():
	"""Weekly maintenance tasks"""
	try:
		generate_sync_report()
	except Exception as e:
		frappe.log_error(f"Weekly task error: {str(e)}", "Wix Integration Weekly Task")

def monthly():
	"""Monthly tasks"""
	try:
		archive_old_logs()
	except Exception as e:
		frappe.log_error(f"Monthly task error: {str(e)}", "Wix Integration Monthly Task")

def daily_sync_check():
	"""Daily sync health check - runs at 2 AM"""
	try:
		settings = frappe.get_single('Wix Settings')
		
		if not settings.enabled:
			return
		
		# Check for items that failed to sync in the last 24 hours
		failed_syncs = frappe.get_all(
			"Wix Integration Log",
			filters={
				"status": "Error",
				"operation_type": "Product Sync",
				"timestamp": [">", add_days(now(), -1)]
			},
			fields=["reference_name", "message"]
		)
		
		if len(failed_syncs) > 10:  # Alert if too many failures
			# Create system notification or email
			frappe.log_error(
				f"High sync failure rate: {len(failed_syncs)} items failed to sync in last 24 hours",
				"Wix Sync Health Alert"
			)
			
	except Exception as e:
		frappe.log_error(f"Daily sync check error: {str(e)}", "Wix Integration Task")

def process_sync_queue():
	"""Process sync queue every 15 minutes"""
	try:
		settings = frappe.get_single('Wix Settings')
		
		if not settings.enabled:
			return
		
		# Find items that need retry
		retry_items = frappe.get_all(
			"Wix Item Mapping",
			filters={
				"sync_status": "Error",
				"last_sync": ["<", add_hours(now(), -1)]  # Retry after 1 hour
			},
			fields=["erpnext_item"],
			limit=10  # Process max 10 items at a time
		)
		
		for item_mapping in retry_items:
			try:
				from wix_integration.wix_integration.api.product_sync import sync_product_to_wix
				
				item_doc = frappe.get_doc("Item", item_mapping.erpnext_item)
				frappe.enqueue(
					sync_product_to_wix,
					queue='short',
					timeout=120,
					item_doc=item_doc,
					trigger_type="retry"
				)
				
			except Exception as e:
				frappe.log_error(
					f"Error queueing retry for item {item_mapping.erpnext_item}: {str(e)}",
					"Wix Sync Queue Error"
				)
				
	except Exception as e:
		frappe.log_error(f"Process sync queue error: {str(e)}", "Wix Integration Task")

def cleanup_logs():
	"""Clean up old integration logs"""
	try:
		cleanup_old_logs()
	except Exception as e:
		frappe.log_error(f"Cleanup logs error: {str(e)}", "Wix Integration Task")

def cleanup_old_logs():
	"""Remove logs older than 90 days"""
	try:
		cutoff_date = add_days(now(), -90)
		
		# Delete old logs
		old_logs = frappe.get_all(
			"Wix Integration Log",
			filters={"timestamp": ["<", cutoff_date]},
			pluck="name"
		)
		
		for log_name in old_logs:
			frappe.delete_doc("Wix Integration Log", log_name, ignore_permissions=True)
		
		if old_logs:
			frappe.db.commit()
			frappe.log_error(f"Cleaned up {len(old_logs)} old integration logs", "Wix Integration Cleanup")
			
	except Exception as e:
		frappe.log_error(f"Error cleaning up logs: {str(e)}", "Wix Integration Cleanup")

def sync_health_check():
	"""Check overall sync health"""
	try:
		settings = frappe.get_single('Wix Settings')
		
		if not settings.enabled:
			return
		
		# Check error rate in last 24 hours
		total_syncs = frappe.db.count(
			"Wix Integration Log",
			filters={
				"operation_type": "Product Sync",
				"timestamp": [">", add_days(now(), -1)]
			}
		)
		
		failed_syncs = frappe.db.count(
			"Wix Integration Log",
			filters={
				"operation_type": "Product Sync",
				"status": "Error",
				"timestamp": [">", add_days(now(), -1)]
			}
		)
		
		if total_syncs > 0:
			error_rate = (failed_syncs / total_syncs) * 100
			
			if error_rate > 20:  # Alert if error rate > 20%
				message = f"Wix sync health alert: {error_rate:.1f}% error rate ({failed_syncs}/{total_syncs} syncs failed)"
				frappe.log_error(message, "Wix Sync Health Alert")
				
	except Exception as e:
		frappe.log_error(f"Sync health check error: {str(e)}", "Wix Integration Task")

def process_failed_syncs():
	"""Retry failed syncs with exponential backoff"""
	try:
		settings = frappe.get_single('Wix Settings')
		
		if not settings.enabled:
			return
		
		# Find failed items that haven't been retried recently
		failed_mappings = frappe.get_all(
			"Wix Item Mapping",
			filters={
				"sync_status": "Error",
				"last_sync": ["<", add_hours(now(), -2)]  # Wait 2 hours before retry
			},
			fields=["erpnext_item", "error_message"],
			limit=5  # Limit retries per hour
		)
		
		for mapping in failed_mappings:
			try:
				# Check if this item has been retried too many times
				recent_errors = frappe.db.count(
					"Wix Integration Log",
					filters={
						"reference_name": mapping.erpnext_item,
						"status": "Error",
						"timestamp": [">", add_days(now(), -1)]
					}
				)
				
				if recent_errors < 3:  # Max 3 retries per day
					from wix_integration.wix_integration.api.product_sync import sync_product_to_wix
					
					item_doc = frappe.get_doc("Item", mapping.erpnext_item)
					frappe.enqueue(
						sync_product_to_wix,
						queue='short',
						timeout=120,
						item_doc=item_doc,
						trigger_type="auto_retry"
					)
					
			except Exception as e:
				frappe.log_error(
					f"Error processing failed sync for {mapping.erpnext_item}: {str(e)}",
					"Wix Integration Task"
				)
				
	except Exception as e:
		frappe.log_error(f"Process failed syncs error: {str(e)}", "Wix Integration Task")

def generate_sync_report():
	"""Generate weekly sync performance report"""
	try:
		settings = frappe.get_single('Wix Settings')
		
		if not settings.enabled:
			return
		
		# Get sync stats for the past week
		week_ago = add_days(now(), -7)
		
		total_syncs = frappe.db.count(
			"Wix Integration Log",
			filters={
				"operation_type": "Product Sync",
				"timestamp": [">", week_ago]
			}
		)
		
		successful_syncs = frappe.db.count(
			"Wix Integration Log",
			filters={
				"operation_type": "Product Sync",
				"status": "Success",
				"timestamp": [">", week_ago]
			}
		)
		
		failed_syncs = total_syncs - successful_syncs
		success_rate = (successful_syncs / total_syncs * 100) if total_syncs > 0 else 0
		
		# Log weekly summary
		report = f"""
		Wix Integration Weekly Report:
		- Total Syncs: {total_syncs}
		- Successful: {successful_syncs}
		- Failed: {failed_syncs}
		- Success Rate: {success_rate:.1f}%
		"""
		
		frappe.log_error(report, "Wix Integration Weekly Report")
		
	except Exception as e:
		frappe.log_error(f"Generate sync report error: {str(e)}", "Wix Integration Task")

def archive_old_logs():
	"""Archive logs older than 6 months"""
	try:
		# This is a placeholder for log archiving
		# In production, you might want to export logs to external storage
		cutoff_date = add_days(now(), -180)  # 6 months
		
		old_logs_count = frappe.db.count(
			"Wix Integration Log",
			filters={"timestamp": ["<", cutoff_date]}
		)
		
		if old_logs_count > 0:
			frappe.log_error(
				f"Found {old_logs_count} logs older than 6 months for archiving",
				"Wix Integration Archive"
			)
			
	except Exception as e:
		frappe.log_error(f"Archive old logs error: {str(e)}", "Wix Integration Task")
