import psutil
from loguru import logger

def get_system_health() -> str:
    """
    Returns a summary of system health stats (CPU, RAM, Battery, Disk).
    """
    try:
        # CPU
        cpu_pct = psutil.cpu_percent(interval=0.5)
        
        # RAM
        mem = psutil.virtual_memory()
        ram_pct = mem.percent
        ram_used_gb = round(mem.used / (1024**3), 1)
        ram_total_gb = round(mem.total / (1024**3), 1)
        
        # Battery
        battery = psutil.sensors_battery()
        batt_str = "No Battery/Desktop"
        if battery:
            plugged = "Plugged In" if battery.power_plugged else "On Battery"
            batt_str = f"{battery.percent}% ({plugged})"
            
        # Disk
        disk = psutil.disk_usage('/')
        disk_pct = disk.percent
        
        status = (
            f"**System Health Report:**\n"
            f"- **CPU Load**: {cpu_pct}%\n"
            f"- **RAM Usage**: {ram_pct}% ({ram_used_gb}/{ram_total_gb} GB)\n"
            f"- **Battery**: {batt_str}\n"
            f"- **Disk (C:)**: {disk_pct}% used"
        )
        
        # Proactive alerts
        alerts = []
        if cpu_pct > 80: alerts.append("⚠️ CPU is under heavy load (>80%). Check for dust/background apps.")
        if ram_pct > 90: alerts.append("⚠️ RAM is critical (>90%). Close some apps.")
        if battery and battery.percent < 20 and not battery.power_plugged: alerts.append("⚠️ Battery Low! Connect charger.")
        
        if alerts:
            status += "\n\n**Alerts:**\n" + "\n".join(alerts)
            
        logger.info(f"Health Check: CPU {cpu_pct}%, RAM {ram_pct}%")
        return status
        
    except Exception as e:
        logger.error(f"Health Check Error: {e}")
        return f"Error checking system health: {e}"
