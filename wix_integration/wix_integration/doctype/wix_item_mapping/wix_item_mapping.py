# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.model.document import Document
from datetime import datetime

class WixItemMapping(Document):
	def validate(self):
		"""Validation logic for Wix Item Mapping"""
		# Ensure item exists
		if not frappe.db.exists("Item", self.item_code):
			frappe.throw(_("Item {0} does not exist").format(self.item_code))
		
		# Set sync status based on sync_enabled
		if not self.sync_enabled:
			self.sync_status = "Disabled"
		elif not self.sync_status or self.sync_status == "Disabled":
			self.sync_status = "Not Synced"
	
	def before_insert(self):
		"""Actions before inserting new mapping"""
		# Fetch item name if not set
		if not self.item_name and self.item_code:
			item_name = frappe.db.get_value("Item", self.item_code, "item_name")
			if item_name:
				self.item_name = item_name
		
		# Set default sync status
		if not self.sync_status:
			self.sync_status = "Not Synced" if self.sync_enabled else "Disabled"
	
	def on_update(self):
		"""Actions after updating mapping"""
		# If sync was just enabled, trigger sync
		if self.has_value_changed("sync_enabled") and self.sync_enabled:
			self.trigger_sync()
	
	def trigger_sync(self):
		"""Trigger sync for this item"""
		from wix_integration.wix_integration.doctype.wix_integration.wix_integration import sync_item_to_wix
		
		try:
			# Update status to pending
			self.sync_status = "Pending"
			self.save(ignore_permissions=True)
			
			# Enqueue sync job
			frappe.enqueue(
				sync_item_to_wix,
				item_doc=None,
				item_code=self.item_code,
				queue='long',
				timeout=300
			)
		except Exception as e:
			frappe.log_error(f"Error triggering sync for {self.item_code}: {str(e)}", "Wix Item Mapping")
	
	def update_sync_status(self, status, wix_product_id=None, error_message=None):
		"""Update sync status and related fields"""
		try:
			self.sync_status = status
			self.last_sync = datetime.now()
			self.total_syncs = (self.total_syncs or 0) + 1
			
			if status == "Synced":
				self.successful_syncs = (self.successful_syncs or 0) + 1
				if wix_product_id:
					self.wix_product_id = wix_product_id
				# Clear previous errors
				self.sync_errors = None
				self.last_error_date = None
			elif status == "Error":
				self.failed_syncs = (self.failed_syncs or 0) + 1
				if error_message:
					error_entry = f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}: {error_message}\n"
					self.sync_errors = (self.sync_errors or "") + error_entry
					self.last_error_date = datetime.now()
					# Trim errors to last 1000 characters
					if len(self.sync_errors) > 1000:
						self.sync_errors = self.sync_errors[-1000:]
			
			self.save(ignore_permissions=True)
		except Exception as e:
			frappe.log_error(f"Error updating sync status for {self.item_code}: {str(e)}", "Wix Item Mapping")

@frappe.whitelist()
def get_or_create_mapping(item_code):
	"""Get existing mapping or create new one"""
	try:
		# Check if mapping exists
		mapping = frappe.db.get_value("Wix Item Mapping", item_code, "name")
		if mapping:
			return frappe.get_doc("Wix Item Mapping", mapping)
		
		# Create new mapping
		item_name = frappe.db.get_value("Item", item_code, "item_name")
		if not item_name:
			frappe.throw(_("Item {0} does not exist").format(item_code))
		
		mapping_doc = frappe.get_doc({
			'doctype': 'Wix Item Mapping',
			'item_code': item_code,
			'item_name': item_name,
			'sync_enabled': 1,
			'sync_status': 'Not Synced',
			'sync_price': 1,
			'sync_inventory': 1,
			'sync_images': 1
		})
		mapping_doc.insert(ignore_permissions=True)
		return mapping_doc
		
	except Exception as e:
		frappe.log_error(f"Error getting/creating mapping for {item_code}: {str(e)}", "Wix Item Mapping")
		return None

@frappe.whitelist()
def bulk_enable_sync(item_codes):
	"""Enable sync for multiple items"""
	if not frappe.has_permission("Wix Item Mapping", "write"):
		frappe.throw(_("Insufficient permissions to modify Wix Item Mappings"))
	
	if isinstance(item_codes, str):
		import json
		item_codes = json.loads(item_codes)
	
	enabled_count = 0
	errors = []
	
	for item_code in item_codes:
		try:
			mapping = get_or_create_mapping(item_code)
			if mapping:
				mapping.sync_enabled = 1
				mapping.save(ignore_permissions=True)
				enabled_count += 1
		except Exception as e:
			errors.append(f"{item_code}: {str(e)}")
	
	return {
		'success': len(errors) == 0,
		'enabled_count': enabled_count,
		'total_count': len(item_codes),
		'errors': errors
	}

@frappe.whitelist()
def bulk_sync_items(item_codes):
	"""Trigger sync for multiple items"""
	if not frappe.has_permission("Wix Item Mapping", "read"):
		frappe.throw(_("Insufficient permissions to sync items"))
	
	if isinstance(item_codes, str):
		import json
		item_codes = json.loads(item_codes)
	
	queued_count = 0
	errors = []
	
	for item_code in item_codes:
		try:
			mapping = get_or_create_mapping(item_code)
			if mapping and mapping.sync_enabled:
				mapping.trigger_sync()
				queued_count += 1
			elif mapping:
				errors.append(f"{item_code}: Sync is disabled")
		except Exception as e:
			errors.append(f"{item_code}: {str(e)}")
	
	return {
		'success': len(errors) == 0,
		'queued_count': queued_count,
		'total_count': len(item_codes),
		'errors': errors
	}

@frappe.whitelist()
def get_sync_statistics():
	"""Get comprehensive sync statistics"""
	if not frappe.has_permission("Wix Item Mapping", "read"):
		frappe.throw(_("Insufficient permissions to view sync statistics"))
	
	stats = frappe.db.sql("""
		SELECT 
			sync_status,
			COUNT(*) as count,
			SUM(total_syncs) as total_syncs,
			SUM(successful_syncs) as successful_syncs,
			SUM(failed_syncs) as failed_syncs
		FROM `tabWix Item Mapping`
		GROUP BY sync_status
	""", as_dict=True)
	
	# Get items with recent errors
	recent_errors = frappe.db.sql("""
		SELECT item_code, item_name, sync_errors, last_error_date
		FROM `tabWix Item Mapping`
		WHERE sync_status = 'Error' 
			AND last_error_date >= DATE_SUB(NOW(), INTERVAL 24 HOUR)
		ORDER BY last_error_date DESC
		LIMIT 10
	""", as_dict=True)
	
	return {
		'status_breakdown': stats,
		'recent_errors': recent_errors
	}