from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table,
                                 TableStyle, HRFlowable, PageBreak, KeepTogether)
from reportlab.lib.enums import TA_CENTER, TA_LEFT

doc = SimpleDocTemplate(
    "/mnt/user-data/outputs/MYLIFE_UML_Diagrams_Guide.pdf",
    pagesize=A4,
    rightMargin=18*mm, leftMargin=18*mm,
    topMargin=18*mm, bottomMargin=18*mm
)

W, H = A4
styles = getSampleStyleSheet()

# Colors
DARK_BLUE   = colors.HexColor("#0D2B45")
MID_BLUE    = colors.HexColor("#1A5276")
LIGHT_BLUE  = colors.HexColor("#2E86C1")
ACCENT_GRN  = colors.HexColor("#1E8449")
ACCENT_PRP  = colors.HexColor("#6C3483")
ACCENT_ORG  = colors.HexColor("#B7770D")
ACCENT_RED  = colors.HexColor("#922B21")
LIGHT_GRAY  = colors.HexColor("#F4F6F9")
MID_GRAY    = colors.HexColor("#D5D8DC")
TEXT        = colors.HexColor("#1C2833")
WHITE       = colors.white

PAGE_W = doc.width

def S(n): return Spacer(1, n*mm)

def style(name, **kw):
    base = kw.pop("parent", styles["Normal"])
    return ParagraphStyle(name, parent=base, **kw)

title_s  = style("T", fontSize=28, textColor=WHITE, alignment=TA_CENTER, fontName="Helvetica-Bold", spaceAfter=3)
sub_s    = style("Sub", fontSize=12, textColor=colors.HexColor("#AED6F1"), alignment=TA_CENTER, fontName="Helvetica", spaceAfter=2)
body_s   = style("B", fontSize=10, textColor=TEXT, leading=16, spaceAfter=3)
bullet_s = style("Bl", fontSize=10, textColor=TEXT, leading=15, spaceAfter=2, leftIndent=14, bulletIndent=4)
code_s   = style("C", fontSize=9, textColor=colors.HexColor("#1A1A2E"), fontName="Courier",
                 leading=14, spaceAfter=1, backColor=colors.HexColor("#EAF0FB"),
                 leftIndent=6, rightIndent=6, borderPad=3)
label_s  = style("L", fontSize=10, textColor=WHITE, fontName="Helvetica-Bold", spaceAfter=0, alignment=TA_CENTER)
note_s   = style("N", fontSize=9, textColor=colors.HexColor("#5D6D7E"), leading=13, spaceAfter=2, leftIndent=10)

def section_header(text, color=MID_BLUE, diagram_num=None):
    prefix = f"Diagram {diagram_num}  ·  " if diagram_num else ""
    return [
        S(3),
        Table([[Paragraph(f"{prefix}{text}", style("SH", fontSize=14, textColor=WHITE,
                fontName="Helvetica-Bold", spaceAfter=0, spaceBefore=0))]],
              colWidths=[PAGE_W],
              style=TableStyle([
                  ("BACKGROUND",(0,0),(-1,-1), color),
                  ("TOPPADDING",(0,0),(-1,-1),9),
                  ("BOTTOMPADDING",(0,0),(-1,-1),9),
                  ("LEFTPADDING",(0,0),(-1,-1),12),
              ])),
        S(3),
    ]

def box_table(rows, left_color=MID_BLUE):
    data = []
    for lbl, val in rows:
        if isinstance(val, list):
            val_cell = val
        else:
            val_cell = Paragraph(val, body_s)
        data.append([
            Paragraph(lbl, style("BL", fontSize=9, textColor=WHITE, fontName="Helvetica-Bold",
                spaceAfter=0, alignment=TA_CENTER)),
            val_cell,
        ])
    return Table(data, colWidths=[PAGE_W*0.20, PAGE_W*0.80],
        style=TableStyle([
            ("BACKGROUND",(0,0),(0,-1), left_color),
            ("BACKGROUND",(1,0),(1,-1), LIGHT_GRAY),
            ("GRID",(0,0),(-1,-1),0.5, MID_GRAY),
            ("VALIGN",(0,0),(-1,-1),"TOP"),
            ("TOPPADDING",(0,0),(-1,-1),7),
            ("BOTTOMPADDING",(0,0),(-1,-1),7),
            ("LEFTPADDING",(0,0),(-1,-1),8),
        ]))

def two_col(left, right, lh="Left", rh="Right", lc=MID_BLUE, rc=MID_BLUE):
    def cell(items):
        return [Paragraph(f"• {i}", bullet_s) for i in items]
    data = [
        [Paragraph(lh, label_s), Paragraph(rh, label_s)],
        [cell(left), cell(right)],
    ]
    return Table(data, colWidths=[PAGE_W/2 - 2, PAGE_W/2 - 2],
        style=TableStyle([
            ("BACKGROUND",(0,0),(0,0), lc),
            ("BACKGROUND",(1,0),(1,0), rc),
            ("BACKGROUND",(0,1),(0,1), LIGHT_GRAY),
            ("BACKGROUND",(1,1),(1,1), colors.HexColor("#F9F9F9")),
            ("GRID",(0,0),(-1,-1),0.5, MID_GRAY),
            ("VALIGN",(0,0),(-1,-1),"TOP"),
            ("TOPPADDING",(0,0),(-1,-1),7),
            ("BOTTOMPADDING",(0,0),(-1,-1),7),
            ("LEFTPADDING",(0,0),(-1,-1),8),
        ]))

