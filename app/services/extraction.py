"""
Stub LLM extraction functions.
Returns deterministic dummy output for local testing.
"""
from typing import Any
import hashlib


def extract_facts(draft_text: str) -> list[dict[str, Any]]:
    """
    Extract facts from a draft text.
    
    In production, this would call an LLM to extract structured facts.
    For now, returns deterministic dummy facts based on the text.
    
    Args:
        draft_text: The text of the draft to extract facts from.
        
    Returns:
        A list of fact dictionaries.
    """
    # Generate deterministic "facts" based on text hash
    text_hash = hashlib.md5(draft_text.encode()).hexdigest()[:8]
    
    facts = [
        {
            "fact_type": "character_trait",
            "subject_type": "character",
            "subject_id": 1,
            "predicate": "appears_in_scene",
            "object_jsonb": {"action": "speaks", "hash": text_hash},
            "confidence": 0.95
        },
        {
            "fact_type": "location_detail",
            "subject_type": "location",
            "subject_id": None,
            "predicate": "setting",
            "object_jsonb": {"description": "interior", "hash": text_hash},
            "confidence": 0.85
        },
        {
            "fact_type": "event",
            "subject_type": "scene",
            "subject_id": None,
            "predicate": "contains_event",
            "object_jsonb": {"event_type": "dialogue", "hash": text_hash},
            "confidence": 0.90
        }
    ]
    
    return facts


def summarize_scene(draft_text: str) -> str:
    """
    Generate a summary of the scene draft.
    
    In production, this would call an LLM to generate a summary.
    For now, returns a deterministic placeholder summary.
    
    Args:
        draft_text: The text of the draft to summarize.
        
    Returns:
        A summary string.
    """
    word_count = len(draft_text.split())
    text_hash = hashlib.md5(draft_text.encode()).hexdigest()[:8]
    
    return f"Scene summary ({word_count} words): A scene involving character interactions and plot development. [Hash: {text_hash}]"


def generate_scene_plan(scene_card: dict[str, Any]) -> dict[str, Any]:
    """
    Generate a plan for writing a scene based on its card.
    
    In production, this would call an LLM to create a detailed outline.
    For now, returns a deterministic placeholder plan.
    
    Args:
        scene_card: The scene's card_jsonb with metadata.
        
    Returns:
        A plan dictionary.
    """
    return {
        "beats": [
            {"order": 1, "description": "Opening hook - establish setting and tension"},
            {"order": 2, "description": "Character introduction and dialogue"},
            {"order": 3, "description": "Rising action - conflict emerges"},
            {"order": 4, "description": "Climactic moment"},
            {"order": 5, "description": "Resolution and transition"}
        ],
        "tone": scene_card.get("tone", "dramatic"),
        "pacing": "medium",
        "word_target": 1500
    }


def generate_draft(scene_card: dict[str, Any], plan: dict[str, Any]) -> str:
    """
    Generate a draft based on the scene card and plan.
    
    In production, this would call an LLM to write the draft.
    For now, returns deterministic placeholder text.
    
    Args:
        scene_card: The scene's card_jsonb with metadata.
        plan: The scene plan from generate_scene_plan.
        
    Returns:
        The draft text.
    """
    title = scene_card.get("title", "Untitled Scene")
    
    return f"""[DRAFT - {title}]

The scene opens with a sense of anticipation hanging in the air. Characters move through the space with purpose, their intentions not yet fully revealed.

"I didn't expect to find you here," said the first character, voice carrying a weight of unspoken history.

"Expectations rarely align with reality," came the measured response. "We both know that better than most."

The dialogue continued, each exchange layered with subtext. The setting—described in vivid detail—served as a silent witness to the unfolding drama.

As tensions mounted, a moment of clarity emerged. The characters faced a choice, one that would echo through the chapters to come.

The scene concluded with a lingering question, a thread left deliberately loose for future exploration.

[END DRAFT - Generated from plan with {len(plan.get('beats', []))} beats]"""


def revise_draft(
    current_draft: str,
    check_findings: list[dict[str, Any]]
) -> str:
    """
    Revise a draft based on check findings.
    
    In production, this would call an LLM to revise the draft.
    For now, appends revision notes to demonstrate the revision happened.
    
    Args:
        current_draft: The current draft text.
        check_findings: Issues found during checks.
        
    Returns:
        The revised draft text.
    """
    finding_count = len(check_findings)
    
    revision_note = f"""

[REVISION NOTE]
Addressed {finding_count} finding(s) from continuity and style checks.
Revisions applied:
"""
    
    for i, finding in enumerate(check_findings, 1):
        issue = finding.get("issue", "unspecified issue")
        revision_note += f"  {i}. Corrected: {issue}\n"
    
    revision_note += "[END REVISION NOTE]"
    
    # In reality, we'd send to LLM for proper revision
    # For now, append note to show revision occurred
    return current_draft + revision_note
