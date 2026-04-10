import sqlite3
import os
import datetime
from collections import Counter
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from reportlab.lib.pagesizes import A4
from reportlab.platypus import Image, SimpleDocTemplate, Paragraph, Spacer, Table
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

try:
    con = sqlite3.connect('soc.db')
    c = con.cursor()
    c.execute("SELECT ip,attack,severity,risk,time,ai_analysis,source FROM logs ORDER BY id DESC LIMIT 500")
    logs = c.fetchall()
    con.close()
    
    report_dir = os.path.join(os.getcwd(), "reports")
    os.makedirs(report_dir, exist_ok=True)

    sev_count = Counter([l[2] for l in logs])
    plt.figure()
    plt.pie(sev_count.values(), labels=sev_count.keys(), autopct="%1.1f%%", colors=["red", "orange", "green"])
    plt.title("Severity Distribution")
    plt.savefig(os.path.join(report_dir, "severity.png"))
    plt.close()

    atk_count = Counter([l[1] for l in logs])
    top_5_atk = dict(atk_count.most_common(5))
    plt.figure(figsize=(6, 4))
    plt.bar(top_5_atk.keys(), top_5_atk.values(), color="#2563eb")
    plt.xticks(rotation=25, ha="right", fontsize=8)
    plt.title("Top Threat Vectors", fontweight="bold")
    plt.tight_layout()
    plt.savefig(os.path.join(report_dir, "attacks.png"))
    plt.close()

    critical_count = len([l for l in logs if l[2] in ["High", "Critical"]])
    ai_remediated = len([l for l in logs if l[5] and "Pending" not in l[5] and "Routine" not in l[5]])

    ips = [l[0] for l in logs]
    attacks = [l[1] for l in logs]
    risks = [(l[0], l[3]) for l in logs]
    sources = [l[6] for l in logs]

    top_attack = Counter(attacks).most_common(1)[0][0] if attacks else "N/A"
    top_ip = Counter(ips).most_common(1)[0][0] if ips else "N/A"
    top_source = Counter(sources).most_common(1)[0][0] if sources else "N/A"

    highest_risk_ip = max(risks, key=lambda x: x[1])[0] if risks else "N/A"
    highest_risk_score = max((l[3] for l in logs), default=0)

    times = [l[4][:13] if l[4] else "Unknown" for l in logs]
    peak_time = Counter(times).most_common(1)[0][0] + ":00" if times else "N/A"

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('TitleStyle', parent=styles['Heading1'], fontSize=24, spaceAfter=20, textColor=colors.HexColor("#0f172a"))
    sub_style = ParagraphStyle('SubStyle', parent=styles['Normal'], fontSize=12, textColor=colors.gray, spaceAfter=20)
    exec_style = ParagraphStyle('ExecStyle', parent=styles['Normal'], fontSize=11, leading=16)

    filename = os.path.join(report_dir, "SOC_Report.pdf")

    doc = SimpleDocTemplate(filename, pagesize=A4, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
    elements=[]
    elements.append(Paragraph("<b>CCL Guard Executive Threat Report</b>", title_style))
    elements.append(Paragraph(f"AI-Driven SOC Intelligence & Network Telemetry<br/>Generated: {datetime.datetime.now().strftime('%B %d, %Y at %H:%M')}<br/>Report ID: GUARD-{datetime.datetime.now().strftime('%Y%m%d%H%M')}", sub_style))
    elements.append(Spacer(1,10))
    elements.append(Paragraph(f"""<b>EXECUTIVE SUMMARY</b><br/>...""", exec_style))
    elements.append(Spacer(1, 15))
    img1 = Image(os.path.join(report_dir, "severity.png"), width=220, height=180)
    img2 = Image(os.path.join(report_dir, "attacks.png"), width=280, height=180)
    chart_table = Table([[img1, img2]], colWidths=[240, 300])
    elements.append(chart_table)
    elements.append(Spacer(1,15))
    
    doc.build(elements)
    print("SUCCESS")
except Exception as e:
    import traceback
    traceback.print_exc()
