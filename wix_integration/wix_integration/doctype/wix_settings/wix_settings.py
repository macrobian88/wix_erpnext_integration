# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.model.document import Document
import requests
import json
from datetime import datetime
from wix_integration.wix_integration.wix_connector import WixConnector

class WixSettings(Document):
	def validate(self):
		"""Validation logic for Wix Settings"""
		if self.enabled:
			self.validate_required_fields()
			if not self.test_mode:
				self.validate_wix_credentials()
			
		# Generate webhook URL if not exists
		if not self.webhook_url:
			site_url = frappe.utils.get_url()
			self.webhook_url = f"{site_url}/api/method/wix_integration.api.webhook.handle_wix_webhook"
			
		# Generate webhook secret if not exists
		if not self.webhook_secret:
			import secrets
			self.webhook_secret = secrets.token_urlsafe(32)
	
	def validate_required_fields(self):
		"""Validate required fields when integration is enabled"""
		if not self.site_id:
			frappe.throw(_("Wix Site ID is required when integration is enabled"))
		if not self.api_key:
			frappe.throw(_("Wix API Key is required when integration is enabled"))
		if not self.account_id:
			frappe.throw(_("Wix Account ID is required when integration is enabled"))
	
	def validate_wix_credentials(self):
		"""Validate Wix API credentials by making a test call"""
		try:
			connector = WixConnector()
			result = connector.test_connection()
			if not result.get('success'):
				frappe.throw(_("Wix API credentials validation failed: {0}").format(result.get('error')))
		except Exception as e:
			frappe.log_error(f"Wix credentials validation error: {str(e)}", "Wix Settings Validation")
			frappe.throw(_("Failed to validate Wix credentials: {0}").format(str(e)))
	
	def on_update(self):
		"""Actions to perform when settings are updated"""
		# Clear cache
		frappe.cache().delete_key("wix_settings")
		
		# Log settings change
		frappe.log_error(
			f"Wix Settings updated by {frappe.session.user}",
			"Wix Settings Update"
		)

@frappe.whitelist()
def get_wix_settings():
	"""Get Wix settings with caching"""
	cached_settings = frappe.cache().get_value("wix_settings")
	if cached_settings:
		return cached_settings
		
	settings = frappe.get_single("Wix Settings")
	frappe.cache().set_value("wix_settings", settings, expires_in_sec=300)  # 5 minutes cache
	return settings

@frappe.whitelist()
def test_wix_connection():
	"""Test Wix API connection"""
	try:
		connector = WixConnector()
		result = connector.test_connection()
		
		if result.get('success'):
			# Update last successful connection time
			settings = frappe.get_single("Wix Settings")
			settings.last_sync = datetime.now()
			settings.save(ignore_permissions=True)
			
		return result
	except Exception as e:
		frappe.log_error(f"Test connection error: {str(e)}", "Wix Connection Test")
		return {
			'success': False,
			'error': str(e)
		}

@frappe.whitelist()
def reset_sync_counters():
	"""Reset sync monitoring counters"""
	if not frappe.has_permission("Wix Settings", "write"):
		frappe.throw(_("Insufficient permissions to reset sync counters"))
	
	settings = frappe.get_single("Wix Settings")
	settings.total_synced_items = 0
	settings.failed_syncs = 0
	settings.sync_errors = ""
	settings.save(ignore_permissions=True)
	
	return {'success': True, 'message': 'Sync counters reset successfully'}

@frappe.whitelist()
def get_sync_statistics():
	"""Get detailed sync statistics"""
	if not frappe.has_permission("Wix Settings", "read"):
		frappe.throw(_("Insufficient permissions to view sync statistics"))
	
	# Get basic stats from settings
	settings = frappe.get_single("Wix Settings")
	
	# Get detailed stats from log
	log_stats = frappe.db.sql("""
		SELECT 
			status,
			COUNT(*) as count,
			MAX(creation) as last_occurrence
		FROM `tabWix Integration Log`
		WHERE creation >= DATE_SUB(NOW(), INTERVAL 7 DAY)
		GROUP BY status
	""", as_dict=True)
	
	return {
		'settings': {
			'total_synced_items': settings.total_synced_items,
			'failed_syncs': settings.failed_syncs,
			'last_sync': settings.last_sync
		},
		'weekly_stats': log_stats
	}