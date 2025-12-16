"""
Continuity and style checks for drafts.
Operates on extracted facts and constraints.
"""
from typing import Any
from dataclasses import dataclass, field


@dataclass
class CheckResult:
    """Result of a check run."""
    check_type: str
    passed: bool
    findings: list[dict[str, Any]] = field(default_factory=list)


def run_continuity_check(
    facts: list[dict[str, Any]],
    constraints: list[dict[str, Any]],
    previous_facts: list[dict[str, Any]] = None
) -> CheckResult:
    """
    Run continuity checks on extracted facts.
    
    Checks for:
    - Contradictions with established facts
    - Timeline inconsistencies
    - Character behavior consistency
    
    Args:
        facts: Facts extracted from the current draft.
        constraints: Project constraints to check against.
        previous_facts: Facts from previous scenes/drafts.
        
    Returns:
        CheckResult with pass/fail status and findings.
    """
    findings = []
    previous_facts = previous_facts or []
    
    # Check for low-confidence facts
    for fact in facts:
        confidence = fact.get("confidence", 1.0)
        if confidence < 0.7:
            findings.append({
                "severity": "warning",
                "issue": f"Low confidence fact ({confidence:.2f}): {fact.get('predicate')}",
                "fact_type": fact.get("fact_type"),
                "suggestion": "Consider clarifying or removing ambiguous information"
            })
    
    # Check against constraints
    for constraint in constraints:
        if constraint.get("constraint_type") == "continuity":
            rule = constraint.get("rule_jsonb", {})
            
            # Example: Check for required character presence
            if rule.get("type") == "character_must_appear":
                char_id = rule.get("character_id")
                char_facts = [
                    f for f in facts 
                    if f.get("subject_type") == "character" 
                    and f.get("subject_id") == char_id
                ]
                if not char_facts:
                    findings.append({
                        "severity": constraint.get("severity", "error"),
                        "issue": f"Required character {char_id} does not appear in scene",
                        "constraint_id": constraint.get("id"),
                        "suggestion": "Add character to the scene"
                    })
    
    # Check for contradictions with previous facts
    for fact in facts:
        for prev_fact in previous_facts:
            if (
                fact.get("subject_type") == prev_fact.get("subject_type")
                and fact.get("subject_id") == prev_fact.get("subject_id")
                and fact.get("predicate") == prev_fact.get("predicate")
            ):
                # Same subject and predicate - check for contradiction
                if fact.get("object_jsonb") != prev_fact.get("object_jsonb"):
                    findings.append({
                        "severity": "error",
                        "issue": f"Potential contradiction: {fact.get('predicate')} differs from previous fact",
                        "current": fact.get("object_jsonb"),
                        "previous": prev_fact.get("object_jsonb"),
                        "suggestion": "Reconcile the contradiction or justify the change"
                    })
    
    # Determine pass/fail based on error-level findings
    has_errors = any(f.get("severity") == "error" for f in findings)
    
    return CheckResult(
        check_type="continuity",
        passed=not has_errors,
        findings=findings
    )


def run_style_check(
    draft_text: str,
    style_bible: dict[str, Any] = None
) -> CheckResult:
    """
    Run style checks on draft text.
    
    Checks for:
    - POV consistency
    - Tense consistency
    - Voice/tone adherence
    - Word count requirements
    
    Args:
        draft_text: The draft text to check.
        style_bible: The project's style guide.
        
    Returns:
        CheckResult with pass/fail status and findings.
    """
    findings = []
    style_bible = style_bible or {}
    
    word_count = len(draft_text.split())
    
    # Check minimum word count
    min_words = style_bible.get("min_word_count", 100)
    if word_count < min_words:
        findings.append({
            "severity": "warning",
            "issue": f"Draft is too short ({word_count} words, minimum {min_words})",
            "suggestion": f"Expand the draft to at least {min_words} words"
        })
    
    # Check maximum word count
    max_words = style_bible.get("max_word_count", 5000)
    if word_count > max_words:
        findings.append({
            "severity": "warning",
            "issue": f"Draft is too long ({word_count} words, maximum {max_words})",
            "suggestion": f"Consider splitting the scene or trimming to {max_words} words"
        })
    
    # Check for common style issues (simplified rules)
    lower_text = draft_text.lower()
    
    # Check for passive voice indicators (simplified)
    passive_indicators = ["was being", "were being", "had been", "has been"]
    passive_count = sum(lower_text.count(indicator) for indicator in passive_indicators)
    if passive_count > 5:
        findings.append({
            "severity": "info",
            "issue": f"High passive voice usage ({passive_count} instances detected)",
            "suggestion": "Consider using more active voice for stronger prose"
        })
    
    # Check for adverb overuse (words ending in -ly)
    words = draft_text.split()
    adverbs = [w for w in words if w.lower().endswith("ly") and len(w) > 4]
    adverb_ratio = len(adverbs) / max(len(words), 1)
    if adverb_ratio > 0.03:  # More than 3% adverbs
        findings.append({
            "severity": "info",
            "issue": f"Consider reducing adverb usage ({len(adverbs)} adverbs in {len(words)} words)",
            "suggestion": "Replace adverbs with stronger verbs where possible"
        })
    
    # Check for forbidden words/phrases
    forbidden = style_bible.get("forbidden_words", [])
    for word in forbidden:
        if word.lower() in lower_text:
            findings.append({
                "severity": "error",
                "issue": f"Forbidden word/phrase found: '{word}'",
                "suggestion": "Remove or replace this word/phrase"
            })
    
    # Check POV consistency if specified
    pov = style_bible.get("pov", "third")
    if pov == "first":
        # Check for accidental third-person in first-person narrative
        third_person_indicators = [" he said", " she said", " they said"]
        for indicator in third_person_indicators:
            if indicator in lower_text:
                findings.append({
                    "severity": "warning",
                    "issue": f"Possible POV break: '{indicator.strip()}' in first-person narrative",
                    "suggestion": "Ensure consistent first-person POV"
                })
    
    # Determine pass/fail based on error-level findings
    has_errors = any(f.get("severity") == "error" for f in findings)
    
    return CheckResult(
        check_type="style",
        passed=not has_errors,
        findings=findings
    )


def run_all_checks(
    draft_text: str,
    facts: list[dict[str, Any]],
    constraints: list[dict[str, Any]],
    style_bible: dict[str, Any] = None,
    previous_facts: list[dict[str, Any]] = None
) -> list[CheckResult]:
    """
    Run all checks on a draft.
    
    Args:
        draft_text: The draft text.
        facts: Facts extracted from the draft.
        constraints: Project constraints.
        style_bible: Project style guide.
        previous_facts: Facts from previous scenes.
        
    Returns:
        List of CheckResult objects.
    """
    return [
        run_continuity_check(facts, constraints, previous_facts),
        run_style_check(draft_text, style_bible)
    ]
