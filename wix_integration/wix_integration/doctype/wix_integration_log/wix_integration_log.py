# -*- coding: utf-8 -*-
# Copyright (c) 2025, Your Company and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document

class WixIntegrationLog(Document):
	"""Document controller for Wix Integration Log"""
	
	def validate(self):
		"""Validate log entry"""
		if not self.timestamp:
			self.timestamp = frappe.utils.now()
	
	def on_submit(self):
		"""Called when log is submitted"""
		pass
	
	def on_cancel(self):
		"""Called when log is cancelled"""
		pass
