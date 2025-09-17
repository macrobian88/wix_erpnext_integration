# -*- coding: utf-8 -*-
"""Webhook endpoints for Wix Integration"""

import frappe
from frappe import _
import json
import hmac
import hashlib
from datetime import datetime
from wix_integration.wix_integration.doctype.wix_integration_log.wix_integration_log import create_integration_log

@frappe.whitelist(allow_guest=True)
def handle_wix_webhook():
	"""Handle incoming webhooks from Wix"""
	try:
		# Get request data
		data = frappe.local.request.get_data(as_text=True)
		headers = frappe.local.request.headers
		
		# Log the webhook received
		frappe.logger().info(f"Received Wix webhook: {headers.get('X-Wix-Webhook-Event-Type', 'unknown')}")
		
		# Verify webhook signature
		if not verify_webhook_signature(data, headers):
			frappe.local.response.http_status_code = 401
			return {"error": "Invalid webhook signature"}
		
		# Parse webhook data
		try:
			webhook_data = json.loads(data) if data else {}
		except json.JSONDecodeError:
			frappe.local.response.http_status_code = 400
			return {"error": "Invalid JSON data"}
		
		# Get event type
		event_type = headers.get('X-Wix-Webhook-Event-Type')
		if not event_type:
			frappe.local.response.http_status_code = 400
			return {"error": "Missing event type header"}
		
		# Process webhook based on event type
		result = process_webhook_event(event_type, webhook_data, headers)
		
		# Log webhook processing
		create_integration_log(
			operation_type="Webhook",
			status="Success" if result.get('success') else "Failed",
			request_data={
				'event_type': event_type,
				'headers': dict(headers),
				'data': webhook_data
			},
			response_data=result,
			error_details=result.get('error') if not result.get('success') else None,
			sync_direction="Wix to ERPNext"
		)
		
		return result
		
	except Exception as e:
		frappe.log_error(f"Error handling Wix webhook: {str(e)}", "Wix Webhook")
		frappe.local.response.http_status_code = 500
		return {"error": "Internal server error"}

def verify_webhook_signature(data, headers):
	"""Verify webhook signature from Wix"""
	try:
		# Get signature from headers
		signature = headers.get('X-Wix-Signature')
		if not signature:
			frappe.logger().warning("No signature found in webhook headers")
			return True  # Allow unsigned webhooks in development
		
		# Get webhook secret from settings
		settings = frappe.get_single("Wix Settings")
		if not settings.webhook_secret:
			frappe.logger().warning("No webhook secret configured")
			return True  # Allow if no secret is configured
		
		# Calculate expected signature
		expected_signature = hmac.new(
			settings.webhook_secret.encode('utf-8'),
			data.encode('utf-8'),
			hashlib.sha256
		).hexdigest()
		
		# Compare signatures
		if not hmac.compare_digest(signature, expected_signature):
			frappe.logger().error(f"Webhook signature mismatch. Expected: {expected_signature}, Got: {signature}")
			return False
		
		return True
		
	except Exception as e:
		frappe.log_error(f"Error verifying webhook signature: {str(e)}", "Wix Webhook")
		return False

def process_webhook_event(event_type, data, headers):
	"""Process different types of webhook events"""
	try:
		frappe.logger().info(f"Processing webhook event: {event_type}")
		
		# Handle different event types
		if event_type == 'OrderPaid':
			return handle_order_paid_event(data)
		elif event_type == 'OrderCreated':
			return handle_order_created_event(data)
		elif event_type == 'ProductChanged':
			return handle_product_changed_event(data)
		elif event_type == 'ProductDeleted':
			return handle_product_deleted_event(data)
		elif event_type == 'InventoryChanged':
			return handle_inventory_changed_event(data)
		else:
			# Unknown event type - log and return success
			frappe.logger().info(f"Unhandled webhook event type: {event_type}")
			return {
				'success': True,
				'message': f'Event {event_type} received but not processed',
				'event_type': event_type
			}
		
	except Exception as e:
		frappe.log_error(f"Error processing webhook event {event_type}: {str(e)}", "Wix Webhook")
		return {'success': False, 'error': str(e)}

def handle_order_paid_event(data):
	"""Handle order paid webhook event"""
	try:
		# Extract order information
		order_data = data.get('data', {})
		order_id = order_data.get('id')
		
		if not order_id:
			return {'success': False, 'error': 'No order ID provided'}
		
		# Check if integration is enabled
		settings = frappe.get_single("Wix Settings")
		if not settings.enabled:
			return {'success': True, 'message': 'Integration disabled'}
		
		# For now, just log the order - implement actual order creation later
		frappe.logger().info(f"Order paid event received for order: {order_id}")
		
		# TODO: Create Sales Order in ERPNext
		# This would involve:
		# 1. Create Customer if doesn't exist
		# 2. Map Wix order items to ERPNext items
		# 3. Create Sales Order
		# 4. Handle payment entries
		
		return {
			'success': True,
			'message': f'Order paid event processed for order {order_id}',
			'order_id': order_id
		}
		
	except Exception as e:
		frappe.log_error(f"Error handling order paid event: {str(e)}", "Wix Webhook")
		return {'success': False, 'error': str(e)}

def handle_order_created_event(data):
	"""Handle order created webhook event"""
	try:
		order_data = data.get('data', {})
		order_id = order_data.get('id')
		
		if not order_id:
			return {'success': False, 'error': 'No order ID provided'}
		
		frappe.logger().info(f"Order created event received for order: {order_id}")
		
		return {
			'success': True,
			'message': f'Order created event processed for order {order_id}',
			'order_id': order_id
		}
		
	except Exception as e:
		frappe.log_error(f"Error handling order created event: {str(e)}", "Wix Webhook")
		return {'success': False, 'error': str(e)}

