# Data-Quality-Checker 🛡️

Data-Quality-Checker is a lightweight framework designed to ensure data integrity by automatically identifying anomalies and outliers in datasets. It helps maintain reliable, consistent, and clean data for analysis or downstream applications.

By catching hidden errors early, it improves the trustworthiness of datasets, reduces the risk of faulty insights, and ensures higher-quality results in analytics and machine learning pipelines.

-----

## 🚀 Features

Data-Quality-Checker offers two powerful modes of operation to suit your needs.

### 1\. SQL Mode 🗄️

  - Upload one or more files and **define table relationships** (One-to-One, One-to-Many, Many-to-One, Many-to-Many).
  - Detects a wide range of issues, including:
      - Numeric anomalies
      - Categorical anomalies
      - Complex pattern anomalies
      - **Insertion, Deletion, and Update anomalies**

### 2\. ML Mode 🤖

  - Upload a single file to quickly detect outliers and anomalies.
  - Detects issues like:
      - Numeric anomalies
      - Categorical anomalies
      - Complex pattern anomalies

-----

## 🕵️‍♂️ What It Detects

### Outliers

  - **Numeric anomalies:** Extreme or unusual numerical values that deviate from the dataset’s distribution.
      - Detected using **z-score** (distance from mean) and **IQR** (values outside Q1–Q3 range).
  - **Categorical anomalies:** Rare or unexpected values in categorical columns that occur with very low frequency.
  - **Complex pattern anomalies:** Models patterns in data and assigns anomaly scores to identify unusual or rare observations.
      - Detected using **LightGBM**.

### Anomalies

  - **Insertion Anomalies ➕**

      - **Duplicate records:** Multiple rows have identical values.
      - **Missing required fields:** Columns that should always have values are missing.
      - **Invalid foreign keys:** Foreign key values do not exist in the parent table.

    <!-- end list -->

    ```
    Insertion anomalies = Duplicate records + Missing required fields + Invalid foreign keys
    ```

  - **Deletion Anomalies ➖**

      - **Orphaned records:** Child records reference non-existent parent records.
      - **Referential integrity violations:** Foreign key constraints are broken after a deletion.
      - **Potential accidental deletions:** Critical columns suddenly have missing values.

    <!-- end list -->

    ```
    Deletion anomalies = Orphaned records + Referential integrity violations + Potential accidental deletions
    ```

  - **Update Anomalies 🔄**

      - **Inconsistent updates:** The same key has conflicting values across related records.
      - **Partial updates:** Only some of the required related columns were updated.
      - **Data type violations:** A column’s value does not match its expected data type.

    <!-- end list -->

    ```
    Update anomalies = Inconsistent updates + Partial updates + Data type violations
    ```

-----

## 📊 Data Quality Score

The **Data Quality Score** measures how clean and reliable your dataset is. It is calculated based on the proportion of anomalies detected:

1.  **Anomaly Percentage:** This is the fraction of rows in your dataset that contain anomalies.
    ```
    Anomaly Percentage = Total Anomalies / Total Rows
    ```
2.  **Quality Score:** The quality score is calculated by subtracting the anomaly percentage from 100. A higher anomaly count results in a lower score. The minimum score is 0.
    ```
    Quality Score = 100 - Anomaly Percentage
    ```

-----

## 🔍 Confidence & Severity

  - **Confidence:**

      - *Complex pattern anomalies:* Probability output from LightGBM, where scores closer to 1 indicate a higher likelihood of an anomaly.
      - *Other anomalies:* Confidence is set to 1 (binary detection: it's either an anomaly or not).

  - **Method Weight ⚖️:**

      - Assigns a predefined importance to each type of anomaly based on its potential impact on data quality.

  - **Severity Score 💥:**

      - Combines detection confidence and method weight to help you prioritize the most critical issues.

    <!-- end list -->

    ```
    severity_score = confidence × method_weight
    ```

-----

✅ Data-Quality-Checker ensures your datasets are clean, reliable, and ready for analysis or ML pipelines.
