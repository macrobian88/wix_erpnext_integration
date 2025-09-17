# -*- coding: utf-8 -*-
"""Wix Webhook Handler - Receives and processes webhooks from Wix

This module handles incoming webhooks from Wix for various events like
order creation, product updates, inventory changes, etc.
"""

import frappe
import json
import hmac
import hashlib
from frappe import _

@frappe.whitelist(allow_guest=True)
def handle_wix_webhook():
	"""
	Handle incoming webhooks from Wix
	This endpoint receives webhook calls from Wix when events occur
	"""
	try:
		# Get webhook data
		data = frappe.request.get_data(as_text=True)
		headers = frappe.request.headers
		
		# Verify webhook signature if secret is configured
		if not verify_webhook_signature(data, headers):
			frappe.log_error("Invalid webhook signature", "Wix Webhook Error")
			return {"status": "error", "message": "Invalid signature"}, 401
		
		# Parse webhook data
		webhook_data = json.loads(data) if data else {}
		
		# Get event type
		event_type = webhook_data.get('eventType') or headers.get('X-Wix-Event-Type')
		
		if not event_type:
			frappe.log_error("No event type in webhook", "Wix Webhook Error")
			return {"status": "error", "message": "No event type"}, 400
		
		# Log incoming webhook
		create_webhook_log(event_type, webhook_data, "Received")
		
		# Route to appropriate handler
		result = route_webhook_event(event_type, webhook_data)
		
		# Log processing result
		status = "Success" if result.get('success') else "Error"
		create_webhook_log(event_type, {"result": result}, status)
		
		return result
		
	except Exception as e:
		error_msg = f"Webhook processing error: {str(e)}"
		frappe.log_error(error_msg, "Wix Webhook Error")
		
		create_webhook_log("unknown", {"error": str(e)}, "Error")
		
		return {"status": "error", "message": "Internal error"}, 500

def verify_webhook_signature(data, headers):
	"""Verify webhook signature for security"""
	try:
		settings = frappe.get_single('Wix Settings')
		webhook_secret = settings.get('webhook_secret')
		
		if not webhook_secret:
			# If no secret configured, skip verification (not recommended for production)
			return True
		
		# Get signature from headers
		signature = headers.get('X-Wix-Signature') or headers.get('X-Hub-Signature-256')
		
		if not signature:
			return False
		
		# Calculate expected signature
		expected_signature = hmac.new(
			webhook_secret.encode('utf-8'),
			data.encode('utf-8'),
			hashlib.sha256
		).hexdigest()
		
		# Compare signatures
		return hmac.compare_digest(f"sha256={expected_signature}", signature)
		
	except Exception as e:
		frappe.log_error(f"Signature verification error: {str(e)}", "Wix Webhook Error")
		return False

def route_webhook_event(event_type, webhook_data):
	"""Route webhook events to appropriate handlers"""
	
	event_handlers = {
		'PRODUCT_CREATED': handle_product_created,
		'PRODUCT_UPDATED': handle_product_updated,
		'PRODUCT_DELETED': handle_product_deleted,
		'INVENTORY_UPDATED': handle_inventory_updated,
		'ORDER_CREATED': handle_order_created,
		'ORDER_UPDATED': handle_order_updated,
		'ORDER_PAID': handle_order_paid,
		'CATEGORY_CREATED': handle_category_created,
		'CATEGORY_UPDATED': handle_category_updated,
	}
	
	handler = event_handlers.get(event_type)
	
	if handler:
		try:
			return handler(webhook_data)
		except Exception as e:
			error_msg = f"Handler error for {event_type}: {str(e)}"
			frappe.log_error(error_msg, "Wix Webhook Handler Error")
			return {"success": False, "error": error_msg}
	else:
		# Unsupported event type
		return {
			"success": True, 
			"message": f"Event type {event_type} not handled",
			"action": "ignored"
		}

def handle_product_created(webhook_data):
	"""Handle product created webhook"""
	# For POC, we primarily sync FROM ERPNext TO Wix
	# This handler would be used for future bidirectional sync
	return {
		"success": True,
		"message": "Product created webhook received",
		"action": "logged"
	}

