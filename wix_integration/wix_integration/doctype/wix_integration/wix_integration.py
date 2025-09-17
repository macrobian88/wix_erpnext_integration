# -*- coding: utf-8 -*-
"""Main Wix Integration logic for syncing products from ERPNext to Wix"""

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import get_site_url, flt, cstr
from datetime import datetime
import json
import time
from wix_integration.wix_integration.wix_connector import WixConnector
from wix_integration.wix_integration.doctype.wix_integration_log.wix_integration_log import create_integration_log

class WixIntegration(Document):
	pass

def sync_item_to_wix(item_doc, method=None, item_code=None):
	"""Main function to sync ERPNext Item to Wix Product"""
	start_time = time.time()
	
	# Get item data
	if not item_doc and item_code:
		item_doc = frappe.get_doc("Item", item_code)
	elif not item_doc:
		frappe.log_error("No item document or item code provided", "Wix Integration")
		return
	
	try:
		# Check if integration is enabled
		settings = frappe.get_single("Wix Settings")
		if not settings.enabled or not settings.auto_sync_items:
			frappe.log_error(f"Wix integration disabled for item {item_doc.item_code}", "Wix Integration")
			return
		
		# Get or create item mapping
		from wix_integration.wix_integration.doctype.wix_item_mapping.wix_item_mapping import get_or_create_mapping
		mapping = get_or_create_mapping(item_doc.item_code)
		if not mapping or not mapping.sync_enabled:
			frappe.log_error(f"Sync disabled for item {item_doc.item_code}", "Wix Integration")
			return
		
		# Update mapping status
		mapping.sync_status = "In Progress"
		mapping.save(ignore_permissions=True)
		
		# Build Wix product data
		product_data = build_wix_product_data(item_doc, mapping, settings)
		
		# Initialize connector
		connector = WixConnector()
		
		# Sync to Wix
		if mapping.wix_product_id:
			# Update existing product
			result = connector.update_product(mapping.wix_product_id, product_data)
			operation_type = "Update Product"
		else:
			# Create new product
			result = connector.create_product(product_data)
			operation_type = "Create Product"
		
		execution_time = time.time() - start_time
		
		# Process result
		if result.get('success'):
			# Success - update mapping
			product_id = result.get('product_id') or mapping.wix_product_id
			mapping.update_sync_status("Synced", wix_product_id=product_id)
			
			# Update Wix product details in mapping
			if result.get('product'):
				wix_product = result.get('product')
				mapping.wix_product_name = wix_product.get('name')
				mapping.wix_product_slug = wix_product.get('slug')
				mapping.save(ignore_permissions=True)
			
			# Create success log
			create_integration_log(
				operation_type=operation_type,
				status="Success",
				item_code=item_doc.item_code,
				wix_product_id=product_id,
				request_data=product_data,
				response_data=result.get('product'),
				execution_time=execution_time
			)
			
			frappe.logger().info(f"Successfully synced item {item_doc.item_code} to Wix product {product_id}")
		else:
			# Error - update mapping
			error_message = result.get('error', 'Unknown error')
			mapping.update_sync_status("Error", error_message=error_message)
			
			# Create error log
			create_integration_log(
				operation_type=operation_type,
				status="Failed",
				item_code=item_doc.item_code,
				wix_product_id=mapping.wix_product_id,
				request_data=product_data,
				response_data=result.get('error_data'),
				error_details=error_message,
				execution_time=execution_time
			)
			
			frappe.log_error(f"Failed to sync item {item_doc.item_code} to Wix: {error_message}", "Wix Integration")
			
	except Exception as e:
		execution_time = time.time() - start_time
		error_message = str(e)
		
		# Update mapping on exception
		try:
			from wix_integration.wix_integration.doctype.wix_item_mapping.wix_item_mapping import get_or_create_mapping
			mapping = get_or_create_mapping(item_doc.item_code)
			if mapping:
				mapping.update_sync_status("Error", error_message=error_message)
		except:
			pass
		
		# Create error log
		create_integration_log(
			operation_type="Create Product",
			status="Failed",
			item_code=item_doc.item_code,
			error_details=error_message,
			execution_time=execution_time
		)
		
		frappe.log_error(f"Exception in sync_item_to_wix for {item_doc.item_code}: {error_message}", "Wix Integration")

