# -*- coding: utf-8 -*-
"""Maintenance Tasks for Wix Integration

This module provides scheduled maintenance tasks for the Wix integration
including cleanup, health checks, and performance optimization.
"""

import frappe
from datetime import datetime, timedelta
from frappe.utils import add_days, now_datetime

def cleanup_old_logs():
	"""Clean up old integration logs to maintain performance"""
	try:
		# Get settings
		settings = frappe.get_single('Wix Settings')
		if not settings.enabled:
			return
		
		# Delete logs older than 30 days
		cutoff_date = add_days(now_datetime(), -30)
		
		old_logs = frappe.get_all(
			"Wix Integration Log",
			filters=[
				["timestamp", "<", cutoff_date]
			],
			limit=1000
		)
		
		for log in old_logs:
			try:
				frappe.delete_doc("Wix Integration Log", log.name, ignore_permissions=True)
			except:
				continue
		
		if old_logs:
			frappe.db.commit()
			frappe.logger().info(f"Cleaned up {len(old_logs)} old Wix integration logs")
		
	except Exception as e:
		frappe.log_error(f"Error cleaning up old logs: {str(e)}", "Wix Maintenance Error")

def health_check():
	"""Perform basic health check of the Wix integration"""
	try:
		settings = frappe.get_single('Wix Settings')
		if not settings.enabled:
			frappe.logger().info("Wix integration is disabled - skipping health check")
			return
		
		# Test Wix API connection
		from wix_integration.wix_integration.wix_connector import WixConnector
		
		connector = WixConnector()
		result = connector.test_connection()
		
		if result.get('success'):
			frappe.logger().info("Wix integration health check passed")
			
			# Update last successful health check
			settings.last_sync = now_datetime()
			settings.save(ignore_permissions=True)
			frappe.db.commit()
			
		else:
			error_msg = f"Wix integration health check failed: {result.get('error')}"
			frappe.log_error(error_msg, "Wix Health Check Failed")
			
			# Update error information in settings
			current_errors = settings.sync_errors or ""
			new_error = f"{now_datetime()}: Health check failed - {result.get('error')}\n"
			settings.sync_errors = (new_error + current_errors)[:2000]  # Limit to 2000 chars
			settings.save(ignore_permissions=True)
			frappe.db.commit()
		
	except Exception as e:
		error_msg = f"Error during health check: {str(e)}"
		frappe.log_error(error_msg, "Wix Health Check Error")

def comprehensive_health_check():
	"""Perform comprehensive weekly health check"""
	try:
		settings = frappe.get_single('Wix Settings')
		if not settings.enabled:
			return
		
		frappe.logger().info("Starting comprehensive Wix integration health check")
		
		# Basic health check
		health_check()
		
		# Check for stalled syncs
		check_stalled_syncs()
		
		# Validate settings configuration
		validate_settings_configuration()
		
		# Check recent error rates
		check_error_rates()
		
		frappe.logger().info("Completed comprehensive Wix integration health check")
		
	except Exception as e:
		frappe.log_error(f"Error during comprehensive health check: {str(e)}", "Wix Comprehensive Health Check Error")

def check_stalled_syncs():
	"""Check for items that may have stalled during sync"""
	try:
		# Find items with sync status 'Pending' or 'Error' for more than 1 hour
		cutoff_time = add_days(now_datetime(), hours=-1)
		
		stalled_items = frappe.get_all(
			"Item",
			filters=[
				["wix_sync_status", "in", ["Pending", "Error"]],
				["wix_last_sync", "<", cutoff_time]
			],
			fields=["name", "item_name", "wix_sync_status", "wix_last_sync"],
			limit=50
		)
		
		if stalled_items:
			frappe.logger().warning(f"Found {len(stalled_items)} stalled sync items")
			
			# Log details about stalled items
			for item in stalled_items[:10]:  # Log first 10
				frappe.logger().warning(
					f"Stalled sync: {item.name} ({item.item_name}) - "
					f"Status: {item.wix_sync_status}, Last sync: {item.wix_last_sync}"
				)
		
	except Exception as e:
		frappe.log_error(f"Error checking stalled syncs: {str(e)}", "Wix Stalled Sync Check Error")

