________________________________________
Data-Quality-Checker 🛡️
Data-Quality-Checker is a lightweight framework designed to ensure data integrity by automatically identifying anomalies and outliers in datasets. It helps maintain reliable, consistent, and clean data for analysis or downstream applications.
By catching hidden errors early, it improves the trustworthiness of datasets, reduces the risk of faulty insights, and ensures higher-quality results in analytics and machine learning pipelines.
________________________________________
🚀 Features
Two Modes of Operation
1.	SQL Mode 🗄️
o	Upload one or more files and define table relationships (One-to-One,One-to-Many,Many-to-One,Many-to-Many)
o	Detect issues like:
	Numeric anomalies 
	Categorical anomalies
	Complex pattern anomalies
	Insertion, Deletion, and Update anomalies
2.	ML Mode 🤖
o	Upload a file to detect outliers and anomalies.
o	Detect issues like:
	Numeric anomalies 
	Categorical anomalies
	Complex pattern anomalies

________________________________________
🕵️‍♂️ What It Detects
Outliers
1.	Numeric anomalies
o	Extreme or unusual numerical values that deviate from the dataset’s distribution
o	Detected using z-score (distance from mean) and IQR (values outside Q1–Q3 range)
2.	Categorical anomalies
o	Rare or unexpected values in categorical columns that occur with very low frequency
3.	Complex pattern anomalies
o	Detected using LightGBM
o	Models patterns in data and assigns anomaly scores to identify unusual or rare observations
________________________________________
Anomalies
1.	Insertion Anomalies ➕
o	Duplicate records – Multiple rows have identical values
o	Missing required fields – Columns that should always have values are missing
o	Invalid foreign keys – Foreign key values are incorrect
o	Insertion anomalies = Duplicate records + Missing required fields + Invalid foreign keys

2.	Deletion Anomalies ➖
o	Orphaned records – Child records reference non-existent parent records
o	Referential integrity violations – Foreign key constraints are broken
o	Potential accidental deletions – Normally critical columns suddenly missing values
o	Deletion anomalies = Orphaned records + Referential integrity violations + Potential accidental deletions

3.	Update Anomalies 🔄
o	Inconsistent updates – Same key has conflicting values in other columns
o	Partial updates – Only some related columns were updated
o	Data type violations – Column values do not match expected type
o	Update anomalies = Inconsistent updates + Partial updates + Data type violations
________________________________________
📊 Data Quality Score
The Data Quality Score measures how clean and reliable your dataset is. It is calculated based on the proportion of anomalies detected:
1.	Anomaly Percentage – This is the fraction of rows in your dataset that contain anomalies:
            Anomaly Percentage = Total Anomalies ÷ Total Rows
2.	Quality Score – The quality score is calculated by subtracting the anomaly percentage from 100, ensuring that higher anomaly counts reduce the score. The minimum score is 0.
            Quality Score = 100 − Anomaly Percentage
________________________________________
🔍 Confidence & Severity
•	Confidence
o	Complex pattern anomalies: Probability output from LightGBM, where scores closer to 1 indicate higher anomaly likelihood
o	Other anomalies: confidence = 1 (binary anomaly detection: yes/no)
•	Method Weight ⚖️
o	Assigns importance to each type of anomaly based on its potential impact
•	Severity Score 💥
o	Combines detection confidence and method weight:
o	severity_score = confidence × method_weight
________________________________________
✅ Data-Quality-Checker ensures your datasets are clean, reliable, and ready for analysis or ML pipelines.
________________________________________

