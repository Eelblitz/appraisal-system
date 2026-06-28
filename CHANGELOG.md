# Changelog

All notable changes to the Annual Performance Evaluation System are documented here.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

-----

## [1.0.0] — 2026-06-28

### 🎉 Initial Release

This is the first production release of the Annual Performance Evaluation System
by Code With Iman.

-----

### Added

#### Platform Administration

- Platform Super Admin dashboard with organisation-wide statistics
- Organisation onboarding workflow (create org → create first HR Admin)
- Configurable subscription percentage per organisation
- Platform-level user management with password reset for any user
- Organisation activation/deactivation (access control for subscription lapses)

#### Multi-Tenancy SaaS Architecture

- Single-database multi-tenancy with `organisation` foreign key on all models
- Complete data isolation between organisations enforced at query level
- Organisation-scoped filtering on every view and form dropdown

#### User Roles and Authentication

- Five distinct roles: Platform Super Admin, HR Admin, Reporting Officer, Countersigning Officer, Employee
- Role-specific dashboards with relevant content per role
- Organisation active check during login (inactive orgs cannot log in)
- Sidebar notification badges that update based on pending workflow actions

#### HR Administration

- Appraisal Category management (create, edit, activate/deactivate)
- Appraisal Cycle management with download fee per cycle
- Appraisal Template management linking cycles to performance aspects
- Custom performance aspect creation per organisation
- Platform default aspects (16 GEN 79 standard aspects) available to all orgs
- Bulk appraisal assignment by department with Select All per department
- Live employee count during bulk assignment
- Safe duplicate prevention using `get_or_create`

#### GEN 79 Four-Part Appraisal Workflow

- Part 1 (Employee): Personal records, Fields 1-11b with pre-fill from profile
- Part 2 (Reporting Officer): Performance assessment, dynamic aspect ratings (A-E)
- Part 3 (Reporting Officer): Training needs, promotability, long-term potential
- Part 4 (Countersigning Officer): Final sign-off with summary of Part 2 ratings
- Draft saving at every step — users can return to incomplete forms
- Strict workflow enforcement — each part unlocks only after previous is submitted
- Auto-redirect from Part 2 submission to Part 3 (same officer fills both)

#### Dynamic Performance Aspects

- 16 standard GEN 79 aspects seeded via management command
- Ratings stored dynamically in `AppraisalAspectRating` (not hardcoded fields)
- HR can add custom aspects per organisation
- HR can deactivate aspects not relevant to their organisation
- Template-based aspect selection — different templates show different aspects

#### Payment Integration (Paystack)

- Payment initiation with unique reference generation
- Redirect to Paystack secure payment page
- Payment verification via Paystack API (never trust redirect alone)
- Revenue split calculation at payment time:
  - Platform earning = amount × subscription percentage
  - Organisation earning = amount - platform earning
- Free download support (zero-fee cycles bypass Paystack)
- Payment attempt history with status tracking
- Re-download after payment at no extra charge

#### PDF Generation

- Professional A4 PDF generated on-the-fly using ReportLab
- Organisation logo and name as document header
- “CONFIDENTIAL” and “ANNUAL PERFORMANCE EVALUATION REPORT” branding
- All four parts included with proper section headers
- Dynamic aspect ratings table with A-E ratings colour-coded
- Overall rating box with visual emphasis
- Signature areas for all officers
- Employee acknowledgement section
- Document reference number in footer
- No “GEN 79” branding on output (as required)

#### User Management

- HR Admin creates all staff accounts within their organisation
- Reporting Officer and Countersigning Officer dropdowns filtered to same organisation
- User profile with full personal and service history fields
- User detail view with appraisal history
- Platform Admin can reset any user’s password

#### System Documentation

- Complete system documentation available as downloadable file
- Accessible to HR Admin and Platform Admin from dashboard
- Covers all roles, processes, testing checklist, and troubleshooting

-----

### Technical Details

- **Django:** 4.2.7 (LTS)
- **Python:** 3.12
- **Database:** PostgreSQL 18
- **Payment:** Paystack API
- **PDF:** ReportLab
- **Frontend:** Bootstrap 5.3, Bootstrap Icons
- **Production:** Gunicorn + WhiteNoise
- **Hosting:** Render

-----

## Upcoming in [1.1.0]

- [ ] Email notifications when appraisal status changes
- [ ] Paystack subaccount integration for automatic revenue split
- [ ] Appraisal deadline reminder notifications
- [ ] HR bulk password reset for staff
- [ ] Export appraisal data to Excel
- [ ] Print-friendly appraisal summary view

-----

*Maintained by Code With Iman — CAC Reg. 9631094, Lafia, Nasarawa State, Nigeria*