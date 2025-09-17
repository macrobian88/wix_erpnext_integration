# -*- coding: utf-8 -*-
"""Product Sync API - Handles ERPNext to Wix product synchronization

This module provides production-grade bidirectional sync between ERPNext Items and Wix Products
using the Wix Stores v3 API with proper error handling, validation, and logging.
"""

import frappe
import json
from datetime import datetime
from frappe import _
from frappe.utils import flt, cstr, get_site_url
from wix_integration.wix_integration.wix_connector import WixConnector

def sync_product_to_wix(item_doc, trigger_type="auto"):
	"""
	Sync an ERPNext Item to Wix as a Product
	
	Args:
		item_doc: ERPNext Item document
		trigger_type: Type of sync trigger ('auto', 'manual', 'bulk')
	
	Returns:
		dict: Sync result with success status and details
	"""
	if not frappe.db.get_single_value('Wix Settings', 'enabled'):
		return {'success': False, 'error': 'Wix integration is not enabled'}
	
	settings = frappe.get_single('Wix Settings')
	
	# Check if auto sync is enabled for this trigger
	if trigger_type == "auto" and not settings.auto_sync_items:
		return {'success': False, 'message': 'Auto sync is disabled'}
	
	try:
		# Prepare Wix product data according to v3 API specification
		product_data = build_wix_product_data(item_doc, settings)
		
		# Initialize Wix connector
		connector = WixConnector()
		
		# Check if item already exists in Wix
		existing_wix_id = item_doc.get('wix_product_id')
		
		if existing_wix_id:
			# Update existing product
			result = connector.update_product(existing_wix_id, product_data)
			operation = "update"
		else:
			# Create new product
			result = connector.create_product(product_data)
			operation = "create"
		
		if result.get('success'):
			# Update item with Wix details
			update_item_with_wix_data(item_doc, result, operation)
			
			# Update sync statistics
			update_sync_statistics(settings, True)
			
			# Log success
			create_integration_log(
				operation_type="Product Sync",
				reference_doctype="Item",
				reference_name=item_doc.name,
				status="Success",
				message=f"Successfully {operation}d product in Wix",
				wix_response=result
			)
			
			return {
				'success': True,
				'operation': operation,
				'wix_product_id': result.get('product_id'),
				'message': f'Product {operation}d successfully in Wix'
			}
		else:
			# Handle failure
			update_sync_statistics(settings, False)
			
			# Log error
			create_integration_log(
				operation_type="Product Sync",
				reference_doctype="Item",
				reference_name=item_doc.name,
				status="Error",
				message=f"Failed to {operation} product in Wix: {result.get('error')}",
				wix_response=result
			)
			
			# Update item sync status
			update_item_sync_status(item_doc.name, "Error", result.get('error'))
			
			return {
				'success': False,
				'error': result.get('error'),
				'error_data': result.get('error_data')
			}
			
	except Exception as e:
		# Handle unexpected errors
		error_message = f"Unexpected error during product sync: {str(e)}"
		frappe.log_error(error_message, "Wix Product Sync Error")
		
		update_sync_statistics(settings, False)
		
		create_integration_log(
			operation_type="Product Sync",
			reference_doctype="Item",
			reference_name=item_doc.name,
			status="Error",
			message=error_message
		)
		
		update_item_sync_status(item_doc.name, "Error", str(e))
		
		return {
			'success': False,
			'error': error_message
		}

def build_wix_product_data(item_doc, settings):
	"""
	Build Wix product data structure according to Stores v3 API
	
	Args:
		item_doc: ERPNext Item document
		settings: Wix Settings document
	
	Returns:
		dict: Wix product data structure
	"""
	
	# Get item price from Item Price doctype
	item_price = get_item_price(item_doc.name)
	
	# Build basic product structure
	product_data = {
		"name": item_doc.item_name or item_doc.name,
		"productType": "PHYSICAL",  # Default to physical product
		"visible": True,
		"visibleInPos": True
	}
	
	# Add description if enabled
	if settings.sync_item_description and item_doc.description:
		product_data["plainDescription"] = item_doc.description
	
	# Add physical properties (required for PHYSICAL products)
	product_data["physicalProperties"] = {}
	
	# Add variant info (required)
	variant_data = {
		"price": {
			"actualPrice": {
				"amount": str(item_price or "0.00")
			}
		},
		"physicalProperties": {}
	}
	
	# Add SKU if available
	if item_doc.item_code:
		variant_data["sku"] = item_doc.item_code
	
	# Add weight if available
	if item_doc.weight_per_unit:
		variant_data["physicalProperties"]["weight"] = flt(item_doc.weight_per_unit)
	
	product_data["variantsInfo"] = {
		"variants": [variant_data]
	}
	
	# Add media (images) if enabled and available
	if settings.sync_item_images and item_doc.image:
		media_items = []
		
		# Add main image
		if item_doc.image:
			site_url = get_site_url(frappe.local.site)
			full_image_url = f"{site_url}{item_doc.image}" if not item_doc.image.startswith('http') else item_doc.image
			
			media_items.append({
				"url": full_image_url
			})
		
		# Add additional images from Website Item if available
		try:
			website_item = frappe.get_doc("Website Item", {"item_code": item_doc.name})
			if website_item and website_item.website_image:
				site_url = get_site_url(frappe.local.site)
				full_image_url = f"{site_url}{website_item.website_image}" if not website_item.website_image.startswith('http') else website_item.website_image
				
				if full_image_url not in [item.get('url') for item in media_items]:
					media_items.append({
						"url": full_image_url
					})
		except:
			pass  # Website Item might not exist
		
		if media_items:
			product_data["media"] = {
				"items": media_items
			}
	
	# Add categories if enabled
	if settings.sync_categories and item_doc.item_group:
		# Get or create category in Wix
		category_id = get_or_create_wix_category(item_doc.item_group)
		if category_id:
			product_data["mainCategoryId"] = category_id
	
	return product_data