def code_block(text):
    return Table([[Paragraph(text, code_s)]], colWidths=[PAGE_W],
        style=TableStyle([
            ("BACKGROUND",(0,0),(-1,-1), colors.HexColor("#EAF0FB")),
            ("GRID",(0,0),(-1,-1),0.5, MID_GRAY),
            ("TOPPADDING",(0,0),(-1,-1),10),
            ("BOTTOMPADDING",(0,0),(-1,-1),10),
            ("LEFTPADDING",(0,0),(-1,-1),10),
        ]))

def tip_box(text, color=colors.HexColor("#EAF4FB")):
    return Table([[Paragraph(f"💡  {text}", note_s)]], colWidths=[PAGE_W],
        style=TableStyle([
            ("BACKGROUND",(0,0),(-1,-1), color),
            ("GRID",(0,0),(-1,-1),0.5, colors.HexColor("#AED6F1")),
            ("TOPPADDING",(0,0),(-1,-1),7),
            ("BOTTOMPADDING",(0,0),(-1,-1),7),
            ("LEFTPADDING",(0,0),(-1,-1),10),
        ]))

# ═══════════════════════════════════════════════════════
story = []

# ── COVER ──────────────────────────────────────────────
story.append(Table([[
    Paragraph("MYLIFE", title_s),
    Paragraph("UML Diagrams — Design Guide", sub_s),
    S(2),
    Paragraph("4 Diagrams · Component · Sequence · Use Case · Deployment", style("C3",
        fontSize=11, textColor=colors.HexColor("#85C1E9"), alignment=TA_CENTER)),
    S(1),
    Paragraph("Everything you need to draw each diagram correctly", style("C4",
        fontSize=10, textColor=colors.HexColor("#AED6F1"), alignment=TA_CENTER)),
]], colWidths=[PAGE_W],
    style=TableStyle([
        ("BACKGROUND",(0,0),(-1,-1), DARK_BLUE),
        ("TOPPADDING",(0,0),(-1,-1),14),
        ("BOTTOMPADDING",(0,0),(-1,-1),14),
        ("LEFTPADDING",(0,0),(-1,-1),10),
    ])))
story.append(S(5))

story.append(Paragraph(
    "This guide gives you the exact elements, notation rules, layout tips, and "
    "text labels to draw all 4 UML diagrams for MYLIFE. Use any tool — "
    "<b>draw.io, Lucidchart, PlantUML, StarUML, or pen and paper.</b>", body_s))
story.append(S(2))

# Quick index
idx = [["#", "Diagram", "Tool Recommended", "Difficulty"],
       ["1", "Component Diagram", "draw.io / Lucidchart", "Medium"],
       ["2", "Sequence Diagram", "PlantUML / draw.io", "Medium"],
       ["3", "Use Case Diagram", "draw.io / StarUML", "Easy"],
       ["4", "Deployment Diagram", "draw.io / Lucidchart", "Medium"],]
story.append(Table(idx, colWidths=[PAGE_W*0.06, PAGE_W*0.34, PAGE_W*0.35, PAGE_W*0.25],
    style=TableStyle([
        ("BACKGROUND",(0,0),(-1,0), DARK_BLUE),
        ("TEXTCOLOR",(0,0),(-1,0), WHITE),
        ("FONTNAME",(0,0),(-1,0),"Helvetica-Bold"),
        ("FONTSIZE",(0,0),(-1,-1), 10),
        ("ROWBACKGROUNDS",(0,1),(-1,-1), [LIGHT_GRAY, WHITE]),
        ("GRID",(0,0),(-1,-1),0.5, MID_GRAY),
        ("TOPPADDING",(0,0),(-1,-1),6),("BOTTOMPADDING",(0,0),(-1,-1),6),
        ("LEFTPADDING",(0,0),(-1,-1),8),
        ("ALIGN",(0,0),(0,-1),"CENTER"),
    ])))
story.append(PageBreak())

# ═══════════════════════════════════════════════════════
# DIAGRAM 1 — COMPONENT DIAGRAM
# ═══════════════════════════════════════════════════════
story += section_header("Component Diagram", DARK_BLUE, "1")
story.append(Paragraph(
    "<b>Purpose:</b> Shows the software components of MYLIFE and how they are connected. "
    "Think of it as a bird's-eye view of the system's building blocks.", body_s))
story.append(S(2))

story.append(Paragraph("What is a Component Diagram?", style("H2", fontSize=12, textColor=MID_BLUE, fontName="Helvetica-Bold", spaceAfter=3)))
story.append(Paragraph(
    "A Component Diagram shows <b>what parts exist</b> in the system and <b>how they talk to each other</b>. "
    "Each box is a component (frontend, service, database). Lines/arrows show communication.", body_s))
story.append(S(2))

story.append(Paragraph("Components to Draw (12 total)", style("H2", fontSize=12, textColor=MID_BLUE, fontName="Helvetica-Bold", spaceAfter=3)))

