# 04_rules.py
# Agent Rules with YAML
# Pairs with 04_rules.R
# Tim Fraser

# This script demonstrates how to use rules in an agentic workflow to make agents more precise.
# Rules are incorporated into the agent's role/system message to guide behavior.

# 0. SETUP ###################################

## 0.1 Load Packages #################################

import pandas as pd  # for data manipulation
import yaml          # for reading YAML files
import requests      # for HTTP requests

# If you haven't already, install these packages...
# pip install pandas pyyaml requests

## 0.2 Load Functions #################################

# Load helper functions for agent orchestration
from functions import agent_run, get_shortages, df_as_text

# 1. CONFIGURATION ###################################

# Select model of interest
MODEL = "smollm2:135m"

# 2. LOAD RULES FROM YAML ###################################

# Rules are structured guidance that can be incorporated into agent prompts
# to make their behavior more precise and consistent.
# Rules are defined in 04_rules.yaml for easier maintenance and version control.

# Learn more about standard AI rules formatting here: https://aicodingrules.org/

# Load in rules
with open("04_rules.yaml", "r") as f:
    rules = yaml.safe_load(f)

# Extract rules as dictionaries for easy access
rules_summary_report = rules["rules"]["summary_report"][0]
rules_formatted_output = rules["rules"]["formatted_output"][0]

# 3. HELPER FUNCTION: FORMAT RULES FOR PROMPT ###################################

def format_rules_for_prompt(ruleset):
    """
    Format a ruleset into a string that can be included in the agent's role.
    
    Parameters:
    -----------
    ruleset : dict
        A ruleset dictionary with 'name', 'description', and 'guidance' keys
    
    Returns:
    --------
    str
        Formatted rules string
    """
    
    return f"{ruleset['name']}\n{ruleset['description']}\n\n{ruleset['guidance']}"

# 4. AGENTIC WORKFLOW WITH RULES ###################################
#
# Workflow:
# 1. Agent 1 (Data Analyst - code): use FDA Drug Shortages API + pandas
#    to get raw data, filter to current shortages, and summarize by generic_name.
#    Output: result1 (text table of current shortages).
# 2. Agent 1 → Agent 2 (Report Writer): take result1 and write a narrative
#    summary (key findings, notable shortages, context). Output: result2.
# 3. Agent 2 → Agent 3 (Formatter): take result2 and produce a formatted
#    markdown report suitable for sharing. Output: result3.

categories = [
    "Analgesia/Addiction", "Anesthesia", "Anti-Infective", "Antiviral",
    "Cardiovascular", "Dental", "Dermatology", "Endocrinology/Metabolism",
    "Gastroenterology", "Hematology", "Inborn Errors", "Medical Imaging",
    "Musculoskeletal", "Neurology", "Oncology", "Ophthalmology", "Other",
    "Pediatric", "Psychiatry", "Pulmonary/Allergy", "Renal", "Reproductive",
    "Rheumatology", "Total Parenteral Nutrition", "Transplant", "Urology"
]

# 5. WORKFLOW EXECUTION ###################################

# Start with an input type of medication to search
input_category = {"category": "Neurology"}

# Task 1 - Function / Data Analyst -------------------------
# Get data on drug shortages for the category of interest
data = get_shortages(category=input_category["category"], limit=500)

# Process the data into some summary table
# Filter for items that are currently unavailable
stat = (data
        .groupby("generic_name")
        .apply(lambda x: x.loc[x["update_date"].idxmax()])
        .reset_index(drop=True)
        .query("availability == 'Unavailable'"))

# Convert the data to a text string (Data Table output)
result1 = df_as_text(stat)

# Task 2 - Report Writer Agent with Rules -------------------------
# This agent takes the data table and produces a narrative summary.
role2_base = (
    "You are a medical drug-shortage report writer. "
    "Using the table of current shortages provided by the user, write a clear, concise "
    "narrative summary describing the overall situation, key findings, notable drugs, "
    "and any important patterns or implications. Do not produce another table; focus on narrative."
)

# Add rules to the role
role2_with_rules = f"{role2_base}\n\n{format_rules_for_prompt(rules_summary_report)}"

# Run the agent with rules
result2 = agent_run(role=role2_with_rules, task=result1, model=MODEL, output="text")

# Task 3 - Formatter Agent with Rules -------------------------
# This agent takes the narrative summary and produces a formatted markdown report.
role3_base = (
    "You take the narrative summary of current medicine shortages provided by the user "
    "and produce a well-structured, formatted report in markdown suitable for sharing "
    "with healthcare administrators and policy makers."
)

# Add rules to the role
role3_with_rules = f"{role3_base}\n\n{format_rules_for_prompt(rules_formatted_output)}"

# Run the agent with rules
result3 = agent_run(role=role3_with_rules, task=result2, model=MODEL, output="text")

# Note that the performance of the agent depends significantly on how much context you allow in one call.
# https://docs.ollama.com/context-length

# 6. DISPLAY RESULTS ###################################

# Display all results in workflow order
print("📊 Data Table:")
print(result1)
print()

print("📝 Summary:")
print(result2)
print()

print("📰 Formatted Output:")
print(result3)

