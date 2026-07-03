# Hostinger Cold Email Automation

A full-stack automation platform designed to process leads from a CSV, intelligently classify their website issues (UI, SEO, etc.), and send highly personalized cold emails via Hostinger SMTP. 

## 🚀 Features
- **Smart Classification Engine**: Reads a CSV's "Website Review" column to categorize leads (SEO, Bad UI, Not Working, etc.).
- **Dynamic Templating**: Automatically matches the lead to the correct email template (from `templates/USA`, `UK`, or `UAE`) and renders it with their data.
- **Robust Data Parsing**: Built-in edge-case handling for malformed CSVs, empty cells, and case-sensitive headers.
- **Live Execution Dashboard**: Next.js frontend to monitor campaign speed, progress, and real-time logs.
- **SQLite Campaign History**: Persists all completed campaign statistics (Sent, Failed, Skipped).

## 🛠 Tech Stack
- **Frontend**: Next.js 14, Tailwind CSS, Lucide Icons
- **Backend**: FastAPI, Python 3
- **Database**: SQLite (Campaign Logging)
- **Email**: Hostinger SMTP (Standard `smtplib`)

## 📦 Local Setup Instructions

### 1. Clone the Repository
```bash
git clone https://github.com/your-username/hostinger-cold-email.git
cd hostinger-cold-email
```

### 2. Configure Environment Variables
Create a `.env` file in the root directory (alongside `requirements.txt`) and add your Hostinger credentials:
```env
SMTP_USER="your-email@domain.com"
SMTP_PASS="your-email-password"
```

### 3. Start the Backend (FastAPI)
Open a terminal in the root directory and set up the Python environment:
```bash
# Create a virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows use: venv\Scripts\activate

# Install requirements
pip install -r requirements.txt

# Start the API server
uvicorn backend.api:app --reload
```
The backend will run on `http://localhost:8000`.

### 4. Start the Frontend (Next.js)
Open a **new** terminal window:
```bash
cd frontend

# Install Node dependencies
npm install

# Start the development server
npm run dev
```
The frontend will run on `http://localhost:3000`.

## 📖 How to Use
1. Navigate to `http://localhost:3000`.
2. Select your target country (USA, UK, or UAE) from the dropdown.
3. Upload your `leads.csv` file. (Ensure it has at least the following columns: `Company Name`, `Email`, and `Website Review`).
4. Click **Execute Campaign** to start sending emails. Monitor the transmission in real-time!

## 📁 Project Structure
- `/backend`: FastAPI endpoints, SMTP sender, template renderer, and SQLite database manager.
- `/frontend`: Next.js React application for the Dashboard UI.
- `/templates`: Country-specific `.txt` email templates.
- `/data`: SQLite database and raw uploaded CSVs (generated automatically upon use).
- `/logs`: Detailed success/failed CSV logs for tracking and resuming campaigns (generated automatically upon use).
