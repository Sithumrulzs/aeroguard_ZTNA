import time
import threading
from datetime import datetime
import psutil
import json
import os

from rich.live import Live
from rich.table import Table
from rich.layout import Layout
from rich.panel import Panel
from rich.console import Console
from rich.text import Text
from rich.align import Align
from rich.rule import Rule
from rich import box
from rich.columns import Columns

try:
    from pyfiglet import figlet_format
    _FIGLET = True
except ImportError:
    _FIGLET = False

console = Console()

# ──────────────────────────────────────────────────────────────────────────────
# GLOBAL STATE
# ──────────────────────────────────────────────────────────────────────────────
threat_logs    = []
active_tunnels = []
firewall_status = "LOCKED"
metrics = {
    "total_packets":     0,
    "auth_success":      0,
    "auth_failed":       0,
    "dropped_anomalies": 0,
}

start_time    = time.time()
LOG_FILE_PATH = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), "logs", "access.log"
)

# ──────────────────────────────────────────────────────────────────────────────
# STARTUP SPLASH  (printed once before the live dashboard begins)
# ──────────────────────────────────────────────────────────────────────────────
def print_startup_banner() -> None:
    console.clear()

    if _FIGLET:
        raw = figlet_format("AEROGUARD", font="slant")
        logo = Text(raw, style="bold cyan", justify="center")
    else:
        # Fallback block-letter logo
        logo_lines = [
            " ██████╗ ███████╗██████╗  ██████╗  ██████╗ ██╗   ██╗ █████╗ ██████╗ ██████╗ ",
            "██╔══██╗██╔════╝██╔══██╗██╔═══██╗██╔════╝ ██║   ██║██╔══██╗██╔══██╗██╔══██╗",
            "███████║█████╗  ██████╔╝██║   ██║██║  ███╗██║   ██║███████║██████╔╝██║  ██║",
            "██╔══██║██╔══╝  ██╔══██╗██║   ██║██║   ██║██║   ██║██╔══██║██╔══██╗██║  ██║",
            "██║  ██║███████╗██║  ██║╚██████╔╝╚██████╔╝╚██████╔╝██║  ██║██║  ██║██████╔╝",
            "╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝ ╚═════╝  ╚═════╝  ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝╚═════╝",
        ]
        logo = Text(justify="center")
        for line in logo_lines:
            logo.append(line + "\n", style="bold cyan")

    subtitle = Text(justify="center")
    subtitle.append("✈   ZERO TRUST NETWORK ACCESS GATEWAY   ✈\n", style="bold white")
    subtitle.append("       Datacenter Bastion Node  ·  v3.0.0\n", style="dim")

    splash_text = Text(justify="center")
    splash_text.append_text(logo)
    splash_text.append("\n")
    splash_text.append_text(subtitle)

    console.print(
        Panel(
            Align.center(splash_text),
            box=box.DOUBLE_EDGE,
            border_style="bold cyan",
            padding=(1, 4),
        )
    )

    # Animated init sequence
    init_steps = [
        ("Initialising cryptographic verification engine", "cyan"),
        ("Loading hardware identity vault",               "cyan"),
        ("Connecting to SQLite audit store",              "cyan"),
        ("Enforcing Zero Trust DROP policy",              "yellow"),
        ("Bastion gateway ready",                         "bold green"),
    ]
    console.print()
    for msg, style in init_steps:
        console.print(f"  [dim]▶[/dim]  [{style}]{msg}...[/{style}]")
        time.sleep(0.4)

    console.print()
    console.print(
        Rule("[bold cyan]  ✈  LAUNCHING LIVE DASHBOARD  ✈  [/bold cyan]", style="cyan")
    )
    time.sleep(0.8)


