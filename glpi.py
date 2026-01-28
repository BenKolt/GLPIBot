import requests

def init_session(glpi_url, app_token, user_token):
    headers = {
        "App-Token": app_token,
        "Authorization": f"user_token {user_token}",
    }

    try:
        r = requests.post(f"{glpi_url}/apirest.php/initSession", headers=headers, timeout=5)
        if r.status_code == 200:
            return r.json().get("session_token")
    except Exception:
        return None
    return None


def create_ticket(glpi_url, app_token, session_token, title, description):
    headers = {
        "App-Token": app_token,
        "Session-Token": session_token,
        "Content-Type": "application/json",
    }
    payload = {
        "input": {
            "name": title,
            "content": description,
            "requesttypes_id": 1
        }
    }

    try:
        r = requests.post(f"{glpi_url}/apirest.php/Ticket", headers=headers, json=payload, timeout=5)
        if r.status_code == 201:
            return r.json().get("id")
    except Exception:
        return None
    return None


def get_my_tickets(glpi_url, app_token, session_token, limit=5):
    headers = {
        "App-Token": app_token,
        "Session-Token": session_token,
    }
    params = {"range": f"0-{limit-1}"}

    try:
        r = requests.get(f"{glpi_url}/apirest.php/Ticket", headers=headers, params=params, timeout=5)
        if r.status_code == 200:
            return r.json()
    except Exception:
        return []
    return []
