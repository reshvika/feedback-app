"""
Essay Processing Pipeline

This module implements a three-step pipeline for analyzing essays:
1. Structure Extraction: Extract thesis, main arguments, and overall structure
2. Rubric Evaluation: Score clarity, argument strength, and organization
3. Feedback Generation: Generate actionable improvement suggestions

Each step can use OpenAI API or fallback to mock responses.
"""

import os
import json
import re
from typing import Dict, List
from dataclasses import dataclass
from enum import Enum


class PipelineError(Exception):
    """Custom exception for pipeline errors."""
    pass


class FallbackMode(Enum):
    """Fallback behavior when API is unavailable."""
    MOCK = "mock"  # Use predefined responses
    RAISE = "raise"  # Raise an exception


# Try to import openai, but make it optional
try:
    from openai import OpenAI, APIError
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    APIError = Exception


# Initialize OpenAI client
def get_openai_client():
    """
    Get OpenAI client, handling API key validation.
    
    Returns:
        OpenAI client or None if API key not available
    """
    if not OPENAI_AVAILABLE:
        return None
    
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return None
    
    try:
        return OpenAI(api_key=api_key)
    except Exception as e:
        print(f"Warning: Could not initialize OpenAI client: {e}")
        return None


def call_openai_api(
    prompt: str,
    system_prompt: str = None,
    temperature: float = 0.7,
    max_tokens: int = 1500,
) -> str:
    """
    Call OpenAI API with fallback to mock responses.
    
    Args:
        prompt: The user message/prompt
        system_prompt: Optional system instruction
        temperature: Creativity level (0.0-1.0)
        max_tokens: Maximum response length
        
    Returns:
        API response text or mock response
        
    Raises:
        PipelineError: If API call fails and no fallback available
    """
    client = get_openai_client()
    
    if client:
        try:
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            return response.choices[0].message.content.strip()
        except APIError as e:
            print(f"Warning: OpenAI API error: {e}")
            print("Falling back to mock responses...")
            return None
        except Exception as e:
            print(f"Warning: Unexpected error calling OpenAI: {e}")
            return None
    
    return None


# ============================================================================
# STEP 1: STRUCTURE EXTRACTION
# ============================================================================

def extract_essay_structure(essay_text: str) -> Dict:
    """
    Step 1: Extract thesis statement, main arguments, and overall structure.
    
    Args:
        essay_text: The full essay content
        
    Returns:
        Dictionary containing:
        - thesis: The thesis statement
        - main_arguments: List of main arguments
        - structure_summary: Overall structure description
    """
    if not essay_text or len(essay_text.strip()) < 50:
        raise PipelineError("Essay is too short for analysis (minimum 50 characters)")

    # Try API call first
    system_prompt = """You are an expert writing analyst. Extract the thesis statement, 
    main arguments, and provide a brief structural analysis of the essay.
    
    Respond with ONLY a valid JSON object (no markdown, no explanation) with these keys:
    {
        "thesis": "The main thesis or central claim",
        "main_arguments": ["Argument 1", "Argument 2", "Argument 3"],
        "structure_summary": "Brief description of the essay's structure"
    }"""

    prompt = f"""Analyze this essay and extract its structure:

{essay_text[:2000]}

Provide the thesis, main arguments (as a list of strings), and a structural summary."""

    api_response = call_openai_api(prompt, system_prompt, temperature=0.5, max_tokens=800)
    
    if api_response:
        try:
            return json.loads(api_response)
        except json.JSONDecodeError:
            print("Warning: Could not parse API response, using fallback")
            return get_mock_structure(essay_text)
    
    # Fallback to mock response
    return get_mock_structure(essay_text)


def get_mock_structure(essay_text: str) -> Dict:
    """
    Generate mock structure extraction for testing/fallback.
    
    Args:
        essay_text: The essay content
        
    Returns:
        Mock structure extraction
    """
    sentences = essay_text.split(".")
    
    # Find thesis (usually first paragraph)
    thesis = sentences[0].strip() if sentences else "Thesis statement not found"
    
    # Extract main arguments (paragraphs contain main ideas)
    main_arguments = [
        s.strip()[:100] + "..."
        for s in sentences[1:6]
        if s.strip() and len(s.strip()) > 20
    ][:3]
    
    if not main_arguments:
        main_arguments = [
            "Primary argument about the main topic",
            "Supporting argument with evidence",
            "Additional perspective or counterpoint",
        ]
    
    return {
        "thesis": thesis,
        "main_arguments": main_arguments,
        "structure_summary": f"The essay contains {len(main_arguments)} main arguments "
                            f"supporting the central thesis. The writing follows a logical "
                            f"progression from introduction through body paragraphs to conclusion.",
    }


# ============================================================================
# STEP 2: RUBRIC EVALUATION
# ============================================================================

