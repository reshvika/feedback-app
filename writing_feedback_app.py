"""
AI Writing Feedback System
A Streamlit-based application that provides structured, rubric-based feedback on essays.

Pipeline:
1. Structure Extraction: Extract thesis, arguments, and structure
2. Rubric Evaluation: Score on clarity, argument strength, organization (1-5)
3. Feedback Generation: Provide actionable improvement suggestions
"""

import streamlit as st
import json
from typing import Dict, List, Tuple
from essay_pipeline import (
    extract_essay_structure,
    evaluate_essay_rubric,
    generate_feedback,
    PipelineError,
)

st.set_page_config(
    page_title="AI Writing Feedback",
    page_icon=None,  # removed emoji
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Custom CSS for polished UI
st.markdown(
    """
    <style>
    /* Main theme colors */
    :root {
        --primary: #2563eb;
        --success: #10b981;
        --warning: #f59e0b;
        --danger: #ef4444;
        --bg-light: #f9fafb;
        --border: #e5e7eb;
    }
    
    /* Remove default padding */
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    
    /* Custom card styling */
    .feedback-card {
        background: white;
        border: 1px solid var(--border);
        border-radius: 12px;
        padding: 1.5rem;
        margin: 1rem 0;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    
    .score-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-radius: 12px;
        padding: 1.5rem;
        text-align: center;
        min-height: 150px;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
    }
    
    .score-label {
        font-size: 0.9rem;
        opacity: 0.9;
        font-weight: 500;
        margin-bottom: 0.5rem;
    }
    
    .score-value {
        font-size: 2.5rem;
        font-weight: bold;
        margin: 0.5rem 0;
    }
    
    .score-max {
        font-size: 0.85rem;
        opacity: 0.8;
    }
    
    /* Rubric scores color coding */
    .score-excellent { background: linear-gradient(135deg, #10b981 0%, #059669 100%); }
    .score-good { background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%); }
    .score-fair { background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%); }
    .score-poor { background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%); }
    
    /* Section headers */
    .section-header {
        font-size: 1.5rem;
        font-weight: 700;
        color: #1f2937;
        margin-top: 2rem;
        margin-bottom: 1rem;
        border-bottom: 3px solid #2563eb;
        padding-bottom: 0.5rem;
    }
    
    /* Improvement suggestion styling */
    .suggestion-item {
        background: #f0f9ff;
        border-left: 4px solid #2563eb;
        padding: 1rem;
        margin: 0.75rem 0;
        border-radius: 4px;
        color: #000000;
    }
    
    .suggestion-priority {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 600;
        margin-bottom: 0.5rem;
        color: #000000;
    }
    
    .priority-high {
        background: #fee2e2;
        color: #000000;
    }
    
    .priority-medium {
        background: #fef3c7;
        color: #000000;
    }
    
    .priority-low {
        background: #e0f2fe;
        color: #000000;
    }
    
    /* Loading animation */
    .loading-text {
        font-size: 1.1rem;
        color: #2563eb;
        font-weight: 500;
    }
    
    /* Button styling */
    .stButton > button {
        background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.75rem 2rem;
        font-weight: 600;
        font-size: 1rem;
        cursor: pointer;
        transition: all 0.3s ease;
        width: 100%;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 20px rgba(37, 99, 235, 0.3);
    }
    
    /* Text area styling */
    .stTextArea > textarea {
        border-radius: 8px;
        border: 2px solid #e5e7eb;
        font-family: 'Georgia', serif;
        line-height: 1.6;
    }
    
    .stTextArea > textarea:focus {
        border-color: #2563eb;
        box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.1);
    }
    
    /* Structure extraction styling */
    .structure-block {
        background: #f9fafb;
        border: 1px solid #e5e7eb;
        border-radius: 8px;
        padding: 1rem;
        margin: 0.75rem 0;
    }
    
    .thesis-statement {
        background: #eff6ff;
        border-left: 4px solid #2563eb;
        padding: 1rem;
        border-radius: 4px;
        font-style: italic;
        color: #1e40af;
        margin-bottom: 1rem;
    }
    
    .argument-list {
        background: white;
        border: 1px solid #e5e7eb;
        border-radius: 8px;
        padding: 1rem;
    }
    
    .argument-item {
        padding: 0.75rem;
        border-bottom: 1px solid #f3f4f6;
        display: flex;
        align-items: flex-start;
    }
    
    .argument-item:last-child {
        border-bottom: none;
    }
    
    .argument-number {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 28px;
        height: 28px;
        border-radius: 50%;
        background: #2563eb;
        color: white;
        font-weight: 700;
        margin-right: 0.75rem;
        flex-shrink: 0;
    }
    
    .argument-text {
        color: #374151;
        line-height: 1.5;
    }
    
    /* Error styling */
    .error-box {
        background: #fee2e2;
        border: 1px solid #fca5a5;
        border-radius: 8px;
        padding: 1rem;
        color: #991b1b;
    }
    
    /* Success message */
    .success-message {
        background: #d1fae5;
        border: 1px solid #6ee7b7;
        border-radius: 8px;
        padding: 1rem;
        color: #065f46;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def display_header():
    col1, col2 = st.columns([3, 1], gap="large")
    with col1:
        st.markdown("# AI Writing Feedback System")
        st.markdown(
            """
            Get structured, rubric-based feedback on your essays. 
            Our AI analyzes your writing through a multi-step pipeline 
            to provide actionable insights on clarity, argument strength, and organization.
            """,
            unsafe_allow_html=True,
        )
    with col2:
        st.info("Powered by AI")


def display_structure_extraction(structure: Dict) -> None:
    st.markdown('<div class="section-header">Essay Structure Analysis</div>', unsafe_allow_html=True)

    # Thesis Statement
    if structure.get("thesis"):
        st.markdown(
            f'<div class="thesis-statement"><strong>Thesis Statement:</strong><br/>{structure["thesis"]}</div>',
            unsafe_allow_html=True,
        )

    # Structure Summary ONLY (no arguments)
    if structure.get("structure_summary"):
        st.markdown("#### Structure Summary")
        st.markdown(
            f'<div class="feedback-card">{structure["structure_summary"]}</div>',
            unsafe_allow_html=True,
        )


def get_score_color_class(score: int) -> str:
    """Return CSS class for score coloring."""
    if score >= 4:
        return "score-excellent"
    elif score >= 3:
        return "score-good"
    elif score >= 2:
        return "score-fair"
    else:
        return "score-poor"


def display_rubric_scores(rubric: Dict) -> None:
    """Display rubric scores in an attractive card layout."""
    st.markdown('<div class="section-header">Rubric Evaluation</div>', unsafe_allow_html=True)

    # Create three columns for scores
    cols = st.columns(3, gap="medium")

    categories = ["clarity", "argument_strength", "organization"]
    labels = ["Clarity", "Argument Strength", "Organization"]

    for col, category, label in zip(cols, categories, labels):
        with col:
            if category in rubric:
                score = rubric[category]["score"]
                color_class = get_score_color_class(score)
                html_card = f'''
                <div class="score-card {color_class}">
                    <div class="score-label">{label}</div>
                    <div class="score-value">{score}</div>
                    <div class="score-max">out of 5</div>
                </div>
                '''
                st.markdown(html_card, unsafe_allow_html=True)

                # Display reasoning below score
                reasoning = rubric[category].get("reasoning", "")
                st.markdown(f'<small>{reasoning}</small>', unsafe_allow_html=True)


def display_feedback_suggestions(feedback: Dict) -> None:
    """Display actionable feedback suggestions with priority levels."""
    st.markdown('<div class="section-header">Improvement Suggestions</div>', unsafe_allow_html=True)

    # Overall feedback
    if feedback.get("overall_feedback"):
        st.markdown("#### Overall Assessment")
        st.markdown(
            f'<div class="feedback-card">{feedback["overall_feedback"]}</div>',
            unsafe_allow_html=True,
        )

    # Priority areas
    if feedback.get("priority_areas"):
        st.markdown("#### Priority Areas to Fix")
        for area in feedback["priority_areas"]:
            priority_level = area.get("priority", "medium").lower()
            priority_color = (
                "priority-high"
                if priority_level == "high"
                else ("priority-medium" if priority_level == "medium" else "priority-low")
            )
            priority_text = priority_level.upper()

            html_suggestion = f'''
            <div class="suggestion-item">
                <div class="suggestion-priority {priority_color}"> {priority_text} PRIORITY</div>
                <strong>{area.get("area", "")}</strong>
                <p>{area.get("description", "")}</p>
            </div>
            '''
            st.markdown(html_suggestion, unsafe_allow_html=True)

    # Actionable advice
    if feedback.get("actionable_advice"):
        st.markdown("#### Actionable Advice")
        for i, advice in enumerate(feedback["actionable_advice"], 1):
            st.markdown(f'<div class="feedback-card">**{i}. {advice}**</div>', unsafe_allow_html=True)


def process_essay(essay_text: str) -> Tuple[bool, Dict]:
    """
    Process essay through the multi-step pipeline.
    
    Args:
        essay_text: The essay content to analyze
        
    Returns:
        Tuple of (success: bool, results: dict)
    """
    results = {
        "structure": None,
        "rubric": None,
        "feedback": None,
    }

    try:
        # Step 1: Extract Structure
        with st.spinner(" Extracting essay structure..."):
            results["structure"] = extract_essay_structure(essay_text)

        # Step 2: Evaluate Rubric
        with st.spinner("Evaluating against rubric..."):
            results["rubric"] = evaluate_essay_rubric(essay_text, results["structure"])

        # Step 3: Generate Feedback
        with st.spinner("Generating improvement suggestions..."):
            results["feedback"] = generate_feedback(
                essay_text, results["structure"], results["rubric"]
            )

        return True, results

    except PipelineError as e:
        st.error(f"Pipeline Error: {str(e)}")
        return False, results
    except Exception as e:
        st.error(f"Unexpected Error: {str(e)}")
        return False, results


def main():
    """Main application logic."""
    display_header()

    # Input section
    st.markdown("---")
    st.markdown("###  Paste Your Essay")

    essay_input = st.text_area(
        label="Enter your essay here",
        height=250,
        placeholder="Paste your essay or text that you'd like feedback on...",
        label_visibility="collapsed",
    )

    # Submit button and session state management
    col1, col2 = st.columns([1, 4])
    with col1:
        submit_button = st.button("Get Feedback", type="primary")

    # Process essay on button click
    if submit_button:
        if not essay_input.strip():
            st.error("Please paste an essay before submitting.")
            st.stop()

        if len(essay_input.strip()) < 100:
            st.warning(" Essay seems quite short. Aim for at least 100 characters for better feedback.")

        # Run the pipeline
        success, results = process_essay(essay_input)

        if success:
            # Display success message
            st.markdown(
                '<div class="success-message">Analysis complete!</div>',
                unsafe_allow_html=True,
            )
            st.markdown("---")

            # Display results in tabs
            tab1, tab2, tab3 = st.tabs(["Structure", "Rubric", "Feedback"])

            with tab1:
                if results["structure"]:
                    display_structure_extraction(results["structure"])

            with tab2:
                if results["rubric"]:
                    display_rubric_scores(results["rubric"])

            with tab3:
                if results["feedback"]:
                    display_feedback_suggestions(results["feedback"])

            # Display feedback results directly
            st.markdown("---")
            
            # Create a formatted feedback display
            feedback_text = "#  DETAILED FEEDBACK REPORT\n\n"
            
            # Add overall assessment
            if results["feedback"].get("overall_feedback"):
                feedback_text += "## Overall Assessment\n\n"
                feedback_text += results["feedback"]["overall_feedback"] + "\n\n"
            
            # Add priority areas
            if results["feedback"].get("priority_areas"):
                feedback_text += "## Priority Areas to Address\n\n"
                for area in results["feedback"]["priority_areas"]:
                    priority = area.get("priority", "medium").upper()
                    area_name = area.get("area", "")
                    description = area.get("description", "")
                    feedback_text += f"**[{priority}] {area_name}**\n\n{description}\n\n"
            
            # Add actionable advice
            if results["feedback"].get("actionable_advice"):
                feedback_text += "## Actionable Recommendations\n\n"
                for i, advice in enumerate(results["feedback"]["actionable_advice"], 1):
                    feedback_text += f"{i}. {advice}\n\n"
            
            # Add rubric scores summary
            feedback_text += "## Rubric Scores Summary\n\n"
            for category, data in results["rubric"].items():
                if isinstance(data, dict) and "score" in data:
                    score = data["score"]
                    feedback_text += f"- **{category.replace('_', ' ').title()}**: {score}/5\n"
            
            # Display the formatted feedback
            st.markdown(feedback_text)
            
            # Download button for formatted feedback
            st.markdown("---")
            col1, col2 = st.columns(2)
            with col1:
                st.download_button(
                    label="Download Feedback (Text)",
                    data=feedback_text,
                    file_name="essay_feedback.txt",
                    mime="text/plain",
                )
            with col2:
                st.success(" Feedback displayed above!", icon="📄")


if __name__ == "__main__":
    main()
