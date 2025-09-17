# -*- coding: utf-8 -*-
"""Enhanced Product Synchronization Service

This module provides production-grade product synchronization between ERPNext and Wix,
including comprehensive validation, error handling, and logging.
"""

import frappe
import json
from datetime import datetime
from typing import Dict, Any, Optional, List
from frappe import _
from frappe.utils import get_fullname
from wix_integration.wix_integration.wix_connector import WixConnector

class WixProductSyncService:
	"""Enhanced service for synchronizing products between ERPNext and Wix"""
	
	def __init__(self):
		"""Initialize the sync service with connection and settings"""
		self.wix_connector = WixConnector()
		self.settings = self.wix_connector.settings
		self.validation_errors = []
	
	def sync_product_to_wix(self, item_doc, method=None):
		"""
		Synchronize a single product from ERPNext to Wix
		
		Args:
			item_doc: ERPNext Item document
			method: Frappe hook method (after_insert, on_update, etc.)
		"""
		if not self._should_sync_product(item_doc):
			return
		
		try:
			# Validate prerequisites
			if not self._validate_sync_prerequisites():
				return
			
			# Transform ERPNext item to Wix product format
			wix_product_data = self._transform_erpnext_to_wix(item_doc)
			
			# Validate the transformed data
			if not self._validate_wix_product_data(wix_product_data):
				self._log_validation_errors(item_doc.name)
				return
			
			# Check if product already exists in Wix
			existing_mapping = self._get_existing_mapping(item_doc.name)
			
			if existing_mapping:
				# Update existing product
				result = self._update_wix_product(existing_mapping.wix_product_id, wix_product_data, item_doc)
			else:
				# Create new product
				result = self._create_wix_product(wix_product_data, item_doc)
			
			if result.get('success'):
				self._handle_sync_success(item_doc, result, method)
			else:
				self._handle_sync_error(item_doc, result, method)
				
		except Exception as e:
			frappe.log_error(
				message=f"Unexpected error syncing product {item_doc.name}: {str(e)}",
				title="Wix Product Sync Error"
			)
			self._log_integration_event(item_doc.name, 'Error', f"Unexpected error: {str(e)}")
	
	def _should_sync_product(self, item_doc) -> bool:
		"""
		Determine if the product should be synced to Wix
		
		Args:
			item_doc: ERPNext Item document
			
		Returns:
			bool: True if product should be synced
		"""
		if not self.settings or not self.settings.enabled:
			return False
		
		if not self.settings.auto_sync_items:
			return False
		
		# Skip disabled items
		if item_doc.disabled:
			return False
		
		# Skip template items (only sync variants)
		if item_doc.has_variants:
			return False
		
		# Skip items that are not meant for sale
		if not item_doc.is_sales_item:
			return False
		
		return True
	
	def _validate_sync_prerequisites(self) -> bool:
		"""Validate that all prerequisites for syncing are met"""
		if not self.settings:
			frappe.log_error("Wix settings not found", "Wix Integration Error")
			return False
		
		if not self.settings.enabled:
			return False
		
		if not all([self.settings.site_id, self.settings.api_key, self.settings.account_id]):
			frappe.log_error("Missing Wix credentials", "Wix Integration Error")
			return False
		
		# Test connection if in test mode
		if self.settings.test_mode:
			connection_test = self.wix_connector.test_connection()
			if not connection_test.get('success'):
				frappe.log_error(
					f"Wix connection test failed: {connection_test.get('error')}",
					"Wix Integration Error"
				)
				return False
		
		return True
	
	def _transform_erpnext_to_wix(self, item_doc) -> Dict[str, Any]:
		"""
		Transform ERPNext Item to Wix product format
		
		Args:
			item_doc: ERPNext Item document
			
		Returns:
			Dict containing Wix product data
		"""
		# Base product structure
		wix_product = {
			"name": item_doc.item_name or item_doc.name,
			"productType": "PHYSICAL",  # Default to physical, can be enhanced later
			"visible": not item_doc.disabled,
			"physicalProperties": {},
			"variantsInfo": {
				"variants": []
			}
		}
		
		# Add description if configured and available
		if self.settings.sync_item_description and item_doc.description:
			# For POC, use plainDescription. In production, convert to rich content
			wix_product["plainDescription"] = item_doc.description
		
		# Add brand if available
		if item_doc.brand:
			wix_product["brand"] = {
				"name": item_doc.brand
			}
		
		# Create single variant with pricing
		variant = {
			"price": {
				"actualPrice": {
					"amount": str(item_doc.standard_rate or 0)
				}
			},
			"physicalProperties": {},
			"choices": []
		}
		
		# Add SKU if available
		if item_doc.item_code:
			variant["sku"] = item_doc.item_code
		
		# Add weight if available
		if item_doc.weight_per_unit:
			variant["physicalProperties"]["weight"] = float(item_doc.weight_per_unit)
		
		# Add barcode if available
		if item_doc.barcodes and len(item_doc.barcodes) > 0:
			variant["barcode"] = item_doc.barcodes[0].barcode
		
		wix_product["variantsInfo"]["variants"].append(variant)
		
		# Add media if configured and available
		if self.settings.sync_item_images and item_doc.image:
			wix_product["media"] = {
				"items": [
					{
						"url": self._get_full_image_url(item_doc.image)
					}
				]
			}
		
		return wix_product
	
	def _get_full_image_url(self, image_path: str) -> str:
		"""Get full URL for an image path"""
		if image_path.startswith('http'):
			return image_path
		
		from frappe.utils import get_site_url
		return get_site_url() + image_path
	
	def _validate_wix_product_data(self, product_data: Dict[str, Any]) -> bool:
		"""
		Validate Wix product data before sending to API
		
		Args:
			product_data: Wix product data dictionary
			
		Returns:
			bool: True if data is valid
		"""
		self.validation_errors = []
		
		# Required fields validation
		if not product_data.get('name'):
			self.validation_errors.append("Product name is required")
		
		if not product_data.get('productType'):
			self.validation_errors.append("Product type is required")
		
		if not product_data.get('variantsInfo', {}).get('variants'):
			self.validation_errors.append("At least one variant is required")
		
		# Validate variants
		for i, variant in enumerate(product_data.get('variantsInfo', {}).get('variants', [])):
			if not variant.get('price', {}).get('actualPrice', {}).get('amount'):
				self.validation_errors.append(f"Variant {i+1}: Price is required")
			
			# Validate price is numeric
			try:
				price = variant.get('price', {}).get('actualPrice', {}).get('amount')
				if price:
					float(price)
			except (ValueError, TypeError):
				self.validation_errors.append(f"Variant {i+1}: Price must be numeric")
		
		# Validate product name length (Wix limit)
		if len(product_data.get('name', '')) > 80:
			self.validation_errors.append("Product name exceeds 80 character limit")
		
		return len(self.validation_errors) == 0
	
	def _log_validation_errors(self, item_code: str):
		"""Log validation errors"""
		error_message = "; ".join(self.validation_errors)
		frappe.log_error(
			f"Wix product validation failed for {item_code}: {error_message}",
			"Wix Product Validation Error"
		)
		self._log_integration_event(item_code, 'Validation Error', error_message)
	
	def _get_existing_mapping(self, item_code: str):
		"""Get existing Wix product mapping for an ERPNext item"""
		try:
			return frappe.get_doc("Wix Item Mapping", {"erpnext_item_code": item_code})
		except frappe.DoesNotExistError:
			return None
	
	def _create_wix_product(self, product_data: Dict[str, Any], item_doc) -> Dict[str, Any]:
		"""Create a new product in Wix"""
		self._log_integration_event(item_doc.name, 'Sync Started', 'Creating new product in Wix')
		
		result = self.wix_connector.create_product(product_data)
		
		if result.get('success'):
			# Create mapping record
			self._create_item_mapping(
				item_doc.name,
				result.get('product_id'),
				result.get('product', {})
			)
		
		return result
	
	def _update_wix_product(self, wix_product_id: str, product_data: Dict[str, Any], item_doc) -> Dict[str, Any]:
		"""Update an existing product in Wix"""
		self._log_integration_event(item_doc.name, 'Sync Started', f'Updating existing product {wix_product_id} in Wix')
		
		result = self.wix_connector.update_product(wix_product_id, product_data)
		
		if result.get('success'):
			# Update mapping record
			self._update_item_mapping(item_doc.name, result.get('product', {}))
		
		return result
	
	def _create_item_mapping(self, item_code: str, wix_product_id: str, wix_product_data: Dict[str, Any]):
		"""Create a new Wix item mapping record"""
		try:
			mapping = frappe.get_doc({
				'doctype': 'Wix Item Mapping',
				'erpnext_item_code': item_code,
				'wix_product_id': wix_product_id,
				'wix_product_name': wix_product_data.get('name'),
				'sync_status': 'Synced',
				'last_sync': datetime.now(),
				'wix_product_data': json.dumps(wix_product_data, indent=2)
			})
			mapping.insert(ignore_permissions=True)
			frappe.db.commit()
		except Exception as e:
			frappe.log_error(f"Error creating item mapping: {str(e)}", "Wix Integration Error")
	
	def _update_item_mapping(self, item_code: str, wix_product_data: Dict[str, Any]):
		"""Update existing Wix item mapping record"""
		try:
			mapping = frappe.get_doc("Wix Item Mapping", {"erpnext_item_code": item_code})
			mapping.wix_product_name = wix_product_data.get('name')
			mapping.sync_status = 'Synced'
			mapping.last_sync = datetime.now()
			mapping.wix_product_data = json.dumps(wix_product_data, indent=2)
			mapping.save(ignore_permissions=True)
			frappe.db.commit()
		except Exception as e:
			frappe.log_error(f"Error updating item mapping: {str(e)}", "Wix Integration Error")
	
	def _handle_sync_success(self, item_doc, result: Dict[str, Any], method: str):
		"""Handle successful synchronization"""
		success_message = f"Product {item_doc.name} successfully synced to Wix"
		if method == 'after_insert':
			success_message += " (created)"
		elif method == 'on_update':
			success_message += " (updated)"
		
		self._log_integration_event(item_doc.name, 'Success', success_message)
		
		# Update sync statistics in settings
		self._update_sync_statistics(success=True)
		
		frappe.msgprint(
			_(f"Product '{item_doc.item_name}' synchronized successfully with Wix"),
			title=_("Sync Successful"),
			indicator="green"
		)
	
	def _handle_sync_error(self, item_doc, result: Dict[str, Any], method: str):
		"""Handle synchronization errors"""
		error_message = result.get('error', 'Unknown error')
		error_data = result.get('error_data', {})
		
		detailed_error = f"Failed to sync product {item_doc.name} to Wix: {error_message}"
		if error_data:
			detailed_error += f" | Error details: {json.dumps(error_data)}"
		
		frappe.log_error(detailed_error, "Wix Product Sync Error")
		self._log_integration_event(item_doc.name, 'Error', error_message)
		
		# Update sync statistics in settings
		self._update_sync_statistics(success=False)
		
		# Update mapping status if exists
		try:
			mapping = self._get_existing_mapping(item_doc.name)
			if mapping:
				mapping.sync_status = 'Error'
				mapping.sync_error = error_message
				mapping.save(ignore_permissions=True)
				frappe.db.commit()
		except Exception as e:
			frappe.log_error(f"Error updating mapping status: {str(e)}", "Wix Integration Error")
	
	def _log_integration_event(self, item_code: str, status: str, message: str):
		"""Log integration event for tracking and debugging"""
		try:
			log = frappe.get_doc({
				'doctype': 'Wix Integration Log',
				'reference_doctype': 'Item',
				'reference_name': item_code,
				'operation_type': 'Product Sync',
				'status': status,
				'message': message,
				'timestamp': datetime.now(),
				'user': get_fullname()
			})
			log.insert(ignore_permissions=True)
			frappe.db.commit()
		except Exception as e:
			# Don't fail the main process if logging fails
			frappe.log_error(f"Error logging integration event: {str(e)}", "Wix Integration Error")
	
	def _update_sync_statistics(self, success: bool = True):
		"""Update synchronization statistics in Wix Settings"""
		try:
			if not self.settings:
				return
			
			settings_doc = frappe.get_single("Wix Settings")
			settings_doc.last_sync = datetime.now()
			
			if success:
				settings_doc.total_synced_items = (settings_doc.total_synced_items or 0) + 1
			else:
				settings_doc.failed_syncs = (settings_doc.failed_syncs or 0) + 1
			
			settings_doc.save(ignore_permissions=True)
			frappe.db.commit()
		except Exception as e:
			frappe.log_error(f"Error updating sync statistics: {str(e)}", "Wix Integration Error")

# API Functions for Frappe hooks
def sync_product_to_wix(doc, method=None):
	"""Hook function for Item document events"""
	try:
		sync_service = WixProductSyncService()
		sync_service.sync_product_to_wix(doc, method)
	except Exception as e:
		frappe.log_error(f"Error in sync_product_to_wix hook: {str(e)}", "Wix Integration Error")

def delete_product_from_wix(doc, method=None):
	"""Hook function for Item deletion - placeholder for future implementation"""
	# For POC, we'll just log the deletion
	# In production, implement actual Wix product deletion
	try:
		mapping = frappe.get_doc("Wix Item Mapping", {"erpnext_item_code": doc.name})
		mapping.sync_status = 'Deleted in ERPNext'
		mapping.save(ignore_permissions=True)
		frappe.db.commit()
		
		frappe.log_error(
			f"Item {doc.name} deleted from ERPNext. Manual cleanup required in Wix.",
			"Wix Integration - Item Deleted"
		)
	except frappe.DoesNotExistError:
		pass  # No mapping exists
	except Exception as e:
		frappe.log_error(f"Error handling item deletion: {str(e)}", "Wix Integration Error")
