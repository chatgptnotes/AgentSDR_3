import os
import time
from typing import Dict, Any, Optional, List

import requests
from jinja2 import Template
from urllib.parse import urlencode


class HubSpotService:
    """Lightweight HubSpot OAuth + CRM client for our use cases.

    Stores/accepts tokens via caller and focuses on:
    - OAuth URL building and token exchange
    - Basic CRM fetch helpers (contacts, companies, deals)
    - Proposal drafting via simple Jinja2 template render
    """

    AUTH_URL = "https://app.hubspot.com/oauth/authorize"
    TOKEN_URL = "https://api.hubapi.com/oauth/v1/token"
    API_BASE = "https://api.hubapi.com"

    def __init__(self, access_token: Optional[str] = None, refresh_token: Optional[str] = None):
        self.access_token = access_token
        self.refresh_token = refresh_token
        self._token_acquired_at = time.time() if access_token else None

    # ---------- OAuth ----------
    def get_authorize_url(self, state: str) -> str:
        client_id = os.getenv("HUBSPOT_CLIENT_ID")
        redirect_uri = os.getenv("HUBSPOT_REDIRECT_URI")
        scopes = [
            "crm.objects.contacts.read",
            "crm.objects.deals.read",
            "crm.objects.companies.read",
        ]
        params = {
            "client_id": (client_id or "").strip(),
            "redirect_uri": redirect_uri or "",
            "scope": " ".join(scopes),
            "state": state,
            "response_type": "code",
        }
        return f"{self.AUTH_URL}?{urlencode(params)}"

    def exchange_code_for_tokens(self, code: str) -> Dict[str, Any]:
        client_id = os.getenv("HUBSPOT_CLIENT_ID")
        client_secret = os.getenv("HUBSPOT_CLIENT_SECRET")
        redirect_uri = os.getenv("HUBSPOT_REDIRECT_URI")

        resp = requests.post(
            self.TOKEN_URL,
            data={
                "grant_type": "authorization_code",
                "client_id": client_id,
                "client_secret": client_secret,
                "redirect_uri": redirect_uri,
                "code": code,
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=30,
        )
        resp.raise_for_status()
        tokens = resp.json()
        self.access_token = tokens.get("access_token")
        self.refresh_token = tokens.get("refresh_token")
        self._token_acquired_at = time.time()
        return tokens

    def refresh_access_token(self) -> Dict[str, Any]:
        if not self.refresh_token:
            raise ValueError("No refresh token available")

        client_id = os.getenv("HUBSPOT_CLIENT_ID")
        client_secret = os.getenv("HUBSPOT_CLIENT_SECRET")

        resp = requests.post(
            self.TOKEN_URL,
            data={
                "grant_type": "refresh_token",
                "client_id": client_id,
                "client_secret": client_secret,
                "refresh_token": self.refresh_token,
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=30,
        )
        resp.raise_for_status()
        tokens = resp.json()
        self.access_token = tokens.get("access_token")
        self._token_acquired_at = time.time()
        return tokens

    # ---------- Helpers ----------
    def _auth_headers(self) -> Dict[str, str]:
        if not self.access_token:
            raise ValueError("Missing access token")
        return {"Authorization": f"Bearer {self.access_token}"}

    def _get(self, path: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        url = f"{self.API_BASE}{path}"
        resp = requests.get(url, headers=self._auth_headers(), params=params or {}, timeout=30)
        resp.raise_for_status()
        return resp.json()

    # ---------- CRM Fetch ----------
    def fetch_contacts(self, limit: int = 5) -> List[Dict[str, Any]]:
        # Include properties matching your HubSpot setup
        properties = "email,firstname,lastname,phone,check_up_date,lead_summary,lastmodifieddate,createdate"
        data = self._get("/crm/v3/objects/contacts", params={"limit": limit, "properties": properties})
        return data.get("results", [])

    def fetch_companies(self, limit: int = 5) -> List[Dict[str, Any]]:
        data = self._get("/crm/v3/objects/companies", params={"limit": limit, "properties": "name,domain"})
        return data.get("results", [])

    def fetch_deals(self, limit: int = 5) -> List[Dict[str, Any]]:
        data = self._get("/crm/v3/objects/deals", params={"limit": limit, "properties": "dealname,amount,dealstage,closedate"})
        return data.get("results", [])

    def fetch_patients(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Fetch patient data from HubSpot contacts with healthcare-specific properties"""
        # Properties matching your HubSpot setup
        properties = "email,firstname,lastname,phone,check_up_date,lead_summary,lastmodifieddate,createdate"
        data = self._get("/crm/v3/objects/contacts", params={"limit": limit, "properties": properties})

        patients = []
        for contact in data.get("results", []):
            props = contact.get("properties", {})

            # Build patient name from firstname and lastname
            firstname = props.get("firstname", "")
            lastname = props.get("lastname", "")
            name = f"{firstname} {lastname}".strip() or "Unknown Patient"

            # Parse check_up_date
            check_up_date = props.get("check_up_date", "")
            if check_up_date:
                # Handle format like "15 Aug 2025 (6 days ago)"
                check_update = check_up_date.split(" (")[0] if " (" in check_up_date else check_up_date
            else:
                check_update = "No recent check-up"

            # Get summary from lead_summary or create default
            summary = props.get("lead_summary", "").strip()
            if not summary or summary == "--":
                summary = "Patient record available. Contact for detailed information."

            # Determine status based on check_up_date recency
            status = "stable"  # default
            if "days ago" in check_up_date:
                try:
                    days_match = check_up_date.split("(")[1].split(" days ago")[0]
                    days_ago = int(days_match)
                    if days_ago <= 7:
                        status = "recent"
                    elif days_ago <= 30:
                        status = "stable"
                    else:
                        status = "overdue"
                except:
                    status = "stable"

            patient = {
                'id': contact.get("id"),
                'name': name,
                'phone': props.get("phone", "No phone"),
                'email': props.get("email", "No email"),
                'checkUpdate': check_update,
                'summary': summary,
                'status': status,
                'lastVisit': check_update,
                'nextAppointment': "To be scheduled",
                'lastModified': props.get("lastmodifieddate", ""),
                'created': props.get("createdate", "")
            }
            patients.append(patient)

        return patients

    # ---------- Proposal Drafting ----------
    @staticmethod
    def build_context(industry: str, client_type: str, contacts: List[Dict[str, Any]], companies: List[Dict[str, Any]], deals: List[Dict[str, Any]]) -> Dict[str, Any]:
        return {
            "industry": industry,
            "client_type": client_type,
            "primary_contact": HubSpotService._safe_prop(contacts, 0, ["properties", "firstname"], default="Valued"),
            "company_name": HubSpotService._safe_prop(companies, 0, ["properties", "name"], default="Your Company"),
            "recent_deals": [
                {
                    "name": d.get("properties", {}).get("dealname"),
                    "amount": d.get("properties", {}).get("amount"),
                    "stage": d.get("properties", {}).get("dealstage"),
                }
                for d in deals[:5]
            ],
        }

    @staticmethod
    def _safe_prop(items: List[Dict[str, Any]], index: int, path: List[str], default: Any = None) -> Any:
        try:
            cur: Any = items[index]
            for key in path:
                cur = cur.get(key, {})
            return cur if cur else default
        except Exception:
            return default

    @staticmethod
    def default_template() -> str:
        return (
            """Proposal for {{ company_name }}\n\n"
            "Dear {{ primary_contact }},\n\n"
            "Based on our understanding of the {{ industry }} space and your needs as a {{ client_type }}, "
            "we propose a tailored solution leveraging our experience.\n\n"
            "Recent CRM insights:\n"
            "{% for d in recent_deals %}- Deal: {{ d.name }} | Amount: {{ d.amount }} | Stage: {{ d.stage }}\n{% endfor %}\n"
            "Next steps:\n- Review and customize scope\n- Confirm timeline\n- Finalize commercial terms\n\n"
            "Best regards,\nYour Team\n"""
        )

    @staticmethod
    def render_template_text(template_text: str, context: Dict[str, Any]) -> str:
        try:
            return Template(template_text).render(**context)
        except Exception:
            # Fallback to a plain string if templating fails
            return template_text