def validate_settings_configuration():
	"""Validate that Wix settings are properly configured"""
	try:
		settings = frappe.get_single('Wix Settings')
		
		issues = []
		
		if not settings.site_id:
			issues.append("Missing Wix Site ID")
		
		if not settings.api_key:
			issues.append("Missing Wix API Key")
		
		if not settings.account_id:
			issues.append("Missing Wix Account ID")
		
		if settings.timeout_seconds and settings.timeout_seconds < 10:
			issues.append("Timeout too low (minimum 10 seconds recommended)")
		
		if issues:
			error_msg = "Wix configuration issues found: " + ", ".join(issues)
			frappe.log_error(error_msg, "Wix Configuration Issues")
		else:
			frappe.logger().info("Wix configuration validation passed")
		
	except Exception as e:
		frappe.log_error(f"Error validating settings: {str(e)}", "Wix Settings Validation Error")

def check_error_rates():
	"""Check recent error rates and alert if too high"""
	try:
		# Check error rate over last 24 hours
		yesterday = add_days(now_datetime(), -1)
		
		total_logs = frappe.db.count(
			"Wix Integration Log",
			filters=[["timestamp", ">=", yesterday]]
		)
		
		error_logs = frappe.db.count(
			"Wix Integration Log",
			filters=[
				["timestamp", ">=", yesterday],
				["status", "=", "Error"]
			]
		)
		
		if total_logs > 0:
			error_rate = (error_logs / total_logs) * 100
			
			frappe.logger().info(f"Wix integration error rate (24h): {error_rate:.1f}% ({error_logs}/{total_logs})")
			
			# Alert if error rate is above 20%
			if error_rate > 20:
				frappe.log_error(
					f"High error rate detected: {error_rate:.1f}% ({error_logs}/{total_logs} in last 24h)",
					"Wix High Error Rate Alert"
				)
		
	except Exception as e:
		frappe.log_error(f"Error checking error rates: {str(e)}", "Wix Error Rate Check Error")

def optimize_integration_performance():
	"""Optimize integration performance by cleaning up and reorganizing data"""
	try:
		settings = frappe.get_single('Wix Settings')
		if not settings.enabled:
			return
		
		frappe.logger().info("Starting Wix integration performance optimization")
		
		# Clean up old logs (more aggressive weekly cleanup)
		cutoff_date = add_days(now_datetime(), -7)  # Keep only last 7 days for weekly cleanup
		
		old_logs = frappe.get_all(
			"Wix Integration Log",
			filters=[
				["timestamp", "<", cutoff_date]
			],
			limit=5000  # Process more in weekly cleanup
		)
		
		for log in old_logs:
			try:
				frappe.delete_doc("Wix Integration Log", log.name, ignore_permissions=True)
			except:
				continue
		
		if old_logs:
			frappe.db.commit()
			frappe.logger().info(f"Performance optimization: Cleaned up {len(old_logs)} old logs")
		
		# Reset stuck sync statuses
		reset_stuck_sync_statuses()
		
		frappe.logger().info("Completed Wix integration performance optimization")
		
	except Exception as e:
		frappe.log_error(f"Error during performance optimization: {str(e)}", "Wix Performance Optimization Error")

def reset_stuck_sync_statuses():
	"""Reset items that have been stuck in 'Pending' status for too long"""
	try:
		# Find items stuck in 'Pending' status for more than 24 hours
		cutoff_time = add_days(now_datetime(), -1)
		
		stuck_items = frappe.get_all(
			"Item",
			filters=[
				["wix_sync_status", "=", "Pending"],
				["wix_last_sync", "<", cutoff_time]
			],
			limit=100
		)
		
		for item in stuck_items:
			try:
				frappe.db.set_value("Item", item.name, "wix_sync_status", "Ready")
			except:
				continue
		
		if stuck_items:
			frappe.db.commit()
			frappe.logger().info(f"Reset {len(stuck_items)} stuck sync statuses to 'Ready'")
		
	except Exception as e:
		frappe.log_error(f"Error resetting stuck sync statuses: {str(e)}", "Wix Reset Sync Status Error")