def sync_item_to_wix_on_update(item_doc, method=None):
	"""Sync item to Wix when item is updated"""
	try:
		# Check if this is a relevant update (price, name, description, etc.)
		if should_sync_on_update(item_doc):
			# Enqueue sync to avoid blocking the update
			frappe.enqueue(
				sync_item_to_wix,
				item_doc=item_doc,
				queue='short',
				timeout=300
			)
	except Exception as e:
		frappe.log_error(f"Error in sync_item_to_wix_on_update: {str(e)}", "Wix Integration")

def should_sync_on_update(item_doc):
	"""Determine if item should be synced on update"""
	try:
		# Check if any relevant fields changed
		relevant_fields = [
			'item_name', 'description', 'standard_rate', 'image',
			'item_group', 'brand', 'weight_per_unit', 'is_stock_item'
		]
		
		for field in relevant_fields:
			if item_doc.has_value_changed(field):
				return True
		
		return False
	except:
		# If error checking changes, sync to be safe
		return True

def build_wix_product_data(item_doc, mapping, settings):
	"""Build Wix product data from ERPNext Item"""
	product_data = {
		'name': item_doc.item_name or item_doc.item_code,
		'productType': 'PHYSICAL' if item_doc.is_stock_item else 'DIGITAL',
		'visible': True,
		'visibleInPos': True
	}
	
	# Add description if sync enabled and available
	if settings.sync_item_description and item_doc.description:
		product_data['plainDescription'] = item_doc.description
	
	# Add brand if available
	if item_doc.brand:
		product_data['brand'] = {'name': item_doc.brand}
	
	# Add category if available
	if item_doc.item_group:
		# For now, we'll use item_group as category name
		# In production, you'd want to maintain a mapping of ERPNext item groups to Wix categories
		if settings.sync_categories:
			product_data['categories'] = [item_doc.item_group]
	
	# Build variants info with pricing
	variant_data = {
		'choices': [],  # No variants for basic implementation
		'physicalProperties': {}
	}
	
	# Add price if sync enabled
	if settings.sync_item_price and mapping.sync_price:
		standard_rate = flt(item_doc.standard_rate)
		if standard_rate > 0:
			variant_data['price'] = {
				'actualPrice': {
					'amount': str(standard_rate)
				}
			}
	
	# Add weight if available
	if item_doc.weight_per_unit:
		variant_data['physicalProperties']['weight'] = flt(item_doc.weight_per_unit)
	
	# Add SKU
	variant_data['sku'] = item_doc.item_code
	
	# Set physical properties for main product
	product_data['physicalProperties'] = {}
	if item_doc.weight_per_unit:
		product_data['physicalProperties']['weight'] = flt(item_doc.weight_per_unit)
	
	# Add variants info
	product_data['variantsInfo'] = {
		'variants': [variant_data]
	}
	
	# Add images if sync enabled and available
	if settings.sync_item_images and mapping.sync_images and item_doc.image:
		image_url = get_full_image_url(item_doc.image)
		if image_url:
			product_data['media'] = {
				'items': [{'url': image_url}]
			}
	
	return product_data

def get_full_image_url(image_path):
	"""Get full URL for item image"""
	try:
		if not image_path:
			return None
		
		# If already a full URL, return as is
		if image_path.startswith('http'):
			return image_path
		
		# Build full URL
		site_url = get_site_url()
		if image_path.startswith('/'):
			return f"{site_url}{image_path}"
		else:
			return f"{site_url}/{image_path}"
	except Exception as e:
		frappe.log_error(f"Error building image URL: {str(e)}", "Wix Integration")
		return None

