from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm, cm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table,
    TableStyle, HRFlowable, Image
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
from django.conf import settings
import os


# ── Colour palette matching the website ──────────────
DARK_BLUE = colors.HexColor('#1a3a5c')
MID_BLUE = colors.HexColor('#2e6da4')
LIGHT_BLUE = colors.HexColor('#e8f4fd')
GREY = colors.HexColor('#6c757d')
LIGHT_GREY = colors.HexColor('#f8f9fa')
BORDER_GREY = colors.HexColor('#dee2e6')
SUCCESS_GREEN = colors.HexColor('#28a745')
WARNING_AMBER = colors.HexColor('#ffc107')
DANGER_RED = colors.HexColor('#dc3545')

# Rating colour map
RATING_COLORS = {
    'A': SUCCESS_GREEN,
    'B': colors.HexColor('#17a2b8'),
    'C': colors.HexColor('#6c757d'),
    'D': colors.HexColor('#fd7e14'),
    'E': DANGER_RED,
    'NA': colors.HexColor('#adb5bd'),
}


def get_styles():
    """
    Define all paragraph styles used in the PDF.
    Returns a dict of named styles for easy reference.
    """
    base = getSampleStyleSheet()

    styles = {
        'org_name': ParagraphStyle(
            'org_name',
            fontSize=14,
            fontName='Helvetica-Bold',
            textColor=DARK_BLUE,
            alignment=TA_CENTER,
            spaceAfter=2,
        ),
        'report_title': ParagraphStyle(
            'report_title',
            fontSize=18,
            fontName='Helvetica-Bold',
            textColor=DARK_BLUE,
            alignment=TA_CENTER,
            spaceAfter=4,
        ),
        'confidential': ParagraphStyle(
            'confidential',
            fontSize=10,
            fontName='Helvetica-Bold',
            textColor=colors.red,
            alignment=TA_CENTER,
            spaceAfter=2,
        ),
        'section_header': ParagraphStyle(
            'section_header',
            fontSize=10,
            fontName='Helvetica-Bold',
            textColor=colors.white,
            alignment=TA_LEFT,
            leftIndent=8,
            spaceAfter=0,
        ),
        'field_label': ParagraphStyle(
            'field_label',
            fontSize=8,
            fontName='Helvetica-Bold',
            textColor=GREY,
            spaceAfter=1,
        ),
        'field_value': ParagraphStyle(
            'field_value',
            fontSize=9,
            fontName='Helvetica',
            textColor=colors.black,
            spaceAfter=4,
        ),
        'body': ParagraphStyle(
            'body',
            fontSize=9,
            fontName='Helvetica',
            textColor=colors.black,
            spaceAfter=4,
            alignment=TA_JUSTIFY,
        ),
        'small': ParagraphStyle(
            'small',
            fontSize=8,
            fontName='Helvetica',
            textColor=GREY,
        ),
        'period': ParagraphStyle(
            'period',
            fontSize=9,
            fontName='Helvetica',
            textColor=DARK_BLUE,
            alignment=TA_CENTER,
            spaceAfter=4,
        ),
    }
    return styles


def draw_section_header(elements, title, styles):
    """
    Draws a dark blue section header bar.
    Used to separate each major section of the form.
    """
    header_table = Table(
        [[Paragraph(title, styles['section_header'])]],
        colWidths=[170 * mm]
    )
    header_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), DARK_BLUE),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('ROUNDEDCORNERS', [4, 4, 4, 4]),
    ]))
    elements.append(header_table)
    elements.append(Spacer(1, 4 * mm))


def draw_field(elements, label, value, styles):
    """
    Draws a single label-value pair.
    Label is small grey text, value is normal black text.
    """
    elements.append(Paragraph(label.upper(), styles['field_label']))
    elements.append(
        Paragraph(str(value) if value else '—', styles['field_value'])
    )