def handle_product_updated(webhook_data):
	"""Handle product updated webhook"""
	# For POC, we primarily sync FROM ERPNext TO Wix
	# This handler would be used for future bidirectional sync
	return {
		"success": True,
		"message": "Product updated webhook received",
		"action": "logged"
	}

def handle_product_deleted(webhook_data):
	"""Handle product deleted webhook"""
	try:
		product_data = webhook_data.get('data', {})
		wix_product_id = product_data.get('id')
		
		if wix_product_id:
			# Find corresponding item mapping
			mapping = frappe.db.get_value(
				"Wix Item Mapping",
				{"wix_product_id": wix_product_id},
				["name", "erpnext_item"]
			)
			
			if mapping:
				# Update mapping status
				frappe.db.set_value(
					"Wix Item Mapping",
					mapping[0],
					{
						"sync_status": "Error",
						"error_message": "Product deleted in Wix"
					}
				)
				
				# Update item custom field
				frappe.db.set_value(
					"Item",
					mapping[1],
					{
						"wix_sync_status": "Error",
						"wix_product_id": None
					}
				)
				
				frappe.db.commit()
		
		return {
			"success": True,
			"message": "Product deletion processed",
			"wix_product_id": wix_product_id
		}
		
	except Exception as e:
		return {"success": False, "error": str(e)}

def handle_inventory_updated(webhook_data):
	"""Handle inventory updated webhook"""
	# Placeholder for inventory sync
	return {
		"success": True,
		"message": "Inventory update webhook received",
		"action": "logged"
	}

def handle_order_created(webhook_data):
	"""Handle order created webhook - Create Sales Order in ERPNext"""
	try:
		order_data = webhook_data.get('data', {})
		wix_order_id = order_data.get('id')
		
		if not wix_order_id:
			return {"success": False, "error": "No order ID in webhook data"}
		
		# Check if order already exists
		existing_order = frappe.db.get_value(
			"Sales Order",
			{"wix_order_id": wix_order_id}
		)
		
		if existing_order:
			return {
				"success": True,
				"message": f"Order {wix_order_id} already exists as {existing_order}",
				"action": "skipped"
			}
		
		# Create Sales Order from Wix order data
		sales_order = create_sales_order_from_wix(order_data)
		
		return {
			"success": True,
			"message": f"Sales Order {sales_order.name} created from Wix order {wix_order_id}",
			"sales_order": sales_order.name,
			"wix_order_id": wix_order_id
		}
		
	except Exception as e:
		return {"success": False, "error": str(e)}

def handle_order_updated(webhook_data):
	"""Handle order updated webhook"""
	try:
		order_data = webhook_data.get('data', {})
		wix_order_id = order_data.get('id')
		
		# Find corresponding Sales Order
		sales_order_name = frappe.db.get_value(
			"Sales Order",
			{"wix_order_id": wix_order_id}
		)
		
		if sales_order_name:
			# Update sales order based on Wix data
			# This is a placeholder for order update logic
			return {
				"success": True,
				"message": f"Order update processed for {sales_order_name}",
				"action": "updated"
			}
		else:
			return {
				"success": False,
				"error": f"Sales Order not found for Wix order {wix_order_id}"
			}
			
	except Exception as e:
		return {"success": False, "error": str(e)}

def handle_order_paid(webhook_data):
	"""Handle order paid webhook"""
	# Placeholder for payment processing
	return {
		"success": True,
		"message": "Order payment webhook received",
		"action": "logged"
	}

def handle_category_created(webhook_data):
	"""Handle category created webhook"""
	return {
		"success": True,
		"message": "Category created webhook received",
		"action": "logged"
	}

def handle_category_updated(webhook_data):
	"""Handle category updated webhook"""
	return {
		"success": True,
		"message": "Category updated webhook received",
		"action": "logged"
	}

