"""
Rule-Based Email Classifier

Uses regex patterns to identify casual vs business emails.
Designed for Enron dataset (1999-2002 era emails).

Can be used to:
1. Reclassify potentially mislabeled business emails as casual
2. Provide a baseline classifier for comparison
3. Generate features for the ML model
"""

import re
from typing import Tuple, List, Dict

# =============================================================================
# CASUAL PATTERNS - Organized by confidence level
# =============================================================================

CASUAL_PATTERNS = {
    # High confidence casual signals (weight: 2.0)
    "strong_casual": [
        # Informal language / internet speak
        r"\b(lol|lmao|rofl|haha+|hehe+|ha ha)\b",
        r"\b(omg|wtf|btw|fyi|imho|imo)\b",
        
        # Affection / personal relationships
        r"\b(love you|miss you|xoxo|hugs|kisses)\b",
        r"\b(sweetie|honey|babe|sweetheart)\b",
        
        # Celebrations / personal events
        r"\b(happy birthday|merry christmas|happy thanksgiving|happy new year)\b",
        r"\b(birthday party|wedding|baby shower|anniversary)\b",
        r"\b(congratulations|congrats)\b.*\b(baby|wedding|engaged|new house)\b",
        
        # Social gatherings
        r"\b(party|bbq|barbecue|potluck|cookout)\b",
        r"\b(sleepover|house party|get[- ]together)\b",
        
        # Vacation / personal time
        r"\b(vacation|holiday|road trip|weekend getaway)\b",
        r"\b(beach|camping|hiking|fishing trip)\b",
        
        # Religious/holiday (common in Enron Texas culture)
        r"\b(god bless|prayers?|church|sermon)\b",
        r"\b(easter|thanksgiving dinner|christmas party)\b",
    ],
    
    # Medium confidence (weight: 1.0)
    "medium_casual": [
        # Food/social plans (very common in Enron casual emails)
        r"\b(want to|wanna|gonna)\s+(grab|get|have)\s+(lunch|dinner|drinks|coffee|beer)\b",
        r"\b(lunch|dinner|drinks)\b.*\b(today|tomorrow|friday|thursday)\b",
        r"\b(happy hour|after work drinks|grab a beer)\b",
        r"\b(let'?s (do|get|grab) (lunch|dinner|drinks|coffee))\b",
        
        # Sports (extremely common in Enron)
        r"\b(football|baseball|basketball|hockey|golf|tennis)\s*(game|match|tournament)\b",
        r"\b(playoffs|championship|superbowl|super bowl|world series)\b",
        r"\b(fantasy football|fantasy baseball|fantasy league|draft)\b",
        r"\b(astros|texans|rockets|oilers|cowboys|spurs|rangers|mavs|mavericks)\b",
        r"\b(ncaa|march madness|bowl game)\b",
        r"\b(did you see the game|watch the game|game last night)\b",
        
        # Family mentions in personal context
        r"\b(my (mom|dad|mother|father|brother|sister|wife|husband|son|daughter|kids?))\b",
        r"\b(the kids?|my family|the family)\b.*\b(birthday|school|soccer|little league|recital)\b",
        
        # Jokes / forwarded humor (common in early 2000s)
        r"\b(joke|funny|hilarious|check this out|you'?ll love this)\b",
        r"(fw:|fwd:|forwarded).*\b(joke|funny|humor|laugh)\b",
        r"\b(this is (so )?funny|too funny|made me laugh)\b",
        
        # Weekend / personal plans
        r"\b(this weekend|next weekend|saturday|sunday)\b.*\b(plan|doing|free|busy)\b",
        r"\b(movie|concert|show|game)\b.*\b(tonight|tomorrow|weekend|friday)\b",
        r"\b(are you free|you free|got plans|any plans)\b",
        
        # Personal wellbeing
        r"\b(how are you|how'?s it going|how'?s everything|what'?s up|what'?s new)\b",
        r"\b(sorry to hear|hope you feel better|get well soon|feeling better)\b",
        r"\b(good to see you|great seeing you|nice to meet)\b",
        
        # Pets
        r"\b(my (dog|cat|pet)|the (dog|cat)|puppy|kitten)\b",
        
        # Personal errands
        r"\b(pick up|drop off|grocery|dry clean|pharmacy|doctor)\b",
        r"\b(appointment|dentist|vet|haircut)\b",
        
        # Casual closings
        r"\b(later|cheers|peace out?|take it easy|cya)\b",
        r"\b(gotta go|gotta run|talk later)\b",
        
        # More sports / entertainment
        r"\b(tickets?|seats?)\b.*\b(game|concert|show)\b",
        r"\b(tee time|golf course|round of golf)\b",
    ],
    
    # Weak signals (weight: 0.5) - need multiple to trigger
    "weak_casual": [
        r"\b(thanks!+|great!+|awesome!+|cool!+|nice!+|sweet!+)\b",
        r"\b(see you|talk soon|take care|catch you later|ttyl)\b",
        r"\b(hey|hi there|hello)\b",
        r"\b(yeah|yep|nope|nah|sure thing)\b",
        r"\b(sounds good|sounds great|sounds fun)\b",
        r"\b(no problem|no worries|don'?t worry)\b",
        r"\b(anyway|anyways|anyhow)\b",
        r":[\)\(DPp]|;\)|<3",  # Emoticons
    ],
}

