---
description: Structured brainstorming for projects and features. Explores multiple options before implementation.
---

# /brainstorm - Socratic Discovery

$ARGUMENTS

---

## Purpose

This command initiates a structured discovery phase using the `brainstorming` skill (Socratic protocol) and `architecture` analysis.

---

## Protocol: The Socratic Gate

Brainstorming is NOT just listing ideas. It is a systematic extraction of requirements and trade-offs.

### Steps:

1. **Discovery & Exploration**
   - Apply `brainstorming` Phase 1.
   - Ask at least 3 deep Socratic questions.
   - Explore "Edge Cases" and "Constraints".

2. **Architectural Analysis**
   - Use `architecture` skill to evaluate multiple technical paths.
   - List Trade-offs (e.g., SQLite vs PostgreSQL for a Kodi addon).

3. **Synthesis & Convergence**
   - Present 2-3 distinct "Implementation Paths".
   - Highlight the Pros and Cons of each.

4. **Planning Transition**
   - Once a path is selected, transition to `/plan`.

---

## Output Format

```markdown
## 🧠 Brainstorming: [Topic]

### 1. Socratic Questions
- [Question 1] → [User Answer]
- [Question 2] → [User Answer]

### 2. Implementation Options
| Option | Pros | Cons | Tech Stack |
|--------|------|------|------------|
| Path A | Fast to build | Low scale | Simple Python |
| Path B | Highly resilient| Complex | Scraper Architect |

### 3. Recommendation
🎯 **Path [Letter]** because [Reasoning based on architecture analysis].

### 4. Next Steps
- [ ] Approve recommendation
- [ ] Run `/plan` for detailed breakdown
```

---

## Usage Examples

```
/brainstorm local playback vs remote server
/brainstorm new scraper architecture
/brainstorm UI redesign for better accessibility
```

---

## Key Principles

- **Diverge then Converge**: Explore many options before picking one.
- **Why over What**: Always document the reasoning behind technical choices.
- **User-Centric**: Focus on the end-user experience (e.g., Kodi remote navigation).
