# 🏛️ Annual Performance Evaluation System

<div align="center">

![Python](https://img.shields.io/badge/Python-3.12-blue?style=flat-square&logo=python)
![Django](https://img.shields.io/badge/Django-4.2.7-green?style=flat-square&logo=django)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-18-blue?style=flat-square&logo=postgresql)
![License](https://img.shields.io/badge/License-Proprietary-red?style=flat-square)
![Status](https://img.shields.io/badge/Status-Production%20Ready-brightgreen?style=flat-square)
![CAC](https://img.shields.io/badge/CAC%20Registered-9631094-orange?style=flat-square)

**A SaaS platform that digitises the Nigerian Government GEN 79 Annual Performance Evaluation process for Ministries, Departments and Agencies (MDAs).**

*Built by [Code With Iman](https://github.com/Eelblitz) — Lafia, Nasarawa State, Nigeria*

-----

[Features](#-features) •
[Tech Stack](#-tech-stack) •
[Getting Started](#-getting-started) •
[Architecture](#-architecture) •
[Roles](#-user-roles) •
[License](#-license) •
[Contact](#-contact)

</div>

-----

## 📋 Overview

The **Annual Performance Evaluation System** replaces the manual paper-based GEN 79 appraisal process with a structured, role-controlled digital workflow. Multiple ministries and MDAs can use the same platform simultaneously with complete data isolation between organisations.

### The Problem It Solves

In Nigerian government ministries, the annual staff appraisal process traditionally involves:

- Physical paper forms that get lost or damaged
- No enforcement of the correct submission sequence
- Delays caused by officers being unavailable to sign
- No audit trail of who filled what and when
- No centralised record keeping

### The Solution

This system enforces the correct GEN 79 four-part workflow digitally:

```
Employee fills Part 1 (Personal Records)
        ↓
Reporting Officer fills Part 2 (Performance Assessment) and Part 3 (Training & Promotability)
        ↓
Countersigning Officer fills Part 4 (Final Sign-off)
        ↓
Employee pays a token fee and downloads their official PDF report
```

-----

## ✨ Features

### Multi-Tenancy SaaS

- Multiple organisations (ministries/MDAs) served from one platform
- Complete data isolation — no organisation can see another’s data
- Per-organisation subscription percentage for revenue sharing

### Complete GEN 79 Workflow

- All four parts of the official evaluation form
- Draft saving at every step — users can return to incomplete forms
- Strict workflow enforcement — each part unlocks only when the previous is submitted
- Dynamic performance aspects — HR can add, edit or deactivate rating criteria

### Role-Based Access Control

- Five distinct roles with granular permissions
- Role-specific dashboards with relevant actions and notifications
- Notification badges that update in real-time based on workflow status

### Payment Integration

- Paystack integration for secure PDF download payments
- Automatic revenue split between platform and organisation
- Complete payment audit trail with download logs
- Support for free downloads (zero fee cycles)

### PDF Generation

- Professional PDF generated on-the-fly from live database data
- Organisation logo and branding on every document
- No GEN 79 branding — outputs as “Annual Performance Evaluation Report”
- Unlimited re-downloads after payment

### Platform Administration

- Full platform super admin dashboard for Code With Iman
- Onboard new organisations with configurable subscription rates
- Reset any user’s password across any organisation
- Platform-wide revenue analytics

-----

## 🛠️ Tech Stack

|Layer          |Technology         |Purpose                       |
|---------------|-------------------|------------------------------|
|Backend        |Django 4.2.7       |Web framework                 |
|Language       |Python 3.12        |Programming language          |
|Database       |PostgreSQL 18      |Primary data store            |
|Payment        |Paystack           |Payment processing            |
|PDF            |ReportLab          |PDF generation                |
|Styling        |Bootstrap 5        |Frontend UI                   |
|Icons          |Bootstrap Icons    |UI icons                      |
|Forms          |django-crispy-forms|Form rendering                |
|Static Files   |WhiteNoise         |Production static file serving|
|Web Server     |Gunicorn           |Production WSGI server        |
|Hosting        |Render             |Cloud deployment              |
|Version Control|GitHub             |Source code management        |

-----

## 🚀 Getting Started

### Prerequisites

Before setting up, ensure you have:

- Python 3.12 installed
- PostgreSQL 18 installed and running
- Git installed
- A Paystack account (for payment features)

-----

### 1. Clone the Repository

```bash
git clone https://github.com/Eelblitz/appraisal-system.git
cd appraisal-system
```

-----

### 2. Create and Activate Virtual Environment

```bash
# Create virtual environment
python -m venv venv

# Activate on Windows
venv\Scripts\activate

# Activate on Mac/Linux
source venv/bin/activate
```

-----

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

-----

### 4. Create the Database

Open PostgreSQL and create the database:

```sql
CREATE DATABASE appraisal_db;
```

-----

### 5. Configure Environment Variables

Create a `.env` file in the project root:

```env
# Django
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database
DB_NAME=appraisal_db
DB_USER=postgres
DB_PASSWORD=your-postgres-password
DB_HOST=localhost
DB_PORT=5432

# Paystack
PAYSTACK_SECRET_KEY=sk_test_your_secret_key
PAYSTACK_PUBLIC_KEY=pk_test_your_public_key
PAYSTACK_BASE_URL=https://api.paystack.co
```

> ⚠️ **Security Note:** Never commit `.env` to version control. It is listed in `.gitignore`.

-----

### 6. Run Migrations

```bash
python manage.py migrate
```

-----

### 7. Seed Performance Aspects

This populates the 16 standard GEN 79 performance aspects:

```bash
python manage.py seed_aspects
```

-----

### 8. Create Platform Super Admin

```bash
python manage.py createsuperuser
```

-----

### 9. Start the Development Server

```bash
python manage.py runserver
```

Visit `http://127.0.0.1:8000` and log in with your superuser credentials.

-----

## 🏗️ Architecture

### Application Structure

```
appraisal_project/          ← Django project configuration
│
├── organisations/          ← Multi-tenancy: Organisation model and management
├── accounts/               ← Authentication, user profiles, role management
├── hr/                     ← Cycles, categories, templates, performance aspects
├── appraisal/              ← The 4-part GEN 79 form and workflow engine
├── payments/               ← Paystack integration, PDF generation
├── core/                   ← Role-specific dashboards and context processors
│
├── templates/              ← All HTML templates
├── static/                 ← Static files (CSS, JS, images)
├── media/                  ← User uploaded files (logos, profile photos)
└── docs/                   ← System documentation
```

-----

### Database Design

```
Organisation (Tenant)
    │
    ├── UserProfile (accounts)
    │       └── User (Django built-in)
    │
    ├── AppraisalCategory (hr)
    ├── AppraisalCycle (hr)
    │       └── AppraisalTemplate (hr)
    │               └── TemplateAspect (hr)
    │                       └── PerformanceAspect (hr)
    │
    ├── Appraisal (appraisal)
    │       ├── PartOne
    │       ├── PartTwo
    │       │       └── AppraisalAspectRating
    │       ├── PartThree
    │       └── PartFour
    │
    └── Payment (payments)
            └── PaymentAccessLog
```

-----

### Multi-Tenancy Pattern

Every model has an `organisation` foreign key. Every view filters by the logged-in user’s organisation:

```python
# Every HR view follows this pattern
organisation = request.user.profile.organisation
cycles = AppraisalCycle.objects.filter(organisation=organisation)
```

This ensures complete data isolation between organisations.

-----

## 👥 User Roles

|Role                      |Level       |Key Responsibilities                                          |
|--------------------------|------------|--------------------------------------------------------------|
|**Platform Super Admin**  |Platform    |Manage organisations, set revenue percentages, reset passwords|
|**HR Admin**              |Organisation|Create staff, manage cycles/templates, assign appraisals      |
|**Reporting Officer**     |Organisation|Fill Part 2 and Part 3 for assigned employees                 |
|**Countersigning Officer**|Organisation|Fill Part 4, provide final sign-off                           |
|**Employee**              |Organisation|Fill Part 1, pay and download completed PDF                   |

-----

## 💰 Revenue Model

The platform operates on a **percentage-based revenue share** model:

```
Employee pays ₦X download fee (set by HR per cycle)
        ↓
Platform takes Y% (set per organisation, e.g. 10%)
Organisation receives (100-Y)%

Example: ₦2,000 fee at 10%
    Platform earns:      ₦200
    Organisation earns:  ₦1,800
```

Revenue split is recorded on every payment record and visible on the HR Admin payments dashboard.

-----

## 🔒 Security Features

- **Multi-tenancy isolation** — organisations cannot access each other’s data
- **Role-based access control** — each view checks the user’s role before processing
- **Payment verification** — Paystack payments are always verified via API before unlocking downloads
- **CSRF protection** — all forms include Django’s CSRF tokens
- **Password hashing** — Django’s built-in password hashing (PBKDF2)
- **Environment variables** — all secrets stored in `.env`, never in code
- **Inactive organisation lock** — deactivated organisations cannot log in

-----

## 📄 API Endpoints (Internal)

The system uses standard Django URL routing. Key URL namespaces:

|Namespace      |Base URL     |Purpose                              |
|---------------|-------------|-------------------------------------|
|`accounts`     |`/accounts/` |Authentication and user management   |
|`core`         |`/core/`     |Dashboards                           |
|`hr`           |`/hr/`       |HR tools (cycles, templates, aspects)|
|`appraisal`    |`/appraisal/`|Appraisal forms and workflow         |
|`payments`     |`/payments/` |Payment processing and PDF download  |
|`organisations`|`/platform/` |Platform admin (organisations)       |

-----

## 🧪 Running Tests

Run the full system test checklist documented in `docs/SYSTEM_DOCUMENTATION.md`.

For automated tests (future):

```bash
python manage.py test
```

-----

## 🚢 Deployment on Render

### 1. Push to GitHub

```bash
git add .
git commit -m "Ready for deployment"
git push origin main
```

### 2. Create a Render Account

Go to [render.com](https://render.com) and sign up.

### 3. Create a PostgreSQL Database on Render

- New → PostgreSQL
- Name: `appraisal-db`
- Copy the connection string

### 4. Create a Web Service on Render

- New → Web Service
- Connect your GitHub repository
- Build Command: `pip install -r requirements.txt && python manage.py collectstatic --noinput && python manage.py migrate`
- Start Command: `gunicorn appraisal_project.wsgi:application`

### 5. Set Environment Variables on Render

Add all variables from your `.env` file in the Render dashboard, plus:

```
DATABASE_URL=your-render-postgres-connection-string
DEBUG=False
ALLOWED_HOSTS=your-app-name.onrender.com
```

-----

## 📁 Key Files

|File                                    |Purpose                           |
|----------------------------------------|----------------------------------|
|`requirements.txt`                      |Python package dependencies       |
|`render.yaml`                           |Render deployment configuration   |
|`Procfile`                              |Process file for web server       |
|`.env`                                  |Environment variables (not in git)|
|`docs/SYSTEM_DOCUMENTATION.md`          |Complete system documentation     |
|`hr/management/commands/seed_aspects.py`|Seeds the 16 GEN 79 aspects       |

-----

## 📜 License

Copyright © 2026 Code With Iman. All rights reserved.

This software is proprietary and confidential. The source code is provided for
review and collaboration purposes only. Unauthorised copying, modification,
distribution, or use of this software, in whole or in part, is strictly
prohibited without the express written permission of Code With Iman.

**Business Registration:** CAC Business Name Registration No. 9631094
**Registered:** Federal Republic of Nigeria, 23rd June 2026

See the <LICENSE> file for full terms.

-----

## 📞 Contact

**Code With Iman**
Software Development, Web Design and Intranet Development

- 📍 No. 3, Hospital Road, beside Federal University Teaching Hospital, Lafia, Nasarawa State, Nigeria
- 🏢 CAC Reg. No.: 9631094
- 💼 TIN: 2622591309579
- 🐙 GitHub: [@Eelblitz](https://github.com/Eelblitz)

-----

<div align="center">

Built with ❤️ in Lafia, Nasarawa State, Nigeria

*Digitising government processes, one system at a time.*

</div>