# =============================================================================
# BUSINESS PATTERNS - Organized by confidence level (tiered weights)
# =============================================================================

BUSINESS_PATTERNS = {
    # Strong business signals (weight: -2.0)
    "strong_business": [
        # Legal / contracts
        r"\b(contract|agreement|invoice|purchase order|NDA)\b",
        r"\b(quarterly|annual report|10-?K|SEC filing)\b",
        r"\b(confidential|privileged|attorney[- ]client)\b",
        
        # Financial terms
        r"\b(fiscal|budget|revenue|profit|variance)\b",
        r"\b(forecast|projection|estimate)\b",
        r"\b(deal|transaction|acquisition|merger)\b",
        
        # Stakeholders
        r"\b(client|customer|vendor|supplier|counterparty)\b",
        r"\b(stakeholder|management|executive|board)\b",
    ],
    
    # Medium business signals (weight: -1.0)
    "medium_business": [
        # Meetings / scheduling
        r"\b(meeting|conference call|dial[- ]in|teleconference)\b",
        r"\b(schedule|calendar|agenda|minutes)\b",
        r"\b(action items?|follow[- ]up|next steps)\b",
        
        # Deadlines / deliverables
        r"\b(deadline|deliverable|milestone|due date)\b",
        r"\b(eod|cob|end of day|close of business)\b",
        r"\b(asap|urgent|priority|time[- ]sensitive)\b",
        
        # Documents / formal communication
        r"\b(attached|enclosed|per our discussion|as discussed)\b",
        r"\b(please review|for your (review|approval)|kindly review)\b",
        r"\b(draft|revision|version|redline)\b",
        r"\b(proposal)\b",
        
        # Formal language
        r"\b(pursuant to|in accordance with|regarding|re:)\b",
    ],
    
    # Weak business signals (weight: -0.5)
    "weak_business": [
        r"\b(regards|sincerely|best regards)\b",
        r"\b(please advise|please confirm|please let me know)\b",
        r"\b(best)\b$",  # "Best" at end of email
    ],
}

# =============================================================================
# COMPILE PATTERNS
# =============================================================================

STRONG_CASUAL = [re.compile(p, re.IGNORECASE) for p in CASUAL_PATTERNS["strong_casual"]]
MEDIUM_CASUAL = [re.compile(p, re.IGNORECASE) for p in CASUAL_PATTERNS["medium_casual"]]
WEAK_CASUAL = [re.compile(p, re.IGNORECASE) for p in CASUAL_PATTERNS["weak_casual"]]

# Tiered business patterns
STRONG_BUSINESS = [re.compile(p, re.IGNORECASE) for p in BUSINESS_PATTERNS["strong_business"]]
MEDIUM_BUSINESS = [re.compile(p, re.IGNORECASE) for p in BUSINESS_PATTERNS["medium_business"]]
WEAK_BUSINESS = [re.compile(p, re.IGNORECASE) for p in BUSINESS_PATTERNS["weak_business"]]


# =============================================================================
# CLASSIFICATION FUNCTIONS
# =============================================================================

