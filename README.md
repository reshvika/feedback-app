# AI Writing Feedback System

## Overview
An AI-powered application that analyzes student essays and provides structured, rubric-based feedback.  
The system uses a multi-step pipeline to improve reliability, consistency, and interpretability of feedback.

---

## Features

- Essay input via web interface  
- Structure extraction (thesis and argument analysis)  
- Rubric-based scoring:
  - Clarity  
  - Argument Strength  
  - Organization  
- Actionable feedback and improvement suggestions  
- Downloadable feedback report (.txt)  
- Fallback system when API is unavailable  

---

## System Architecture

The application follows a 3-stage pipeline:

1. Structure Extraction  
   Extracts thesis, key arguments, and structure summary  

2. Rubric Evaluation  
   Assigns scores (1–5) with reasoning for:
   - Clarity  
   - Argument Strength  
   - Organization  

3. Feedback Generation  
   Produces:
   - Overall assessment  
   - Priority areas  
   - Actionable recommendations  

Each stage outputs structured data, improving consistency and debugging.

---

## Tech Stack

- Frontend: Streamlit  
- Backend: Python  
- AI: OpenAI API (with fallback mock system)  
- Architecture: Modular pipeline  

---

## Project Structure
├── writing_feedback_app.py # Streamlit app (UI + orchestration)
├── essay_pipeline.py # Core AI pipeline logic
├── requirements.txt # Dependencies
├── README.md

---

## Installation

```bash
pip install -r requirements.txt