@frappe.whitelist()
def manual_sync_item(item_code):
	"""Manually sync a specific item"""
	try:
		if not frappe.has_permission("Item", "read"):
			frappe.throw(_("Insufficient permissions to sync items"))
		
		item_doc = frappe.get_doc("Item", item_code)
		
		# Enqueue sync job
		frappe.enqueue(
			sync_item_to_wix,
			item_doc=item_doc,
			queue='long',
			timeout=300
		)
		
		return {'success': True, 'message': f'Sync initiated for item {item_code}'}
		
	except Exception as e:
		frappe.log_error(f"Error in manual_sync_item: {str(e)}", "Wix Integration")
		return {'success': False, 'error': str(e)}

@frappe.whitelist()
def get_sync_status(item_code):
	"""Get sync status for an item"""
	try:
		if not frappe.has_permission("Wix Item Mapping", "read"):
			frappe.throw(_("Insufficient permissions to view sync status"))
		
		mapping = frappe.db.get_value(
			"Wix Item Mapping", 
			item_code, 
			["sync_status", "last_sync", "wix_product_id", "sync_enabled"],
			as_dict=True
		)
		
		if not mapping:
			return {
				'status': 'Not Mapped',
				'sync_enabled': False,
				'last_sync': None,
				'wix_product_id': None
			}
		
		return {
			'status': mapping.sync_status,
			'sync_enabled': mapping.sync_enabled,
			'last_sync': mapping.last_sync,
			'wix_product_id': mapping.wix_product_id
		}
		
	except Exception as e:
		frappe.log_error(f"Error getting sync status: {str(e)}", "Wix Integration")
		return {'status': 'Error', 'error': str(e)}

@frappe.whitelist()
def bulk_sync_all_items():
	"""Sync all enabled items to Wix"""
	try:
		if not frappe.has_permission("Wix Item Mapping", "write"):
			frappe.throw(_("Insufficient permissions to sync items"))
		
		# Get all items with sync enabled
		mappings = frappe.get_all(
			"Wix Item Mapping",
			filters={'sync_enabled': 1},
			fields=['item_code']
		)
		
		if not mappings:
			return {'success': False, 'error': 'No items enabled for sync'}
		
		# Enqueue bulk sync job
		frappe.enqueue(
			'wix_integration.tasks.bulk_sync_items',
			item_codes=[m.item_code for m in mappings],
			queue='long',
			timeout=3600  # 1 hour timeout
		)
		
		return {
			'success': True, 
			'message': f'Bulk sync initiated for {len(mappings)} items'
		}
		
	except Exception as e:
		frappe.log_error(f"Error in bulk_sync_all_items: {str(e)}", "Wix Integration")
		return {'success': False, 'error': str(e)}

@frappe.whitelist()
def get_integration_dashboard_data():
	"""Get data for Wix integration dashboard"""
	try:
		if not frappe.has_permission("Wix Settings", "read"):
			frappe.throw(_("Insufficient permissions to view dashboard data"))
		
		# Get settings
		settings = frappe.get_single("Wix Settings")
		
		# Get mapping stats
		mapping_stats = frappe.db.sql("""
			SELECT 
				sync_status,
				COUNT(*) as count
			FROM `tabWix Item Mapping`
			GROUP BY sync_status
		""", as_dict=True)
		
		# Get recent sync activity
		recent_syncs = frappe.db.sql("""
			SELECT 
				operationType,
				status,
				COUNT(*) as count
			FROM `tabWix Integration Log`
			WHERE creation >= DATE_SUB(NOW(), INTERVAL 24 HOUR)
			GROUP BY operationType, status
		""", as_dict=True)
		
		# Get total items count
		total_items = frappe.db.count("Item")
		mapped_items = frappe.db.count("Wix Item Mapping")
		
		return {
			'settings': {
				'enabled': settings.enabled,
				'auto_sync_items': settings.auto_sync_items,
				'test_mode': settings.test_mode,
				'last_sync': settings.last_sync,
				'total_synced_items': settings.total_synced_items,
				'failed_syncs': settings.failed_syncs
			},
			'mapping_stats': mapping_stats,
			'recent_activity': recent_syncs,
			'summary': {
				'total_items': total_items,
				'mapped_items': mapped_items,
				'unmapped_items': total_items - mapped_items
			}
		}
		
	except Exception as e:
		frappe.log_error(f"Error getting dashboard data: {str(e)}", "Wix Integration")
		return {'error': str(e)}