def create_sales_order_from_wix(order_data):
	"""Create ERPNext Sales Order from Wix order data"""
	
	# Extract customer information
	billing_info = order_data.get('billingInfo', {})
	customer_name = f"{billing_info.get('firstName', '')} {billing_info.get('lastName', '')}".strip()
	customer_email = billing_info.get('email')
	
	# Create or get customer
	customer = get_or_create_customer(customer_name, customer_email, billing_info)
	
	# Create Sales Order
	sales_order = frappe.get_doc({
		'doctype': 'Sales Order',
		'customer': customer,
		'wix_order_id': order_data.get('id'),
		'transaction_date': frappe.utils.today(),
		'delivery_date': frappe.utils.add_days(frappe.utils.today(), 7),  # Default 7 days
		'company': frappe.defaults.get_defaults().get('company') or frappe.get_all('Company', limit=1)[0].name,
		'currency': order_data.get('currency', 'USD'),
		'conversion_rate': 1.0,
		'items': []
	})
	
	# Add order items
	line_items = order_data.get('lineItems', [])
	
	for line_item in line_items:
		catalog_reference = line_item.get('catalogReference', {})
		product_id = catalog_reference.get('catalogItemId')
		
		# Find corresponding ERPNext item
		item_mapping = frappe.db.get_value(
			"Wix Item Mapping",
			{"wix_product_id": product_id},
			"erpnext_item"
		)
		
		if item_mapping:
			sales_order.append('items', {
				'item_code': item_mapping,
				'qty': line_item.get('quantity', 1),
				'rate': float(line_item.get('price', {}).get('amount', 0)),
				'delivery_date': sales_order.delivery_date
			})
		else:
			# Create a generic item for unmapped products
			sales_order.append('items', {
				'item_code': 'MISC-ITEM',  # Should exist in ERPNext
				'item_name': line_item.get('name', 'Wix Product'),
				'qty': line_item.get('quantity', 1),
				'rate': float(line_item.get('price', {}).get('amount', 0)),
				'delivery_date': sales_order.delivery_date
			})
	
	# Save and submit if configured
	sales_order.insert(ignore_permissions=True)
	
	# Auto-submit if configured
	settings = frappe.get_single('Wix Settings')
	if settings.get('auto_submit_orders'):
		sales_order.submit()
	
	frappe.db.commit()
	return sales_order

def get_or_create_customer(customer_name, email, billing_info):
	"""Get existing customer or create new one"""
	
	# Try to find existing customer by email
	if email:
		existing_customer = frappe.db.get_value("Customer", {"email_id": email})
		if existing_customer:
			return existing_customer
	
	# Create new customer
	customer_doc = frappe.get_doc({
		'doctype': 'Customer',
		'customer_name': customer_name or email or 'Wix Customer',
		'customer_type': 'Individual',
		'customer_group': 'Commercial',  # Adjust as needed
		'territory': 'All Territories',
		'email_id': email
	})
	
	# Add address information if available
	if billing_info.get('address'):
		address = billing_info['address']
		customer_doc.customer_primary_address = create_address_for_customer(
			customer_doc.customer_name,
			address,
			'Billing'
		)
	
	customer_doc.insert(ignore_permissions=True)
	frappe.db.commit()
	
	return customer_doc.name

def create_address_for_customer(customer_name, address_data, address_type):
	"""Create address for customer"""
	
	address_doc = frappe.get_doc({
		'doctype': 'Address',
		'address_title': f"{customer_name} - {address_type}",
		'address_type': address_type,
		'address_line1': address_data.get('addressLine1', ''),
		'address_line2': address_data.get('addressLine2', ''),
		'city': address_data.get('city', ''),
		'state': address_data.get('subdivision', ''),
		'pincode': address_data.get('zipCode', ''),
		'country': address_data.get('country', ''),
		'links': [{
			'link_doctype': 'Customer',
			'link_name': customer_name
		}]
	})
	
	address_doc.insert(ignore_permissions=True)
	frappe.db.commit()
	
	return address_doc.name

def create_webhook_log(event_type, data, status):
	"""Create webhook log entry"""
	try:
		frappe.get_doc({
			'doctype': 'Wix Integration Log',
			'operation_type': 'Webhook',
			'reference_doctype': 'Webhook',
			'reference_name': event_type,
			'status': status,
			'message': f"Webhook {event_type} {status.lower()}",
			'timestamp': frappe.utils.now(),
			'wix_response': json.dumps(data, default=str)[:5000]
		}).insert(ignore_permissions=True)
		
		frappe.db.commit()
		
	except Exception as e:
		frappe.log_error(f"Error creating webhook log: {str(e)}", "Wix Webhook Log Error")
