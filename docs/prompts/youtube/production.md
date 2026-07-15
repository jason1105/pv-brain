# Production Prompts

## Faceless Video Concept

- **Purpose:** turn a topic into a complete production brief.
- **Inputs:** `{{niche}}`, `{{audience}}`, `{{topic}}`.
- **Output:** production brief (title, script direction, assets, thumbnail).

```text
Create a complete faceless YouTube video concept for a {{niche}} channel
targeting {{audience}}, on the topic: {{topic}}.

Include:
- SEO-optimized video title
- Full script outline (no camera needed)
- Voiceover instructions (tone, pace)
- Stock footage keywords to search
- Background music mood
- Thumbnail concept (text + color + emotion)
- Monetization angle beyond AdSense
```

## High-Retention Script

- **Purpose:** write the full narration script for a video.
- **Inputs:** `{{topic}}`, `{{target_minutes}}`, `{{audience}}`.
- **Output:** timed script with retention devices marked.

```text
Write a HIGH-RETENTION YouTube narration script about {{topic}} for
{{audience}}, targeting {{target_minutes}} minutes.

The script must:
- Hook the viewer in the first 3 seconds
- Use open loops to keep curiosity high
- Add pattern interrupts every 10-15 seconds
- Use storytelling and suspense
- Include re-engagement lines where drop-off is likely
- End with a strong but natural call to action

Mark likely drop-off points and how the script counters them.
Structure the output into titled sections with narration text.
```