# ──────────────────────────────────────────────────────────────────────────────
# LOG FILE WATCHER
# ──────────────────────────────────────────────────────────────────────────────
def follow_log_file() -> None:
    global firewall_status, metrics, active_tunnels

    if not os.path.exists(LOG_FILE_PATH):
        os.makedirs(os.path.dirname(LOG_FILE_PATH), exist_ok=True)
        with open(LOG_FILE_PATH, "w") as f:
            f.write(f"{datetime.now().isoformat()}|SYSTEM|INFO|Dashboard Initialized\n")

    with open(LOG_FILE_PATH, "r") as file:
        file.seek(0, os.SEEK_END)
        while True:
            line = file.readline()
            if not line:
                time.sleep(0.5)
                continue
            try:
                parts = line.strip().split("|")
                if len(parts) >= 4:
                    timestamp, ip, level, message = (
                        parts[0], parts[1], parts[2], parts[3]
                    )
                    metrics["total_packets"] += 1

                    if level == "SUCCESS":
                        metrics["auth_success"] += 1
                        firewall_status = "OPEN"
                        if ip not in active_tunnels and ip != "SYSTEM":
                            active_tunnels.append(ip)
                    elif level == "WARNING":
                        metrics["auth_failed"] += 1
                        if "EXPIRED" in message and ip in active_tunnels:
                            active_tunnels.remove(ip)
                        if not active_tunnels:
                            firewall_status = "LOCKED"
                    elif level == "CRITICAL":
                        metrics["dropped_anomalies"] += 1

                    colors = {
                        "INFO":     "dim white",
                        "SUCCESS":  "bold green",
                        "WARNING":  "bold yellow",
                        "CRITICAL": "bold red",
                    }
                    ts_fmt = (
                        timestamp.split("T")[1][:12]
                        if "T" in timestamp
                        else timestamp
                    )
                    threat_logs.append(
                        (ts_fmt, ip, message, colors.get(level, "white"))
                    )
                    if len(threat_logs) > 15:
                        threat_logs.pop(0)
            except Exception:
                pass


# ──────────────────────────────────────────────────────────────────────────────
# PANEL GENERATORS
# ──────────────────────────────────────────────────────────────────────────────
def generate_header() -> Panel:
    uptime = time.strftime("%H:%M:%S", time.gmtime(time.time() - start_time))
    now    = datetime.now().strftime("%d %b %Y   %H:%M:%S")

    grid = Table.grid(expand=True, padding=(0, 2))
    grid.add_column(justify="left",  ratio=3)
    grid.add_column(justify="center", ratio=4)
    grid.add_column(justify="right", ratio=3)

    left = Text()
    left.append("  ✈  ", style="bold cyan")
    left.append("AEROGUARD", style="bold bright_cyan")
    left.append("  ZTNA\n", style="bold white")
    left.append("      Zero Trust Network Access", style="dim")

    center = Text(justify="center")
    center.append("DATACENTER BASTION GATEWAY\n", style="bold white")
    center.append("─" * 30, style="dim cyan")

    right = Text(justify="right")
    fw_color = "bold green" if firewall_status == "OPEN" else "bold red"
    fw_icon  = "⬤  BRIDGE OPEN" if firewall_status == "OPEN" else "⬤  BLACKHOLE"
    right.append(f"{fw_icon}\n", style=fw_color)
    right.append(f"↑ {uptime}   {now}  ", style="dim")

    grid.add_row(left, center, right)
    return Panel(
        grid,
        box=box.DOUBLE_EDGE,
        border_style="bold cyan",
        style="on black",
        padding=(0, 1),
    )


def generate_system_panel() -> Panel:
    cpu = psutil.cpu_percent()
    ram = psutil.virtual_memory().percent

    cpu_color = "red" if cpu > 80 else "yellow" if cpu > 50 else "green"
    ram_color = "red" if ram > 80 else "yellow" if ram > 50 else "green"

    grid = Table.grid(expand=True, padding=(0, 2))
    grid.add_column(justify="left")
    grid.add_column(justify="right")

    grid.add_row("[dim]CPU Load[/dim]",    f"[{cpu_color}]{cpu:5.1f}%[/{cpu_color}]")
    grid.add_row("[dim]Memory[/dim]",      f"[{ram_color}]{ram:5.1f}%[/{ram_color}]")
    grid.add_row("[dim]FastAPI Core[/dim]","[bold green]ONLINE[/bold green]")
    grid.add_row("[dim]API Port[/dim]",    "[bold white]TCP  8000[/bold white]")

    return Panel(
        grid,
        title="[bold]⚙  VM Diagnostics[/bold]",
        border_style="blue",
        box=box.ROUNDED,
    )


