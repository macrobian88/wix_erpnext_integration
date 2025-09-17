# -*- coding: utf-8 -*-
"""Wix API Connector - Debug version to identify 403 issue"""

import frappe
import requests
import json
from datetime import datetime
from frappe import _
from frappe.utils import get_site_url

class WixConnector:
	"""Main class for handling Wix API connections using Wix Stores v1 Catalog API"""
	
	def __init__(self):
		self.settings = self.get_settings()
		self.base_url = "https://www.wixapis.com"
		self.headers = self.get_headers()
		
		# Debug: Log initialization details
		frappe.log_error(f"WixConnector initialized. Settings loaded: {bool(self.settings)}", "Wix Debug")
		if self.settings:
			frappe.log_error(f"Site ID: {self.settings.site_id}, Account ID: {self.settings.account_id}", "Wix Debug")
			frappe.log_error(f"API Key present: {bool(self.settings.api_key)}, Length: {len(self.settings.api_key) if self.settings.api_key else 0}", "Wix Debug")
	
	def get_settings(self):
		"""Get Wix settings with caching"""
		try:
			# Try direct access first
			settings = frappe.get_single('Wix Settings')
			frappe.log_error(f"Settings retrieved directly: enabled={settings.enabled}, site_id={settings.site_id}", "Wix Debug")
			return settings
		except Exception as e:
			frappe.log_error(f"Error getting Wix settings: {str(e)}", "Wix Connector Error")
			return None
	
	def get_headers(self):
		"""Get API request headers"""
		if not self.settings or not self.settings.api_key:
			frappe.log_error("No settings or API key found for headers", "Wix Debug")
			return {}
		
		# Get the actual API key value (decrypt if needed)
		api_key = self.settings.get_password('api_key')
		if not api_key:
			api_key = self.settings.api_key
		
		headers = {
			'Content-Type': 'application/json',
			'Authorization': f'Bearer {api_key}',
			'wix-site-id': self.settings.site_id,
			'wix-account-id': self.settings.account_id
		}
		
		# Debug: Log headers (without full API key)
		frappe.log_error(f"Headers prepared: Authorization starts with 'Bearer {api_key[:10]}...', Site ID: {self.settings.site_id}", "Wix Debug")
		
		return headers
	
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
		"""Create a product in Wix using Stores v1 Catalog API"""
		if not self.settings or not self.settings.enabled:
			return {'success': False, 'error': 'Wix integration is not enabled'}
		
		try:
			url = f"{self.base_url}/stores/v1/products"
			
			# Prepare the request payload according to Wix Catalog V1 API requirements
			payload = {
				'product': product_data
			}
			
			# Debug: Log request details
			frappe.log_error(f"Creating product at URL: {url}", "Wix Debug")
			frappe.log_error(f"Payload: {json.dumps(payload, indent=2)}", "Wix Debug")
			frappe.log_error(f"Headers: {json.dumps({k: v[:20] + '...' if k == 'Authorization' else v for k, v in self.headers.items()}, indent=2)}", "Wix Debug")
			
			response = requests.post(
				url,
				headers=self.headers,
				data=json.dumps(payload),
				timeout=self.settings.timeout_seconds or 30
			)
			
			# Debug: Log response
			frappe.log_error(f"Response status: {response.status_code}", "Wix Debug")
			frappe.log_error(f"Response headers: {dict(response.headers)}", "Wix Debug")
			frappe.log_error(f"Response text: {response.text[:500]}...", "Wix Debug")
			
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
				
				# Log detailed error for debugging
				frappe.log_error(f"Product creation failed - Status: {response.status_code}, Error: {error_data}", "Wix Debug")
				
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
		"""Update a product in Wix using Stores v1 Catalog API"""
		if not self.settings or not self.settings.enabled:
			return {'success': False, 'error': 'Wix integration is not enabled'}
		
		try:
			url = f"{self.base_url}/stores/v1/products/{product_id}"
			
			# Prepare the request payload
			payload = {
				'product': product_data
			}
			
			# Debug: Log request details
			frappe.log_error(f"Updating product {product_id} at URL: {url}", "Wix Debug")
			frappe.log_error(f"Update payload: {json.dumps(payload, indent=2)}", "Wix Debug")
			
			response = requests.patch(
				url,
				headers=self.headers,
				data=json.dumps(payload),
				timeout=self.settings.timeout_seconds or 30
			)
			
			# Debug: Log response
			frappe.log_error(f"Update response status: {response.status_code}", "Wix Debug")
			frappe.log_error(f"Update response text: {response.text[:500]}...", "Wix Debug")
			
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
			url = f"{self.base_url}/stores/v1/products/{product_id}"
			
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
		"""Create a category in Wix using Categories v1 API"""
		if not self.settings or not self.settings.enabled:
			return {'success': False, 'error': 'Wix integration is not enabled'}
		
		try:
			url = f"{self.base_url}/stores/v1/collections"
			
			# Prepare the request payload for V1 collections (categories)
			payload = {
				'collection': {
					'name': category_data.get('name'),
					'description': category_data.get('description', ''),
					'visible': category_data.get('visible', True)
				}
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
					'category_id': result.get('collection', {}).get('id'),
					'category': result.get('collection'),
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
