# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.model.document import Document
from datetime import datetime, timedelta
import json

class WixIntegrationLog(Document):
	def before_insert(self):
		"""Set default values before inserting"""
		if not self.created_by_user:
			self.created_by_user = frappe.session.user
			
		if not self.sync_direction:
			self.sync_direction = "ERPNext to Wix"  # Default direction
	
	def validate(self):
		"""Validation logic"""
		# Ensure request_data and response_data are valid JSON
		if self.request_data:
			try:
				json.loads(self.request_data)
			except (json.JSONDecodeError, TypeError):
				if isinstance(self.request_data, dict):
					self.request_data = json.dumps(self.request_data, indent=2)
				else:
					self.request_data = str(self.request_data)
		
		if self.response_data:
			try:
				json.loads(self.response_data)
			except (json.JSONDecodeError, TypeError):
				if isinstance(self.response_data, dict):
					self.response_data = json.dumps(self.response_data, indent=2)
				else:
					self.response_data = str(self.response_data)
	
	def after_insert(self):
		"""Post-insert actions"""
		# Update settings counters
		if self.status == "Success":
			self.update_success_counter()
		elif self.status == "Failed":
			self.update_failure_counter()
			
		# Schedule retry if needed
		if self.status == "Failed" and self.should_retry():
			self.schedule_retry()
	
	def update_success_counter(self):
		"""Update successful sync counter in settings"""
		try:
			frappe.db.sql("""
				UPDATE `tabWix Settings`
				SET total_synced_items = total_synced_items + 1,
					last_sync = NOW()
				WHERE name = 'Wix Settings'
			""")
			frappe.db.commit()
		except Exception as e:
			frappe.log_error(f"Error updating success counter: {str(e)}", "Wix Integration Log")
	
	def update_failure_counter(self):
		"""Update failed sync counter in settings"""
		try:
			error_summary = self.error_details[:500] if self.error_details else "Unknown error"
			
			frappe.db.sql("""
				UPDATE `tabWix Settings`
				SET failed_syncs = failed_syncs + 1,
					sync_errors = CONCAT(COALESCE(sync_errors, ''), %s, '\n')
				WHERE name = 'Wix Settings'
			""", (f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}: {error_summary}",))
			frappe.db.commit()
		except Exception as e:
			frappe.log_error(f"Error updating failure counter: {str(e)}", "Wix Integration Log")
	
	def should_retry(self):
		"""Check if this operation should be retried"""
		settings = frappe.get_single("Wix Settings")
		return (
			self.retry_count < settings.retry_attempts and
			self.operation_type in ["Create Product", "Update Product", "Sync Inventory"] and
			"rate limit" not in (self.error_details or "").lower()
		)
	
	def schedule_retry(self):
		"""Schedule a retry with exponential backoff"""
		# Calculate next retry time with exponential backoff
		base_delay = 60  # 1 minute base delay
		delay_minutes = base_delay * (2 ** self.retry_count)
		next_retry = datetime.now() + timedelta(minutes=delay_minutes)
		
		# Update this log entry
		frappe.db.sql("""
			UPDATE `tabWix Integration Log`
			SET status = 'Retry', next_retry = %s
			WHERE name = %s
		""", (next_retry, self.name))
		frappe.db.commit()
		
		# Schedule background job for retry
		frappe.enqueue(
			'wix_integration.tasks.retry_failed_sync',
			log_name=self.name,
			queue='long',
			timeout=600,
			at_time=next_retry
		)

@frappe.whitelist()
def create_integration_log(operation_type, status, item_code=None, wix_product_id=None, 
						  request_data=None, response_data=None, error_details=None,
						  execution_time=None, sync_direction="ERPNext to Wix"):
	"""Helper function to create integration log entries"""
	try:
		log_entry = frappe.get_doc({
			'doctype': 'Wix Integration Log',
			'operation_type': operation_type,
			'status': status,
			'item_code': item_code,
			'wix_product_id': wix_product_id,
			'request_data': json.dumps(request_data, indent=2) if request_data else None,
			'response_data': json.dumps(response_data, indent=2) if response_data else None,
			'error_details': error_details,
			'execution_time': execution_time,
			'sync_direction': sync_direction
		})
		log_entry.insert(ignore_permissions=True)
		return log_entry.name
	except Exception as e:
		frappe.log_error(f"Error creating integration log: {str(e)}", "Wix Integration Log")
		return None

@frappe.whitelist()
def get_sync_stats(days=7):
	"""Get sync statistics for the specified number of days"""
	if not frappe.has_permission("Wix Integration Log", "read"):
		frappe.throw(_("Insufficient permissions to view sync statistics"))
	
	stats = frappe.db.sql("""
		SELECT 
			operationType,
			status,
			COUNT(*) as count,
			AVG(executionTime) as avg_execution_time,
			MAX(creation) as last_occurrence
		FROM `tabWix Integration Log`
		WHERE creation >= DATE_SUB(NOW(), INTERVAL %s DAY)
		GROUP BY operationType, status
		ORDER BY operationType, status
	""", (days,), as_dict=True)
	
	return stats

@frappe.whitelist()
def cleanup_old_logs(days=30):
	"""Clean up old log entries"""
	if not frappe.has_permission("Wix Integration Log", "delete"):
		frappe.throw(_("Insufficient permissions to cleanup logs"))
	
	cutoff_date = datetime.now() - timedelta(days=days)
	
	# Delete old successful logs
	deleted_count = frappe.db.sql("""
		DELETE FROM `tabWix Integration Log`
		WHERE creation < %s AND status = 'Success'
	""", (cutoff_date,))
	
	frappe.db.commit()
	
	return {
		'success': True,
		'message': f'Deleted {deleted_count} old log entries',
		'deleted_count': deleted_count
	}