def evaluate_essay_rubric(essay_text: str, structure: Dict) -> Dict:
    """
    Step 2: Evaluate essay on clarity, argument strength, and organization.
    Each category receives a score (1-5) and reasoning.
    
    Args:
        essay_text: The full essay content
        structure: Result from step 1 (used for context)
        
    Returns:
        Dictionary with scores and reasoning for each category:
        {
            "clarity": {"score": 4, "reasoning": "..."},
            "argument_strength": {"score": 3, "reasoning": "..."},
            "organization": {"score": 4, "reasoning": "..."}
        }
    """
    system_prompt = """You are an expert writing evaluator. Score an essay on three criteria:
    - Clarity: How clear and understandable is the writing?
    - Argument Strength: How strong are the arguments and evidence?
    - Organization: How well is the essay structured and organized?
    
    Respond with ONLY a valid JSON object (no markdown, no explanation):
    {
        "clarity": {"score": 4, "reasoning": "Clear explanations..."},
        "argument_strength": {"score": 3, "reasoning": "Arguments supported by..."},
        "organization": {"score": 4, "reasoning": "Well-structured with..."}
    }
    
    Scores range from 1 (poor) to 5 (excellent).
    Keep reasoning concise (1-2 sentences)."""

    prompt = f"""Evaluate this essay on a 1-5 scale for clarity, argument strength, and organization:

ESSAY:
{essay_text[:2000]}

STRUCTURE ANALYSIS (for reference):
Thesis: {structure.get('thesis', 'N/A')}
Arguments: {', '.join(structure.get('main_arguments', [])[:2])}

Provide scores and reasoning for each criterion."""

    api_response = call_openai_api(prompt, system_prompt, temperature=0.5, max_tokens=600)
    
    if api_response:
        try:
            return json.loads(api_response)
        except json.JSONDecodeError:
            print("Warning: Could not parse rubric API response, using fallback")
            return get_mock_rubric(essay_text)
    
    # Fallback
    return get_mock_rubric(essay_text)


def get_mock_rubric(essay_text: str) -> Dict:
    """
    Generate mock rubric evaluation for testing/fallback.
    
    Args:
        essay_text: The essay content
        
    Returns:
        Mock rubric scores
    """
    # Simple heuristics for mock scoring
    clarity_score = 3 + (1 if len(essay_text.split()) > 500 else 0)
    avg_sentence_length = sum(
        len(s.split()) for s in essay_text.split(".") if s.strip()
    ) / max(len(essay_text.split(".")), 1)
    organization_score = 3 + (1 if 200 < avg_sentence_length < 20 else 0)
    
    return {
        "clarity": {
            "score": min(clarity_score, 5),
            "reasoning": "The essay demonstrates generally clear writing with well-formed sentences and coherent ideas.",
        },
        "argument_strength": {
            "score": 3,
            "reasoning": "Arguments are present and supported, though some could be strengthened with more specific evidence.",
        },
        "organization": {
            "score": min(organization_score, 5),
            "reasoning": "The essay follows a logical structure with clear progression from introduction to conclusion.",
        },
    }


# ============================================================================
# STEP 3: FEEDBACK GENERATION
# ============================================================================

def generate_feedback(essay_text: str, structure: Dict, rubric: Dict) -> Dict:
    """
    Step 3: Generate actionable feedback suggestions based on structure and rubric scores.
    
    Args:
        essay_text: The full essay content
        structure: Result from step 1
        rubric: Result from step 2
        
    Returns:
        Dictionary with:
        - overall_feedback: High-level assessment
        - priority_areas: List of areas that need attention (with priority level)
        - actionable_advice: List of specific, actionable recommendations
    """
    # Calculate overall score
    overall_score = sum(
        v["score"] for v in rubric.values() if isinstance(v, dict) and "score" in v
    ) / 3

    system_prompt = """You are an expert writing coach. Based on essay scores and structure,
    provide actionable feedback for improvement.
    
    Respond with ONLY a valid JSON object (no markdown, no explanation):
    {
        "overall_feedback": "Overall assessment paragraph",
        "priority_areas": [
            {"area": "Area name", "description": "What needs fixing", "priority": "high|medium|low"},
            ...
        ],
        "actionable_advice": [
            "Specific, actionable recommendation 1",
            "Specific, actionable recommendation 2",
            ...
        ]
    }
    
    Keep feedback specific, constructive, and actionable."""

    prompt = f"""Provide detailed feedback for improvement on this essay.

RUBRIC SCORES:
- Clarity: {rubric.get('clarity', {}).get('score', 3)}/5
- Argument Strength: {rubric.get('argument_strength', {}).get('score', 3)}/5
- Organization: {rubric.get('organization', {}).get('score', 3)}/5

ESSAY EXCERPT:
{essay_text[:1500]}

THESIS: {structure.get('thesis', 'N/A')}

Generate overall feedback, identify 2-3 priority areas for improvement, and provide 3-4 
specific, actionable recommendations for enhancing the essay."""

    api_response = call_openai_api(prompt, system_prompt, temperature=0.7, max_tokens=1000)
    
    if api_response:
        try:
            return json.loads(api_response)
        except json.JSONDecodeError:
            print("Warning: Could not parse feedback API response, using fallback")
            return get_mock_feedback(rubric)
    
    # Fallback
    return get_mock_feedback(rubric)


