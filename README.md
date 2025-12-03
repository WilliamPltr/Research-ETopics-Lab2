# Lab 2: Steel Production Prediction - ML Pipeline

A complete machine learning project for predicting steel plant production using the Global Iron and Steel Tracker dataset.

## 📋 Project Overview

This lab implements a full ML pipeline to predict steel production (ttpa - thousand tonnes per annum) for steel plants worldwide based on their characteristics like workforce size, capacity, and location.

**Dataset**: Global Iron and Steel Tracker (September 2025)
- 255 steel plants with production data from 2023
- Features: workforce size, capacity, region, and engineered features
- Target: Crude steel production in 2023

## 🔧 Technologies Used

- **Python 3.x**
- **Data Processing**: pandas, numpy
- **Visualization**: matplotlib, seaborn, plotly
- **Machine Learning**: scikit-learn
  - Linear Regression
  - Ridge Regression
  - Random Forest Regressor
- **Model Tracking**: MLflow
- **Hyperparameter Optimization**: Optuna
- **Model Persistence**: joblib

## 🚀 Getting Started

### Installation

```bash
pip install -r requirements.txt
```

### Running the Notebook

```bash
jupyter notebook lab_2.ipynb
```

### View MLflow Results

```bash
mlflow ui
```
Then open http://localhost:5000 in your browser.

## 📁 Project Structure

```
.
├── lab_2.ipynb                          # Main notebook
├── requirements.txt                     # Python dependencies
├── Plant-level-data-...xlsx            # Dataset
├── steel_model.joblib                  # Saved model
├── model_info.json                     # Model metadata
└── mlruns/                             # MLflow tracking data
```

## 📈 Results

The Random Forest model achieved excellent performance with 97.3% R² score, significantly outperforming linear models. Key predictors of steel production are:
- Plant capacity (strongest predictor)
- Workforce size
- Geographic region

## 🎓 Lab Sections

1. Data Setup and Exploration
2. Building Baseline & Linear Models
3. Model Evaluation and Selection
4. Model Lifecycle (Tracking, Saving, Loading)
5. Deployment & Monitoring (Conceptual)
6. Reflection

## 📝 License

MIT LICENSE
