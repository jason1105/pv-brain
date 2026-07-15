# Niche Research Prompts

## Niche Discovery

- **Purpose:** pick a niche worth building a channel in.
- **Inputs:** `{{interests}}`, `{{constraints}}` (time, budget, skills).
- **Output:** ranked niche candidates with rationale.

```text
I want to build an automated, faceless YouTube channel.
My interests: {{interests}}
My constraints: {{constraints}}

Analyze and give me:
- Top 5 niches with the highest realistic CPM rates
- Which niche best fits my interests and constraints
- Competitor gap analysis for each niche
- Realistic income potential at 1K / 10K / 100K subscribers
- Which niche can be started today with zero budget

Rank by: easiest to monetize fastest. Return structured results.
```

## Competitor Breakdown

- **Purpose:** map the competitive landscape of a chosen niche.
- **Inputs:** `{{niche}}`.
- **Output:** competitor analysis + 10 differentiated video ideas.

```text
Analyze top YouTube channels in {{niche}}.

Give me:
- Top 5 fastest growing channels
- What type of videos drive their growth
- Their average views vs subscribers ratio
- Content gaps they are not covering
- Weaknesses in their thumbnails or titles
- What a new channel can do better immediately

Then give me 10 video ideas designed to outperform them.
```
