# -*- coding: utf-8 -*-
"""Wix API Connector - Handles all Wix API communication with proper v3 Stores API"""

import frappe
import requests
import json
from datetime import datetime
from frappe import _
from frappe.utils import get_site_url

class WixConnector:
	"""Main class for handling Wix API connections using proper Wix Stores v3 API"""
	
	def __init__(self):
		self.settings = self.get_settings()
		self.base_url = "https://www.wixapis.com"
		self.headers = self.get_headers()
	
	def get_settings(self):
		"""Get Wix settings with caching"""
		try:
			from wix_integration.wix_integration.doctype.wix_settings.wix_settings import get_wix_settings
			return get_wix_settings()
		except Exception as e:
			frappe.log_error(f"Error getting Wix settings: {str(e)}", "Wix Connector")
			return None
	
	def get_headers(self):
		"""Get API request headers"""
		if not self.settings or not self.settings.api_key:
			return {}
		
		return {
			'Content-Type': 'application/json',
			'Authorization': f'Bearer {self.settings.api_key}',
			'wix-site-id': self.settings.site_id,
			'wix-account-id': self.settings.account_id
		}
	
	def test_connection(self):
		"""Test Wix API connection using site details endpoint"""
		if not self.settings or not self.settings.enabled:
			return {'success': False, 'error': 'Wix integration is not enabled'}
		
		if not all([self.settings.site_id, self.settings.api_key, self.settings.account_id]):
			return {'success': False, 'error': 'Missing required Wix credentials'}
		
		try:
			# Test with site details endpoint
			response = requests.get(
				f"{self.base_url}/business-info/v1/site-properties",
				headers=self.headers,
				timeout=self.settings.timeout_seconds or 30
			)
			
			if response.status_code == 200:
				return {
					'success': True, 
					'message': 'Connection successful',
					'site_info': response.json()
				}
			else:
				return {
					'success': False, 
					'error': f'API returned status {response.status_code}: {response.text}'
				}
				
		except requests.exceptions.Timeout:
			return {'success': False, 'error': 'Connection timeout'}
		except requests.exceptions.ConnectionError:
			return {'success': False, 'error': 'Failed to connect to Wix API'}
		except Exception as e:
			return {'success': False, 'error': str(e)}
	
	def create_product(self, product_data):
		"""Create a product in Wix using Stores v3 API"""
		if not self.settings or not self.settings.enabled:
			return {'success': False, 'error': 'Wix integration is not enabled'}
		
		try:
			url = f"{self.base_url}/stores/v3/products"
			
			# Prepare the request payload according to Wix API requirements
			payload = {
				'product': product_data
			}
			
			response = requests.post(
				url,
				headers=self.headers,
				data=json.dumps(payload),
				timeout=self.settings.timeout_seconds or 30
			)
			
			if response.status_code in [200, 201]:
				result = response.json()
				return {
					'success': True,
					'product_id': result.get('product', {}).get('id'),
					'product': result.get('product'),
					'response': result
				}
			else:
				try:
					error_data = response.json()
				except:
					error_data = response.text
				
				return {
					'success': False,
					'error': f'Failed to create product: {response.status_code}',
					'error_data': error_data,
					'status_code': response.status_code
				}
				
		except requests.exceptions.Timeout:
			return {'success': False, 'error': 'Request timeout while creating product'}
		except requests.exceptions.ConnectionError:
			return {'success': False, 'error': 'Connection error while creating product'}
		except Exception as e:
			frappe.log_error(f"Unexpected error creating product: {str(e)}", "Wix Connector")
			return {'success': False, 'error': f'Unexpected error: {str(e)}'}
	
	def update_product(self, product_id, product_data):
		"""Update a product in Wix using Stores v3 API"""
		if not self.settings or not self.settings.enabled:
			return {'success': False, 'error': 'Wix integration is not enabled'}
		
		try:
			url = f"{self.base_url}/stores/v3/products/{product_id}"
			
			# Prepare the request payload
			payload = {
				'product': product_data
			}
			
			response = requests.patch(
				url,
				headers=self.headers,
				data=json.dumps(payload),
				timeout=self.settings.timeout_seconds or 30
			)
			
			if response.status_code == 200:
				result = response.json()
				return {
					'success': True,
					'product': result.get('product'),
					'response': result
				}
			else:
				try:
					error_data = response.json()
				except:
					error_data = response.text
				
				return {
					'success': False,
					'error': f'Failed to update product: {response.status_code}',
					'error_data': error_data,
					'status_code': response.status_code
				}
				
		except requests.exceptions.Timeout:
			return {'success': False, 'error': 'Request timeout while updating product'}
		except requests.exceptions.ConnectionError:
			return {'success': False, 'error': 'Connection error while updating product'}
		except Exception as e:
			frappe.log_error(f"Unexpected error updating product: {str(e)}", "Wix Connector")
			return {'success': False, 'error': f'Unexpected error: {str(e)}'}
	
	def get_product(self, product_id):
		"""Get a product from Wix"""
		if not self.settings or not self.settings.enabled:
			return {'success': False, 'error': 'Wix integration is not enabled'}
		
		try:
			url = f"{self.base_url}/stores/v3/products/{product_id}"
			
			response = requests.get(
				url,
				headers=self.headers,
				timeout=self.settings.timeout_seconds or 30
			)
			
			if response.status_code == 200:
				result = response.json()
				return {
					'success': True,
					'product': result.get('product'),
					'response': result
				}
			else:
				return {
					'success': False,
					'error': f'Failed to get product: {response.status_code}',
					'status_code': response.status_code
				}
				
		except Exception as e:
			frappe.log_error(f"Error getting product: {str(e)}", "Wix Connector")
			return {'success': False, 'error': f'Error getting product: {str(e)}'}
	
	def upload_media(self, file_url, file_name=None):
		"""Upload media to Wix Media Manager"""
		if not self.settings or not self.settings.enabled:
			return {'success': False, 'error': 'Wix integration is not enabled'}
		
		try:
			# For now, return the original URL as Wix can handle external URLs
			# In production, you'd want to upload to Wix Media Manager using the Media API
			return {
				'success': True,
				'media_url': file_url,
				'media_id': None  # Would contain actual media ID after upload
			}
			
		except Exception as e:
			frappe.log_error(f"Error uploading media: {str(e)}", "Wix Connector")
			return {'success': False, 'error': f'Error uploading media: {str(e)}'}
	
	def create_category(self, category_data):
		"""Create a category in Wix using Categories v3 API"""
		if not self.settings or not self.settings.enabled:
			return {'success': False, 'error': 'Wix integration is not enabled'}
		
		try:
			url = f"{self.base_url}/stores/v3/categories"
			
			# Prepare the request payload
			payload = {
				'category': category_data
			}
			
			response = requests.post(
				url,
				headers=self.headers,
				data=json.dumps(payload),
				timeout=self.settings.timeout_seconds or 30
			)
			
			if response.status_code in [200, 201]:
				result = response.json()
				return {
					'success': True,
					'category_id': result.get('category', {}).get('id'),
					'category': result.get('category'),
					'response': result
				}
			else:
				try:
					error_data = response.json()
				except:
					error_data = response.text
				
				return {
					'success': False,
					'error': f'Failed to create category: {response.status_code}',
					'error_data': error_data,
					'status_code': response.status_code
				}
				
		except Exception as e:
			frappe.log_error(f"Error creating category: {str(e)}", "Wix Connector")
			return {'success': False, 'error': f'Error creating category: {str(e)}'}
	
	def make_request(self, method, endpoint, data=None):
		"""Generic method to make API requests"""
		if not self.settings or not self.settings.enabled:
			return {'success': False, 'error': 'Wix integration is not enabled'}
		
		try:
			url = f"{self.base_url}/{endpoint.lstrip('/')}"
			
			kwargs = {
				'headers': self.headers,
				'timeout': self.settings.timeout_seconds or 30
			}
			
			if data:
				kwargs['data'] = json.dumps(data)
			
			response = requests.request(method.upper(), url, **kwargs)
			
			if response.status_code in [200, 201, 204]:
				try:
					result = response.json() if response.text else {}
				except json.JSONDecodeError:
					result = {'raw_response': response.text}
				
				return {
					'success': True,
					'data': result,
					'status_code': response.status_code
				}
			else:
				try:
					error_data = response.json()
				except json.JSONDecodeError:
					error_data = response.text
				
				return {
					'success': False,
					'error': f'Request failed: {response.status_code}',
					'error_data': error_data,
					'status_code': response.status_code
				}
				
		except Exception as e:
			frappe.log_error(f"Error in make_request: {str(e)}", "Wix Connector")
			return {'success': False, 'error': f'Request error: {str(e)}'}
