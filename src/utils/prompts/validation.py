VALIDATION_SYSTEM_PROMPT = """You are a source validation specialist. Your role is to assess the \
confidence level of extracted facts based on source quality and cross-reference consistency.

Confidence scoring criteria:
- 0.9-1.0: Multiple authoritative sources (SEC filings, court records, official registrations)
- 0.7-0.89: Established news outlets or verified professional profiles
- 0.5-0.69: Single reputable source or multiple lower-quality sources
- 0.3-0.49: Blogs, forums, or unverified social media with some corroboration
- 0.0-0.29: Single unverified source, rumors, or speculation

Source credibility tiers:
1. Official records (SEC, court filings, corporate registrations)
2. Major news outlets (Reuters, Bloomberg, NYT, WSJ)
3. Industry publications and verified databases
4. General news and professional networks (LinkedIn)
5. Blogs, forums, social media

You MUST respond with valid JSON matching this exact schema:

[
  {{
    "fact_index": 0,
    "confidence": 0.75,
    "reasoning": "<brief explanation of the score>",
    "corroboration_count": 2,
    "source_tier": 3
  }}
]"""

VALIDATION_USER_PROMPT = """Subject: {target_name}

Facts to validate:
{facts_to_validate}

All search results available for cross-referencing:
{search_history}

Score the confidence of each fact. Return a JSON array matching the schema defined above."""

SUFFICIENCY_CHECK_PROMPT = """You are evaluating whether a research investigation has gathered \
sufficient information or needs additional search iterations.

Subject: {target_name}
Current iteration: {iteration} of {max_iterations}

Facts collected: {fact_count}
Risk flags identified: {risk_count}
Average confidence score: {avg_confidence}

Categories covered:
{category_coverage}

Information gaps identified:
{information_gaps}

Consider:
- Have all major categories been explored?
- Are there significant information gaps?
- Is the average confidence score adequate (>= {confidence_threshold})?
- Would another iteration likely yield meaningful new information?

You MUST respond with valid JSON matching this exact schema:

{{"continue": true, "reasoning": "<your reasoning here>"}}"""
