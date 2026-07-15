# YouTube 12-Prompt Playbook (X thread)

- **Date collected:** 2026-07-15
- **Source:** X thread by [@suryanshti777](https://x.com/suryanshti777/status/2048074833263738922) (12 prompts + 1 bonus)
- **Status:** external source material, preserved verbatim in condensed form

## Why this matters to pv-brain

The thread is a manual playbook for running an AI-assisted faceless YouTube
channel. Each prompt is one step a human copy-pastes into an LLM. pv-brain's
thesis (workflow first, cloud first) turns exactly this kind of playbook into
an automated pipeline: the prompts become workflow steps, the human becomes a
supervisor. This thread therefore serves as seed material for the
[auto video generation software spec](../specs/).

Mapping to our pipeline stages:

| # | Prompt | Pipeline stage |
|---|--------|----------------|
| 1 | Find Your Money Niche | Niche research |
| 2 | Faceless Video System | Video concept / production brief |
| 3 | Viral Title Machine | Packaging (titles) |
| 4 | AI Automation Workflow | Meta: the automation system itself |
| 5 | Multiple Income Streams | Monetization strategy |
| 6 | Algorithm Hack System | Distribution strategy |
| 7 | 90-Day Money Map | Channel roadmap |
| 8 | Retention Killer Script | Scriptwriting |
| 9 | Thumbnail Psychology | Packaging (thumbnails) |
| 10 | Shorts Growth Engine | Distribution (Shorts) |
| 11 | Competitor Breakdown | Niche research (competitors) |
| 12 | First 10 Videos Blueprint | Channel bootstrap |
| B | Content Calendar Generator | Scheduling |

## Source material (condensed)

### 1/ Find Your Money Niche

> I am [AGE] years old with interest in [TOPICS]. I want to make money on
> YouTube with AI. Analyze and give me: top 5 niches with highest CPM rates;
> which niche fits my age & interests; competitor gap analysis for each
> niche; realistic income potential at 1K/10K/100K subs; which niche can I
> start TODAY with zero budget. Rank by: easiest to monetize fastest.

### 2/ Faceless Video System

> Create a complete faceless YouTube video concept for [NICHE] channel
> targeting [AUDIENCE]. Include: video title (SEO optimized); full script
> (no camera needed); voiceover instructions; stock footage keywords to
> search; background music mood; thumbnail concept (text + color + emotion);
> estimated CPM for this video topic; monetization angle beyond AdSense.

### 3/ Viral Title Machine

> I make YouTube videos about [TOPIC]. Generate 20 titles that will go
> viral: 5 curiosity-gap, 5 number-based, 5 fear/urgency, 5 transformation.
> For each title give: predicted CTR score (1-10); target emotion triggered;
> best thumbnail style to match; SEO keyword strength. Rank all 20 from most
> to least viral.

### 4/ AI Automation Workflow

> Design a complete YouTube automation system for a [NICHE] channel with $0
> budget. Map out: free AI tools for each production step; script →
> voiceover → edit → thumbnail workflow; time required per video (target
> under 2 hours); batch production system for 1 month of content; upload
> schedule for maximum algorithm boost; how to run 3 channels
> simultaneously; when to reinvest first earnings into paid tools.

### 5/ Multiple Income Streams

> I have a YouTube channel about [NICHE] with [X] subscribers and [X]
> monthly views. Build me a complete income blueprint: AdSense revenue
> estimate; top 10 affiliate programs for my niche; digital product ideas;
> sponsorship rate card for my channel size; merchandise potential; paid
> community model; course or coaching opportunity. Show total realistic
> monthly income at 1K / 5K / 10K / 50K subscribers.

### 6/ Algorithm Hack System

> Analyze YouTube's current algorithm for [NICHE]. Tell me exactly: ideal
> video length for maximum watch time; best upload frequency; tags strategy;
> thumbnail A/B testing approach; how to trigger the suggested video
> algorithm; community post strategy; Shorts strategy to feed main channel
> growth; first 24-hour post strategy. Give me a weekly checklist.

### 7/ 90-Day Money Map

> I am [AGE] starting a YouTube channel about [NICHE] with $[BUDGET] and [X]
> hours/week. Build my complete 90-day money roadmap (weeks 1-2 setup, weeks
> 3-4 growth, month 2 monetization prep, month 3 first income milestone).
> Include: daily action checklist; weekly subscriber targets; first
> monetization date estimate; $100/$500/$1000 milestones; what to do when
> growth stalls; biggest mistakes to avoid.

### 8/ Retention Killer Script

> I want to create a HIGH-RETENTION YouTube video about [TOPIC]. Write a
> script that: hooks the viewer in first 3 seconds; uses open loops; adds
> pattern interrupts every 10–15 seconds; uses storytelling + suspense;
> includes re-engagement lines where drop-off is likely; ends with a natural
> CTA. Also mark where viewers are most likely to drop off and how to fix it.

### 9/ Thumbnail Psychology

> I am creating a YouTube video titled: [TITLE]. Design 5 thumbnail concepts
> that maximize CTR. For each: exact text (3–5 words); facial expression or
> emotion; color combination; visual contrast strategy; curiosity gap
> explanation; why people will click. Rank by CTR potential.

### 10/ Shorts Growth Engine

> I want to use Shorts to grow my YouTube channel in [NICHE]. Create a
> Shorts strategy that: generates 30 viral Shorts ideas; uses proven hook
> formats; converts Shorts viewers into long-form subscribers; includes
> posting frequency; best video length; loop strategy; CTA that drives
> profile clicks. Also give 5 Shorts scripts I can post today.

### 11/ Competitor Breakdown

> Analyze top YouTube channels in [NICHE]. Give me: top 5 fastest growing
> channels; what videos drive their growth; average views vs subscribers
> ratio; content gaps they are not covering; weaknesses in their thumbnails
> or titles; what I can do better immediately. Then give me 10 video ideas
> to outperform them.

### 12/ First 10 Videos Blueprint

> I am starting a new YouTube channel in [NICHE]. Give me my first 10
> videos: titles optimized for clicks; why each will perform; suggested
> thumbnail angle; target audience intent; expected views range. Arrange in
> the order I should post them for fastest growth.

### BONUS/ Content Calendar Generator

> Create a 30-day YouTube content calendar for [NICHE]. Include: daily video
> ideas; content mix (educational, viral, trending); best posting days;
> which videos are for growth vs monetization; trending angles. Make it
> balanced for both views and revenue.

## Assessment

- The playbook is marketing-flavored (income claims are unverified hype),
  but its **structure** is sound: it decomposes channel operation into
  research → strategy → production → packaging → distribution → monetization.
- Prompts 2, 3, 8, 9 are directly automatable as pipeline steps today.
- Prompts 1, 5, 6, 7, 11, 12, BONUS are strategy-level: they run once per
  channel (or periodically), not once per video.
- Prompt 4 describes the automation system itself — which is what pv-brain
  is building; we replace "free AI tools glued by a human" with one runtime.
- Distilled, variable-normalized versions live in
  [`../prompts/youtube/`](../prompts/youtube/).
