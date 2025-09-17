# -*- coding: utf-8 -*-
"""Wix API Testing and Utility Functions

This module provides whitelisted methods for testing and debugging Wix integration.
"""

import frappe
from frappe import _
from wix_integration.wix_integration.wix_connector import WixConnector

@frappe.whitelist()
def test_wix_connection():
	"""Test Wix API connection - whitelisted method"""
	if not frappe.has_permission("Wix Settings", "read"):
		frappe.throw(_("Insufficient permissions to test Wix connection"))
	
	try:
		connector = WixConnector()
		result = connector.test_connection()
		return result
		
	except Exception as e:
		frappe.log_error(f"Error testing Wix connection: {str(e)}", "Wix Connection Test Error")
		return {
			'success': False,
			'error': f'Connection test failed: {str(e)}'
		}

@frappe.whitelist()
def manual_product_sync(item_name):
	"""Manually sync a specific item to Wix - whitelisted method"""
	if not frappe.has_permission("Item", "write"):
		frappe.throw(_("Insufficient permissions to sync products"))
	
	try:
		from wix_integration.wix_integration.api.product_sync import sync_product_to_wix
		
		# Get the item
		item_doc = frappe.get_doc("Item", item_name)
		
		# Sync to Wix
		result = sync_product_to_wix(item_doc, "manual")
		
		return result
		
	except Exception as e:
		frappe.log_error(f"Error in manual product sync: {str(e)}", "Wix Manual Sync Error")
		return {
			'success': False,
			'error': f'Manual sync failed: {str(e)}'
		}

@frappe.whitelist()
def get_sync_status(item_name):
	"""Get sync status for a specific item"""
	if not frappe.has_permission("Item", "read"):
		frappe.throw(_("Insufficient permissions to view sync status"))
	
	try:
		item = frappe.get_doc("Item", item_name)
		
		return {
			'item_name': item.name,
			'item_title': item.item_name,
			'wix_product_id': item.get('wix_product_id'),
			'wix_sync_status': item.get('wix_sync_status'),
			'wix_last_sync': item.get('wix_last_sync'),
			'wix_sync_error': item.get('wix_sync_error')
		}
		
	except Exception as e:
		return {
			'success': False,
			'error': str(e)
		}

@frappe.whitelist()
def get_integration_logs(limit=10):
	"""Get recent integration logs"""
	if not frappe.has_permission("Wix Integration Log", "read"):
		frappe.throw(_("Insufficient permissions to view integration logs"))
	
	try:
		logs = frappe.get_all(
			"Wix Integration Log",
			fields=[
				"name", "operation_type", "reference_doctype", "reference_name", 
				"status", "message", "timestamp"
			],
			order_by="timestamp desc",
			limit=limit
		)
		
		return logs
		
	except Exception as e:
		return {
			'success': False,
			'error': str(e)
		}

@frappe.whitelist()
def reset_item_sync_status(item_name):
	"""Reset an item's sync status to Ready"""
	if not frappe.has_permission("Item", "write"):
		frappe.throw(_("Insufficient permissions to reset sync status"))
	
	try:
		frappe.db.set_value("Item", item_name, {
			"wix_sync_status": "Ready",
			"wix_sync_error": None
		})
		
		frappe.db.commit()
		
		return {
			'success': True,
			'message': f'Reset sync status for {item_name} to Ready'
		}
		
	except Exception as e:
		return {
			'success': False,
			'error': str(e)
		}

@frappe.whitelist()
def get_wix_settings_status():
	"""Get current Wix settings status"""
	if not frappe.has_permission("Wix Settings", "read"):
		frappe.throw(_("Insufficient permissions to view Wix settings"))
	
	try:
		settings = frappe.get_single('Wix Settings')
		
		# Get sync statistics
		total_items = frappe.db.count("Item", filters={
			"disabled": 0,
			"is_stock_item": 1
		})
		
		synced_items = frappe.db.count("Item", filters={
			"disabled": 0,
			"is_stock_item": 1,
			"wix_sync_status": "Synced"
		})
		
		error_items = frappe.db.count("Item", filters={
			"disabled": 0,
			"is_stock_item": 1,
			"wix_sync_status": "Error"
		})
		
		return {
			'enabled': settings.enabled,
			'test_mode': settings.test_mode,
			'auto_sync_items': settings.auto_sync_items,
			'site_id': settings.site_id,
			'account_id': settings.account_id,
			'has_api_key': bool(settings.api_key),
			'last_sync': settings.last_sync,
			'total_synced_items': settings.total_synced_items or 0,
			'failed_syncs': settings.failed_syncs or 0,
			'statistics': {
				'total_items': total_items,
				'synced_items': synced_items,
				'error_items': error_items,
				'sync_rate': (synced_items / max(total_items, 1)) * 100
			}
		}
		
	except Exception as e:
		return {
			'success': False,
			'error': str(e)
		}