def get_item_price(item_code):
	"""Get item price from Item Price doctype"""
	try:
		item_price = frappe.get_all(
			"Item Price",
			filters={
				"item_code": item_code,
				"selling": 1
			},
			fields=["price_list_rate"],
			order_by="valid_from desc",
			limit=1
		)
		
		if item_price:
			return flt(item_price[0].price_list_rate, 2)
		
		# Fallback to standard rate from item
		item = frappe.get_doc("Item", item_code)
		return flt(item.standard_rate or 0, 2)
		
	except Exception as e:
		frappe.log_error(f"Error getting item price for {item_code}: {str(e)}", "Wix Price Sync")
		return 0.00

def get_or_create_wix_category(item_group):
	"""Get existing or create new category in Wix"""
	try:
		# Check if category mapping exists
		mapping = frappe.db.get_value(
			"Wix Category Mapping",
			{"erpnext_item_group": item_group},
			["wix_category_id"]
		)
		
		if mapping:
			return mapping
		
		# Create new category in Wix
		connector = WixConnector()
		category_data = {
			"name": item_group,
			"visible": True
		}
		
		result = connector.create_category(category_data)
		
		if result.get('success'):
			category_id = result.get('category_id')
			
			# Create mapping record
			frappe.get_doc({
				'doctype': 'Wix Category Mapping',
				'erpnext_item_group': item_group,
				'wix_category_id': category_id,
				'category_name': item_group,
				'sync_status': 'Synced',
				'last_sync': datetime.now()
			}).insert(ignore_permissions=True)
			
			frappe.db.commit()
			return category_id
		
		return None
		
	except Exception as e:
		frappe.log_error(f"Error handling category {item_group}: {str(e)}", "Wix Category Sync")
		return None

def update_item_with_wix_data(item_doc, wix_result, operation):
	"""Update ERPNext item with Wix product data"""
	try:
		# Update custom fields
		frappe.db.set_value("Item", item_doc.name, {
			"wix_product_id": wix_result.get('product_id'),
			"wix_sync_status": "Synced",
			"wix_last_sync": datetime.now()
		})
		
		# Create or update item mapping
		mapping_name = frappe.db.get_value(
			"Wix Item Mapping",
			{"erpnext_item": item_doc.name}
		)
		
		if mapping_name:
			# Update existing mapping
			frappe.db.set_value("Wix Item Mapping", mapping_name, {
				"wix_product_id": wix_result.get('product_id'),
				"sync_status": "Synced",
				"last_sync": datetime.now(),
				"sync_direction": "ERPNext to Wix"
			})
		else:
			# Create new mapping
			frappe.get_doc({
				'doctype': 'Wix Item Mapping',
				'erpnext_item': item_doc.name,
				'item_name': item_doc.item_name or item_doc.name,
				'wix_product_id': wix_result.get('product_id'),
				'sync_status': 'Synced',
				'last_sync': datetime.now(),
				'sync_direction': 'ERPNext to Wix'
			}).insert(ignore_permissions=True)
		
		frappe.db.commit()
		
	except Exception as e:
		frappe.log_error(f"Error updating item {item_doc.name} with Wix data: {str(e)}", "Wix Item Update Error")