comp_rows = [
    ("React Frontend", "«component»\nLabel: React Frontend\nNote: Runs in user's browser. Sends HTTP requests to API Gateway."),
    ("API Gateway", "«component»\nLabel: API Gateway (NGINX)\nNote: Single entry point. Routes /auth→8001, /records→8002, /family→8003, /ai→8004, /notify→8005"),
    ("Auth Service", "«component»\nLabel: Auth Service\nPort: 8001\nNote: Handles login, JWT, roles."),
    ("Medical Records Service", "«component»\nLabel: Medical Records Service\nPort: 8002\nNote: Core records, QR sharing, emergency profile."),
    ("Family & Profile Service", "«component»\nLabel: Family & Profile Service\nPort: 8003\nNote: Family links, women's health tracking."),
    ("AI Processing Service", "«component»\nLabel: AI Processing Service\nPort: 8004\nNote: Calls Claude API, extracts medical data."),
    ("Notification Service", "«component»\nLabel: Notification Service\nPort: 8005\nNote: Sends email/push alerts."),
    ("Supabase PostgreSQL", "«database»\nLabel: Supabase PostgreSQL\nNote: 5 schemas — auth, medical, family, ai, notification."),
    ("Supabase Storage", "«component»\nLabel: Supabase Storage\nNote: Stores uploaded PDF and image files."),
    ("Supabase Auth", "«component»\nLabel: Supabase Auth\nNote: Manages JWT issue & session storage."),
    ("Claude API", "«external system»\nLabel: Claude API (Anthropic)\nNote: External AI. Receives document, returns extracted data."),
    ("Email / Push Provider", "«external system»\nLabel: SendGrid / Firebase FCM\nNote: External email and push notification delivery."),
]
for lbl, val in comp_rows:
    story.append(KeepTogether([
        Paragraph(f"<b>{lbl}</b>", style("CL", fontSize=10, textColor=MID_BLUE, fontName="Helvetica-Bold", spaceAfter=1)),
        code_block(val),
        S(1),
    ]))

story.append(S(2))
story.append(Paragraph("Connections to Draw (arrows)", style("H2", fontSize=12, textColor=MID_BLUE, fontName="Helvetica-Bold", spaceAfter=3)))

conn_rows = [
    ["React Frontend → API Gateway", "REST HTTP", "All user requests go here first"],
    ["API Gateway → Auth Service", "REST HTTP", "Routes /auth/* requests"],
    ["API Gateway → Medical Records Service", "REST HTTP", "Routes /records/* requests"],
    ["API Gateway → Family & Profile Service", "REST HTTP", "Routes /family/* and /health/* requests"],
    ["API Gateway → AI Processing Service", "REST HTTP", "Routes /ai/* requests"],
    ["API Gateway → Notification Service", "REST HTTP", "Routes /notify/* requests"],
    ["Medical Records Service → Auth Service", "REST HTTP", "Validate JWT token"],
    ["Medical Records Service → AI Processing Service", "REST HTTP", "Send file for extraction"],
    ["Medical Records Service → Notification Service", "REST HTTP", "Trigger upload notification"],
    ["AI Processing Service → Claude API", "HTTPS REST", "Send document for AI extraction"],
    ["AI Processing Service → Notification Service", "REST HTTP", "Trigger completion notification"],
    ["Notification Service → SendGrid / FCM", "HTTPS REST", "Deliver email/push"],
    ["All 5 Services → Supabase PostgreSQL", "SQL / Supabase SDK", "Each reads its own schema only"],
    ["Medical Records Service → Supabase Storage", "Supabase SDK", "Upload/download medical files"],
    ["Auth Service → Supabase Auth", "Supabase SDK", "JWT issue and session management"],
]
conn_data = [[Paragraph(h, label_s) for h in ["From → To", "Protocol", "Why"]]] + \
            [[Paragraph(r[i], body_s if i>0 else code_s) for i in range(3)] for r in conn_rows]
story.append(Table(conn_data, colWidths=[PAGE_W*0.36, PAGE_W*0.20, PAGE_W*0.44],
    style=TableStyle([
        ("BACKGROUND",(0,0),(-1,0), MID_BLUE),
        ("ROWBACKGROUNDS",(0,1),(-1,-1),[LIGHT_GRAY, WHITE]),
        ("GRID",(0,0),(-1,-1),0.5,MID_GRAY),
        ("TOPPADDING",(0,0),(-1,-1),5),("BOTTOMPADDING",(0,0),(-1,-1),5),
        ("LEFTPADDING",(0,0),(-1,-1),6),("VALIGN",(0,0),(-1,-1),"TOP"),
    ])))
story.append(S(3))

story.append(Paragraph("Layout Tips", style("H2", fontSize=12, textColor=MID_BLUE, fontName="Helvetica-Bold", spaceAfter=3)))
story.append(code_block(
"""LAYOUT (top → bottom, 4 rows):

Row 1:  [ React Frontend ]
Row 2:  [ API Gateway ]
Row 3:  [ Auth ] [ Medical ] [ Family ] [ AI ] [ Notification ]
Row 4:  [ Supabase Auth ] [ Supabase PostgreSQL ] [ Supabase Storage ] [ Claude API ] [ SendGrid/FCM ]

Group Row 3 in a dashed box labeled: "MYLIFE Microservices (Docker)"
Group Row 4 external systems in a dashed box labeled: "External / Managed Services"

Arrow style: solid line with open arrowhead for REST, dashed line for database connections.
Label each arrow with the protocol: REST, SQL, HTTPS."""))
story.append(S(2))
story.append(tip_box("In draw.io: use the 'UML' shape library. Components use the component shape (box with two small tabs on the left side). Databases use a cylinder shape. External systems use a box with a shaded header."))

story.append(PageBreak())

# ═══════════════════════════════════════════════════════
# DIAGRAM 2 — SEQUENCE DIAGRAM
# ═══════════════════════════════════════════════════════
story += section_header("Sequence Diagram", ACCENT_GRN, "2")
story.append(Paragraph(
    "<b>Purpose:</b> Shows the step-by-step message flow for one specific action — "
    "how components interact over time. We'll diagram the most important flow: "
    "<b>Patient uploads and processes a medical record.</b>", body_s))
story.append(S(2))

