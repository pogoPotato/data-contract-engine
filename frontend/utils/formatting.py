from datetime import datetime

def format_timestamp(ts: str) -> str:
    try:
        dt = datetime.fromisoformat(ts.replace('Z', '+00:00'))
        return dt.strftime('%Y-%m-%d %H:%M:%S')
    except:
        return ts

def format_number(num: float, decimals: int = 2) -> str:
    return f"{num:,.{decimals}f}"

def format_percentage(num: float, decimals: int = 1) -> str:
    return f"{num:.{decimals}f}%"

def format_bytes(bytes: int) -> str:
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes < 1024:
            return f"{bytes:.2f} {unit}"
        bytes /= 1024
    return f"{bytes:.2f} TB"

def truncate_text(text: str, length: int = 50) -> str:
    return text[:length] + "..." if len(text) > length else text
