# Mutual Fund Data Analysis Project

A comprehensive data analysis platform for mutual fund investments with real-time NAV data, portfolio analysis, and risk assessment.

## 🎯 Project Overview

This project analyzes mutual fund data from AMFI (Association of Mutual Funds in India) to provide:

- Fund performance tracking
- Risk grade analysis
- Portfolio composition insights
- NAV historical analysis
- Fund category comparison

## 📦 Project Structure

```
MutualFund/
├── data/
│   ├── raw/                      # Raw CSV and API data
│   └── processed/                # Cleaned and processed datasets
├── notebooks/                    # Jupyter notebooks for analysis
├── sql/                          # SQL queries for database operations
├── dashboard/                    # Dashboard configuration and assets
├── reports/                      # Generated analysis reports
├── day1_data_ingestion.py       # Data loading and API fetching
├── requirements.txt              # Python dependencies
├── .gitignore                    # Git ignore rules
├── DAY1_SUMMARY.md              # Day 1 completion report
└── README.md                     # This file
```

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- Git
- Internet connection (for API calls)

### Installation

1. **Clone the repository**

   ```bash
   cd c:\Users\SUJAL\MutualFund
   ```

2. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

3. **Set up data directory**
   Place your CSV files in `data/raw/`:
   - fund_master.csv
   - nav_history.csv
   - scheme_details.csv
   - aum_history.csv
   - expense_ratio.csv
   - fund_returns.csv
   - portfolio_holdings.csv
   - fund_categories.csv
   - scheme_codes.csv
   - historical_nav.csv

4. **Run data ingestion**
   ```bash
   python day1_data_ingestion.py
   ```

## 📊 Data Sources

### Primary Data

- **AMFI Mutual Fund API:** https://api.mfapi.in
- **CSV Datasets:** Local data storage in `data/raw/`

### Key Schemes Tracked

| Fund                | AMFI Code | Fund House       |
| ------------------- | --------- | ---------------- |
| HDFC Top 100 Direct | 125497    | HDFC Mutual Fund |
| SBI Bluechip        | 119551    | SBI Mutual Fund  |
| ICICI Bluechip      | 120503    | ICICI Prudential |
| Nippon Large Cap    | 118632    | Nippon India     |
| Axis Bluechip       | 119092    | Axis Mutual Fund |
| Kotak Bluechip      | 120841    | Kotak Mahindra   |

## 📚 Key Features

### Data Processing

- ✅ Automated CSV loading with error handling
- ✅ Live NAV fetching from AMFI API
- ✅ Data quality validation and anomaly detection
- ✅ AMFI code consistency checks

### Analysis Capabilities

- Fund performance metrics
- Risk grade classification
- Category-based comparisons
- Historical NAV tracking
- Portfolio composition analysis

### Reporting

- Data quality summary reports
- Fund house statistics
- Category distribution analysis
- Risk profile summaries

## 🔧 Configuration

### Dependencies

All dependencies are listed in `requirements.txt`:

- **Data Processing:** pandas, numpy, scipy
- **Visualization:** matplotlib, seaborn, plotly
- **Database:** sqlalchemy
- **API:** requests
- **Notebooks:** jupyter, ipython

### API Configuration

- **Timeout:** 10 seconds (adjustable)
- **Retries:** Automatic retry logic for failed requests
- **Rate Limiting:** Respects API rate limits

## 📈 Usage Examples

### Load Data

```python
import pandas as pd

# Load processed data
df = pd.read_csv('data/processed/fund_analysis.csv')
```

### Fetch Live NAV

```python
import requests
response = requests.get('https://api.mfapi.in/mf/125497')
data = response.json()
```

## 📊 Data Quality

The project includes comprehensive data quality checks:

- Null value detection
- Duplicate record identification
- Data type validation
- AMFI code consistency verification
- Fund master to NAV history reconciliation

See `data/processed/data_quality_summary.json` for detailed metrics.

## 🐛 Troubleshooting

### API Timeout Issues

- Increase timeout value in the script
- Check internet connectivity
- Verify API endpoint availability

### Missing Data Files

- Ensure CSV files are in `data/raw/` directory
- Check file naming conventions match expected names
- Verify CSV format and encoding (UTF-8 recommended)

### Import Errors

- Reinstall dependencies: `pip install -r requirements.txt --force-reinstall`
- Verify Python version: `python --version`

## 🔄 Git Workflow

```bash
# Check status
git status

# Add changes
git add .

# Commit
git commit -m "Day X: Description"

# Push to GitHub
git push origin main
```

## 📝 Logging

- Data ingestion logs: Console output (can be redirected)
- Data quality reports: `data/processed/data_quality_summary.json`
- Processing summaries: `DAY1_SUMMARY.md`

## 🎓 Learning Resources

- [AMFI Official Website](https://www.amfiindia.com)
- [Mutual Fund Basics](https://www.amfiindia.com/investor-education/learning-center)
- [Risk Grades Explained](https://www.amfiindia.com)

## 📄 License

This project is for educational and personal analysis purposes.

## 👤 Author

Data Analyst

## 📞 Support

For issues or questions:

1. Check `DAY1_SUMMARY.md` for status and next steps
2. Review error messages in console output
3. Verify all data files are in correct locations
4. Ensure all dependencies are installed

---

**Last Updated:** 2026-06-03  
**Project Status:** ✅ Day 1 Complete - Data Ingestion  
**Next Phase:** Day 2 - Data Quality & Exploration
