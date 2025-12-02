import re

# --- 1. Define personal / non-business patterns ---

PERSONAL_PATTERNS = [

    # Very casual / social language
    r"\b(hey bestie|hey babe|hey boo)\b",
    r"\b(lol|lmao|rofl|omg|wtf|idk|ikr)\b",

    # Family / friends / relationships
    r"\b(my (mom|dad|sister|brother|grandma|grandpa|cousin|boyfriend|girlfriend|partner))\b",
    r"\b(love you|miss you|xoxo|hugs|kisses)\b",

    # Parties / hanging out / social plans
    r"\b(party|sleepover|hang out|hangout|kickback|house party|pre[- ]game)\b",
    r"\b(movie night|game night|board game night)\b",

    # School / student life (you may want these to be "business" if school-related work counts!)
    r"\b(dorm|roommate|dining hall|cafeteria|meal plan)\b",
    r"\b(fraternity|sorority|rush week|greek life)\b",

    # Streaming / entertainment
    r"\b(netflix|hulu|disney\+|spotify|crunchyroll|anime)\b",
    r"\b(binge[- ]watch|watch party)\b",

    # Shopping / personal discount codes / newsletters
    r"\b(promo code|discount code|limited time offer|20% off|50% off)\b",
    r"\b(newsletter|unsubscribe from this list)\b",

    # Social media / apps
    r"\b(instagram|tiktok|snapchat|twitter|x\.com|reddit)\b",
    r"\b(dms?|snap me|add me|follow me)\b",

    # Money transfers between friends
    r"\b(venmo|cashapp|cash app|zelle)\b",
    r"\b(split the bill|i'll pay you back|pay me back)\b",

    # Obvious personal lifecycle stuff
    r"\b(birthday party|wedding invitation|baby shower|bachelorette|bachelor party)\b",

    # Informal sign-offs
    r"(^|[\n\r])\s*(cheers|see ya|see you soon|talk soon|ttyl)[,!]?\s*$",
]

PERSONAL_REGEXES = [re.compile(pat, re.IGNORECASE) for pat in PERSONAL_PATTERNS]


def is_likely_personal(email_text: str) -> bool:
    """
    Returns True if the email looks personal / non-business
    according to our regex patterns.
    """
    # Normalize whitespace a bit
    text = " ".join(email_text.split())

    for regex in PERSONAL_REGEXES:
        if regex.search(text):
            return True
    return False


def apply_personal_rules(emails_and_tag: dict) -> dict:
    """
    Given a dict: {email_text: True/False},
    if the email looks non-business, force the tag to False.

    Returns a NEW dict with updated tags.
    """
    updated = {}
    for email_text, tag in emails_and_tag.items():
        if is_likely_personal(email_text):
            updated[email_text] = False   # force to "not business"
        else:
            updated[email_text] = tag     # leave as-is
    return updated
