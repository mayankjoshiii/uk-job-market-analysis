"""
analyse_jobs.py - UK BA/DA job listings analysis pipeline
Cleans listings, parses salary ranges, maps regions and work arrangements, and counts skill mentions.
Author: Mayank Joshi

The repo ships with sample_listings.csv, a small sample of 25 UK Business Analyst and
Data Analyst listings (January 2025). Results from 25 rows are indicative only. Point the script at a
larger CSV with the same columns to analyse more:  python analyse_jobs.py my_listings.csv
"""

import re
import sys

import numpy as np
import pandas as pd

SKILL_PATTERNS = {
    "SQL": r"\bsql\b", "Excel": r"\bexcel\b", "Power BI": r"\bpower ?bi\b", "Python": r"\bpython\b",
    "Tableau": r"\btableau\b", "R": r"\br\b", "Agile": r"\bagile\b", "Jira": r"\bjira\b",
    "Confluence": r"\bconfluence\b", "Stakeholder management": r"stakeholder", "Requirements gathering": r"requirements",
    "BPMN / process mapping": r"\bbpmn\b|process mapping", "Statistics": r"statistic|hypothesis",
    "Data visualisation": r"visuali[sz]ation", "Looker": r"\blooker\b", "Cloud (AWS/Azure/GCP)": r"\baws\b|\bazure\b|\bgcp\b",
}
REGIONS = ["London", "Manchester", "Birmingham", "Leeds", "Bristol", "Edinburgh", "Glasgow", "Cardiff",
           "Nottingham", "Reading", "York", "Derby"]


def load_listings(filepath: str = "sample_listings.csv") -> pd.DataFrame:
    df = pd.read_csv(filepath)
    print(f"Loaded {len(df):,} listings from {filepath}")
    return df


def parse_salary(salary: str) -> float:
    """Midpoint of a range like '£45000-£55000'; NaN if no usable number."""
    if pd.isna(salary):
        return np.nan
    nums = [int(n.replace(",", "")) for n in re.findall(r"\d[\d,]*", str(salary))]
    nums = [n for n in nums if n > 1000]
    return float(np.mean(nums)) if nums else np.nan


def clean(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]
    df["salary_mid"] = df["salary"].apply(parse_salary)
    loc = df["location"].fillna("")
    df["region"] = loc.str.extract("(" + "|".join(REGIONS) + ")", expand=False).fillna("Other")
    df["work_type"] = np.select([loc.str.contains("Hybrid", case=False), loc.str.contains("Remote", case=False)],
                                ["Hybrid", "Remote"], default="Not stated / office")
    before = len(df)
    df = df.drop_duplicates(subset=["job_title", "company", "location"])
    print(f"Removed {before - len(df)} duplicates, {len(df):,} listings remain")
    return df


def skill_counts(df: pd.DataFrame) -> pd.DataFrame:
    text = df["description"].fillna("").str.lower()
    rows = [(skill, int(text.str.contains(pat, regex=True).sum())) for skill, pat in SKILL_PATTERNS.items()]
    out = pd.DataFrame(rows, columns=["skill", "listings"]).sort_values("listings", ascending=False)
    out["pct_of_listings"] = (100 * out["listings"] / len(df)).round(0)
    return out[out["listings"] > 0].reset_index(drop=True)


def main(path: str = "sample_listings.csv"):
    df = clean(load_listings(path))
    print("\n--- Skills mentioned ---")
    print(skill_counts(df).to_string(index=False))
    print("\n--- Salary midpoint by region (GBP) ---")
    print(df.groupby("region")["salary_mid"].agg(["median", "count"]).round(0)
            .sort_values("median", ascending=False).to_string())
    print(f"\nOverall median salary midpoint: GBP {df['salary_mid'].median():,.0f}")
    print("\n--- Work arrangement (from location text) ---")
    print(df["work_type"].value_counts().to_string())
    print("\n--- Roles ---")
    print(df["job_title"].value_counts().to_string())


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "sample_listings.csv")
