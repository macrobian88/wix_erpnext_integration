# -*- coding: utf-8 -*-
"""Production Installation and Setup Module

This module handles the installation, configuration, and validation
of the Wix ERPNext integration in production environments.
"""

import frappe
import json
from datetime import datetime
from frappe import _
from frappe.utils import get_site_url, get_fullname

class WixIntegrationInstaller:
	"""Production-grade installer for Wix ERPNext integration"""
	
	def __init__(self):
		self.installation_log = []
		self.errors = []
		self.warnings = []
	
	def install(self):
		"""Main installation method"""
		try:
			self.log_step("Starting Wix ERPNext Integration installation...")
			
			# Step 1: Validate prerequisites
			self.validate_prerequisites()
			
			# Step 2: Create default settings
			self.create_default_settings()
			
			# Step 3: Setup custom fields
			self.setup_custom_fields()
			
			# Step 4: Create default integration log entries
			self.setup_integration_logging()
			
			# Step 5: Setup user roles and permissions
			self.setup_user_roles()
			
			# Step 6: Create sample documentation
			self.create_documentation()
			
			# Step 7: Validate installation
			self.validate_installation()
			
			self.log_step("Installation completed successfully!")
			return self.generate_installation_report()
			
		except Exception as e:
			self.log_error(f"Installation failed: {str(e)}")
			raise
	
	def validate_prerequisites(self):
		"""Validate system prerequisites"""
		self.log_step("Validating prerequisites...")
		
		# Check Frappe/ERPNext version
		frappe_version = frappe.__version__
		if not self.is_version_compatible(frappe_version, "15.0.0"):
			self.log_warning(f"Frappe version {frappe_version} may not be fully compatible. Recommended: 15.0.0+")
		
		# Check required modules
		required_modules = ['erpnext']
		for module in required_modules:
			try:
				__import__(module)
			except ImportError:
				self.log_error(f"Required module '{module}' is not available")
		
		# Check system requirements
		self.validate_system_requirements()
		
		self.log_step("Prerequisites validation completed")
	
	def is_version_compatible(self, current_version, required_version):
		"""Check if current version meets requirements"""
		try:
			current_parts = [int(x) for x in current_version.split('.')]
			required_parts = [int(x) for x in required_version.split('.')]
			
			for i in range(max(len(current_parts), len(required_parts))):
				current_part = current_parts[i] if i < len(current_parts) else 0
				required_part = required_parts[i] if i < len(required_parts) else 0
				
				if current_part > required_part:
					return True
				elif current_part < required_part:
					return False
			
			return True
		except Exception:
			return False
	
	def validate_system_requirements(self):
		"""Validate system requirements"""
		# Check database connection
		try:
			frappe.db.sql("SELECT 1")
		except Exception as e:
			self.log_error(f"Database connection issue: {str(e)}")
		
		# Check write permissions
		try:
			frappe.get_doc({
				'doctype': 'ToDo',
				'description': 'Wix Integration Test - Safe to delete'
			}).insert(ignore_permissions=True)
			frappe.db.rollback()
		except Exception as e:
			self.log_error(f"Database write permission issue: {str(e)}")
	
	def create_default_settings(self):
		"""Create default Wix settings"""
		self.log_step("Creating default settings...")
		
		try:
			# Check if settings already exist
			existing_settings = frappe.db.exists('Wix Settings', 'Wix Settings')
			if existing_settings:
				self.log_warning("Wix Settings already exist. Skipping default creation.")
				return
			
			# Create default settings
			settings = frappe.get_doc({
				'doctype': 'Wix Settings',
				'name': 'Wix Settings',
				'enabled': 0,
				'test_mode': 1,
				'auto_sync_items': 1,
				'sync_item_name': 1,
				'sync_item_description': 1,
				'sync_item_price': 1,
				'sync_item_images': 1,
				'sync_inventory': 1,
				'sync_categories': 1,
				'retry_attempts': 3,
				'timeout_seconds': 30,
				'log_level': 'INFO'
			})
			
			settings.insert(ignore_permissions=True)
			frappe.db.commit()
			
			self.log_step("Default settings created successfully")
			
		except Exception as e:
			self.log_error(f"Error creating default settings: {str(e)}")
	
	def setup_custom_fields(self):
		"""Setup custom fields for integration"""
		self.log_step("Setting up custom fields...")
		
		custom_fields = [
			# Item fields
			{
				'doctype': 'Custom Field',
				'dt': 'Item',
				'fieldname': 'wix_integration_section',
				'label': 'Wix Integration',
				'fieldtype': 'Section Break',
				'collapsible': 1,
				'description': 'Wix integration related fields'
			},
			{
				'doctype': 'Custom Field',
				'dt': 'Item',
				'fieldname': 'wix_product_id',
				'label': 'Wix Product ID',
				'fieldtype': 'Data',
				'read_only': 1,
				'no_copy': 1,
				'description': 'Wix Product ID for synced items'
			},
			{
				'doctype': 'Custom Field',
				'dt': 'Item',
				'fieldname': 'wix_sync_status',
				'label': 'Wix Sync Status',
				'fieldtype': 'Select',
				'options': 'Not Synced\nSynced\nError\nPending',
				'default': 'Not Synced',
				'read_only': 1,
				'no_copy': 1
			},
			{
				'doctype': 'Custom Field',
				'dt': 'Item',
				'fieldname': 'wix_column_break',
				'fieldtype': 'Column Break'
			},
			{
				'doctype': 'Custom Field',
				'dt': 'Item',
				'fieldname': 'wix_last_sync',
				'label': 'Wix Last Sync',
				'fieldtype': 'Datetime',
				'read_only': 1,
				'no_copy': 1
			},
			{
				'doctype': 'Custom Field',
				'dt': 'Item',
				'fieldname': 'wix_sync_error',
				'label': 'Wix Sync Error',
				'fieldtype': 'Small Text',
				'read_only': 1,
				'no_copy': 1
			},
			
			# Sales Order fields
			{
				'doctype': 'Custom Field',
				'dt': 'Sales Order',
				'fieldname': 'wix_integration_section',
				'label': 'Wix Integration',
				'fieldtype': 'Section Break',
				'collapsible': 1
			},
			{
				'doctype': 'Custom Field',
				'dt': 'Sales Order',
				'fieldname': 'wix_order_id',
				'label': 'Wix Order ID',
				'fieldtype': 'Data',
				'read_only': 1,
				'no_copy': 1,
				'description': 'Original Wix Order ID'
			},
			{
				'doctype': 'Custom Field',
				'dt': 'Sales Order',
				'fieldname': 'wix_order_status',
				'label': 'Wix Order Status',
				'fieldtype': 'Data',
				'read_only': 1,
				'no_copy': 1
			},
			
			# Customer fields
			{
				'doctype': 'Custom Field',
				'dt': 'Customer',
				'fieldname': 'wix_customer_id',
				'label': 'Wix Customer ID',
				'fieldtype': 'Data',
				'read_only': 1,
				'no_copy': 1
			}
		]
		
		created_count = 0
		for field_config in custom_fields:
			try:
				# Check if field already exists
				existing = frappe.db.exists('Custom Field', {
					'dt': field_config['dt'],
					'fieldname': field_config['fieldname']
				})
				
				if not existing:
					field_doc = frappe.get_doc(field_config)
					field_doc.insert(ignore_permissions=True)
					created_count += 1
				
			except Exception as e:
				self.log_warning(f"Error creating custom field {field_config['fieldname']}: {str(e)}")
		
		frappe.db.commit()
		self.log_step(f"Custom fields setup completed. Created {created_count} new fields.")
	
	def setup_integration_logging(self):
		"""Setup integration logging structure"""
		self.log_step("Setting up integration logging...")
		
		# Create a welcome log entry
		try:
			welcome_log = frappe.get_doc({
				'doctype': 'Wix Integration Log',
				'reference_doctype': 'Wix Settings',
				'reference_name': 'Wix Settings',
				'operation_type': 'Installation',
				'status': 'Success',
				'message': 'Wix ERPNext Integration installed successfully',
				'timestamp': datetime.now(),
				'user': get_fullname()
			})
			welcome_log.insert(ignore_permissions=True)
			frappe.db.commit()
			
		except Exception as e:
			self.log_warning(f"Could not create welcome log entry: {str(e)}")
	
	def setup_user_roles(self):
		"""Setup user roles and permissions"""
		self.log_step("Setting up user roles...")
		
		try:
			# Create Wix Manager role if it doesn't exist
			if not frappe.db.exists('Role', 'Wix Manager'):
				role_doc = frappe.get_doc({
					'doctype': 'Role',
					'role_name': 'Wix Manager',
					'desk_access': 1,
					'is_custom': 1
				})
				role_doc.insert(ignore_permissions=True)
				frappe.db.commit()
				self.log_step("Created Wix Manager role")
			
			# Setup role permissions for doctypes
			doctypes_permissions = [
				'Wix Settings',
				'Wix Integration Log',
				'Wix Item Mapping'
			]
			
			for doctype in doctypes_permissions:
				self.ensure_role_permissions('Wix Manager', doctype)
			
		except Exception as e:
			self.log_warning(f"Error setting up user roles: {str(e)}")
	
	def ensure_role_permissions(self, role, doctype):
		"""Ensure role has necessary permissions for doctype"""
		try:
			perms = frappe.get_doc('DocPerm', {
				'parent': doctype,
				'role': role
			})
		except frappe.DoesNotExistError:
			# Create permissions
			perm_doc = frappe.get_doc({
				'doctype': 'DocPerm',
				'parent': doctype,
				'parenttype': 'DocType',
				'parentfield': 'permissions',
				'role': role,
				'read': 1,
				'write': 1,
				'create': 1,
				'delete': 1,
				'submit': 0,
				'cancel': 0,
				'amend': 0
			})
			perm_doc.insert(ignore_permissions=True)
	
	def create_documentation(self):
		"""Create sample documentation and help content"""
		self.log_step("Creating documentation...")
		
		# Documentation content is already provided in README and other files
		# This is a placeholder for any additional setup documentation
		pass
	
	def validate_installation(self):
		"""Validate that installation was successful"""
		self.log_step("Validating installation...")
		
		# Check if core doctypes exist
		required_doctypes = [
			'Wix Settings',
			'Wix Integration Log',
			'Wix Item Mapping'
		]
		
		for doctype in required_doctypes:
			if not frappe.db.exists('DocType', doctype):
				self.log_error(f"Required DocType '{doctype}' is missing")
		
		# Check if custom fields were created
		test_field = frappe.db.exists('Custom Field', {
			'dt': 'Item',
			'fieldname': 'wix_product_id'
		})
		
		if not test_field:
			self.log_warning("Some custom fields may not have been created properly")
		
		self.log_step("Installation validation completed")
	
	def log_step(self, message):
		"""Log installation step"""
		self.installation_log.append({
			'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
			'type': 'INFO',
			'message': message
		})
		print(f"[INFO] {message}")
	
	def log_warning(self, message):
		"""Log installation warning"""
		self.warnings.append(message)
		self.installation_log.append({
			'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
			'type': 'WARNING',
			'message': message
		})
		print(f"[WARNING] {message}")
	
	def log_error(self, message):
		"""Log installation error"""
		self.errors.append(message)
		self.installation_log.append({
			'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
			'type': 'ERROR',
			'message': message
		})
		print(f"[ERROR] {message}")
	
	def generate_installation_report(self):
		"""Generate installation report"""
		report = {
			'status': 'success' if not self.errors else 'failed',
			'errors': self.errors,
			'warnings': self.warnings,
			'installation_log': self.installation_log,
			'next_steps': self.get_next_steps()
		}
		
		# Save report to file if possible
		try:
			report_content = json.dumps(report, indent=2, default=str)
			frappe.log_error(report_content, "Wix Integration Installation Report")
		except Exception:
			pass
		
		return report
	
	def get_next_steps(self):
		"""Get next steps after installation"""
		return [
			"1. Go to Wix Settings and configure your Wix API credentials",
			"2. Enable the integration and test the connection",
			"3. Configure sync settings according to your requirements",
			"4. Test product synchronization with a sample item",
			"5. Monitor the Wix Integration Log for any issues",
			"6. Assign Wix Manager role to users who need access",
			"7. Review the README.md file for detailed usage instructions"
		]

# Installation functions that Frappe expects
def after_install():
	"""After installation hook function"""
	try:
		installer = WixIntegrationInstaller()
		report = installer.install()
		
		if report.get('errors'):
			frappe.log_error(
				f"Installation completed with errors: {'; '.join(report['errors'])}", 
				"Wix Integration Installation"
			)
		else:
			frappe.msgprint(
				_("Wix Integration installed successfully! Please go to Wix Settings to configure your API credentials."),
				title=_("Installation Complete"),
				indicator="green"
			)
			
	except Exception as e:
		frappe.log_error(f"Installation error: {str(e)}", "Wix Integration Installation")
		frappe.throw(_("Installation failed: {0}").format(str(e)))

def install_wix_integration():
	"""Alternative installation function"""
	installer = WixIntegrationInstaller()
	return installer.install()

# Command line installation
if __name__ == "__main__":
	install_wix_integration()
