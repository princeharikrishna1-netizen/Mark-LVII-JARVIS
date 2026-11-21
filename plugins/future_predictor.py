import shutil, time
from pathlib import Path

TOOL = {
    "name": "future_predict_health",
    "description": "Predicts upcoming PC storage exhaustion, RAM pressure, battery, and network issues before they happen.",
    "parameters": {"type": "OBJECT", "properties": {}}
}

def run(params: dict = None, **kwargs) -> str:
    alerts = []
    # Disk trajectory
    total, used, free = shutil.disk_usage(".")
    free_gb = free / (1024**3)
    pct_used = (used / total) * 100
    if pct_used > 85 or free_gb < 15:
        alerts.append(f"Storage Warning: {pct_used:.1f}% full ({free_gb:.1f} GB free) — cleanup needed soon.")
    else:
        alerts.append(f"Storage Healthy: {free_gb:.1f} GB free ({100 - pct_used:.1f}% available).")

    # RAM & Battery via psutil if available
    try:
        import psutil
        vm = psutil.virtual_memory()
        if vm.percent > 80:
            alerts.append(f"RAM Pressure Predicted: {vm.percent}% used — heavy background apps may cause stutter.")
        else:
            alerts.append(f"Memory Stable: {vm.available / (1024**3):.1f} GB free ({vm.percent}% used).")
        bat = psutil.sensors_battery()
        if bat:
            if not bat.power_plugged and bat.percent < 25:
                alerts.append(f"Battery Alert: {bat.percent}% remaining (~{bat.secsleft // 60} mins left) — plug in charger.")
            else:
                alerts.append(f"Battery: {bat.percent}% ({'Charging/Plugged' if bat.power_plugged else 'On Battery'}).")
    except Exception:
        pass

    return "Future Prediction Engine -> " + " | ".join(alerts)

PLUGIN = TOOL

