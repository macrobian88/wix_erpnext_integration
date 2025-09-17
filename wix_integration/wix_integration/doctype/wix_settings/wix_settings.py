# -*- coding: utf-8 -*-
"""Wix Settings DocType Controller

Enhanced controller for managing Wix integration configuration with
production-grade validation, security, and monitoring features.
"""

import frappe
import json
from datetime import datetime
from frappe import _
from frappe.model.document import Document
from frappe.utils import get_site_url
from wix_integration.wix_integration.wix_connector import WixConnector

class WixSettings(Document):
	"""Controller for Wix Settings DocType"""
	
	def validate(self):
		"""Validate Wix settings before saving"""
		self.validate_required_credentials()
		self.validate_configuration_consistency()
		self.generate_webhook_url()
		
		# Test connection if enabled and credentials are provided
		if self.enabled and self.test_connection_on_save:
			self.test_wix_connection()
	
	def on_update(self):
		"""Handle post-save operations"""
		self.clear_cache()
		
		# Create custom fields if not exist
		if self.enabled:
			self.ensure_custom_fields()
	
	def validate_required_credentials(self):
		"""Validate that all required credentials are provided when integration is enabled"""
		if self.enabled:
			required_fields = ['site_id', 'api_key', 'account_id']
			missing_fields = []
			
			for field in required_fields:
				if not self.get(field):
					missing_fields.append(_(field.replace('_', ' ').title()))
			
			if missing_fields:
				frappe.throw(
					_("The following fields are required when Wix Integration is enabled: {0}").format(
						', '.join(missing_fields)
					)
				)
	
	def validate_configuration_consistency(self):
		"""Validate configuration consistency"""
		# Validate timeout settings
		if self.timeout_seconds and (self.timeout_seconds < 5 or self.timeout_seconds > 300):
			frappe.throw(_("Timeout must be between 5 and 300 seconds"))
		
		# Validate retry attempts
		if self.retry_attempts and (self.retry_attempts < 0 or self.retry_attempts > 10):
			frappe.throw(_("Retry attempts must be between 0 and 10"))
		
		# Validate webhook secret strength
		if self.webhook_secret and len(self.webhook_secret) < 16:
			frappe.throw(_("Webhook secret must be at least 16 characters long"))
	
	def generate_webhook_url(self):
		"""Generate webhook URL for Wix callbacks"""
		if not self.webhook_url:
			site_url = get_site_url()
			self.webhook_url = f"{site_url}/api/wix-webhook"
	
	def test_wix_connection(self):
		"""Test connection to Wix API"""
		try:
			connector = WixConnector()
			result = connector.test_connection()
			
			if not result.get('success'):
				frappe.throw(
					_("Wix connection test failed: {0}").format(result.get('error', 'Unknown error'))
				)
			else:
				frappe.msgprint(
					_("Wix connection test successful!"),
					title=_("Connection Test"),
					indicator="green"
				)
				
				# Store connection test results
				self.last_connection_test = datetime.now()
				self.connection_test_status = "Success"
				
		except Exception as e:
			frappe.log_error(f"Wix connection test error: {str(e)}", "Wix Integration Error")
			frappe.throw(_("Connection test failed: {0}").format(str(e)))
	
	def clear_cache(self):
		"""Clear Wix settings cache"""
		frappe.cache().delete_value('wix_settings')
		frappe.cache().delete_value('wix_integration_enabled')
	
	def ensure_custom_fields(self):
		"""Create custom fields for ERPNext doctypes if they don't exist"""
		custom_fields = [
			{
				'doctype': 'Custom Field',
				'dt': 'Item',
				'fieldname': 'wix_product_id',
				'label': 'Wix Product ID',
				'fieldtype': 'Data',
				'read_only': 1,
				'no_copy': 1,
				'description': 'Wix Product ID for synced items'
			},
			{
				'doctype': 'Custom Field',
				'dt': 'Item',
				'fieldname': 'wix_sync_status',
				'label': 'Wix Sync Status',
				'fieldtype': 'Select',
				'options': 'Not Synced\nSynced\nError\nPending',
				'default': 'Not Synced',
				'read_only': 1,
				'no_copy': 1
			},
			{
				'doctype': 'Custom Field',
				'dt': 'Item',
				'fieldname': 'wix_last_sync',
				'label': 'Wix Last Sync',
				'fieldtype': 'Datetime',
				'read_only': 1,
				'no_copy': 1
			},
			{
				'doctype': 'Custom Field',
				'dt': 'Sales Order',
				'fieldname': 'wix_order_id',
				'label': 'Wix Order ID',
				'fieldtype': 'Data',
				'read_only': 1,
				'no_copy': 1,
				'description': 'Original Wix Order ID'
			}
		]
		
		for field_data in custom_fields:
			try:
				existing_field = frappe.get_doc('Custom Field', {
					'dt': field_data['dt'],
					'fieldname': field_data['fieldname']
				})
			except frappe.DoesNotExistError:
				# Field doesn't exist, create it
				custom_field = frappe.get_doc(field_data)
				custom_field.insert(ignore_permissions=True)
				frappe.db.commit()
			except Exception as e:
				frappe.log_error(f"Error creating custom field: {str(e)}", "Wix Integration Error")
	
	@frappe.whitelist()
	def test_connection(self):
		"""API method to test Wix connection"""
		self.test_wix_connection()
		return {"status": "success", "message": "Connection test successful"}
	
	@frappe.whitelist()
	def reset_sync_statistics(self):
		"""Reset synchronization statistics"""
		self.total_synced_items = 0
		self.failed_syncs = 0
		self.sync_errors = ""
		self.last_sync = None
		self.save(ignore_permissions=True)
		frappe.db.commit()
		
		frappe.msgprint(
			_("Sync statistics have been reset"),
			title=_("Statistics Reset"),
			indicator="blue"
		)
	
	@frappe.whitelist()
	def get_sync_dashboard_data(self):
		"""Get data for sync dashboard"""
		# Get recent sync logs
		recent_logs = frappe.get_all(
			"Wix Integration Log",
			filters={"operation_type": "Product Sync"},
			fields=["status", "message", "timestamp", "reference_name"],
			order_by="timestamp desc",
			limit=10
		)
		
		# Get item mappings statistics
		mapping_stats = frappe.db.sql("""
			SELECT sync_status, COUNT(*) as count
			FROM `tabWix Item Mapping`
			GROUP BY sync_status
		""", as_dict=True)
		
		# Calculate success rate
		total_synced = self.total_synced_items or 0
		total_failed = self.failed_syncs or 0
		success_rate = 0
		if total_synced + total_failed > 0:
			success_rate = round((total_synced / (total_synced + total_failed)) * 100, 2)
		
		return {
			"recent_logs": recent_logs,
			"mapping_stats": mapping_stats,
			"success_rate": success_rate,
			"total_synced": total_synced,
			"total_failed": total_failed,
			"last_sync": self.last_sync
		}