def analyze_subject(text: str) -> Tuple[float, List[str]]:
    """
    Extract subject line and return casual/business score modifier.
    
    Args:
        text: Full email text (may contain Subject: header)
        
    Returns:
        Tuple of (score_modifier, matched_patterns)
    """
    subject_match = re.search(r"subject:\s*(.+?)(\n|$)", text, re.IGNORECASE)
    if not subject_match:
        return 0.0, []
    
    subject = subject_match.group(1)
    score = 0.0
    matched = []
    
    # Multiple forwards = likely joke/chain email
    fw_count = subject.lower().count("fw:") + subject.lower().count("fwd:")
    if fw_count >= 2:
        score += 2.0
        matched.append(f"SUBJ: multiple forwards ({fw_count}x)")
    
    # Business subject keywords
    if re.search(r"\b(Q[1-4]|budget|report|meeting|action|agenda)\b", subject, re.IGNORECASE):
        score -= 1.0
        matched.append("SUBJ: business keyword")
    
    # Casual subject keywords
    if re.search(r"\b(joke|funny|fwd|fw|re: re:|lol|haha)\b", subject, re.IGNORECASE):
        score += 1.0
        matched.append("SUBJ: casual keyword")
    
    return score, matched


def classify_email(email_text: str) -> Tuple[bool, float, List[str]]:
    """
    Classify email as casual or business using rule-based patterns.
    
    Args:
        email_text: The email text to classify
        
    Returns:
        Tuple of (is_casual, confidence, matched_patterns)
        - is_casual: True if classified as casual
        - confidence: 0.0 to 1.0 confidence score
        - matched_patterns: List of patterns that matched (for debugging)
    """
    text = " ".join(email_text.split())
    matched = []
    score = 0.0
    
    # Analyze subject line first
    subject_score, subject_matched = analyze_subject(text)
    score += subject_score
    matched.extend(subject_matched)
    
    # Check tiered business patterns (negative scores)
    # Strong business signals (weight: -2.0)
    for regex in STRONG_BUSINESS:
        if regex.search(text):
            score -= 2.0
            matched.append(f"BIZ_STRONG: {regex.pattern[:30]}...")
    
    # Medium business signals (weight: -1.0)
    for regex in MEDIUM_BUSINESS:
        if regex.search(text):
            score -= 1.0
            matched.append(f"BIZ_MED: {regex.pattern[:30]}...")
    
    # Weak business signals (weight: -0.5)
    weak_biz_count = sum(1 for r in WEAK_BUSINESS if r.search(text))
    if weak_biz_count >= 1:
        score -= 0.5 * weak_biz_count
        matched.append(f"BIZ_WEAK: {weak_biz_count} patterns")
    
    # Strong casual signals (weight: 2.0)
    for regex in STRONG_CASUAL:
        if regex.search(text):
            score += 2.0
            matched.append(f"CASUAL_STRONG: {regex.pattern[:30]}...")
    
    # Medium casual signals (weight: 1.0)
    for regex in MEDIUM_CASUAL:
        if regex.search(text):
            score += 1.0
            matched.append(f"CASUAL_MED: {regex.pattern[:30]}...")
    
    # Weak casual signals - need multiple to contribute
    weak_count = sum(1 for r in WEAK_CASUAL if r.search(text))
    if weak_count >= 2:
        score += 0.5 * weak_count
        matched.append(f"CASUAL_WEAK: {weak_count} patterns")
    
    # Short email handling: boost casual confidence for short casual messages
    word_count = len(text.split())
    if word_count <= 10 and score > 0:
        score += 0.5
        matched.append(f"SHORT_BOOST: {word_count} words")
    
    # Determine classification
    is_casual = score > 0
    
    # Calculate confidence (normalized to 0-1)
    confidence = min(abs(score) / 5.0, 1.0)
    
    return is_casual, confidence, matched


def is_likely_personal(email_text: str) -> bool:
    """
    Simple boolean check - returns True if email looks casual/personal.
    Backwards compatible with original API.
    """
    is_casual, confidence, _ = classify_email(email_text)
    return is_casual and confidence >= 0.3


