"""
JARVIS Plugin: Real-time Performance Monitoring
- Tracks and displays CPU and RAM usage of the system in real-time.
"""
import psutil

PLUGIN = {
    "name": "performance_monitor",
    "version": "1.0.0",
    "description": "Monitors and displays current CPU and RAM usage percentages."
}

TOOL = {
    "name": "get_system_performance",
    "description": "Retrieves the current CPU and RAM utilization of the system.",
    "parameters": {
        "type": "OBJECT",
        "properties": {},
        "required": []
    }
}

def run(args, player=None, session_memory=None):
    try:
        cpu_usage = psutil.cpu_percent(interval=1)
        ram = psutil.virtual_memory()
        ram_usage = ram.percent
        ram_available_gb = round(ram.available / (1024 ** 3), 2)
        
        msg = f"సార్, ప్రస్తుత సిస్టమ్ స్థితి: CPU వాడకం {cpu_usage}%, RAM వాడకం {ram_usage}% (అందుబాటులో ఉన్న RAM: {ram_available_gb} GB)."
    except Exception as e:
        msg = f"క్షమించండి Hari, సిస్టమ్ పెర్ఫార్మెన్స్ తెలుసుకోవడంలో లోపం ఏర్పడింది: {str(e)}"

    if player and hasattr(player, "write_log"):
        player.write_log(f"SYS: {msg}")
        
    return msg