def generate_status_panel() -> Panel:
    if firewall_status == "OPEN":
        body   = Text("\n  >>>  BRIDGE OPEN  <<<\n", style="bold green blink", justify="center")
        sub    = Text("  Routing Authorised Traffic  ", style="green", justify="center")
        border = "green"
    else:
        body   = Text("\n  |||  BLACK HOLE ACTIVE  |||\n", style="bold red", justify="center")
        sub    = Text("  Default DROP policy enforced  ", style="dim red", justify="center")
        border = "red"

    body.append_text(sub)
    return Panel(
        body,
        title="[bold]🔒  Iptables State[/bold]",
        border_style=border,
        box=box.ROUNDED,
    )


def generate_metrics_panel() -> Panel:
    grid = Table.grid(expand=True, padding=(0, 2))
    grid.add_column(justify="left")
    grid.add_column(justify="right")

    grid.add_row("[dim]API Requests[/dim]",     f"[bold cyan]{metrics['total_packets']}[/bold cyan]")
    grid.add_row("[dim]Verified Knocks[/dim]",  f"[bold green]{metrics['auth_success']}[/bold green]")
    grid.add_row("[dim]Rejected Knocks[/dim]",  f"[bold yellow]{metrics['auth_failed']}[/bold yellow]")
    grid.add_row("[dim]Intrusion Attempts[/dim]",f"[bold red]{metrics['dropped_anomalies']}[/bold red]")

    return Panel(
        grid,
        title="[bold]📡  Telemetry[/bold]",
        border_style="blue",
        box=box.ROUNDED,
    )


def generate_threat_table() -> Panel:
    table = Table(
        show_header=True,
        header_style="bold cyan",
        expand=True,
        box=box.SIMPLE_HEAVY,
    )
    table.add_column("Time",        style="dim",        width=14)
    table.add_column("Source IP",                       width=16)
    table.add_column("Security Event / Action")

    for ts, ip, event, color in reversed(threat_logs):
        table.add_row(ts, ip, f"[{color}]{event}[/{color}]")

    return Panel(
        table,
        title="[bold]🛡  Live Traffic Audit & Threat Intel[/bold]",
        border_style="cyan",
        box=box.ROUNDED,
    )


def generate_tunnels_panel() -> Panel:
    table = Table(
        show_header=True,
        header_style="bold green",
        expand=True,
        box=box.SIMPLE_HEAVY,
    )
    table.add_column("✈  Authorised Active Sessions", style="bold green")

    if not active_tunnels:
        table.add_row("[dim]No active sessions.[/dim]")
    else:
        for ip in active_tunnels:
            table.add_row(f"▶  {ip}")

    return Panel(
        table,
        title="[bold]🔗  Active Tunnels[/bold]",
        border_style="green",
        box=box.ROUNDED,
    )


def generate_layout() -> Layout:
    layout = Layout()
    layout.split_column(
        Layout(name="header",     size=4),
        Layout(name="dashboard",  size=8),
        Layout(name="main_view"),
    )
    layout["dashboard"].split_row(
        Layout(name="system",  ratio=1),
        Layout(name="status",  ratio=1),
        Layout(name="metrics", ratio=1),
    )
    layout["main_view"].split_row(
        Layout(name="logs",    ratio=2),
        Layout(name="tunnels", ratio=1),
    )

    layout["header"].update(generate_header())
    layout["system"].update(generate_system_panel())
    layout["status"].update(generate_status_panel())
    layout["metrics"].update(generate_metrics_panel())
    layout["logs"].update(generate_threat_table())
    layout["tunnels"].update(generate_tunnels_panel())

    return layout


# ──────────────────────────────────────────────────────────────────────────────
# ENTRY POINT
# ──────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print_startup_banner()

    watcher = threading.Thread(target=follow_log_file, daemon=True)
    watcher.start()

    with Live(
        generate_layout(),
        refresh_per_second=4,
        screen=True,
    ) as live:
        try:
            while True:
                time.sleep(0.25)
                live.update(generate_layout())
        except KeyboardInterrupt:
            console.print("\n[bold red]  Shutting down AeroGuard Gateway Dashboard...[/bold red]")