story.append(Paragraph("What is a Sequence Diagram?", style("H2", fontSize=12, textColor=ACCENT_GRN, fontName="Helvetica-Bold", spaceAfter=3)))
story.append(Paragraph(
    "Actors/components are shown as columns (lifelines) across the top. "
    "Time goes downward. Messages are horizontal arrows between lifelines. "
    "Each arrow has a label describing what is sent.", body_s))
story.append(S(2))

story.append(Paragraph("Lifelines (Columns) — Draw These Across the Top", style("H2", fontSize=12, textColor=ACCENT_GRN, fontName="Helvetica-Bold", spaceAfter=3)))
lifelines = [
    ["1", "Patient", "The person using the app. Not a system — draw as a stick figure or actor box."],
    ["2", "React Frontend", "The browser/app. Sends requests, shows responses."],
    ["3", "API Gateway", "NGINX router. Forwards requests to correct service."],
    ["4", "Auth Service", "Validates the JWT token."],
    ["5", "Medical Records Service", "Stores the record, coordinates the flow."],
    ["6", "AI Processing Service", "Extracts data from the document."],
    ["7", "Claude API", "External AI — returns structured extraction."],
    ["8", "Notification Service", "Sends the completion email."],
    ["9", "Supabase PostgreSQL", "Database — stores metadata and extraction results."],
    ["10", "Supabase Storage", "File storage — holds the uploaded PDF/image."],
]
ll_data = [[Paragraph(h, label_s) for h in ["#","Lifeline Name","Description"]]] + \
          [[Paragraph(r[i], body_s) for i in range(3)] for r in lifelines]
story.append(Table(ll_data, colWidths=[PAGE_W*0.05, PAGE_W*0.25, PAGE_W*0.70],
    style=TableStyle([
        ("BACKGROUND",(0,0),(-1,0), ACCENT_GRN),
        ("ROWBACKGROUNDS",(0,1),(-1,-1),[LIGHT_GRAY, WHITE]),
        ("GRID",(0,0),(-1,-1),0.5,MID_GRAY),
        ("TOPPADDING",(0,0),(-1,-1),5),("BOTTOMPADDING",(0,0),(-1,-1),5),
        ("LEFTPADDING",(0,0),(-1,-1),6),("VALIGN",(0,0),(-1,-1),"TOP"),
        ("ALIGN",(0,0),(0,-1),"CENTER"),
    ])))
story.append(S(3))

story.append(Paragraph("Message Sequence — Draw These as Arrows", style("H2", fontSize=12, textColor=ACCENT_GRN, fontName="Helvetica-Bold", spaceAfter=3)))

seq_rows = [
    ["1", "Patient → Frontend", "→ solid", "User selects PDF file and clicks Upload"],
    ["2", "Frontend → API Gateway", "→ solid", "POST /records  {file, JWT token, metadata}"],
    ["3", "API Gateway → Medical Records Service", "→ solid", "Forward: POST /records"],
    ["4", "Medical Records Service → Auth Service", "→ solid", "GET /auth/validate  {JWT token}"],
    ["5", "Auth Service → Medical Records Service", "← dashed", "200 OK  {userId, role: PATIENT}"],
    ["6", "Medical Records Service → Supabase Storage", "→ solid", "upload(file) → returns fileUrl"],
    ["7", "Supabase Storage → Medical Records Service", "← dashed", "fileUrl: 'storage.supabase.co/...'"],
    ["8", "Medical Records Service → Supabase PostgreSQL", "→ solid", "INSERT INTO medical_schema.medical_records {userId, fileUrl, status:'processing'}"],
    ["9", "Supabase PostgreSQL → Medical Records Service", "← dashed", "recordId: 'rec_001'"],
    ["10", "Medical Records Service → AI Processing Service", "→ solid", "POST /ai/process  {fileUrl, recordId}"],
    ["11", "Medical Records Service → Frontend", "← dashed", "202 Accepted  {recordId, status:'processing'}"],
    ["12", "Frontend → Patient", "display", "Show: 'Upload successful, processing...'"],
    ["13", "AI Processing Service → Claude API", "→ solid", "POST /v1/messages  {document, prompt: extract medical data}"],
    ["14", "Claude API → AI Processing Service", "← dashed", "200 OK  {diagnosis, medications, dates, summary}"],
    ["15", "AI Processing Service → Supabase PostgreSQL", "→ solid", "INSERT INTO ai_schema.extracted_reports {recordId, extractedData}"],
    ["16", "AI Processing Service → Medical Records Service", "→ solid", "PATCH /records/rec_001  {status:'verified', extractionId}"],
    ["17", "Medical Records Service → Supabase PostgreSQL", "→ solid", "UPDATE medical_records SET status='verified'"],
    ["18", "AI Processing Service → Notification Service", "→ solid", "POST /notify/email  {userId, message:'Your record is ready'}"],
    ["19", "Notification Service → Patient (email)", "→ solid", "Email: 'MYLIFE: Your medical record has been processed'"],
    ["20", "Patient → Frontend", "→ solid", "Patient opens app, clicks on record"],
    ["21", "Frontend → API Gateway", "→ solid", "GET /records/rec_001  {JWT}"],
    ["22", "API Gateway → Medical Records Service", "→ solid", "Forward: GET /records/rec_001"],
    ["23", "Medical Records Service → Supabase PostgreSQL", "→ solid", "SELECT * FROM medical_records + extracted_reports WHERE id='rec_001'"],
    ["24", "Supabase PostgreSQL → Medical Records Service", "← dashed", "Full record + AI extraction data"],
    ["25", "Medical Records Service → Frontend", "← dashed", "200 OK  {record, summary, status:'verified'}"],
    ["26", "Frontend → Patient", "display", "Show: Verified medical record with AI summary"],
]
sq_data = [[Paragraph(h, label_s) for h in ["#","From → To","Arrow","Message Label"]]] + \
          [[Paragraph(r[i], code_s if i in [2,3] else body_s) for i in range(4)] for r in seq_rows]
