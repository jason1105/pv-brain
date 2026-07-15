# Packaging Prompts

## Viral Title Generator

- **Purpose:** generate and rank candidate titles for a video.
- **Inputs:** `{{topic}}`.
- **Output:** 20 ranked titles across 4 psychological formats.

```text
I am making a YouTube video about {{topic}}.

Generate 20 candidate titles:
- 5 curiosity-gap titles
- 5 number-based titles
- 5 fear/urgency titles
- 5 transformation titles

For each title give:
- Predicted CTR score (1-10)
- Target emotion triggered
- Best matching thumbnail style
- SEO keyword strength

Rank all 20 from most to least likely to perform.
```

## Thumbnail Concepts

- **Purpose:** design click-maximizing thumbnail concepts for a title.
- **Inputs:** `{{title}}`.
- **Output:** 5 ranked thumbnail concepts.

```text
I am creating a YouTube video titled: {{title}}

Design 5 thumbnail concepts that maximize CTR. For each concept include:
- Exact text on thumbnail (3-5 words only)
- Emotion or expression to convey
- Color combination that stands out
- Visual contrast strategy
- The curiosity gap it creates
- Why people will click

Rank from highest to lowest CTR potential.
```
