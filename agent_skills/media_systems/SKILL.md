# SKILL: Media Systems & Information Ecosystems
`agent_skills/media_systems/SKILL.md`

## 1. Purpose & Domain Scope
Guides the architecture, implementation, and evaluation of fictional and simulated media ecosystems within SALTBOR: radio stations, newspapers, television broadcasts, digital press, community megaphones, podcasts, and sports commentary.

## 2. When to Use
- Implementing media broadcasts, press agencies, or journalistic editorial desks.
- Designing information diffusion, broadcast ranges, and receptor tuning.
- Connecting external environmental or economic crises to synthetic news reports.
- Evaluating media credibility, bias, and audience reach.

## 3. Workflows & Procedures
1. **Source Fact Ingestion**: Ingest ground-truth events from `EnvironmentEngine`, `ConflictEngine`, or `TerritorialEconomyEngine`.
2. **Editorial Processing**: Synthesize news items with editorial stance, urgency, and credibility index $C \in [0, 1]$.
3. **Broadcasting & Reception**: Transmit over spatial frequency/reach; agents receive broadcasts based on device possession (e.g. transistor radio, smartphone) and schedule.
4. **Cognitive Ingestion**: Broadcast triggers `SyntheticHuman` appraisal, belief updates, and social discussion.

## 4. Technical References & Repositories
- *Agenda Setting Theory* (McCombs & Shaw, 1972).
- *Two-Step Flow of Communication* (Katz & Lazarsfeld, 1955).
- Reference Repositories: NetLogo Media Diffusion models; Mesa Information Dynamics.

## 5. Validation Criteria
- Fictional content is unambiguously tagged as simulated (`is_fictional=True`).
- Broadcast does not alter agent beliefs uniformly; acceptance depends on individual trust and cognitive appraisal.
- News generation produces zero memory leaks and runs under 0.1 ms per broadcast.
