"""
JARVIS Plugin: External API Integration & Data Enrichment
- Fetches and analyzes real-time data from external web APIs for JARVIS workflows.
"""
import requests

PLUGIN = {
    "name": "external_api_enrichment",
    "version": "1.0.0",
    "description": "Connects to external APIs to enrich project data and pull real-time information."
}

TOOL = {
    "name": "fetch_external_data",
    "description": "Fetches real-time data or information from a specified external API endpoint.",
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "api_url": {
                "type": "STRING",
                "description": "The URL of the external API to query."
            }
        },
        "required": ["api_url"]
    }
}

def run(args, player=None, session_memory=None):
    url = args.get("api_url", "")
    if not url:
        return "దయచేసి సరైన API URL అందించండి Hari."

    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            msg = f"సార్, ఎక్స్‌టర్నల్ API నుండి విజయవంతമായി డేటా ఫెచ్ చేయబడింది."
        else:
            msg = f"API రెస్పాన్స్ ఎర్రర్: Status code {response.status_code}"
    except Exception as e:
        msg = f"క్షమించండి Hari, API కనెక్షన్‌లో లోపం ఏర్పడింది: {str(e)}"

    if player and hasattr(player, "write_log"):
        player.write_log(f"SYS: {msg}")
        
    return msg