def minutes_to_hhmm(minutes):
    if minutes is None:
        return "00:00"

    try:
        total = int(round(float(minutes)))
        h = total // 60
        m = total % 60
        return f"{h:02d}:{m:02d}"
    except:
        return "00:00"


def highlight_sla(val, safe, warning):
    try:
        # 🔥 HAPUS ICON DI BELAKANG
        val = val.replace(" ✅", "").replace(" ⚠️", "").replace(" 🔥", "")

        h, m = map(int, val.split(":"))
        minutes = h * 60 + m
    except:
        return ""

    if minutes <= safe:
        return "color: #28a745; font-weight: bold;"
    elif minutes <= warning:
        return "color: #ffc107; font-weight: bold;"
    else:
        return "color: #dc3545; font-weight: bold;"

def get_sla_minutes(val):
    try:
        val = val.replace(" ✅", "").replace(" ⚠️", "").replace(" 🔥", "")
        h, m = map(int, val.split(":"))
        return h * 60 + m
    except:
        return 0


def add_icon(val, safe, warning):
    if not val:
        return val

    minutes = get_sla_minutes(val)

    if minutes <= safe:
        return f"{val} ✅"
    elif minutes <= warning:
        return f"{val} ⚠️"
    else:
        return f"{val} 🔥"
    
def highlight_tt(val):
    try:
        val = int(val)
    except:
        return ""

    if val <= 50:
        return "color: #28a745; background-color: rgba(40,167,69,0.15); font-weight: bold;"
    elif val <= 70:
        return "color: #ffc107; background-color: rgba(255,193,7,0.15); font-weight: bold;"
    else:
        return "color: #dc3545; background-color: rgba(220,53,69,0.15); font-weight: bold;"