story.append(Table(sq_data, colWidths=[PAGE_W*0.05, PAGE_W*0.30, PAGE_W*0.12, PAGE_W*0.53],
    style=TableStyle([
        ("BACKGROUND",(0,0),(-1,0), ACCENT_GRN),
        ("ROWBACKGROUNDS",(0,1),(-1,-1),[LIGHT_GRAY, WHITE]),
        ("GRID",(0,0),(-1,-1),0.5,MID_GRAY),
        ("TOPPADDING",(0,0),(-1,-1),4),("BOTTOMPADDING",(0,0),(-1,-1),4),
        ("LEFTPADDING",(0,0),(-1,-1),5),("VALIGN",(0,0),(-1,-1),"TOP"),
        ("ALIGN",(0,0),(0,-1),"CENTER"),
    ])))
story.append(S(3))

story.append(Paragraph("UML Notation Rules for Sequence Diagram", style("H2", fontSize=12, textColor=ACCENT_GRN, fontName="Helvetica-Bold", spaceAfter=3)))
story.append(code_block(
"""Arrow types:
  →  solid filled arrow  =  synchronous call (sender waits for response)
  ←  dashed open arrow   =  return message / response
  →  solid thin arrow    =  asynchronous message (fire and forget)

Activation boxes:
  Draw a thin rectangle on each lifeline when that component is actively working.
  Start box when it receives a message, end box when it returns.

Alt/Opt frames (optional but good):
  Wrap steps 4-5 in an [alt] frame labeled:
    [token valid] → continue
    [token invalid] → return 401 Unauthorized

Numbering:
  Number each arrow 1, 2, 3... as listed above."""))
story.append(S(2))
story.append(tip_box("In PlantUML you can generate this automatically. In draw.io, use the 'Sequence' diagram template. Place all lifelines first, then draw arrows top-to-bottom."))

story.append(PageBreak())

# ═══════════════════════════════════════════════════════
# DIAGRAM 3 — USE CASE DIAGRAM
# ═══════════════════════════════════════════════════════
story += section_header("Use Case Diagram", ACCENT_PRP, "3")
story.append(Paragraph(
    "<b>Purpose:</b> Shows WHO uses the system and WHAT they can do. "
    "No technical details — just actors and their actions.", body_s))
story.append(S(2))

story.append(Paragraph("What is a Use Case Diagram?", style("H2", fontSize=12, textColor=ACCENT_PRP, fontName="Helvetica-Bold", spaceAfter=3)))
story.append(Paragraph(
    "Actors (stick figures) are outside the system boundary box. "
    "Use cases (ovals) are inside the box. Lines connect actors to the use cases they perform. "
    "«include» and «extend» show relationships between use cases.", body_s))
story.append(S(2))

story.append(Paragraph("Actors — Draw as Stick Figures", style("H2", fontSize=12, textColor=ACCENT_PRP, fontName="Helvetica-Bold", spaceAfter=3)))
actors = [
    ["Patient", "Primary user. Can do most things — upload, view, share records."],
    ["Doctor", "Verified medical professional. Can verify records and view shared records."],
    ["Family Member", "Linked account. Can view records of family they are linked to (with permission)."],
    ["Admin", "Platform administrator. Manages users, doctors, and system health."],
]
act_data = [[Paragraph(h, label_s) for h in ["Actor","Description"]]] + \
           [[Paragraph(r[i], body_s) for i in range(2)] for r in actors]
story.append(Table(act_data, colWidths=[PAGE_W*0.25, PAGE_W*0.75],
    style=TableStyle([
        ("BACKGROUND",(0,0),(-1,0), ACCENT_PRP),
        ("ROWBACKGROUNDS",(0,1),(-1,-1),[LIGHT_GRAY, WHITE]),
        ("GRID",(0,0),(-1,-1),0.5,MID_GRAY),
        ("TOPPADDING",(0,0),(-1,-1),6),("BOTTOMPADDING",(0,0),(-1,-1),6),
        ("LEFTPADDING",(0,0),(-1,-1),8),("VALIGN",(0,0),(-1,-1),"TOP"),
    ])))
story.append(S(3))

story.append(Paragraph("Use Cases — Draw as Ovals Inside the System Box", style("H2", fontSize=12, textColor=ACCENT_PRP, fontName="Helvetica-Bold", spaceAfter=3)))
usecases = [
    ["UC01", "Register / Login", "Patient, Doctor, Family Member, Admin", "Auth Service"],
    ["UC02", "Upload Medical Record", "Patient", "Medical Records Service"],
    ["UC03", "View Medical Records", "Patient, Doctor, Family Member", "Medical Records Service"],
    ["UC04", "Share Record via QR Code", "Patient", "Medical Records Service"],
    ["UC05", "Delete Medical Record", "Patient", "Medical Records Service"],
    ["UC06", "Verify Medical Record", "Doctor", "Medical Records Service + Auth Service"],
    ["UC07", "Trigger Emergency Mode", "Patient", "Medical Records Service"],
    ["UC08", "View Emergency Profile", "Doctor, Family Member", "Medical Records Service"],
    ["UC09", "Link Family Account", "Patient", "Family & Profile Service"],
    ["UC10", "Manage Family Permissions", "Patient", "Family & Profile Service"],
    ["UC11", "Track Menstrual Cycle", "Patient", "Family & Profile Service"],
    ["UC12", "Track Pregnancy", "Patient", "Family & Profile Service"],
    ["UC13", "Process Document with AI", "Patient (auto-triggered)", "AI Processing Service"],
    ["UC14", "Receive Notifications", "Patient, Doctor, Family Member", "Notification Service"],
    ["UC15", "Manage Users", "Admin", "Auth Service"],
    ["UC16", "Update Profile", "Patient, Doctor", "Auth Service"],
]
uc_data = [[Paragraph(h, label_s) for h in ["ID","Use Case Name","Actor(s)","Handled By"]]] + \
          [[Paragraph(r[i], body_s) for i in range(4)] for r in usecases]
