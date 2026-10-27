# Marine Pollution Dashboard

A Flask-based web application for exploring and analyzing marine pollution and environmental monitoring data, with a focus on NOAA-style pollution records and supporting admin management tools.

## Overview

This project provides a dashboard for:

- viewing summary statistics about marine pollution datasets
- exploring individual records by pollutant, location, and year
- analyzing trends and historical patterns
- viewing pollution data on an interactive map
- managing admin access and audit logs

The application is designed for exploratory environmental analysis and educational interpretation. It does not replace formal environmental assessment or regulatory decision-making.

## Features

- Home dashboard with dataset totals and pollutant summaries
- Explore page to filter pollution records by pollutant, location, and year
- Analytics page with insights, historical trends, and forecast-style estimates
- Map view showing geolocated pollution observations
- Admin login and dashboard
- Pollutant management page
- Audit log viewing for administrative activity
- Health endpoint for simple service checks

## Database & Security Highlights

- **Relational Schema:** Structured relational tables for NOAA pollution records, normalized pollutant lists, administrator accounts, and secure audit tracking.
- **Data Integrity & Security:** Secure password hashing (Werkzeug) for admin authentication and parameterized queries protecting against SQL injection.
- **Audit Logging:** Automated database logging tracking administrative actions, logins, and data modifications with timestamps.

## Tech Stack

- Python
- Flask
- Flask-WTF / CSRF protection
- MySQL Connector for Python
- MySQL database
- HTML templates and static assets for the UI

## Project Structure

```text
marine_pollution/
├── app.py                  # Flask application and routes
├── db.py                  # Database connection settings
├── create_admin.py        # Create an admin account
├── import_data.py         # Import NOAA CSV data into MySQL
├── test_db.py             # Database connectivity check
├── requirements.txt       # Python dependencies
├── data/
│   └── noaa_pollution_expanded.csv
├── static/                # CSS, JS, images
├── templates/             # HTML pages
└── README.md
```

## Prerequisites

Before running the project, make sure you have:

- Python 3.9+
- MySQL server installed and running
- access to a database user with privileges to create and modify tables
- a configured environment for Flask secrets and database connection settings

## Environment Variables

Set the following environment variables before running the app:

```bash
export FLASK_SECRET_KEY="your-secret-key"
export DB_HOST="localhost"
export DB_PORT="3306"
export DB_USER="root"
export DB_PASSWORD="your-password"
export DB_NAME="marine_pollution_db"
```

On Windows PowerShell:

```powershell
$env:FLASK_SECRET_KEY="your-secret-key"
$env:DB_HOST="localhost"
$env:DB_PORT="3306"
$env:DB_USER="root"
$env:DB_PASSWORD="your-password"
$env:DB_NAME="marine_pollution_db"
```

## Database Setup

Create a MySQL database and configure the app to use it. The project expects tables such as:

- `noaa_pollution_data`
- `pollutants`
- `admin_users`
- `audit_logs`

The app code queries these tables directly, so the database schema must match the expected structure.

## Installation

1. Open a terminal in the project folder.
2. Create and activate a virtual environment:

```bash
python -m venv venv
```

On Windows:

```powershell
venv\Scripts\activate
```

On macOS/Linux:

```bash
source venv/bin/activate
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

## Importing Data

To load the NOAA pollution CSV into the database:

```bash
python import_data.py
```

This script reads the CSV in `data/noaa_pollution_expanded.csv` and inserts new records into `noaa_pollution_data`.

## Creating an Admin Account

To create an administrator account for the admin login:

```bash
python create_admin.py
```

You will be prompted for:

- admin username
- admin password

## Running the Application

Start the Flask app:

```bash
python app.py
```

Then open the app in a browser at:

```text
http://localhost:5000/
```

## Main Routes

- `/` — main dashboard
- `/explore` — filtered data exploration
- `/analytics` — trends, summaries, and educational guidance
- `/map` — map-based pollution view
- `/admin/login` — administrator login
- `/admin` — admin dashboard
- `/admin/pollutants` — pollutant management
- `/admin/audit-logs` — audit log review
- `/health` — health check endpoint

## Notes

- The analytics pages provide source hypotheses and safety guidance based on the selected pollutant type, but they are educational summaries rather than confirmed cause attribution.
- The app is intended for environmental data exploration, not for emergency response or formal regulatory interpretation.

## License

This project does not currently declare a license. If you plan to share or distribute it publicly, add an appropriate open-source license file.
> Project status: Active and running!

## Team & Contributors

- **Sanjana Dyaga** (`sanjana-web67`) — Database Integration, Git Workflow & Analytics
- **Shiban** (`Shibxn`) — Frontend Development & UI Design
- **Project Lead / Collaborator** (`ashx-bla`) — Core Platform Architecture
