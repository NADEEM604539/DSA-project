"""
PDF generation service for library fines
Generates professional fine challans (payment invoices)
"""

from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
from datetime import datetime, timedelta
from models import UserFine, IssueRecord, User, Book


def generate_fine_challan(user_id: int, fine_id: int, db) -> BytesIO:
    """
    Generate a beautiful, professional fine challan PDF with larger fonts and proper tables
    Returns BytesIO object that can be downloaded
    """
    # Fetch fine details
    fine = db.query(UserFine).filter(UserFine.fine_id == fine_id).first()
    if not fine:
        return None
    
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        return None
    
    issue = None
    book = None
    if fine.issue_id:
        issue = db.query(IssueRecord).filter(IssueRecord.issue_id == fine.issue_id).first()
        if issue and issue.book_id:
            book = db.query(Book).filter(Book.book_id == issue.book_id).first()
    
    # Create PDF with optimized margins for vertical expansion
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer, 
        pagesize=letter, 
        topMargin=0.3*inch, 
        bottomMargin=0.3*inch,
        leftMargin=0.4*inch,
        rightMargin=0.4*inch
    )
    
    elements = []
    styles = getSampleStyleSheet()
    
    # ===== CUSTOM STYLES - BIGGER FONTS =====
    title_style = ParagraphStyle(
        'Title',
        parent=styles['Heading1'],
        fontSize=22,
        textColor=colors.HexColor('#ffffff'),
        spaceAfter=0,
        alignment=1,
        fontName='Helvetica-Bold'
    )
    
    section_style = ParagraphStyle(
        'Section',
        parent=styles['Heading2'],
        fontSize=12,
        textColor=colors.HexColor('#ffffff'),
        spaceAfter=0,
        fontName='Helvetica-Bold'
    )
    
    label_style = ParagraphStyle(
        'Label',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.HexColor('#333333'),
        fontName='Helvetica-Bold',
        spaceAfter=0
    )
    
    value_style = ParagraphStyle(
        'Value',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.HexColor('#000000'),
        spaceAfter=0
    )
    
    normal_style = ParagraphStyle(
        'Normal',
        parent=styles['Normal'],
        fontSize=10,
        spaceAfter=2,
        leading=13
    )
    
    bold_value_style = ParagraphStyle(
        'BoldValue',
        parent=styles['Normal'],
        fontSize=11,
        textColor=colors.HexColor('#cc0000'),
        fontName='Helvetica-Bold',
        spaceAfter=0
    )
    
    instruction_style = ParagraphStyle(
        'Instruction',
        parent=styles['Normal'],
        fontSize=9.5,
        spaceAfter=1,
        leading=12
    )
    
    # ===== HEADER =====
    header_data = [
        [Paragraph('📚 LIBRARY FINE CHALLAN', title_style)],
    ]
    header_table = Table(header_data, colWidths=[7.2*inch])
    header_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#1a1a2e')),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 12),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ('BORDER', (0, 0), (-1, -1), 0, colors.HexColor('#1a1a2e')),
    ]))
    elements.append(header_table)
    elements.append(Spacer(1, 0.12*inch))
    
    # ===== CHALLAN & MEMBER INFO TABLE =====
    info_table_data = [
        [
            Paragraph('<b>Challan No.:</b>', label_style),
            Paragraph(f'CHAL-{fine.fine_id:05d}', value_style),
            Paragraph('<b>Name:</b>', label_style),
            Paragraph(user.full_name, value_style),
        ],
        [
            Paragraph('<b>Fine ID:</b>', label_style),
            Paragraph(f'{fine.fine_id}', value_style),
            Paragraph('<b>Member ID:</b>', label_style),
            Paragraph(f'{user.user_id}', value_style),
        ],
        [
            Paragraph('<b>Issued:</b>', label_style),
            Paragraph(datetime.now().strftime('%d %b %Y'), value_style),
            Paragraph('<b>Email:</b>', label_style),
            Paragraph(user.email, value_style),
        ],
    ]
    
    info_table = Table(info_table_data, colWidths=[1.4*inch, 1.5*inch, 1.4*inch, 2.9*inch])
    info_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f5f5f5')),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('BORDER', (0, 0), (-1, -1), 0.5, colors.HexColor('#cccccc')),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cccccc')),
    ]))
    elements.append(info_table)
    elements.append(Spacer(1, 0.12*inch))
    
    # ===== FINE DETAILS SECTION =====
    section_data = [[Paragraph('FINE DETAILS', section_style)]]
    section_table = Table(section_data, colWidths=[7.2*inch])
    section_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#e74c3c')),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('BORDER', (0, 0), (-1, -1), 0, colors.HexColor('#e74c3c')),
    ]))
    elements.append(section_table)
    
    fine_type = fine.fine_type.value if fine.fine_type else "LATE_RETURN"
    fine_type_display = "⏰ Late Return" if fine_type == "LATE_RETURN" else "📦 Book Lost"
    
    fine_table_data = [
        [
            Paragraph('<b>Fine Type:</b>', label_style),
            Paragraph(fine_type_display, value_style),
            Paragraph('<b>Amount:</b>', label_style),
            Paragraph(f'Rs{fine.fine_amount:.2f}', bold_value_style),
        ],
        [
            Paragraph('<b>Status:</b>', label_style),
            Paragraph('⚠️ UNPAID' if not fine.is_paid else '✓ PAID', value_style),
            Paragraph('<b>Created:</b>', label_style),
            Paragraph(fine.created_at.strftime('%d %b %Y') if fine.created_at else 'N/A', value_style),
        ],
    ]
    
    if book:
        fine_table_data.insert(0, [
            Paragraph('<b>Book Title:</b>', label_style),
            Paragraph(book.title, value_style),
            Paragraph('', label_style),
            Paragraph('', value_style),
        ])
    
    fine_table = Table(fine_table_data, colWidths=[1.4*inch, 1.9*inch, 1.4*inch, 2.5*inch])
    fine_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#fef5e7')),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ('BORDER', (0, 0), (-1, -1), 0.5, colors.HexColor('#d0d0d0')),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#d0d0d0')),
    ]))
    elements.append(fine_table)
    elements.append(Spacer(1, 0.12*inch))
    
    # ===== PAYMENT DEADLINE (ALERT) =====
    payment_deadline = datetime.now() + timedelta(days=7)
    
    deadline_data = [
        [
            Paragraph(f'<b>⚠️ PAYMENT DEADLINE:</b><br/>{payment_deadline.strftime("%d %B %Y")}<br/><b>7 DAYS REMAINING</b>', 
                     ParagraphStyle('DeadlineText', parent=styles['Normal'], fontSize=11, textColor=colors.HexColor('#8B0000'), 
                                   fontName='Helvetica-Bold', alignment=1)),
        ]
    ]
    
    deadline_table = Table(deadline_data, colWidths=[7.2*inch])
    deadline_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#ffe6e6')),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
        ('TOPPADDING', (0, 0), (-1, -1), 12),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ('BORDER', (0, 0), (-1, -1), 2, colors.HexColor('#8B0000')),
    ]))
    elements.append(deadline_table)
    elements.append(Spacer(1, 0.12*inch))
    
    # ===== PAYMENT INSTRUCTIONS SECTION =====
    section_data = [[Paragraph('HOW TO PAY', section_style)]]
    section_table = Table(section_data, colWidths=[7.2*inch])
    section_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#2980b9')),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('BORDER', (0, 0), (-1, -1), 0, colors.HexColor('#2980b9')),
    ]))
    elements.append(section_table)
    
    instructions = """
    <b>1.</b> Visit the library counter with this challan printed or on your mobile<br/>
    <b>2.</b> Pay via online portal using your Member ID (available on member dashboard)<br/>
    <b>3.</b> Keep the receipt or payment confirmation for your records<br/>
    <b>4.</b> Payment must be completed within 7 days to avoid account suspension
    """
    
    instruction_table_data = [[Paragraph(instructions, instruction_style)]]
    instruction_table = Table(instruction_table_data, colWidths=[7.2*inch])
    instruction_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#ebf5fb')),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
        ('TOPPADDING', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ('BORDER', (0, 0), (-1, -1), 0.5, colors.HexColor('#2980b9')),
    ]))
    elements.append(instruction_table)
    elements.append(Spacer(1, 0.12*inch))
    
    # ===== IMPORTANT NOTICE SECTION =====
    section_data = [[Paragraph('IMPORTANT NOTICE', section_style)]]
    section_table = Table(section_data, colWidths=[7.2*inch])
    section_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#c0392b')),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('BORDER', (0, 0), (-1, -1), 0, colors.HexColor('#c0392b')),
    ]))
    elements.append(section_table)
    
    notice = """
    <b>Non-payment will result in:</b><br/>
    ⚠️ Account suspension and inability to borrow books<br/>
    ⚠️ Blocking of library services until fine is settled<br/>
    ⚠️ Additional late fees may apply<br/>
    <br/>
    <b>For payment plans or queries, contact library administration immediately.</b>
    """
    
    notice_table_data = [[Paragraph(notice, instruction_style)]]
    notice_table = Table(notice_table_data, colWidths=[7.2*inch])
    notice_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#fadbd8')),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
        ('TOPPADDING', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ('BORDER', (0, 0), (-1, -1), 0.5, colors.HexColor('#c0392b')),
    ]))
    elements.append(notice_table)
    elements.append(Spacer(1, 0.1*inch))
    
    # ===== FOOTER =====
    footer_style = ParagraphStyle(
        'Footer',
        parent=styles['Normal'],
        fontSize=8,
        textColor=colors.grey,
        alignment=1,
        spaceAfter=0
    )
    elements.append(Paragraph(
        f"Generated: {datetime.now().strftime('%d %b %Y | %H:%M')} | Electronically Generated Document | Valid for Payment",
        footer_style
    ))
    
    # Build PDF
    doc.build(elements)
    buffer.seek(0)
    return buffer