def get_mock_feedback(rubric: Dict) -> Dict:
    """
    Generate mock feedback for testing/fallback.
    
    Args:
        rubric: Rubric scores from step 2
        
    Returns:
        Mock feedback suggestions
    """
    clarity_score = rubric.get("clarity", {}).get("score", 3)
    argument_score = rubric.get("argument_strength", {}).get("score", 3)
    org_score = rubric.get("organization", {}).get("score", 3)

    priority_areas = []

    # Determine priority areas based on low scores
    if clarity_score <= 2:
        priority_areas.append({
            "area": "Clarity and Expression",
            "description": "Many sentences are unclear or difficult to follow. Consider breaking long sentences into shorter ones and using simpler language.",
            "priority": "high",
        })
    elif clarity_score == 3:
        priority_areas.append({
            "area": "Clarity and Expression",
            "description": "Some sentences could be clearer. Review for wordiness and ensure each sentence has a clear purpose.",
            "priority": "medium",
        })

    if argument_score <= 2:
        priority_areas.append({
            "area": "Argument Strength",
            "description": "Arguments need stronger support. Add specific examples, statistics, or quotes from credible sources.",
            "priority": "high",
        })
    elif argument_score == 3:
        priority_areas.append({
            "area": "Argument Strength",
            "description": "While arguments are present, they could be more compelling. Provide more detailed evidence.",
            "priority": "medium",
        })

    if org_score <= 2:
        priority_areas.append({
            "area": "Organization",
            "description": "The essay lacks clear structure. Consider using topic sentences and ensuring logical flow between paragraphs.",
            "priority": "high",
        })

    actionable_advice = [
        "Review your thesis statement to ensure it clearly states the main argument of your essay.",
        "For each body paragraph, start with a topic sentence that connects to your thesis.",
        "Add transitions between paragraphs to improve logical flow and coherence.",
        "Support each argument with specific evidence, examples, or quotes from reliable sources.",
        "Proofread carefully for grammar, spelling, and punctuation errors.",
    ]

    return {
        "overall_feedback": f"Your essay demonstrates solid foundational skills with areas for improvement. "
                          f"The writing has a score of approximately {(clarity_score + argument_score + org_score) / 3:.1f}/5. "
                          f"Focus on the priority areas below to significantly enhance your essay.",
        "priority_areas": priority_areas[:3] if priority_areas else [
            {
                "area": "Strengthen Evidence",
                "description": "Add more specific examples and citations to support your claims.",
                "priority": "medium",
            }
        ],
        "actionable_advice": actionable_advice,
    }


# ============================================================================
# FULL PIPELINE ORCHESTRATION
# ============================================================================

def run_full_pipeline(essay_text: str) -> Dict:
    """
    Run the complete three-step pipeline on an essay.
    
    Args:
        essay_text: The essay content to analyze
        
    Returns:
        Dictionary with results from all three steps
        
    Raises:
        PipelineError: If any step fails critically
    """
    try:
        print("🔄 Starting essay analysis pipeline...")

        # Step 1
        print("📋 Step 1: Extracting essay structure...")
        structure = extract_essay_structure(essay_text)
        print(f"   ✓ Thesis: {structure['thesis'][:50]}...")
        print(f"   ✓ Arguments: {len(structure['main_arguments'])} identified")

        # Step 2
        print("📊 Step 2: Evaluating essay against rubric...")
        rubric = evaluate_essay_rubric(essay_text, structure)
        clarity = rubric.get("clarity", {}).get("score", "?")
        argument = rubric.get("argument_strength", {}).get("score", "?")
        org = rubric.get("organization", {}).get("score", "?")
        print(f"   ✓ Clarity: {clarity}/5")
        print(f"   ✓ Argument Strength: {argument}/5")
        print(f"   ✓ Organization: {org}/5")

        # Step 3
        print("💡 Step 3: Generating feedback...")
        feedback = generate_feedback(essay_text, structure, rubric)
        print(f"   ✓ Priority areas: {len(feedback.get('priority_areas', []))}")
        print(f"   ✓ Actionable advice: {len(feedback.get('actionable_advice', []))}")

        print("✅ Pipeline complete!\n")

        return {
            "structure": structure,
            "rubric": rubric,
            "feedback": feedback,
            "status": "success",
        }

    except PipelineError as e:
        print(f"❌ Pipeline error: {e}")
        raise
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        raise PipelineError(f"Pipeline failed: {str(e)}")