story.append(Table(uc_data, colWidths=[PAGE_W*0.08, PAGE_W*0.28, PAGE_W*0.30, PAGE_W*0.34],
    style=TableStyle([
        ("BACKGROUND",(0,0),(-1,0), ACCENT_PRP),
        ("ROWBACKGROUNDS",(0,1),(-1,-1),[LIGHT_GRAY, WHITE]),
        ("GRID",(0,0),(-1,-1),0.5,MID_GRAY),
        ("TOPPADDING",(0,0),(-1,-1),5),("BOTTOMPADDING",(0,0),(-1,-1),5),
        ("LEFTPADDING",(0,0),(-1,-1),6),("VALIGN",(0,0),(-1,-1),"TOP"),
        ("ALIGN",(0,0),(0,-1),"CENTER"),
    ])))
story.append(S(3))

story.append(Paragraph("Include & Extend Relationships", style("H2", fontSize=12, textColor=ACCENT_PRP, fontName="Helvetica-Bold", spaceAfter=3)))
story.append(code_block(
"""«include» — one use case always requires another:
  UC02 Upload Medical Record  «include»  UC01 Register / Login
  UC03 View Medical Records   «include»  UC01 Register / Login
  UC04 Share via QR           «include»  UC02 Upload Medical Record
  UC06 Verify Record          «include»  UC01 Register / Login
  UC13 AI Processing          «include»  UC02 Upload Medical Record

«extend» — one use case optionally extends another:
  UC07 Emergency Mode         «extend»   UC03 View Medical Records
  UC08 View Emergency Profile «extend»   UC03 View Medical Records
  UC14 Receive Notifications  «extend»   UC02, UC06, UC13 (any event)

Draw these as dashed arrows with the label «include» or «extend»."""))
story.append(S(2))

story.append(Paragraph("Layout Tips", style("H2", fontSize=12, textColor=ACCENT_PRP, fontName="Helvetica-Bold", spaceAfter=3)))
story.append(code_block(
"""LAYOUT:

  [Patient] ───── UC01 Register/Login
                  UC02 Upload Record ────── [Doctor] (verify)
                  UC03 View Records  ────── [Family Member]
                  UC04 Share via QR
                  UC07 Emergency Mode
                  UC09 Link Family
                  UC11 Cycle Tracking
                  UC12 Pregnancy Tracking

  [Admin] ──────  UC15 Manage Users

  Place actors on LEFT (Patient, Family Member) and RIGHT (Doctor, Admin).
  System boundary box label: "MYLIFE Healthcare Platform"
  Group related use cases with a comment label e.g. "Health Tracking" cluster."""))
story.append(S(2))
story.append(tip_box("Keep it clean — don't draw lines from every actor to every use case. Only draw the connection if that actor directly triggers that use case.", colors.HexColor("#F4ECF7")))

story.append(PageBreak())

# ═══════════════════════════════════════════════════════
# DIAGRAM 4 — DEPLOYMENT DIAGRAM
# ═══════════════════════════════════════════════════════
story += section_header("Deployment Diagram", ACCENT_RED, "4")
story.append(Paragraph(
    "<b>Purpose:</b> Shows where each component physically runs — servers, containers, "
    "cloud services, and user devices. Shows the infrastructure, not the code.", body_s))
story.append(S(2))

story.append(Paragraph("What is a Deployment Diagram?", style("H2", fontSize=12, textColor=ACCENT_RED, fontName="Helvetica-Bold", spaceAfter=3)))
story.append(Paragraph(
    "Nodes are physical or virtual machines (servers, devices, cloud services). "
    "Artifacts are what runs on them (Docker containers, apps, databases). "
    "Lines show communication paths between nodes.", body_s))
story.append(S(2))

story.append(Paragraph("Nodes and What Runs on Them", style("H2", fontSize=12, textColor=ACCENT_RED, fontName="Helvetica-Bold", spaceAfter=3)))
nodes = [
    ["User Device\n(Client Node)", "«device»", "Web Browser or Mobile App\nArtifact: React Frontend App (SPA)"],
    ["Vercel CDN\n(Cloud Node)", "«cloud»", "Artifact: React Frontend Build\nNote: Auto-deployed from GitHub. Serves static files globally."],
    ["Railway / Render\nServer (Cloud Node)", "«server»",
     "Docker Container: NGINX API Gateway\nDocker Container: Auth Service (Python/FastAPI, port 8001)\nDocker Container: Medical Records Service (Python/FastAPI, port 8002)\nDocker Container: Family & Profile Service (Python/FastAPI, port 8003)\nDocker Container: AI Processing Service (Python/FastAPI, port 8004)\nDocker Container: Notification Service (Python/FastAPI, port 8005)"],
    ["Supabase Cloud\n(Managed Node)", "«cloud»",
     "Artifact: PostgreSQL Database (5 schemas)\nArtifact: Supabase Auth (JWT management)\nArtifact: Supabase Storage (medical files)"],
    ["Anthropic Cloud\n(External Node)", "«external system»", "Artifact: Claude API\nNote: Receives document, returns structured AI extraction."],
    ["SendGrid / Firebase\n(External Node)", "«external system»", "Artifact: Email Delivery Service (SendGrid)\nArtifact: Push Notification Service (Firebase FCM)"],
    ["GitHub\n(DevOps Node)", "«cloud»", "Artifact: Source Code Repository\nArtifact: GitHub Actions CI/CD Pipeline"],
]
nd_data = [[Paragraph(h, label_s) for h in ["Node Name","UML Stereotype","Artifacts / Services Running"]]] + \
          [[Paragraph(r[i], code_s if i==1 else body_s) for i in range(3)] for r in nodes]
