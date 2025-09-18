import React from "react";

export default function DataQualityChecker() {
  return (
    <div>
      {/* Header */}
      <h1 className="text-3xl font-bold mb-4 text-center">
        Data-Quality-Checker 🛡️
      </h1>
      <p className="text-lg mb-6">
        Data-Quality-Checker is a lightweight framework designed to ensure data
        integrity by automatically identifying anomalies and outliers in
        datasets. It helps maintain reliable, consistent, and clean data for
        analysis or downstream applications.
      </p>
      <p className="mb-6">
        By catching hidden errors early, it improves the trustworthiness of
        datasets, reduces the risk of faulty insights, and ensures higher-quality
        results in analytics and machine learning pipelines.
      </p>

      {/* Features */}
      <section className="mb-8">
        <h2 className="text-2xl font-semibold mb-3">🚀 Features</h2>
        <h3 className="text-xl font-medium mb-2">Two Modes of Operation</h3>
        <ul className="list-disc ml-6 space-y-2">
          <li>
            <strong>SQL Mode 🗄️</strong>
            <ul className="list-disc ml-6 space-y-1">
              <li>Upload one or more files and define table relationships (One-to-One, One-to-Many, Many-to-One, Many-to-Many)</li>
              <li>Detect issues like: Numeric anomalies, Categorical anomalies, Complex pattern anomalies, Insertion, Deletion, and Update anomalies</li>
            </ul>
          </li>
          <li>
            <strong>ML Mode 🤖</strong>
            <ul className="list-disc ml-6 space-y-1">
              <li>Upload a file to detect outliers and anomalies</li>
              <li>Detect issues like: Numeric anomalies, Categorical anomalies, Complex pattern anomalies</li>
            </ul>
          </li>
        </ul>
      </section>

      {/* What it Detects */}
      <section className="mb-8">
        <h2 className="text-2xl font-semibold mb-3">🕵️‍♂️ What It Detects</h2>
        <h3 className="text-xl font-medium">Outliers</h3>
        <ul className="list-disc ml-6 space-y-2 mb-4">
          <li>
            <strong>Numeric anomalies</strong> – Extreme values detected using z-score & IQR
          </li>
          <li>
            <strong>Categorical anomalies</strong> – Rare or unexpected categorical values
          </li>
          <li>
            <strong>Complex pattern anomalies</strong> – Detected using LightGBM with anomaly scores
          </li>
        </ul>

        <h3 className="text-xl font-medium">Anomalies</h3>
        <ul className="list-disc ml-6 space-y-2">
          <li>
            <strong>Insertion Anomalies ➕</strong> – Duplicate records, Missing required fields, Invalid foreign keys
          </li>
          <li>
            <strong>Deletion Anomalies ➖</strong> – Orphaned records, Referential integrity violations, Potential accidental deletions
          </li>
          <li>
            <strong>Update Anomalies 🔄</strong> – Inconsistent updates, Partial updates, Data type violations
          </li>
        </ul>
      </section>

      {/* Data Quality Score */}
      <section className="mb-8">
        <h2 className="text-2xl font-semibold mb-3">📊 Data Quality Score</h2>
        <p className="mb-4">
          The Data Quality Score measures how clean and reliable your dataset is.
          It is calculated based on the proportion of anomalies detected:
        </p>
        <ul className="list-disc ml-6 space-y-2">
          <li>
            <strong>Anomaly Percentage</strong> = Total Anomalies ÷ Total Rows
          </li>
          <li>
            <strong>Quality Score</strong> = 100 − Anomaly Percentage (minimum score = 0)
          </li>
        </ul>
      </section>

      {/* Confidence & Severity */}
      <section className="mb-8">
        <h2 className="text-2xl font-semibold mb-3">🔍 Confidence & Severity</h2>
        <ul className="list-disc ml-6 space-y-2">
          <li>
            <strong>Confidence</strong> – Probability output from LightGBM (0–1), or 1 for binary anomalies
          </li>
          <li>
            <strong>Method Weight ⚖️</strong> – Importance of anomaly type based on impact
          </li>
          <li>
            <strong>Severity Score 💥</strong> = confidence × method_weight
          </li>
        </ul>
      </section>

      {/* Footer */}
      <div className="bg-green-50 border-l-4 border-green-500 p-4 rounded">
        <p className="font-medium">
          ✅ Data-Quality-Checker ensures your datasets are clean, reliable, and
          ready for analysis or ML pipelines.
        </p>
      </div>
    </div>
  );
}
