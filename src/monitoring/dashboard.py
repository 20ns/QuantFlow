"""
Simple real-time dashboard for monitoring trading engine status
"""
import asyncio
from typing import Dict, Any
from rich.console import Console
from rich.table import Table
from datetime import datetime

class RealTimeDashboard:
    def __init__(self):
        self.console = Console()

    async def display_status(self, status: Dict[str, Any]):
        table = Table(title=f"QuantFlow Real-Time Status @ {datetime.now().strftime('%H:%M:%S')}")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="magenta")
        for k, v in status.items():
            table.add_row(str(k), str(v))
        self.console.clear()
        self.console.print(table)
