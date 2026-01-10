import requests
from typing import Dict, List, Optional, Any
import json

class APIClient:
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
    
    def _request(self, method: str, endpoint: str, **kwargs) -> Any:
        url = f"{self.base_url}/{endpoint}"
        try:
            response = self.session.request(method, url, **kwargs)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            error_msg = f"{e}"
            try:
                error_detail = response.json()
                error_msg = f"{e} - {error_detail}"
            except:
                pass
            raise Exception(error_msg)
    
    def get_contracts(self, domain: Optional[str] = None, limit: int = 100, is_active: bool = True) -> List[Dict]:
        params = {"limit": limit, "is_active": is_active}
        if domain:
            params["domain"] = domain
        result = self._request("GET", "contracts", params=params)
        
        if isinstance(result, list):
            return result
        elif isinstance(result, dict):
            if "contracts" in result:
                return result["contracts"]
            elif "items" in result:
                return result["items"]
        return []
    
    def get_contract(self, contract_id: str) -> Dict:
        return self._request("GET", f"contracts/{contract_id}")
    
    def create_contract(self, name: str, domain: str, yaml_content: str, description: str = "") -> Dict:
        data = {
            "name": name,
            "domain": domain,
            "yaml_content": yaml_content,
            "description": description
        }
        return self._request("POST", "contracts", json=data)
    
    def update_contract(self, contract_id: str, yaml_content: str) -> Dict:
        data = {"yaml_content": yaml_content}
        return self._request("PUT", f"contracts/{contract_id}", json=data)
    
    def delete_contract(self, contract_id: str, hard_delete: bool = False) -> Dict:
        params = {"hard_delete": "true"} if hard_delete else {}
        return self._request("DELETE", f"contracts/{contract_id}", params=params)
    
    def activate_contract(self, contract_id: str) -> Dict:
        return self._request("POST", f"contracts/{contract_id}/activate")
    
    def validate_single(self, contract_id: str, data: Dict) -> Dict:
        payload = {"data": data}
        return self._request("POST", f"validate/{contract_id}", json=payload)
    
    def validate_batch(self, contract_id: str, file_content: str, file_type: str) -> Dict:
        import base64
        encoded = base64.b64encode(file_content.encode()).decode()
        payload = {
            "file_data": encoded,
            "file_type": file_type
        }
        return self._request("POST", f"validate/{contract_id}/batch", json=payload)
    
    def get_validation_results(self, contract_id: str, limit: int = 100) -> List[Dict]:
        params = {"limit": limit}
        result = self._request("GET", f"validate/{contract_id}/results", params=params)
        
        if isinstance(result, list):
            return result
        elif isinstance(result, dict):
            if "results" in result:
                return result["results"]
            elif "items" in result:
                return result["items"]
        return []
    
    def get_contract_versions(self, contract_id: str) -> List[Dict]:
        result = self._request("GET", f"contract-versions/{contract_id}/versions")

        if isinstance(result, list):
            return result
        elif isinstance(result, dict) and "versions" in result:
            return result["versions"]
        return []

    def compare_versions(self, contract_id: str, v1: str, v2: str) -> Dict:
        return self._request("GET", f"contract-versions/{contract_id}/diff/{v1}/{v2}")
    
    def get_daily_metrics(self, contract_id: str, days: int = 30) -> List[Dict]:
        params = {"days": days}
        result = self._request("GET", f"metrics/{contract_id}/daily", params=params)
        
        if isinstance(result, list):
            return result
        elif isinstance(result, dict):
            if "metrics" in result:
                return result["metrics"]
            elif "items" in result:
                return result["items"]
        return []
    
    def get_trend_data(self, contract_id: str, days: int = 90) -> Dict:
        params = {"days": days}
        return self._request("GET", f"metrics/{contract_id}/trend", params=params)
    
    def get_platform_summary(self) -> Dict:
        return self._request("GET", "metrics/summary")