def generate_appraisal_pdf(appraisal, output_buffer):
    """
    Main function — generates the complete appraisal PDF.

    Parameters:
        appraisal — the Appraisal model instance
        output_buffer — a BytesIO buffer to write the PDF into

    Why BytesIO?
    We don't save the PDF to disk. We generate it in memory
    and serve it directly to the browser. This is faster,
    uses no disk space, and is more secure.

    Structure:
        Page 1: Cover + Part 1 (Personal Records)
        Page 2: Part 2 (Performance Assessment + Aspect Ratings)
        Page 3: Part 3 (Training + Promotability)
        Page 4: Part 4 (Countersigning Officer Report)
    """
    doc = SimpleDocTemplate(
        output_buffer,
        pagesize=A4,
        rightMargin=20 * mm,
        leftMargin=20 * mm,
        topMargin=15 * mm,
        bottomMargin=15 * mm,
    )

    styles = get_styles()
    elements = []
    page_width = 170 * mm  # A4 width minus margins

    organisation = appraisal.organisation
    cycle = appraisal.cycle
    employee = appraisal.employee

    # Try to get related parts safely
    try:
        part_one = appraisal.part_one
    except Exception:
        part_one = None

    try:
        part_two = appraisal.part_two
        aspect_ratings = list(
            part_two.aspect_ratings.select_related('aspect')
            .order_by('aspect__order')
        )
    except Exception:
        part_two = None
        aspect_ratings = []

    try:
        part_three = appraisal.part_three
    except Exception:
        part_three = None

    try:
        part_four = appraisal.part_four
    except Exception:
        part_four = None

    try:
        profile = employee.profile
    except Exception:
        profile = None

    # ══════════════════════════════════════════════════
    # DOCUMENT HEADER
    # ══════════════════════════════════════════════════

    # Organisation logo
    if organisation.logo:
        try:
            logo_path = organisation.logo.path
            if os.path.exists(logo_path):
                logo = Image(logo_path, width=30 * mm, height=20 * mm)
                logo.hAlign = 'CENTER'
                elements.append(logo)
                elements.append(Spacer(1, 3 * mm))
        except Exception:
            pass

    # Confidential stamp
    elements.append(
        Paragraph('CONFIDENTIAL', styles['confidential'])
    )

    # Organisation name
    elements.append(
        Paragraph(organisation.name.upper(), styles['org_name'])
    )

    # Report title
    elements.append(Paragraph(
        'ANNUAL PERFORMANCE EVALUATION REPORT',
        styles['report_title']
    ))

    # Horizontal rule
    elements.append(
        HRFlowable(
            width=page_width,
            thickness=2,
            color=DARK_BLUE,
            spaceAfter=4 * mm
        )
    )

    # Period of report
    elements.append(Paragraph(
        f'Period of Report: '
        f'{cycle.period_from.strftime("%d %B %Y")} '
        f'to {cycle.period_to.strftime("%d %B %Y")}',
        styles['period']
    ))
    elements.append(Paragraph(
        cycle.name,
        styles['period']
    ))

    elements.append(Spacer(1, 6 * mm))

    # ══════════════════════════════════════════════════
    # PART ONE — Personal Records
    # ══════════════════════════════════════════════════

    draw_section_header(
        elements,
        'PART ONE — PERSONAL RECORDS OF EMPLOYEE',
        styles
    )

    # Two-column layout for personal details
    col1_data = [
        [
            Paragraph('1. NAME OF OFFICER', styles['field_label']),
            Paragraph('2. DATE OF BIRTH', styles['field_label']),
        ],
        [
            Paragraph(
                employee.get_full_name() or '—',
                styles['field_value']
            ),
            Paragraph(
                profile.date_of_birth.strftime('%d %B %Y')
                if profile and profile.date_of_birth else '—',
                styles['field_value']
            ),
        ],
    ]

    personal_table = Table(
        col1_data,
        colWidths=[page_width * 0.6, page_width * 0.4]
    )
    personal_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
    ]))
    elements.append(personal_table)
    elements.append(Spacer(1, 2 * mm))

    # Department info — three columns
    dept_data = [
        [
            Paragraph('3(i). LOCAL GOVERNMENT', styles['field_label']),
            Paragraph('3(ii). DEPARTMENT', styles['field_label']),
            Paragraph('3(iii). SECTION', styles['field_label']),
        ],
        [
            Paragraph(
                profile.local_government if profile else '—',
                styles['field_value']
            ),
            Paragraph(
                profile.department if profile else '—',
                styles['field_value']
            ),
            Paragraph(
                profile.section if profile else '—',
                styles['field_value']
            ),
        ],
    ]

    dept_table = Table(
        dept_data,
        colWidths=[
            page_width * 0.33,
            page_width * 0.34,
            page_width * 0.33
        ]
    )
    dept_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
    ]))
    elements.append(dept_table)
    elements.append(Spacer(1, 2 * mm))

    if part_one:
        # Qualification
        draw_field(
            elements,
            '4. Qualification held (Degree, Diploma, Certificate, etc.)',
            part_one.qualification,
            styles
        )

        # Service history — three columns
        service_data = [
            [
                Paragraph(
                    '5. DATE OF FIRST APPOINTMENT',
                    styles['field_label']
                ),
                Paragraph(
                    '6. PRESENT SUBSTANTIVE GRADE',
                    styles['field_label']
                ),
                Paragraph(
                    '7. DATE APPOINTED TO GRADE',
                    styles['field_label']
                ),
            ],
            [
                Paragraph(
                    part_one.date_of_first_appointment.strftime('%d %B %Y')
                    if part_one.date_of_first_appointment else '—',
                    styles['field_value']
                ),
                Paragraph(
                    part_one.present_substantive_grade or '—',
                    styles['field_value']
                ),
                Paragraph(
                    part_one.date_appointed_to_grade.strftime('%d %B %Y')
                    if part_one.date_appointed_to_grade else '—',
                    styles['field_value']
                ),
            ],
        ]

        service_table = Table(
            service_data,
            colWidths=[
                page_width * 0.33,
                page_width * 0.34,
                page_width * 0.33
            ]
        )
        service_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ]))
        elements.append(service_table)
        elements.append(Spacer(1, 2 * mm))

        if part_one.acting_appointment:
            draw_field(
                elements,
                '8. Acting Appointment',
                part_one.acting_appointment,
                styles
            )

        if part_one.courses_undertaken:
            draw_field(
                elements,
                '9. Courses Undertaken',
                part_one.courses_undertaken,
                styles
            )

        draw_field(
            elements,
            '10. Total Days Absent on Sick Leave',
            str(part_one.days_absent_sick),
            styles
        )

        draw_field(
            elements,
            '11. Present Job',
            part_one.present_job,
            styles
        )

        draw_field(
            elements,
            'Job Description',
            part_one.job_description,
            styles
        )

        # Main duties table
        duties = [
            d for d in [
                part_one.main_duty_1,
                part_one.main_duty_2,
                part_one.main_duty_3,
                part_one.main_duty_4,
                part_one.main_duty_5,
            ] if d
        ]

        if duties:
            elements.append(
                Paragraph(
                    '11(a). MAIN DUTIES IN ORDER OF IMPORTANCE',
                    styles['field_label']
                )
            )
            duty_rows = []
            for i, duty in enumerate(duties, 1):
                duty_rows.append([
                    Paragraph(str(i), styles['small']),
                    Paragraph(duty, styles['body']),
                ])

            duty_table = Table(
                duty_rows,
                colWidths=[8 * mm, page_width - 8 * mm]
            )
            duty_table.setStyle(TableStyle([
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('TOPPADDING', (0, 0), (-1, -1), 3),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
                ('LINEBELOW', (0, 0), (-1, -2), 0.5, BORDER_GREY),
            ]))
            elements.append(duty_table)
            elements.append(Spacer(1, 2 * mm))

        if part_one.adhoc_duties:
            draw_field(
                elements,
                '11(b). Adhoc Duties',
                part_one.adhoc_duties,
                styles
            )

    elements.append(Spacer(1, 6 * mm))

    # ══════════════════════════════════════════════════
    # PART TWO — Reporting Officer's Assessment
    # ══════════════════════════════════════════════════

    draw_section_header(
        elements,
        "PART TWO — REPORTING OFFICER'S ASSESSMENT",
        styles
    )

    if part_two:
        # Field 12
        agreement = 'YES' if part_two.agrees_with_job_description else 'NO'
        draw_field(
            elements,
            '12. Agreement on Job Description and Order of Importance',
            agreement,
            styles
        )

        if not part_two.agrees_with_job_description and \
                part_two.job_description_disagreement:
            draw_field(
                elements,
                'Unresolved Differences',
                part_two.job_description_disagreement,
                styles
            )

        # Field 13
        draw_field(
            elements,
            '13. Assessment of Performance',
            part_two.performance_assessment,
            styles
        )

        # Field 14 — Aspect ratings table
        if aspect_ratings:
            elements.append(
                Paragraph(
                    '14. ASPECTS OF PERFORMANCE',
                    styles['field_label']
                )
            )
            elements.append(Spacer(1, 2 * mm))

            # Header row
            rating_header = [
                Paragraph('ASPECT', styles['field_label']),
                Paragraph('OUTSTANDING (A)', styles['field_label']),
                Paragraph('UNSATISFACTORY (E)', styles['field_label']),
                Paragraph('RATING', styles['field_label']),
            ]

            rating_rows = [rating_header]

            for ar in aspect_ratings:
                rating_color = RATING_COLORS.get(ar.rating, GREY)
                rating_rows.append([
                    Paragraph(ar.aspect.label, styles['body']),
                    Paragraph(
                        ar.aspect.outstanding_description,
                        styles['small']
                    ),
                    Paragraph(
                        ar.aspect.unsatisfactory_description,
                        styles['small']
                    ),
                    Paragraph(
                        f'<font color="{rating_color.hexval()}">'
                        f'<b>{ar.rating}</b></font>',
                        ParagraphStyle(
                            'rating',
                            fontSize=14,
                            alignment=TA_CENTER
                        )
                    ),
                ])

            aspect_table = Table(
                rating_rows,
                colWidths=[
                    page_width * 0.22,
                    page_width * 0.33,
                    page_width * 0.33,
                    page_width * 0.12,
                ]
            )
            aspect_table.setStyle(TableStyle([
                # Header row styling
                ('BACKGROUND', (0, 0), (-1, 0), LIGHT_BLUE),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 8),
                # All cells
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('FONTSIZE', (0, 1), (-1, -1), 8),
                ('TOPPADDING', (0, 0), (-1, -1), 4),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                ('LEFTPADDING', (0, 0), (-1, -1), 6),
                ('RIGHTPADDING', (0, 0), (-1, -1), 6),
                # Grid
                ('GRID', (0, 0), (-1, -1), 0.5, BORDER_GREY),
                # Alternating row colours
                *[
                    ('BACKGROUND', (0, i), (-1, i), LIGHT_GREY)
                    for i in range(2, len(rating_rows), 2)
                ],
                # Rating column centered
                ('ALIGN', (3, 0), (3, -1), 'CENTER'),
            ]))
            elements.append(aspect_table)
            elements.append(Spacer(1, 4 * mm))

        # Overall rating box
        overall_display = dict(
            part_two.OVERALL_RATING_CHOICES
        ).get(part_two.overall_rating, '—')

        overall_data = [[
            Paragraph(
                'OVERALL PERFORMANCE RATING',
                styles['field_label']
            ),
            Paragraph(
                f'<b>{part_two.overall_rating} — {overall_display}</b>',
                ParagraphStyle(
                    'overall',
                    fontSize=12,
                    fontName='Helvetica-Bold',
                    textColor=DARK_BLUE,
                    alignment=TA_CENTER
                )
            ),
        ]]

        overall_table = Table(
            overall_data,
            colWidths=[page_width * 0.5, page_width * 0.5]
        )
        overall_table.setStyle(TableStyle([
            ('BACKGROUND', (1, 0), (1, 0), LIGHT_BLUE),
            ('BOX', (0, 0), (-1, -1), 1, DARK_BLUE),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        elements.append(overall_table)
        elements.append(Spacer(1, 4 * mm))

        # Reporting officer signature area
        sig_data = [
            [
                Paragraph('REPORTING OFFICER', styles['field_label']),
                Paragraph('GRADE', styles['field_label']),
                Paragraph('JOB TITLE', styles['field_label']),
                Paragraph('YEARS KNOWN', styles['field_label']),
            ],
            [
                Paragraph(
                    part_two.reporting_officer.get_full_name(),
                    styles['field_value']
                ),
                Paragraph(
                    part_two.reporting_officer_grade or '—',
                    styles['field_value']
                ),
                Paragraph(
                    part_two.reporting_officer_job_title or '—',
                    styles['field_value']
                ),
                Paragraph(
                    str(part_two.years_known),
                    styles['field_value']
                ),
            ],
            [
                Paragraph('Signature: ___________________', styles['small']),
                Paragraph(
                    f'Date: {part_two.submitted_at.strftime("%d/%m/%Y") if part_two.submitted_at else "—"}',
                    styles['small']
                ),
                Paragraph('', styles['small']),
                Paragraph('', styles['small']),
            ],
        ]

        sig_table = Table(
            sig_data,
            colWidths=[
                page_width * 0.35,
                page_width * 0.2,
                page_width * 0.3,
                page_width * 0.15
            ]
        )
        sig_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), LIGHT_GREY),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('BOX', (0, 0), (-1, -1), 0.5, BORDER_GREY),
            ('LINEBELOW', (0, 0), (-1, 0), 0.5, BORDER_GREY),
        ]))
        elements.append(sig_table)

    elements.append(Spacer(1, 6 * mm))

    # ══════════════════════════════════════════════════
    # PART THREE — Training and Promotability
    # ══════════════════════════════════════════════════

    draw_section_header(
        elements,
        'PART THREE — TRAINING NEEDS AND PROMOTABILITY',
        styles
    )

    if part_three:
        if part_three.training_needs:
            draw_field(
                elements,
                '15(a). Training Needs',
                part_three.training_needs,
                styles
            )

        if part_three.training_how_met:
            draw_field(
                elements,
                '15(b). How Training Needs Can Be Met',
                part_three.training_how_met,
                styles
            )

        # Next job
        next_job_items = []
        if part_three.different_job_same_grade:
            next_job_items.append(
                'Different job in the same grade: YES'
            )
        if part_three.transfer_to_another_cadre:
            next_job_items.append(
                'Transfer to another occupational group or cadre: YES'
            )

        if next_job_items:
            draw_field(
                elements,
                '16. Next Job Recommendation',
                ' | '.join(next_job_items),
                styles
            )
            if part_three.next_job_reasons:
                draw_field(
                    elements,
                    'Reasons',
                    part_three.next_job_reasons,
                    styles
                )

        # Promotability
        if part_three.promotion_fitness:
            from appraisal.models import PartThree as PT
            fitness_display = dict(
                PT.PROMOTION_FITNESS_CHOICES
            ).get(
                part_three.promotion_fitness,
                part_three.promotion_fitness
            )

            draw_field(
                elements,
                '17(a). Normal Promotion',
                f'{fitness_display} for promotion to Grade: '
                f'{part_three.promotion_to_grade or "—"}',
                styles
            )

            if part_three.promotion_comment:
                draw_field(
                    elements,
                    'Comment on Recommendation',
                    part_three.promotion_comment,
                    styles
                )

        if part_three.special_promotion_grade:
            draw_field(
                elements,
                '17(b). Special Promotion to Grade',
                part_three.special_promotion_grade,
                styles
            )
            if part_three.special_promotion_reasons:
                draw_field(
                    elements,
                    'Reasons',
                    part_three.special_promotion_reasons,
                    styles
                )

        if part_three.long_term_potential:
            from appraisal.models import PartThree as PT
            potential_display = dict(
                PT.LONG_TERM_POTENTIAL_CHOICES
            ).get(
                part_three.long_term_potential,
                part_three.long_term_potential
            )
            draw_field(
                elements,
                '18. Long Term Potential',
                potential_display,
                styles
            )

        if part_three.general_remarks:
            draw_field(
                elements,
                '19. General Remarks',
                part_three.general_remarks,
                styles
            )

        # Part 3 signature
        p3_sig_data = [
            [
                Paragraph('NAME (BLOCK LETTERS)', styles['field_label']),
                Paragraph('GRADE', styles['field_label']),
                Paragraph('YEARS SERVED', styles['field_label']),
                Paragraph('DATE', styles['field_label']),
            ],
            [
                Paragraph(
                    part_three.reporting_officer_name or
                    part_three.reporting_officer.get_full_name(),
                    styles['field_value']
                ),
                Paragraph(
                    part_three.reporting_officer_grade or '—',
                    styles['field_value']
                ),
                Paragraph(
                    str(part_three.years_served_under_reporting_officer),
                    styles['field_value']
                ),
                Paragraph(
                    part_three.submitted_at.strftime('%d/%m/%Y')
                    if part_three.submitted_at else '—',
                    styles['field_value']
                ),
            ],
            [
                Paragraph('Signature: ___________________', styles['small']),
                Paragraph('', styles['small']),
                Paragraph('', styles['small']),
                Paragraph('', styles['small']),
            ],
        ]

        p3_sig_table = Table(
            p3_sig_data,
            colWidths=[
                page_width * 0.4,
                page_width * 0.2,
                page_width * 0.2,
                page_width * 0.2
            ]
        )
        p3_sig_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), LIGHT_GREY),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('BOX', (0, 0), (-1, -1), 0.5, BORDER_GREY),
            ('LINEBELOW', (0, 0), (-1, 0), 0.5, BORDER_GREY),
        ]))
        elements.append(p3_sig_table)

    elements.append(Spacer(1, 6 * mm))

    # ══════════════════════════════════════════════════
    # PART FOUR — Countersigning Officer
    # ══════════════════════════════════════════════════

    draw_section_header(
        elements,
        "PART FOUR — COUNTERSIGNING OFFICER'S REPORT",
        styles
    )

    if part_four:
        draw_field(
            elements,
            "20. Countersigning Officer's Report",
            part_four.countersigning_report,
            styles
        )

        p4_sig_data = [
            [
                Paragraph('NAME (BLOCK LETTERS)', styles['field_label']),
                Paragraph('GRADE', styles['field_label']),
                Paragraph('YEARS SERVED', styles['field_label']),
                Paragraph('DATE', styles['field_label']),
            ],
            [
                Paragraph(
                    part_four.countersigning_name or
                    part_four.countersigning_officer.get_full_name(),
                    styles['field_value']
                ),
                Paragraph(
                    part_four.countersigning_grade or '—',
                    styles['field_value']
                ),
                Paragraph(
                    str(part_four.years_served_under_countersigning),
                    styles['field_value']
                ),
                Paragraph(
                    part_four.submitted_at.strftime('%d/%m/%Y')
                    if part_four.submitted_at else '—',
                    styles['field_value']
                ),
            ],
            [
                Paragraph('Signature: ___________________', styles['small']),
                Paragraph('', styles['small']),
                Paragraph('', styles['small']),
                Paragraph('', styles['small']),
            ],
        ]

        p4_sig_table = Table(
            p4_sig_data,
            colWidths=[
                page_width * 0.4,
                page_width * 0.2,
                page_width * 0.2,
                page_width * 0.2
            ]
        )
        p4_sig_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), LIGHT_GREY),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('BOX', (0, 0), (-1, -1), 0.5, BORDER_GREY),
            ('LINEBELOW', (0, 0), (-1, 0), 0.5, BORDER_GREY),
        ]))
        elements.append(p4_sig_table)

    # ══════════════════════════════════════════════════
    # EMPLOYEE ACKNOWLEDGEMENT
    # ══════════════════════════════════════════════════

    elements.append(Spacer(1, 6 * mm))
    elements.append(
        HRFlowable(
            width=page_width,
            thickness=1,
            color=BORDER_GREY,
            spaceAfter=4 * mm
        )
    )

    ack_text = (
        'I certify that I have seen the contents of this Report '
        'and that my superior has discussed them with me. '
        'I have the following comment to add:'
    )
    elements.append(Paragraph(ack_text, styles['body']))
    elements.append(Spacer(1, 8 * mm))

    ack_data = [
        [
            Paragraph(
                'Signature of Officer reported on: '
                '____________________________',
                styles['small']
            ),
            Paragraph(
                'Grade Level: ___________',
                styles['small']
            ),
        ],
        [
            Paragraph('', styles['small']),
            Paragraph('', styles['small']),
        ],
        [
            Paragraph(
                'Job Title: __________________________________',
                styles['small']
            ),
            Paragraph(
                f'Date: ___________',
                styles['small']
            ),
        ],
    ]

    ack_table = Table(
        ack_data,
        colWidths=[page_width * 0.65, page_width * 0.35]
    )
    ack_table.setStyle(TableStyle([
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    elements.append(ack_table)

    # ══════════════════════════════════════════════════
    # FOOTER NOTE
    # ══════════════════════════════════════════════════

    elements.append(Spacer(1, 6 * mm))
    elements.append(
        HRFlowable(
            width=page_width,
            thickness=0.5,
            color=BORDER_GREY,
            spaceAfter=2 * mm
        )
    )
    elements.append(Paragraph(
        f'Generated by {organisation.name} Appraisal Management System '
        f'| Powered by Code With Iman | '
        f'Document Reference: APR-{appraisal.pk:05d}',
        ParagraphStyle(
            'footer',
            fontSize=7,
            textColor=GREY,
            alignment=TA_CENTER
        )
    ))

    # Build the PDF
    doc.build(elements)