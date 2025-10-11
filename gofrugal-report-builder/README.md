# GoFrugal Report Builder

**Custom Report Builder for GoFrugal HO Portal - No Vendor Fees Required!**

## 🎯 Overview

This application helps you:
- **Auto-login** to GoFrugal HO portal
- **Discover all available reports** in the portal
- **Extract schemas** (columns) from any report
- **Build custom reports** by selecting columns from multiple reports
- **Eliminate vendor customization fees**

## 🏗️ Architecture

```
gofrugal-report-builder/
├── backend/                    # Python FastAPI backend
│   ├── server.py              # REST API server
│   ├── portal_scraper.py      # Playwright automation for GoFrugal
│   ├── requirements.txt       # Python dependencies
│   └── .env                   # Credentials (secure)
├── frontend/                   # React frontend
│   ├── src/
│   │   ├── components/
│   │   │   ├── Dashboard.js   # Main control panel
│   │   │   ├── SchemaViewer.js # View extracted schemas
│   │   │   └── ReportBuilder.js # Build custom reports
│   │   ├── App.js
│   │   └── index.js
│   └── package.json
├── database/
│   └── schemas/               # Extracted report schemas (JSON)
├── logs/                      # Screenshots & logs
└── README.md
```

## 🚀 Features

### Phase 2 Implementation (Current)

✅ **Portal Automation**
- Automated login to GoFrugal HO portal
- Session management
- Error handling and retries

✅ **Report Discovery**
- Auto-discover all available reports
- Extract report names and URLs
- Catalog all reports in the system

✅ **Schema Extraction**
- Extract column names from any report
- Sample data extraction
- Store schemas in JSON format
- Visual screenshots of each report

✅ **Report Builder UI**
- Dashboard for scraper control
- Schema viewer (all columns from all reports)
- Custom report builder (drag-and-drop column selection)
- Export report configurations

✅ **Future Enhancements**
- Apply conversion rules (Cartons, Boxes, Pieces)
- Schedule automatic scraping every 4 hours
- Data fetching and transformation
- Multi-format export (CSV, Excel, PDF)

## 📋 Prerequisites

- Python 3.11+
- Node.js 18+
- Yarn package manager
- GoFrugal HO portal credentials

## 🔧 Installation

1. **Install Backend Dependencies**
```bash
cd /app/gofrugal-report-builder/backend
pip install -r requirements.txt
playwright install chromium
```

2. **Install Frontend Dependencies**
```bash
cd /app/gofrugal-report-builder/frontend
yarn install
```

3. **Configure Environment**
Edit `/app/gofrugal-report-builder/backend/.env`:
```env
GOFRUGAL_URL=https://bbcohq.gofrugal.com
GOFRUGAL_USERNAME=your_username
GOFRUGAL_PASSWORD=your_password
```

## 🎮 Usage

### Option 1: Manual Start

**Start Backend:**
```bash
cd /app/gofrugal-report-builder/backend
python3 server.py
```

**Start Frontend:**
```bash
cd /app/gofrugal-report-builder/frontend
yarn start
```

### Option 2: Supervisor (Recommended)

```bash
sudo supervisorctl -c /app/gofrugal-report-builder/supervisord.conf restart all
```

## 🌐 Access

- **Frontend UI:** http://localhost:3000
- **Backend API:** http://localhost:8001
- **API Docs:** http://localhost:8001/docs

## 📖 How to Use

### Step 1: Initialize Scraper
1. Open the Dashboard
2. Click "1. Initialize & Login"
3. Wait for successful login confirmation

### Step 2: Discover Reports
1. Click "2. Discover Reports"
2. View all available reports in the portal
3. Screenshots will be saved in `/logs` directory

### Step 3: Extract Schemas
1. Click "3. Extract Report 474" (or any report)
2. Schema will be extracted and saved
3. View extracted columns in Schema Viewer tab

### Step 4: Build Custom Reports
1. Go to "Report Builder" tab
2. Select columns from any report
3. Build your custom report layout
4. Export configuration

## 🔌 API Endpoints

### Scraper Control
- `POST /api/scraper/initialize` - Initialize and login
- `POST /api/scraper/discover-reports` - Discover all reports
- `POST /api/scraper/extract-schema` - Extract schema from report
- `POST /api/scraper/close` - Close scraper

### Schema Management
- `GET /api/schemas` - List all extracted schemas
- `GET /api/schemas/{report_id}` - Get specific schema
- `GET /api/screenshots` - List screenshots
- `GET /api/screenshots/{filename}` - Get screenshot

## 📊 Data Storage

### Extracted Schemas
Location: `/app/gofrugal-report-builder/database/schemas/`

Format:
```json
{
  "report_id": 474,
  "report_url": "https://...",
  "extracted_at": "2025-10-11T...",
  "columns": ["Item Code", "Item Name", "Stock Qty", ...],
  "sample_data": ["value1", "value2", ...]
}
```

### Screenshots
Location: `/app/gofrugal-report-builder/logs/`
- `login_page.png` - Login page
- `after_login.png` - After login
- `main_page.png` - Main portal page
- `report_474.png` - Report screenshots

## 🔒 Security

- Credentials stored in `.env` file (not committed to git)
- Browser runs in sandboxed environment
- No data stored on external servers
- All data stays local

## 🐛 Troubleshooting

### Login Failed
- Check credentials in `.env` file
- Verify portal URL is correct
- Check screenshots in `/logs` for error messages

### Report Not Found
- Try different URL patterns
- Check if you have access to the report
- View HTML source in `/logs/main_page.html`

### Schema Extraction Failed
- Report may use JavaScript rendering
- Try manual navigation to the report first
- Check browser screenshots

## 🔄 Next Steps

1. ✅ Portal automation and login
2. ✅ Report discovery
3. ✅ Schema extraction
4. ✅ Basic report builder UI
5. ⏳ Integration with conversion master
6. ⏳ Automated scheduling (every 4 hours)
7. ⏳ Data fetching and processing
8. ⏳ Export to multiple formats

## 📝 License

MIT

## 🙏 Credits

Built to reduce vendor customization costs and give you full control over your reports!
