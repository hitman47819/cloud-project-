# front_end/utils.py
from flask import session
import requests

def get_current_user():
    return session.get('user_id')

def api_request(service, endpoint, method='GET', data=None):
    SERVICES = {
        'user': 'http://localhost:5001',  # Change port from 5001 to 5000
        'transaction': 'http://localhost:5002',
        'reporting': 'http://localhost:5003'
    }

    
    try:
        response = requests.request(
            method,
            f"{service_urls[service]}/{endpoint}",
            json=data
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"API Error: {e}")
        return None
