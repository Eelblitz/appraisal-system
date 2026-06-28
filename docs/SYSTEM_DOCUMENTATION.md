# Annual Performance Evaluation System

## Complete System Documentation

### Code With Iman — CAC Reg. No. 9631094

---

> **Document Purpose:** This document explains every function, logic, process and role in the Annual Performance Evaluation System. It is intended for system administrators, HR officers, developers, and end users.

---

## Table of Contents

1. [System Overview](#1-system-overview)
2. [User Roles and Permissions](#2-user-roles-and-permissions)
3. [System Architecture](#3-system-architecture)
4. [Getting Started — Setup Sequence](#4-getting-started--setup-sequence)
5. [Platform Administration](#5-platform-administration)
6. [Organisation Management](#6-organisation-management)
7. [HR Administration](#7-hr-administration)
8. [The Appraisal Workflow](#8-the-appraisal-workflow)
9. [Part 1 — Employee Personal Records](#9-part-1--employee-personal-records)
10. [Part 2 — Reporting Officer Assessment](#10-part-2--reporting-officer-assessment)
11. [Part 3 — Training and Promotability](#11-part-3--training-and-promotability)
12. [Part 4 — Countersigning Officer Report](#12-part-4--countersigning-officer-report)
13. [Payment and PDF Download](#13-payment-and-pdf-download)
14. [Revenue Split Model](#14-revenue-split-model)
15. [Performance Aspects](#15-performance-aspects)
16. [Data Isolation and Security](#16-data-isolation-and-security)
17. [Testing Checklist](#17-testing-checklist)
18. [Troubleshooting Common Issues](#18-troubleshooting-common-issues)
19. [Glossary](#19-glossary)

---

## 1. System Overview

The **Annual Performance Evaluation System** is a SaaS (Software as a Service) web application that digitises the Nigerian government's GEN 79 Annual Performance Evaluation process for ministries and MDAs (Ministries, Departments and Agencies).

### What It Replaces
Previously, the GEN 79 appraisal was a physical paper form filled manually, often lost, delayed, or inconsistently completed. This system replaces that process with a structured, role-controlled digital workflow.

### What It Does
- Manages the entire 4-part annual appraisal form digitally
- Enforces the correct workflow sequence (each part unlocks only after the previous is completed)
- Allows multiple organisations (ministries) to use the same platform with complete data isolation
- Collects payment from employees before releasing their completed PDF report
- Splits payment revenue between the platform (Code With Iman) and the organisation

### Technology Stack
```
Backend:      Django 4.2.7 (Python 3.12)
Database:     PostgreSQL 18
Payment:      Paystack
PDF:          ReportLab
Deployment:   Render
```

---

## 2. User Roles and Permissions

The system has **five distinct roles** operating at two levels.

---

### LEVEL 1 — Platform Level

#### Platform Super Admin (Code With Iman)
This is the business owner — you. There is only one platform-level admin.

**Can do:**
- Create and manage organisation accounts (ministries/MDAs)
- Set the subscription percentage per organisation
- View all users across all organisations
- Reset any user's password
- Activate or deactivate any organisation
- View platform-wide revenue and statistics

**Cannot be created by anyone else — only via Django's `createsuperuser` command.**

---

### LEVEL 2 — Organisation Level

All organisation-level users belong to exactly one organisation and can only see data belonging to that organisation.

#### HR Admin
Created by the Platform Super Admin when onboarding a new organisation.

**Can do:**
- Create and manage staff accounts within their organisation
- Create appraisal categories, cycles, templates and performance aspects
- Assign appraisals in bulk to employees
- View all appraisals and payment records in their organisation
- Reset passwords for staff within their organisation

**Example:** The HR Manager at the Federal Ministry of Finance is an HR Admin.

---

#### Reporting Officer
A senior staff member responsible for assessing the employees under them.

**Can do:**
- View appraisals of employees assigned to them
- Fill Part 2 (Performance Assessment) and Part 3 (Training and Promotability)
- Save drafts and return to complete forms

**Cannot do:**
- See appraisals of employees not assigned to them
- Fill Part 1 (employee's responsibility) or Part 4 (countersigning officer's responsibility)

**Example:** A Head of Department who assesses officers directly under them.

---

#### Countersigning Officer
A more senior officer who provides the final sign-off.

**Can do:**
- View Parts 1, 2 and 3 of appraisals assigned to them
- Fill Part 4 (Countersigning Officer Report)
- Complete the appraisal, unlocking the employee's PDF download

**Cannot do:**
- Edit any part filled by others
- Access appraisals not assigned to them

**Example:** A Director who countersigns appraisals assessed by Heads of Department.

---

#### Employee
The staff member being appraised.

**Can do:**
- Fill Part 1 of their own appraisal
- Save Part 1 as a draft and return to edit before submission
- View their appraisal status at each stage
- Pay the download fee and download their completed PDF

**Cannot do:**
- See another employee's appraisal
- Edit Part 1 after submission
- Access Parts 2, 3 or 4

---

## 3. System Architecture

### Multi-Tenancy (SaaS)

The system serves multiple organisations from one application and one database. Data isolation is enforced by an `organisation` field on every model.

```
Platform (Code With Iman)
│
├── Organisation: Federal Ministry of Finance
│       ├── Categories, Cycles, Templates
│       ├── Users (HR Admin, Officers, Employees)
│       └── Appraisals, Payments
│
├── Organisation: Ministry of Health
│       ├── Categories, Cycles, Templates
│       ├── Users (HR Admin, Officers, Employees)
│       └── Appraisals, Payments
│
└── Organisation: FIRS
        └── ...
```

**Rule:** Every database query is filtered by `organisation`. An HR Admin from the Ministry of Finance can never see data belonging to the Ministry of Health, even if they know the URL.

---

### Application Structure

```
appraisal_project/          ← Django project settings
│
├── organisations/          ← Tenant management
├── accounts/               ← Authentication, user profiles, roles
├── hr/                     ← Cycles, categories, templates, aspects
├── appraisal/              ← The 4-part form, workflow logic
├── payments/               ← Paystack integration, PDF generation
└── core/                   ← Dashboards, context processors
```

---

### Appraisal Status Flow

Every appraisal record has a `status` field that moves through these stages:

```
pending
    ↓ (employee submits Part 1)
part1_submitted
    ↓ (reporting officer submits Part 2)
part2_submitted
    ↓ (reporting officer submits Part 3)
part3_submitted
    ↓ (countersigning officer submits Part 4)
completed
    ↓ (employee pays download fee)
closed
```

Each status change unlocks the next step for the appropriate role. No step can be skipped.

---

## 4. Getting Started — Setup Sequence

Before employees can start filling appraisals, the system must be set up in this exact order. Skipping steps will cause errors.

### Step 1: Platform Admin Onboards an Organisation
The Platform Super Admin creates the organisation account and sets the subscription percentage.

**Required information:**
- Organisation full name (e.g. Federal Ministry of Finance)
- Acronym (e.g. FMF)
- Official email
- Logo (optional but recommended — appears on PDF)
- Subscription percentage (e.g. 10 for 10%)

---

### Step 2: Platform Admin Creates the First HR Admin
Immediately after creating the organisation, the platform admin creates the first HR Admin account for that organisation.

**Why the platform admin does this (not the organisation):**
The organisation has no users yet. Someone must create the first account. After this, the HR Admin can create all other staff accounts themselves.

---

### Step 3: HR Admin Creates Staff Accounts

**Correct creation order:**
1. Create Reporting Officers first
2. Create Countersigning Officers second
3. Create Employees last — assign Reporting Officer and Countersigning Officer during creation

**Why this order?**
When creating an employee, the system shows dropdowns for Reporting Officer and Countersigning Officer. These dropdowns only show users who already exist in the system with those roles. If you create employees first, the dropdowns will be empty.

---

### Step 4: HR Admin Creates a Category

Categories group employees by staff type.

**Examples:**
- Admin Staff
- Technical Staff
- Medical Officers
- Teaching Staff

---

### Step 5: HR Admin Creates a Cycle

A cycle represents one appraisal period.

**Example:**
```
Name:         2024 Annual Performance Evaluation
Category:     Admin Staff
Year:         2024
Period From:  01/01/2024
Period To:    31/12/2024
Download Fee: ₦2,000
Status:       Draft (activate when ready)
```

**Important:** Set the Download Fee here. This is what employees pay to download their completed PDF.

---

### Step 6: HR Admin Creates a Template

A template links a cycle to a set of performance aspects.

**Example:**
```
Name:    2024 Admin Staff Appraisal Template
Cycle:   2024 Annual Performance Evaluation
Aspects: ✅ Foresight
         ✅ Penetration
         ✅ Judgement
         ... (select all applicable aspects)
```

---

### Step 7: HR Admin Activates the Cycle

Change cycle status from **Draft** → **Active**.

Only active cycles appear in the bulk assignment page. This prevents HR from accidentally assigning employees to an unfinished cycle.

---

### Step 8: HR Admin Assigns Appraisals in Bulk

Go to **Assign Appraisals** in the sidebar.

1. Select the active cycle
2. Select the template
3. Tick employees to assign (or use "Select All" per department)
4. Click **Assign Appraisals**

The system creates one `Appraisal` record per selected employee. Employees can now log in and see their appraisal.

---

## 5. Platform Administration

### Accessing Platform Admin
Log in with the Django superuser account. The sidebar shows a **Platform Admin** section not visible to other users.

### Organisation List
Shows all organisations with:
- Name and acronym
- Subscription percentage
- Active/Inactive status
- Date joined

### Managing Organisations
- **Edit** — update name, contact info, logo, subscription percentage
- **Toggle** — activate or deactivate an organisation (deactivated organisations cannot log in)
- **Create HR Admin** — add a new HR Admin account for an organisation

### All Users
Platform admin can search across all users in all organisations, filter by organisation, and reset any user's password.

**Use case:** An HR Admin forgets their password. Platform admin finds them in All Users and resets it.

---

## 6. Organisation Management

### How Data Isolation Works

Every time an HR Admin logs in and views any data, the system automatically adds this filter to every database query:

```python
organisation = request.user.profile.organisation
data = Model.objects.filter(organisation=organisation)
```

This means:
- Ministry of Finance HR Admin sees only Ministry of Finance data
- They cannot access another organisation's data even by guessing URLs
- If they try `/hr/cycles/` they only see their own cycles

### Organisation Settings
HR Admin (or Org Super Admin) can update:
- Official email
- Phone number
- Address
- Logo

They **cannot** change the subscription percentage — that is set by the Platform Admin.

---

## 7. HR Administration

### Categories

Categories are staff groupings. One category can have multiple cycles.

**Example scenario:**
A ministry has Admin Staff and Medical Officers. They create two categories. Each category can have its own appraisal cycle with different settings.

---

### Cycles

A cycle is one appraisal period. Key fields:

| Field | Purpose | Example |
|-------|---------|---------|
| Name | Identifies the cycle | 2024 Annual Appraisal |
| Category | Links to staff type | Admin Staff |
| Year | The appraisal year | 2024 |
| Period From/To | The evaluation period | Jan 2024 — Dec 2024 |
| Download Fee | What employees pay for PDF | ₦2,000 |
| Status | Draft/Active/Closed | Active |
| Part Deadlines | Optional deadline per part | 31 Jan 2024 |

**Cycle Status Rules:**
- `Draft` → HR is still setting up, employees cannot see it
- `Active` → Employees can be assigned and begin filling forms
- `Closed` → No new submissions accepted

**Only one cycle per organisation can be Active at a time.** The system prevents activating a second cycle if one is already active.

---

### Templates

Templates link a cycle to specific performance aspects. This allows different staff types to be rated on different aspects.

**Example:**
- Template A (Admin Staff): All 16 standard aspects
- Template B (Medical Officers): 14 aspects (excludes "Management of Staff" and "Relations with Public")

Same cycle, different templates, different aspect sets.

---

### Performance Aspects

The 16 standard aspects come from the GEN 79 form and are seeded by the platform. They are available to all organisations.

**The 16 Standard Aspects:**
1. Foresight
2. Penetration
3. Judgement
4. Expression on Paper
5. Oral Expression
6. Numerical Ability
7. Relations with Colleagues
8. Relations with the Public
9. Acceptance of Responsibility
10. Reliability under Pressure
11. Drive and Determination
12. Application of Professional/Technical Knowledge
13. Management of Staff
14. Output of Work
15. Quality of Work
16. Punctuality

**HR can:**
- Edit the description of any aspect
- Deactivate an aspect (hides it from templates)
- Create custom aspects for their organisation

**HR cannot:**
- Delete platform default aspects
- Affect other organisations' aspects

---

### Bulk Appraisal Assignment

This is the most important HR action. It creates the `Appraisal` records that link employees to cycles.

**How it works:**
1. Select an active cycle
2. Select a template
3. Employees are grouped by department in the list
4. Tick individual employees or click "Select All" per department
5. A live counter shows how many are selected
6. Click "Assign Appraisals"

**What happens behind the scenes:**
For each selected employee, the system runs:
```python
Appraisal.objects.get_or_create(
    employee=employee,
    cycle=cycle,
    defaults={'template': template, 'status': 'pending'}
)
```

`get_or_create` means: if an appraisal for this employee+cycle already exists, skip it. If not, create one. This prevents duplicates.

**Result message example:**
`15 appraisal(s) assigned successfully. 3 skipped (already assigned to this cycle).`

---

### User Management

HR Admin can:
- Create new staff accounts
- Edit existing staff profiles
- View staff appraisal history
- See which reporting officer and countersigning officer each employee is assigned to

**Important tip:** Always create Reporting Officers and Countersigning Officers before creating Employees. The employee creation form has dropdown fields for these — they must exist first.

---

## 8. The Appraisal Workflow

### The Four-Part Sequence

The GEN 79 form is divided into four parts. Each part is filled by a different person:

```
PART 1 — Employee
    Fields 1-11b
    Personal records, job description, main duties

PART 2 — Reporting Officer
    Fields 12-14
    Assessment of performance, aspect ratings (A-E), overall rating

PART 3 — Reporting Officer (same person as Part 2)
    Fields 15-19
    Training needs, promotability, long-term potential, general remarks

PART 4 — Countersigning Officer
    Field 20
    Final confirmation or disagreement with reporting officer's assessment
```

### Workflow Enforcement

The system enforces strict sequence. No one can fill a later part until the earlier part is submitted:

| Status | Who Can Act | What They Do |
|--------|------------|--------------|
| `pending` | Employee | Fill and submit Part 1 |
| `part1_submitted` | Reporting Officer | Fill and submit Part 2 |
| `part2_submitted` | Reporting Officer | Fill and submit Part 3 |
| `part3_submitted` | Countersigning Officer | Fill and submit Part 4 |
| `completed` | Employee | Pay and download PDF |
| `closed` | Employee | Re-download PDF |

### Draft Saving

Parts 1, 2, 3 and 4 all support draft saving. This means:
- A user can fill half the form, click "Save Draft", and come back later
- The draft is saved to the database
- When they return, all their previous entries are pre-filled
- Nothing is locked until they click "Submit"

**Technical note:** The form uses two buttons:
```html
<button name="action" value="draft">Save Draft</button>
<button name="action" value="submit">Submit Part X</button>
```
The view reads `request.POST.get('action')` to determine which behaviour to apply.

---

## 9. Part 1 — Employee Personal Records

### What the Employee Sees

The form is pre-filled at the top with fields 1-3 from their profile (read-only):
- Name (Surname and Forenames)
- Date of Birth
- Local Government, Department, Section

The employee fills fields 4-11b themselves:

| Field | Label | Notes |
|-------|-------|-------|
| 4 | Qualification | Degree, diploma, certificate etc. |
| 5 | Date of First Appointment | When they first joined the service |
| 6 | Present Substantive Grade | Their current grade level |
| 7 | Date Appointed to Grade | When they reached this grade |
| 8 | Acting Appointment | Any acting role during the period |
| 9 | Courses Undertaken | Training courses attended |
| 10 | Days Absent on Sick Leave | Total sick days in the period |
| 11 | Present Job and Description | Current role and what it involves |
| 11a | Main Duties (1-5) | In order of importance |
| 11b | Adhoc Duties | Non-continuous duties performed |

### Pre-filling Explained

Fields 1-3 are shown from the UserProfile but NOT saved by this form. They are already in the database. We display them so the employee can verify them. If they are wrong, the employee contacts HR to correct them.

### Submission Lock

Once submitted, Part 1 cannot be edited. This is intentional — the form is a formal government document. Any changes must go through HR.

---

## 10. Part 2 — Reporting Officer Assessment

### Reference Section

At the top of Part 2, the Reporting Officer sees the employee's main duties from Part 1 as read-only reference. This gives them context while rating.

### Field 12 — Job Description Agreement

The officer confirms whether they agree with the employee's description of their job and duties.
- **YES** — they agree, no action needed
- **NO** — they explain the unresolved differences in the text box

### Field 13 — Performance Assessment Narrative

A free-text assessment of how effectively the employee performed the duties listed in 11(a). The officer should address each duty specifically.

### Field 14 — Aspect Ratings

This is the core of Part 2. Each aspect is rated on a scale of A to E:

```
A = Outstanding
B = Above Average
C = Average
D = Below Average
E = Unsatisfactory
```

**How to rate:**
- A or E should only be given if the statement is GENERALLY true and can be supported by specific examples
- B, C, D represent behaviour between the two described extremes
- "Not Applicable" (NA) is available for aspects irrelevant to the role

**The aspects shown depend on the template assigned.** If HR created a template with 14 aspects, the officer sees 14 aspect rows.

### Overall Rating (Diamond Boxes)

After rating individual aspects, the officer selects ONE overall rating:

| Rating | Label | Meaning |
|--------|-------|---------|
| 1 | Outstanding | Exceptionally effective |
| 2 | Very Good | More than generally effective but not positively outstanding |
| 3 | Good | Generally effective |
| 4 | Fair | Performs duties moderately well without serious shortcomings |
| 5 | Unsatisfactory | Definitely ineffective and not up to the duties |

**Important:** This overall rating should reflect the ACTUAL performance in the ACTUAL circumstances that prevailed during the period. External factors affecting performance should be taken into account.

### After Part 2 Submission

After the officer clicks "Submit Part 2", they are automatically redirected to Part 3. This is intentional — the GEN 79 form treats Parts 2 and 3 as one continuous assessment by the same officer.

---

## 11. Part 3 — Training and Promotability

Also filled by the Reporting Officer, immediately after Part 2.

### Field 15 — Training Needs

**(a)** If the appraisal reveals performance could be improved by training, specify exactly what training is needed.

**(b)** If that training cannot be provided on the job, suggest how it could be met (e.g. external courses, workshops, secondment).

**Note:** The officer should take into account any views expressed by the employee themselves about their training needs.

### Field 16 — Next Job

Should this employee be considered in the next year for:
- **(a) A different job in the same grade** — YES or NO
- **(b) Transfer to a similar level in another cadre** — YES or NO

If YES to either, the officer states which kind of job and gives their reasons.

### Field 17 — Promotability

**(a) Normal Promotion:**
The officer selects one of:
- Well Fitted — for promotion to [Grade]
- Fitted — for promotion to [Grade]
- Not Fitted

Then comments on the recommendation.

**(b) Special Promotion:**
For selection to training grades, grade skipping, or promotion into another group. The officer names the target grade and gives reasons.

### Field 18 — Long Term Potential

The officer's assessment of where this employee can go in the long run:

| Option | Meaning |
|--------|---------|
| 1 | Unlikely to progress further |
| 2 | Potential to rise about one grade but probably no further |
| 3 | Potential to rise two or three grades |
| 4 | Exceptional potential |

### Field 19 — General Remarks

Any additional relevant information — particular strengths, weaknesses, or anything not covered by the other fields.

Also records how many years the employee has served under this reporting officer.

---

## 12. Part 4 — Countersigning Officer Report

The final part. The Countersigning Officer:
1. Sees a summary of the Reporting Officer's aspect ratings and overall rating
2. Writes their own report (Field 20)
3. Confirms agreement or notes disagreements

### Field 20 — What to Write

The Countersigning Officer should:
- Confirm agreement with the Reporting Officer's assessment
- OR indicate any remaining disagreements after discussion
- State how frequently they have seen the work of the person reported on
- Add any further relevant comments
- Note whether assessments in the report have been brought to the attention of the employee

### After Part 4 Submission

The appraisal status changes to `completed`. The employee receives a notification on their dashboard showing a green banner with the "Pay & Download PDF" button.

---

## 13. Payment and PDF Download

### Payment Flow

```
Employee sees "Pay & Download PDF" button on dashboard
        ↓
Clicks button
        ↓
System checks: has employee already paid? 
    YES → skip to download
    NO → continue
        ↓
System generates a unique reference (e.g. APPR-1-3A7BC2F1)
        ↓
System calls Paystack API to initialise transaction
        ↓
Paystack returns an authorization URL
        ↓
Employee is redirected to Paystack's secure payment page
        ↓
Employee enters card details on Paystack (we never see card details)
        ↓
Paystack processes payment
        ↓
Paystack redirects employee back to our callback URL
        ↓
Our system calls Paystack's verify API to confirm payment
(we NEVER trust the redirect alone)
        ↓
Paystack confirms payment is genuine
        ↓
System records the payment with revenue split
Appraisal status changes to 'closed'
        ↓
Employee is redirected to PDF download
```

### Why We Verify Payments

After Paystack redirects the employee back to our site, we do NOT immediately give access. We first call Paystack's verification API:

```
GET https://api.paystack.co/transaction/verify/{reference}
Authorization: Bearer sk_test_...
```

Paystack responds with the actual payment status. Only if they confirm `status: success` do we unlock the PDF.

**Why this matters:** Without verification, a malicious user could manually visit the callback URL with a fake reference and download PDFs without paying.

### Test Card Details (for testing)

Use these Paystack test card details:
```
Card Number: 4084 0840 8408 4081
Expiry:      Any future date
CVV:         408
PIN:         0000
OTP:         123456
```

### PDF Generation

The PDF is generated on-the-fly when the employee clicks download. It is NOT stored on disk.

**Why on-the-fly?**
- No disk storage required
- Always reflects current database data
- More secure — no PDF files to accidentally expose

**PDF Contents:**
- Organisation logo and name at top
- "CONFIDENTIAL" and "ANNUAL PERFORMANCE EVALUATION REPORT" headers
- Period of report
- Part 1: All personal records
- Part 2: Performance assessment narrative, aspect ratings table (A-E), overall rating
- Part 3: Training needs, promotability recommendation
- Part 4: Countersigning officer's report
- Employee acknowledgement signature area
- Footer with document reference number

**Note:** "GEN 79" does not appear on the PDF by design.

### Re-downloading

Once paid, the employee can download their PDF as many times as they want at no extra charge. Every download is logged in the `PaymentAccessLog` table for audit purposes.

---

## 14. Revenue Split Model

### How It Works

When an employee pays a download fee, the revenue is split between:
- **Code With Iman (Platform)** — receives the subscription percentage
- **The Organisation** — receives the remainder

**Example with ₦2,000 fee and 10% subscription:**
```
Employee pays:           ₦2,000
Platform earns (10%):    ₦200   → Code With Iman
Organisation earns (90%):₦1,800 → Ministry of Finance
```

### Where the Split is Stored

Every payment record stores:
```
amount                   = ₦2,000
platform_earning         = ₦200
organisation_earning     = ₦1,800
platform_percentage_used = 10.00
```

The `platform_percentage_used` is stored at the time of payment. This means if the rate changes later, historical payments still show the correct rate that was applied.

### Setting Different Rates Per Organisation

The Platform Admin can set different subscription percentages for different organisations:
- Large organisation (high volume): 8%
- Standard organisation: 10%
- Small organisation (low volume): 12%

This allows flexible pricing negotiations with each client.

### Revenue Reports

- **Platform Admin dashboard** — shows total platform revenue across all organisations
- **HR Admin payments page** — shows their organisation's payment history with the split breakdown
- **Employee payments page** — shows their own payment history

---

## 15. Performance Aspects

### The Rating Scale

Each of the 16 aspects (or custom aspects) is rated on a 5-point scale:

| Rating | Meaning | When to Use |
|--------|---------|-------------|
| A | Outstanding | Generally true, supported by specific examples |
| B | Above Average | Between A and C |
| C | Average | Middle ground |
| D | Below Average | Between C and E |
| E | Unsatisfactory | Generally true, supported by specific examples |
| NA | Not Applicable | Aspect is irrelevant to this role |

### Adding Custom Aspects

HR Admin can add aspects specific to their organisation:

1. Go to **Performance Aspects** in the sidebar
2. Click **Add Custom Aspect**
3. Fill in:
   - Label (e.g. "Digital Literacy")
   - Outstanding Description (e.g. "Uses digital tools with exceptional proficiency")
   - Unsatisfactory Description (e.g. "Struggles with basic digital tools")
   - Order (where it appears in the list)

Custom aspects are only visible to the organisation that created them.

### Deactivating Aspects

If an aspect is not relevant to your organisation, deactivate it instead of deleting:
- It disappears from template selection
- Historical data is preserved

---

## 16. Data Isolation and Security

### The Multi-Tenancy Rule

Every model in the system has an `organisation` foreign key:
```python
class AppraisalCycle(models.Model):
    organisation = models.ForeignKey(Organisation, ...)
    name = models.CharField(...)
```

Every view filters by the logged-in user's organisation:
```python
cycles = AppraisalCycle.objects.filter(
    organisation=request.user.profile.organisation
)
```

This means:
- Even if an HR Admin from Ministry of Finance guesses the URL `/hr/cycles/3/edit/` where cycle 3 belongs to Ministry of Health, they get a 404 error
- The system does not reveal that cycle 3 exists — it simply says "not found"

### Role-Based Access Control

Each view has a decorator that checks the user's role before processing:

```python
@hr_required       # Only hr_admin and super_admin can access
@login_required    # Must be logged in
```

If a user tries to access a view they don't have permission for:
- They are redirected to their dashboard
- They see an error message
- No data is revealed

### Inactive Organisation Lock

If the Platform Admin deactivates an organisation, ALL users in that organisation cannot log in. The login view checks:
```python
if not profile.organisation.is_active:
    # Reject login with message
```

This is used when an organisation's subscription lapses.

---

## 17. Testing Checklist

Use this checklist for full system testing. Test each role separately.

---

### Platform Admin Tests

```
Account Setup
[ ] Login as superuser at http://127.0.0.1:8000
[ ] Dashboard shows platform statistics
[ ] Sidebar shows Platform Admin section only

Organisation Management
[ ] Click Organisations → see list (or empty state)
[ ] Click Onboard New Organisation → form loads
[ ] Fill form and submit → redirected to Create HR Admin
[ ] Create HR Admin → success message
[ ] Organisation appears in list with correct percentage
[ ] Click Edit on organisation → can change subscription %
[ ] Click Toggle → organisation becomes Inactive
[ ] Toggle again → organisation becomes Active

User Management
[ ] Click All Users → see all users across all organisations
[ ] Search by name → filters results
[ ] Filter by organisation → shows only that org's users
[ ] Click Reset Password on any user → form loads
[ ] Enter new password → success message
[ ] Login as that user with new password → works
```

---

### HR Admin Tests

```
Login and Dashboard
[ ] Login as HR Admin
[ ] Dashboard shows organisation name in blue banner
[ ] Dashboard shows stats (all zeros initially)
[ ] Sidebar does NOT show Platform Admin section
[ ] Sidebar shows HR Tools section

Categories
[ ] Click Categories → empty list with Create button
[ ] Create a category (e.g. "Admin Staff") → appears in list
[ ] Edit the category → changes saved
[ ] Deactivate → badge changes to Inactive

Cycles
[ ] Click Appraisal Cycles → empty list
[ ] Create a cycle → all fields save correctly
[ ] Download fee is set correctly (e.g. ₦2,000)
[ ] Cycle status shows Draft
[ ] Click Activate → status changes to Active
[ ] Try to activate second cycle → warning message appears

Templates
[ ] Click Templates → empty list
[ ] Create a template → select cycle and aspects
[ ] All 16 aspects appear in checkbox list
[ ] Save → template appears in list showing aspect count

Performance Aspects
[ ] Click Performance Aspects → all 16 standard aspects visible
[ ] Edit one aspect → description saves correctly
[ ] Deactivate an aspect → shows Inactive badge
[ ] Add Custom Aspect → appears in list with "Custom" badge
[ ] Custom aspect appears in template creation

User Management
[ ] Create a Reporting Officer account
[ ] Create a Countersigning Officer account
[ ] Create an Employee → Reporting/Countersigning dropdowns show correct users
[ ] View user list → all created users appear
[ ] View user detail → shows profile info and appraisal history
[ ] Edit user → changes save

Bulk Assignment
[ ] Click Assign Appraisals
[ ] Select cycle → only active cycles appear
[ ] Select template
[ ] Employees appear grouped by department
[ ] Tick individual employees
[ ] Click Select All → all employees ticked
[ ] Live count updates correctly
[ ] Click Assign → success message with created/skipped count
[ ] Click Assign again → all skipped (no duplicates)

Payment Reports
[ ] Click All Payments → shows payment table
[ ] After test payment: revenue split shows correctly
[ ] Total Collected, Org Share, Platform Fee all correct
```

---

### Employee Tests

```
Login and Dashboard
[ ] Login as employee
[ ] Dashboard shows welcome banner with name and organisation
[ ] Yellow notification shows if appraisal is pending
[ ] Sidebar shows badge count on My Appraisals

Part 1
[ ] Click Start Part 1 → form loads
[ ] Fields 1, 2, 3 are pre-filled (read only)
[ ] Fill qualification and other fields
[ ] Click Save Draft → saved, form reloads with data
[ ] Close browser, login again → draft data still there
[ ] Submit Part 1 → success message
[ ] Status changes to "Awaiting Reporting Officer"
[ ] Cannot access Part 1 again after submission

After Completion
[ ] Status changes to Completed after all parts done
[ ] Green notification banner appears on dashboard
[ ] "Pay & Download PDF" button visible
[ ] My Payments sidebar shows "1 ready" badge
[ ] Click Pay & Download PDF → redirects to Paystack
[ ] Complete test payment on Paystack
[ ] Redirected back to our site
[ ] Success message shows
[ ] PDF downloads automatically
[ ] PDF opens in PDF reader
[ ] PDF shows organisation name (not GEN 79)
[ ] All 4 parts visible in PDF
[ ] Aspect ratings shown correctly in table
[ ] Click Download PDF again → re-downloads without paying again
```

---

### Reporting Officer Tests

```
Login and Dashboard
[ ] Login as reporting officer
[ ] Dashboard shows pending assessment count
[ ] Only sees employees assigned to them

Part 2
[ ] Click Start Assessment on an employee's appraisal
[ ] Employee's main duties visible at top (read only)
[ ] Can rate all aspects A-E using radio buttons
[ ] Overall rating clickable (1-5)
[ ] Save draft → ratings preserved
[ ] Submit Part 2 → auto redirected to Part 3

Part 3
[ ] Part 3 form loads with all fields
[ ] Select promotion fitness
[ ] Select long term potential
[ ] Submit Part 3 → redirected to appraisal detail
[ ] Status shows "Awaiting Countersign"
```

---

### Countersigning Officer Tests

```
Login and Dashboard
[ ] Login as countersigning officer
[ ] Dashboard shows pending countersign count

Part 4
[ ] Click Countersign
[ ] Summary of reporting officer's ratings visible at top
[ ] Overall rating displayed
[ ] Can write countersigning report
[ ] Submit Part 4 → appraisal status becomes Completed
[ ] Employee receives notification on their dashboard
```

---

### Data Isolation Tests

```
[ ] Login as HR Admin of Org A
[ ] Note number of categories visible
[ ] Login as HR Admin of Org B (different browser/incognito)
[ ] Their categories page shows only Org B's data
[ ] Manually visit /hr/cycles/{id} where id belongs to Org A → 404
[ ] Employee from Org A cannot see Org B employee's appraisal
[ ] Reporting Officer can only see their own subordinates' appraisals
```

---

## 18. Troubleshooting Common Issues

### "No active cycles found" on Assign Appraisals page
**Cause:** The cycle exists but its status is still "Draft"
**Fix:** Go to Appraisal Cycles → click Activate on the relevant cycle

---

### Employee's Reporting/Countersigning Officer dropdown is empty
**Cause:** No users with that role exist yet in the organisation
**Fix:** Create the Reporting Officer and Countersigning Officer accounts first, then create the employee

---

### Part 2 is not available for the Reporting Officer
**Cause:** The employee has not yet submitted Part 1
**Fix:** Employee must log in and submit Part 1 first

---

### Payment redirects to Paystack but fails
**Cause:** The employee's account has no email address
**Fix:** HR Admin should edit the employee's account and add a valid email address

---

### Payment shows "Failed" immediately without going to Paystack
**Cause:** The `PAYSTACK_SECRET_KEY` in `.env` is set to the public key (starts with `pk_test_`)
**Fix:** Replace with the secret key (starts with `sk_test_`) from your Paystack dashboard

---

### PDF downloads but some fields show "—"
**Cause:** Some form fields were left blank during submission
**Fix:** This is expected behaviour — "—" appears for optional fields that were not filled

---

### "Organisation not found" after logging in
**Cause:** The user account has no organisation linked to their profile
**Fix:** Platform Admin should check the user in "All Users" and verify their organisation field is set

---

### HR Admin can see all categories from all organisations
**Cause:** A view is using `.all()` instead of filtering by organisation
**Fix:** Check that `category_list` view filters by `organisation=get_user_organisation(request)`

---

## 19. Glossary

| Term | Definition |
|------|-----------|
| **Appraisal** | One employee's complete evaluation record for one cycle |
| **Aspect** | A specific quality being rated (e.g. Foresight, Punctuality) |
| **Callback URL** | The page Paystack sends the user back to after payment |
| **Category** | A staff grouping (e.g. Admin Staff, Medical Officers) |
| **Closed** | Appraisal status after employee has paid and downloaded PDF |
| **Completed** | Appraisal status after all 4 parts are submitted — PDF ready for payment |
| **Countersigning Officer** | Senior officer who provides final sign-off (Part 4) |
| **Cycle** | One appraisal period with its own settings and download fee |
| **Django** | The Python web framework the system is built on |
| **Download Fee** | Amount the employee pays to download their PDF — set by HR per cycle |
| **Draft** | A partially-filled form saved but not yet submitted |
| **GEN 79** | The official Nigerian government annual performance evaluation form (not shown on PDF output) |
| **HR Admin** | Organisation-level administrator who manages staff and appraisal setup |
| **Kobo** | Nigerian currency subdivision (100 kobo = 1 Naira) — Paystack uses kobo |
| **MDA** | Ministry, Department or Agency |
| **Multi-tenancy** | One system serving multiple independent organisations simultaneously |
| **Organisation** | A ministry or MDA using the platform |
| **Overall Rating** | The 1-5 summary rating of an employee's total performance |
| **Paystack** | The Nigerian payment gateway used for collecting download fees |
| **PDF** | The downloadable evaluation report generated after all 4 parts are completed and paid for |
| **Platform Admin** | Code With Iman — the business owner who manages all organisations |
| **Reporting Officer** | The officer who assesses the employee (Parts 2 and 3) |
| **Revenue Split** | The percentage split of download fees between platform and organisation |
| **SaaS** | Software as a Service — one application serving many organisations |
| **Status** | The current stage of an appraisal (pending → part1_submitted → ... → closed) |
| **Subscription Percentage** | The platform's cut from each employee's download fee |
| **Template** | A named set of aspects linked to a cycle |
| **Verification** | Calling Paystack's API to confirm a payment is genuine before unlocking access |

---

*Document Version: 1.0*
*System: Annual Performance Evaluation System*
*Developer: Code With Iman — CAC Reg. 9631094, Lafia, Nasarawa State*
*Last Updated: June 2026*