def handle_product_changed_event(data):
	"""Handle product changed webhook event"""
	try:
		product_data = data.get('data', {})
		product_id = product_data.get('id')
		
		if not product_id:
			return {'success': False, 'error': 'No product ID provided'}
		
		frappe.logger().info(f"Product changed event received for product: {product_id}")
		
		# Find corresponding ERPNext item
		item_mapping = frappe.db.get_value(
			"Wix Item Mapping", 
			{"wix_product_id": product_id}, 
			["item_code", "sync_enabled"], 
			as_dict=True
		)
		
		if item_mapping and item_mapping.sync_enabled:
			# TODO: Implement bidirectional sync
			# Update ERPNext item with Wix product changes
			frappe.logger().info(f"Would update ERPNext item {item_mapping.item_code} from Wix product {product_id}")
		
		return {
			'success': True,
			'message': f'Product changed event processed for product {product_id}',
			'product_id': product_id
		}
		
	except Exception as e:
		frappe.log_error(f"Error handling product changed event: {str(e)}", "Wix Webhook")
		return {'success': False, 'error': str(e)}

def handle_product_deleted_event(data):
	"""Handle product deleted webhook event"""
	try:
		product_data = data.get('data', {})
		product_id = product_data.get('id')
		
		if not product_id:
			return {'success': False, 'error': 'No product ID provided'}
		
		frappe.logger().info(f"Product deleted event received for product: {product_id}")
		
		# Find and update corresponding item mapping
		item_mapping = frappe.db.get_value(
			"Wix Item Mapping", 
			{"wix_product_id": product_id}, 
			"name"
		)
		
		if item_mapping:
			# Update mapping to reflect deletion
			mapping_doc = frappe.get_doc("Wix Item Mapping", item_mapping)
			mapping_doc.sync_status = "Error"
			mapping_doc.sync_errors = f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}: Product deleted from Wix\n" + (mapping_doc.sync_errors or "")
			mapping_doc.save(ignore_permissions=True)
		
		return {
			'success': True,
			'message': f'Product deleted event processed for product {product_id}',
			'product_id': product_id
		}
		
	except Exception as e:
		frappe.log_error(f"Error handling product deleted event: {str(e)}", "Wix Webhook")
		return {'success': False, 'error': str(e)}

def handle_inventory_changed_event(data):
	"""Handle inventory changed webhook event"""
	try:
		inventory_data = data.get('data', {})
		product_id = inventory_data.get('productId')
		variant_id = inventory_data.get('variantId')
		new_quantity = inventory_data.get('quantity', 0)
		
		if not product_id:
			return {'success': False, 'error': 'No product ID provided'}
		
		frappe.logger().info(f"Inventory changed event received for product: {product_id}, new quantity: {new_quantity}")
		
		# Find corresponding ERPNext item
		item_mapping = frappe.db.get_value(
			"Wix Item Mapping", 
			{"wix_product_id": product_id}, 
			["item_code", "sync_enabled", "sync_inventory"], 
			as_dict=True
		)
		
		if item_mapping and item_mapping.sync_enabled and item_mapping.sync_inventory:
			# TODO: Implement inventory sync from Wix to ERPNext
			# This would involve creating Stock Entry to adjust inventory
			frappe.logger().info(f"Would update ERPNext inventory for item {item_mapping.item_code} to {new_quantity}")
		
		return {
			'success': True,
			'message': f'Inventory changed event processed for product {product_id}',
			'product_id': product_id,
			'new_quantity': new_quantity
		}
		
	except Exception as e:
		frappe.log_error(f"Error handling inventory changed event: {str(e)}", "Wix Webhook")
		return {'success': False, 'error': str(e)}

@frappe.whitelist()
def test_webhook_endpoint():
	"""Test webhook endpoint for development"""
	try:
		if not frappe.has_permission("Wix Settings", "write"):
			frappe.throw(_("Insufficient permissions to test webhook"))
		
		# Create a test webhook payload
		test_payload = {
			'eventType': 'ProductChanged',
			'data': {
				'id': 'test-product-123',
				'name': 'Test Product',
				'price': 99.99
			},
			'timestamp': datetime.now().isoformat()
		}
		
		# Process test webhook
		result = process_webhook_event('ProductChanged', test_payload, {})
		
		return {
			'success': True,
			'message': 'Test webhook processed successfully',
			'result': result
		}
		
	except Exception as e:
		frappe.log_error(f"Error testing webhook: {str(e)}", "Wix Webhook Test")
		return {'success': False, 'error': str(e)}

@frappe.whitelist()
def get_webhook_url():
	"""Get the webhook URL for Wix configuration"""
	try:
		if not frappe.has_permission("Wix Settings", "read"):
			frappe.throw(_("Insufficient permissions to view webhook URL"))
		
		site_url = frappe.utils.get_site_url()
		webhook_url = f"{site_url}/api/method/wix_integration.api.webhook.handle_wix_webhook"
		
		return {
			'success': True,
			'webhook_url': webhook_url,
			'instructions': [
				'Copy this URL and add it to your Wix webhook configuration',
				'Make sure to configure the webhook secret in Wix Settings',
				'Enable the events you want to sync (OrderPaid, ProductChanged, etc.)'
			]
		}
		
	except Exception as e:
		return {'success': False, 'error': str(e)}