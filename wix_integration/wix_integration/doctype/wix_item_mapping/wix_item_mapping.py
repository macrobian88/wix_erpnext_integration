# -*- coding: utf-8 -*-
# Copyright (c) 2025, Your Company and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document

class WixItemMapping(Document):
	"""Document controller for Wix Item Mapping"""
	
	def validate(self):
		"""Validate mapping entry"""
		if not self.created_at:
			self.created_at = frappe.utils.now()
		
		self.updated_at = frappe.utils.now()
	
	def before_save(self):
		"""Called before saving the document"""
		# Ensure unique mapping per item
		existing = frappe.db.get_value(
			"Wix Item Mapping",
			{
				"erpnext_item": self.erpnext_item,
				"name": ["!=", self.name]
			}
		)
		
		if existing:
			frappe.throw(f"Mapping already exists for item {self.erpnext_item}")
	
	@frappe.whitelist()
	def sync_to_wix(self):
		"""Manually sync this item to Wix"""
		try:
			from wix_integration.wix_integration.api.product_sync import sync_product_to_wix
			
			item_doc = frappe.get_doc("Item", self.erpnext_item)
			result = sync_product_to_wix(item_doc, "manual")
			
			if result.get('success'):
				frappe.msgprint(f"Successfully synced {self.erpnext_item} to Wix")
				return {"status": "success", "message": "Item synced successfully"}
			else:
				frappe.throw(f"Sync failed: {result.get('error')}")
				
		except Exception as e:
			frappe.throw(f"Error during sync: {str(e)}")