def reclassify_dataset(emails_and_labels: Dict[str, int], 
                       threshold: float = 0.5,
                       verbose: bool = True) -> Dict[str, int]:
    """
    Re-classify business emails that appear to be casual.
    
    Only changes business (1) -> casual (0), never the reverse.
    This is a one-way safety mechanism to avoid incorrectly labeling
    actual casual emails as business.
    
    Args:
        emails_and_labels: Dictionary of {email_text: label} where 1=business, 0=casual
        threshold: Confidence threshold required to flip a label (0.0 to 1.0)
        verbose: Print summary statistics
        
    Returns:
        New dictionary with updated labels
    """
    updated = {}
    flipped_count = 0
    flipped_examples = []
    
    for email_text, label in emails_and_labels.items():
        if label == 1:  # Only check business emails
            is_casual, confidence, patterns = classify_email(email_text)
            
            if is_casual and confidence >= threshold:
                updated[email_text] = 0  # Flip to casual
                flipped_count += 1
                if len(flipped_examples) < 5:
                    flipped_examples.append((email_text[:100], confidence, patterns[:3]))
            else:
                updated[email_text] = label
        else:
            updated[email_text] = label
    
    if verbose:
        total_business = sum(1 for v in emails_and_labels.values() if v == 1)
        print(f"\nRule-Based Reclassification Results:")
        print(f"  Analyzed: {total_business:,} business emails")
        print(f"  Reclassified as casual: {flipped_count:,} ({flipped_count/total_business*100:.1f}%)")
        print(f"  Threshold used: {threshold}")
        
        if flipped_examples:
            print(f"\n  Example reclassifications:")
            for text, conf, patterns in flipped_examples:
                print(f"    [{conf:.0%}] \"{text}...\"")
                print(f"         Patterns: {patterns}")
    
    return updated


def analyze_dataset(emails_and_labels: Dict[str, int]) -> Dict:
    """
    Analyze a dataset to see how many emails would be reclassified
    at different confidence thresholds.
    
    Args:
        emails_and_labels: Dictionary of {email_text: label}
        
    Returns:
        Analysis dictionary with statistics
    """
    thresholds = [0.3, 0.4, 0.5, 0.6, 0.7, 0.8]
    results = {t: 0 for t in thresholds}
    
    business_emails = [(text, label) for text, label in emails_and_labels.items() if label == 1]
    
    for email_text, _ in business_emails:
        is_casual, confidence, _ = classify_email(email_text)
        if is_casual:
            for t in thresholds:
                if confidence >= t:
                    results[t] += 1
    
    print("\nDataset Analysis - Potential Reclassifications:")
    print(f"  Total business emails: {len(business_emails):,}")
    print(f"\n  Emails flagged as casual at each threshold:")
    for t in thresholds:
        pct = results[t] / len(business_emails) * 100 if business_emails else 0
        print(f"    {t:.0%} confidence: {results[t]:,} ({pct:.1f}%)")
    
    return results


# =============================================================================
# TEST / DEMO
# =============================================================================

def test_classifier():
    """Test the classifier with example emails."""
    examples = [
        ("Hey, want to grab lunch today? The new Thai place looks good.", "casual"),
        ("Please review the attached contract and provide feedback by EOD.", "business"),
        ("LOL that joke was hilarious! Forward it to Steve.", "casual"),
        ("The Q3 budget meeting is scheduled for Tuesday at 2pm.", "business"),
        ("How about drinks after work on Friday? Happy hour at the usual place.", "casual"),
        ("Game tonight - Astros vs Yankees. Want to watch at my place?", "casual"),
        ("Per our discussion, I've attached the revised proposal for your review.", "business"),
        ("Happy birthday! Hope you have a great day with the family!", "casual"),
        ("My wife and I are throwing a BBQ this Saturday - you should come!", "casual"),
        ("Action items from today's meeting are listed below.", "business"),
    ]
    
    print("=" * 70)
    print("Rule-Based Classifier Test")
    print("=" * 70)
    
    correct = 0
    for email, expected in examples:
        is_casual, conf, patterns = classify_email(email)
        predicted = "casual" if is_casual else "business"
        match = "✓" if predicted == expected else "✗"
        if predicted == expected:
            correct += 1
        
        print(f"\n{match} [{conf:.0%}] {predicted.upper()}: \"{email[:55]}...\"")
        if patterns:
            print(f"   Matched: {patterns[:3]}")
    
    print(f"\n{'=' * 70}")
    print(f"Accuracy: {correct}/{len(examples)} ({correct/len(examples)*100:.0f}%)")


if __name__ == "__main__":
    test_classifier()
