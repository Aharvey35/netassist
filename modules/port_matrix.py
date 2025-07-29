# modules/port_matrix.py

import psutil
from rich import print
from rich.table import Table
import socket

COMMON_PORTS = {
    22: "SSH",
    80: "HTTP",
    443: "HTTPS",
    53: "DNS",
    21: "FTP",
    25: "SMTP",
    110: "POP3",
    143: "IMAP",
    3306: "MySQL",
    3389: "RDP",
    5900: "VNC",
    6379: "Redis",
    8080: "HTTP-Alt",
    8443: "HTTPS-Alt"
}

def get_service(port):
    return COMMON_PORTS.get(port, "Unknown")

def get_connections():
    conns = psutil.net_connections(kind='inet')
    results = []

    for c in conns:
        if c.status != psutil.CONN_LISTEN:
            continue
        laddr = c.laddr
        port = laddr.port if hasattr(laddr, 'port') else laddr[1]
        proto = "TCP" if c.type == socket.SOCK_STREAM else "UDP"
        service = get_service(port)
        results.append((proto, port, service))
    
    return results

def show_port_matrix():
    print("[bold cyan]\n>> PORT MATRIX <<[/bold cyan]")
    conns = get_connections()

    if not conns:
        print("[yellow]No listening ports found.[/yellow]")
        return

    table = Table(show_header=True, header_style="bold blue")
    table.add_column("Protocol")
    table.add_column("Port")
    table.add_column("Service")

    for proto, port, service in sorted(conns, key=lambda x: x[1]):
        port_color = "green" if port in COMMON_PORTS else ("yellow" if port < 1024 else "red")
        table.add_row(proto, f"[{port_color}]{port}[/{port_color}]", service)

    print(table)
