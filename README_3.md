# 🩺 Healthcare Analytics Dashboard

An interactive **Streamlit** dashboard for exploring patient-level healthcare data — including demographics, disease trends, BMI, and blood pressure analysis — with real-time filtering and KPI tracking.

🔗 **Live App:** [healthcaredashboard-bqpvgxxszg3chmahhmogws.streamlit.app](https://healthcaredashboard-bqpvgxxszg3chmahhmogws.streamlit.app/)
📦 **Repository:** [github.com/nupurm688-cmyk/healthcare_dashboard](https://github.com/nupurm688-cmyk/healthcare_dashboard)

---

## 📋 Overview

This dashboard allows healthcare analysts, researchers, or clinicians to upload patient datasets and instantly visualize key health metrics — no coding required. It supports flexible column naming, automatically derives missing fields (like BMI from height/weight), and categorizes patients using standard clinical thresholds.

---

## ✨ Features

- **📁 Patient Data Upload** — Upload CSV or Excel files, or explore with built-in sample data (500 synthetic patients)
- **👥 Age Distribution** — Histogram and age-group breakdowns
- **🦠 Disease Distribution** — Bar and pie charts of conditions, cross-tabulated by gender
- **⚖️ BMI Analysis** — Distribution histogram with clinical threshold markers, category breakdown (Underweight/Normal/Overweight/Obese)
- **❤️ Blood Pressure Analysis** — Systolic vs. diastolic scatter plot, BP category classification (Normal → Hypertensive Crisis), trends by age group
- **⚧ Gender Analysis** — Distribution and age comparison across genders
- **📊 KPI Cards** — Total patients, average age, average BMI, average blood pressure, and % of patients with a diagnosed condition
- **🔍 Interactive Filters** — Filter by gender, disease, and age range; all charts and KPIs update live
- **⬇️ Data Export** — Download filtered data as CSV

---

## 🗂️ Expected Data Format

The app auto-detects common column name variations. Supported fields:

| Field | Accepted column names |
|---|---|
| Age | `age`, `patient_age`, `years` |
| Gender | `gender`, `sex` |
| Disease/Condition | `disease`, `diagnosis`, `condition` |
| BMI | `bmi`, `body_mass_index` (or auto-computed from height + weight) |
| Height | `height`, `height_cm` |
| Weight | `weight`, `weight_kg` |
| Systolic BP | `systolic_bp`, `bp_systolic`, `sbp` |
| Diastolic BP | `diastolic_bp`, `bp_diastolic`, `dbp` |
| Patient ID | `patient_id`, `id` |

> If your file doesn't have all these columns, the dashboard will simply skip the sections it can't compute.

---

## 🚀 Getting Started

### Prerequisites
- Python 3.8+
- pip

### Installation

```bash
# Clone the repository
git clone https://github.com/nupurm688-cmyk/healthcare_dashboard.git
cd healthcare_dashboard

# Create and activate a virtual environment
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Run locally

```bash
streamlit run healthcare_dashboard.py
```

The app will open automatically at `http://localhost:8501`.

---

## ☁️ Deployment (Streamlit Community Cloud)

1. Push this repository to GitHub (already done ✅)
2. Go to [share.streamlit.io](https://share.streamlit.io) and sign in with GitHub
3. Click **New app** → select this repository and branch
4. Set **Main file path** to `healthcare_dashboard.py`
5. Click **Deploy**

---

## 🛠️ Tech Stack

- [Streamlit](https://streamlit.io/) — app framework
- [Pandas](https://pandas.pydata.org/) — data processing
- [Plotly](https://plotly.com/python/) — interactive visualizations
- [NumPy](https://numpy.org/) — numerical computing
- [OpenPyXL](https://openpyxl.readthedocs.io/) — Excel file support

---

## 📁 Project Structure

```
healthcare_dashboard/
├── healthcare_dashboard.py   # Main Streamlit application
├── requirements.txt          # Python dependencies
└── README.md                 # Project documentation
```

---

## ⚠️ Disclaimer

This dashboard is intended for **demonstration and analytical purposes only**. It is not a certified medical device and should not be used as a substitute for professional clinical judgment or diagnosis.

---

## 📄 License

This project is open source and available under the [MIT License](LICENSE).

---

## 🤝 Contributing

Contributions, issues, and feature requests are welcome. Feel free to check the [issues page](https://github.com/nupurm688-cmyk/healthcare_dashboard/issues) or open a pull request.

---

## 👤 Author

**Nupur M**
GitHub: [@nupurm688-cmyk](https://github.com/nupurm688-cmyk)