# Global functions for integration
@frappe.whitelist()
def get_wix_settings():
	"""Get Wix settings with caching"""
	cached_settings = frappe.cache().get_value('wix_settings')
	
	if not cached_settings:
		try:
			settings = frappe.get_single('Wix Settings')
			frappe.cache().set_value('wix_settings', settings, expires_in_sec=300)  # 5 min cache
			return settings
		except Exception as e:
			frappe.log_error(f"Error getting Wix settings: {str(e)}", "Wix Integration Error")
			return None
	
	return cached_settings

@frappe.whitelist()
def is_wix_integration_enabled():
	"""Check if Wix integration is enabled"""
	cached_status = frappe.cache().get_value('wix_integration_enabled')
	
	if cached_status is None:
		try:
			settings = get_wix_settings()
			status = bool(settings and settings.enabled)
			frappe.cache().set_value('wix_integration_enabled', status, expires_in_sec=300)
			return status
		except Exception:
			return False
	
	return cached_status

@frappe.whitelist()
def trigger_manual_sync(item_code=None):
	"""Manually trigger product sync for testing"""
	if not is_wix_integration_enabled():
		frappe.throw(_("Wix Integration is not enabled"))
	
	try:
		if item_code:
			# Sync specific item
			item_doc = frappe.get_doc("Item", item_code)
			from wix_integration.wix_integration.api.product_sync import sync_product_to_wix
			sync_product_to_wix(item_doc, "manual")
			
			frappe.msgprint(
				_("Manual sync initiated for item: {0}").format(item_code),
				title=_("Sync Initiated"),
				indicator="blue"
			)
		else:
			frappe.throw(_("Item code is required for manual sync"))
			
	except Exception as e:
		frappe.log_error(f"Manual sync error: {str(e)}", "Wix Integration Error")
		frappe.throw(_("Manual sync failed: {0}").format(str(e)))

@frappe.whitelist()
def get_integration_health():
	"""Get integration health status"""
	try:
		settings = get_wix_settings()
		if not settings or not settings.enabled:
			return {
				"status": "disabled",
				"message": "Integration is disabled",
				"health_score": 0
			}
		
		health_score = 100
		issues = []
		
		# Check credentials
		if not all([settings.site_id, settings.api_key, settings.account_id]):
			health_score -= 30
			issues.append("Missing credentials")
		
		# Check recent sync errors
		recent_error_count = frappe.db.count(
			"Wix Integration Log",
			filters={
				"status": "Error",
				"timestamp": [">", frappe.utils.add_days(frappe.utils.now(), -7)]
			}
		)
		
		if recent_error_count > 10:
			health_score -= 20
			issues.append(f"High error rate ({recent_error_count} errors in past 7 days)")
		
		# Check last successful sync
		if settings.last_sync:
			days_since_sync = frappe.utils.date_diff(frappe.utils.now(), settings.last_sync)
			if days_since_sync > 7:
				health_score -= 15
				issues.append(f"No sync activity for {days_since_sync} days")
		else:
			health_score -= 25
			issues.append("No sync activity recorded")
		
		# Determine status
		if health_score >= 80:
			status = "healthy"
		elif health_score >= 60:
			status = "warning"
		else:
			status = "critical"
		
		return {
			"status": status,
			"health_score": max(health_score, 0),
			"issues": issues,
			"message": "Integration is functioning normally" if not issues else "; ".join(issues)
		}
		
	except Exception as e:
		frappe.log_error(f"Health check error: {str(e)}", "Wix Integration Error")
		return {
			"status": "error",
			"health_score": 0,
			"message": f"Health check failed: {str(e)}"
		}