def update_item_sync_status(item_name, status, error_message=None):
	"""Update item sync status"""
	try:
		update_data = {
			"wix_sync_status": status,
			"wix_last_sync": datetime.now()
		}
		
		frappe.db.set_value("Item", item_name, update_data)
		
		# Update mapping status
		mapping_name = frappe.db.get_value(
			"Wix Item Mapping",
			{"erpnext_item": item_name}
		)
		
		if mapping_name:
			mapping_data = {
				"sync_status": status,
				"last_sync": datetime.now()
			}
			
			if error_message:
				mapping_data["error_message"] = error_message[:500]  # Limit error message length
			
			frappe.db.set_value("Wix Item Mapping", mapping_name, mapping_data)
		
		frappe.db.commit()
		
	except Exception as e:
		frappe.log_error(f"Error updating sync status for {item_name}: {str(e)}", "Wix Status Update Error")

def update_sync_statistics(settings, success):
	"""Update sync statistics in settings"""
	try:
		if success:
			settings.total_synced_items = (settings.total_synced_items or 0) + 1
		else:
			settings.failed_syncs = (settings.failed_syncs or 0) + 1
		
		settings.last_sync = datetime.now()
		settings.save(ignore_permissions=True)
		frappe.db.commit()
		
	except Exception as e:
		frappe.log_error(f"Error updating sync statistics: {str(e)}", "Wix Stats Update Error")

def create_integration_log(operation_type, reference_doctype, reference_name, status, message, wix_response=None):
	"""Create integration log entry"""
	try:
		log_doc = frappe.get_doc({
			'doctype': 'Wix Integration Log',
			'operation_type': operation_type,
			'reference_doctype': reference_doctype,
			'reference_name': reference_name,
			'status': status,
			'message': message[:1000],  # Limit message length
			'timestamp': datetime.now(),
			'wix_response': json.dumps(wix_response, default=str)[:5000] if wix_response else None
		})
		
		log_doc.insert(ignore_permissions=True)
		frappe.db.commit()
		
	except Exception as e:
		frappe.log_error(f"Error creating integration log: {str(e)}", "Wix Log Creation Error")

# Webhook handlers and bulk operations

@frappe.whitelist()
def bulk_sync_items(filters=None):
	"""Bulk sync items to Wix"""
	if not frappe.db.get_single_value('Wix Settings', 'enabled'):
		frappe.throw(_("Wix integration is not enabled"))
	
	# Get items based on filters
	item_filters = filters or {}
	item_filters.update({
		'disabled': 0,
		'is_stock_item': 1
	})
	
	items = frappe.get_all(
		"Item",
		filters=item_filters,
		fields=["name", "item_name", "item_code"],
		limit=100  # Process in batches
	)
	
	if not items:
		return {"status": "warning", "message": "No items found to sync"}
	
	results = {
		'total': len(items),
		'success': 0,
		'failed': 0,
		'errors': []
	}
	
	for item in items:
		try:
			item_doc = frappe.get_doc("Item", item.name)
			result = sync_product_to_wix(item_doc, "bulk")
			
			if result.get('success'):
				results['success'] += 1
			else:
				results['failed'] += 1
				results['errors'].append({
					'item': item.name,
					'error': result.get('error', 'Unknown error')
				})
				
		except Exception as e:
			results['failed'] += 1
			results['errors'].append({
				'item': item.name,
				'error': str(e)
			})
			frappe.log_error(f"Bulk sync error for {item.name}: {str(e)}", "Wix Bulk Sync Error")
	
	return {
		'status': 'completed',
		'message': f"Bulk sync completed: {results['success']} successful, {results['failed']} failed",
		'results': results
	}

# Item hooks integration

def on_item_update(doc, method=None):
	"""Hook: Called when Item is updated"""
	try:
		# Check if Wix integration is enabled and auto-sync is on
		settings = frappe.get_single('Wix Settings')
		if not (settings.enabled and settings.auto_sync_items):
			return
		
		# Only sync if item is stock item and not disabled
		if doc.disabled or not doc.is_stock_item:
			return
		
		# Check if this is a significant update that should trigger sync
		if should_sync_item_update(doc):
			# Sync in background to avoid blocking user operations
			frappe.enqueue(
				sync_product_to_wix,
				queue='short',
				timeout=120,
				item_doc=doc,
				trigger_type="auto"
			)
			
	except Exception as e:
		# Log error but don't fail the item save operation
		frappe.log_error(f"Error in item update hook: {str(e)}", "Wix Item Hook Error")

def should_sync_item_update(doc):
	"""Check if item update should trigger sync"""
	# Define fields that should trigger sync when changed
	sync_fields = [
		'item_name', 'description', 'image', 'standard_rate',
		'item_group', 'disabled', 'is_stock_item'
	]
	
	if doc.is_new():
		return True
	
	# Check if any sync-relevant fields changed
	for field in sync_fields:
		if doc.has_value_changed(field):
			return True
	
	return False