story.append(Table(nd_data, colWidths=[PAGE_W*0.22, PAGE_W*0.15, PAGE_W*0.63],
    style=TableStyle([
        ("BACKGROUND",(0,0),(-1,0), ACCENT_RED),
        ("ROWBACKGROUNDS",(0,1),(-1,-1),[LIGHT_GRAY, WHITE]),
        ("GRID",(0,0),(-1,-1),0.5,MID_GRAY),
        ("TOPPADDING",(0,0),(-1,-1),6),("BOTTOMPADDING",(0,0),(-1,-1),6),
        ("LEFTPADDING",(0,0),(-1,-1),6),("VALIGN",(0,0),(-1,-1),"TOP"),
    ])))
story.append(S(3))

story.append(Paragraph("Communication Paths (Lines Between Nodes)", style("H2", fontSize=12, textColor=ACCENT_RED, fontName="Helvetica-Bold", spaceAfter=3)))
comm_rows = [
    ["User Device → Vercel CDN", "HTTPS", "Load the React app"],
    ["User Device → Railway Server (API Gateway)", "HTTPS REST", "All API calls"],
    ["Railway (API Gateway) → Railway (5 Services)", "HTTP internal", "Internal Docker network routing"],
    ["Railway (Auth Service) → Supabase Cloud", "HTTPS / Supabase SDK", "JWT validation, user data"],
    ["Railway (Medical Service) → Supabase Cloud", "HTTPS / Supabase SDK", "Store records + files"],
    ["Railway (Family Service) → Supabase Cloud", "HTTPS / Supabase SDK", "Family and health data"],
    ["Railway (AI Service) → Supabase Cloud", "HTTPS / Supabase SDK", "Store extraction results"],
    ["Railway (Notification) → Supabase Cloud", "HTTPS / Supabase SDK", "Log notifications"],
    ["Railway (AI Service) → Anthropic Cloud", "HTTPS REST", "Send document, receive extraction"],
    ["Railway (Notification) → SendGrid / Firebase", "HTTPS REST", "Deliver email / push"],
    ["GitHub → Railway Server", "CI/CD (GitHub Actions)", "Auto-deploy on git push"],
    ["GitHub → Vercel CDN", "CI/CD (Vercel Git Integration)", "Auto-deploy frontend on git push"],
]
cp_data = [[Paragraph(h, label_s) for h in ["Path","Protocol","Purpose"]]] + \
          [[Paragraph(r[i], code_s if i==1 else body_s) for i in range(3)] for r in comm_rows]
story.append(Table(cp_data, colWidths=[PAGE_W*0.38, PAGE_W*0.22, PAGE_W*0.40],
    style=TableStyle([
        ("BACKGROUND",(0,0),(-1,0), ACCENT_RED),
        ("ROWBACKGROUNDS",(0,1),(-1,-1),[LIGHT_GRAY, WHITE]),
        ("GRID",(0,0),(-1,-1),0.5,MID_GRAY),
        ("TOPPADDING",(0,0),(-1,-1),5),("BOTTOMPADDING",(0,0),(-1,-1),5),
        ("LEFTPADDING",(0,0),(-1,-1),6),("VALIGN",(0,0),(-1,-1),"TOP"),
    ])))
story.append(S(3))

story.append(Paragraph("Layout (How to Arrange the Diagram)", style("H2", fontSize=12, textColor=ACCENT_RED, fontName="Helvetica-Bold", spaceAfter=3)))
story.append(code_block(
"""LAYOUT (left to right flow):

┌─────────────┐    HTTPS    ┌──────────────────────────────────────────┐
│ User Device │ ──────────► │           Vercel CDN                     │
│ (Browser /  │             │      [React Frontend App]                │
│  Mobile)    │             └──────────────────────────────────────────┘
└─────────────┘
      │ HTTPS REST (API calls)
      ▼
┌─────────────────────────────────────────────────────────────────────┐
│                   Railway / Render Cloud Server                      │
│  ┌─────────────┐                                                     │
│  │ NGINX       │ ──► Auth Service (8001)                            │
│  │ API Gateway │ ──► Medical Records Service (8002)                 │
│  │             │ ──► Family & Profile Service (8003)                │
│  │             │ ──► AI Processing Service (8004)                   │
│  │             │ ──► Notification Service (8005)                    │
│  └─────────────┘                                                     │
└─────────────────────────────────────────────────────────────────────┘
      │ Supabase SDK          │ HTTPS              │ HTTPS
      ▼                       ▼                    ▼
┌──────────────┐   ┌─────────────────┐   ┌──────────────────────┐
│  Supabase    │   │  Anthropic      │   │  SendGrid / Firebase  │
│  Cloud       │   │  Cloud          │   │  (Email + Push)       │
│  PostgreSQL  │   │  Claude API     │   └──────────────────────┘
│  Auth        │   └─────────────────┘
│  Storage     │
└──────────────┘

GitHub (top-right corner) with CI/CD arrows pointing to Vercel and Railway."""))
story.append(S(2))

