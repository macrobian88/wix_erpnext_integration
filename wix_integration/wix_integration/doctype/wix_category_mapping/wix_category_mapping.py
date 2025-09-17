# -*- coding: utf-8 -*-
# Copyright (c) 2025, Your Company and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document

class WixCategoryMapping(Document):
	"""Document controller for Wix Category Mapping"""
	
	def validate(self):
		"""Validate category mapping"""
		pass
	
	def before_save(self):
		"""Called before saving the document"""
		# Ensure unique mapping per item group
		existing = frappe.db.get_value(
			"Wix Category Mapping",
			{
				"erpnext_item_group": self.erpnext_item_group,
				"name": ["!=", self.name]
			}
		)
		
		if existing:
			frappe.throw(f"Mapping already exists for item group {self.erpnext_item_group}")