story.append(Paragraph("UML Notation Rules for Deployment Diagram", style("H2", fontSize=12, textColor=ACCENT_RED, fontName="Helvetica-Bold", spaceAfter=3)))
story.append(code_block(
"""Nodes      → Draw as 3D boxes (cube icon in top-right corner)
             Label with «stereotype» above the name

Artifacts  → Draw as rectangles with folded top-right corner (document icon)
             Place INSIDE the node they run on

Docker     → Group the 5 services inside a dashed box inside Railway node
             Label the dashed box: «execution environment» Docker Compose

Lines      → Solid lines with label showing protocol (HTTPS, SQL, Supabase SDK)
             Use «communication path» label if needed

External   → External systems (Claude API, SendGrid) go on the far right side"""))
story.append(S(2))
story.append(tip_box("In draw.io: search for 'deployment node' in shape search. Use the '3D box' or 'server' shape for nodes. Use the 'document' shape for artifacts inside nodes.", colors.HexColor("#FDEDEC")))

story.append(PageBreak())

# ═══════════════════════════════════════════════════════
# QUICK REFERENCE CHEATSHEET
# ═══════════════════════════════════════════════════════
story += section_header("Quick Reference Cheatsheet", DARK_BLUE)
story.append(S(1))

cheat = [
    ["Diagram", "Main Shapes", "Lines/Arrows", "Key Rule"],
    ["Component", "«component» box\n«database» cylinder\n«external» shaded box",
     "Solid → REST\nDashed → DB/SDK",
     "Every service box must show its port number. Group microservices in a dashed Docker boundary."],
    ["Sequence", "Lifeline (box + vertical line)\nActivation bar (thin rect)\nActor (stick figure)",
     "→ solid = call\n← dashed = return",
     "Time flows downward. Number every arrow. Add [alt] frame for auth failure path."],
    ["Use Case", "Actor (stick figure)\nUse case (oval)\nSystem boundary (rectangle)",
     "─── actor to use case\n«include» dashed\n«extend» dashed",
     "Only connect actors to use cases they initiate. Put system name in the boundary box."],
    ["Deployment", "Node (3D box)\nArtifact (folded doc)\nExecution env (dashed box)",
     "─── communication path\nLabel with protocol",
     "Artifacts live INSIDE nodes. Show Docker containers as nested artifacts inside Railway node."],
]
ch_data = [[Paragraph(h, label_s) for h in cheat[0]]] + \
          [[Paragraph(r[i], code_s if i in [1,2] else body_s) for i in range(4)] for r in cheat[1:]]
story.append(Table(ch_data, colWidths=[PAGE_W*0.16, PAGE_W*0.22, PAGE_W*0.20, PAGE_W*0.42],
    style=TableStyle([
        ("BACKGROUND",(0,0),(-1,0), DARK_BLUE),
        ("ROWBACKGROUNDS",(0,1),(-1,-1),[LIGHT_GRAY, WHITE]),
        ("GRID",(0,0),(-1,-1),0.5,MID_GRAY),
        ("TOPPADDING",(0,0),(-1,-1),7),("BOTTOMPADDING",(0,0),(-1,-1),7),
        ("LEFTPADDING",(0,0),(-1,-1),6),("VALIGN",(0,0),(-1,-1),"TOP"),
    ])))
story.append(S(3))

story.append(Paragraph("Recommended Tools", style("H2", fontSize=12, textColor=DARK_BLUE, fontName="Helvetica-Bold", spaceAfter=3)))
tools = [
    ["draw.io (diagrams.net)", "Free, browser-based. Best for all 4 diagrams. Has UML shape library. Export as PNG/PDF.", "https://draw.io"],
    ["Lucidchart", "Clean UI, good collaboration. Free tier available.", "https://lucidchart.com"],
    ["PlantUML", "Code-based. Type text, get a diagram. Best for Sequence Diagram.", "https://plantuml.com"],
    ["StarUML", "Desktop app. Great for Use Case and Component diagrams.", "https://staruml.io"],
    ["Mermaid (VS Code)", "Markdown-based diagrams. Good for Sequence diagrams in docs.", "https://mermaid.js.org"],
]
tool_data = [[Paragraph(h, label_s) for h in ["Tool","Why Use It","URL"]]] + \
            [[Paragraph(r[i], body_s) for i in range(3)] for r in tools]
story.append(Table(tool_data, colWidths=[PAGE_W*0.22, PAGE_W*0.50, PAGE_W*0.28],
    style=TableStyle([
        ("BACKGROUND",(0,0),(-1,0), DARK_BLUE),
        ("ROWBACKGROUNDS",(0,1),(-1,-1),[LIGHT_GRAY, WHITE]),
        ("GRID",(0,0),(-1,-1),0.5,MID_GRAY),
        ("TOPPADDING",(0,0),(-1,-1),6),("BOTTOMPADDING",(0,0),(-1,-1),6),
        ("LEFTPADDING",(0,0),(-1,-1),6),("VALIGN",(0,0),(-1,-1),"TOP"),
    ])))

story.append(S(5))
story.append(HRFlowable(width=PAGE_W, color=MID_GRAY))
story.append(S(2))
story.append(Paragraph(
    "MYLIFE UML Diagrams Guide · 4 Diagrams Edition · Component · Sequence · Use Case · Deployment",
    style("Footer", fontSize=8, textColor=colors.gray, alignment=TA_CENTER)))

doc.build(story)
print("PDF done")
