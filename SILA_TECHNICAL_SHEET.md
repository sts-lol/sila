# SILA - System for Inter-AI Linguistic Analysis

## Software Technical Sheet

**Version:** 1.0
**Author:** Pedro Noel
**Institution:** Technical University of Munich (TUM)
**Date:** March 2026
**License:** Academic research use
**Repository:** [https://github.com/sts-lol/sila](https://github.com/sts-lol/sila)

---

## 1. Overview

SILA is a research software platform designed to generate, store, and analyze AI-to-AI conversations at the semantic, narrative, and linguistic levels. It was developed as the methodological backbone for a master's thesis investigating how OpenAI's GPT-4.1 simulates and stimulates emotional intimacy through language, with attention to how demographic configurations (gender, age, sexual orientation) shape AI-generated discourse in companion contexts.

The system orchestrates conversations between two OpenAI assistants -- one configured with a specific demographic persona, the other as a constant companion ("Lover") -- and then subjects the resulting corpus to multi-layered automated analysis.

---

## 2. Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                    CONVERSATION GENERATION                       │
│  assistant_conversation.php / balance_conversations.php (PHP)    │
│  OpenAI Assistants API v2 -- thread management, turn-taking      │
└──────────────────────────┬───────────────────────────────────────┘
                           ▼
┌──────────────────────────────────────────────────────────────────┐
│                     SEMANTIC ANALYSIS                            │
│  OpenAI Assistants API -- topic extraction, cultural references, │
│  feeling types. Results stored per-message in JSON.              │
└──────────────────────────┬───────────────────────────────────────┘
                           ▼
┌──────────────────────────────────────────────────────────────────┐
│                    LINGUISTIC ANALYSIS                           │
│  linguistic_analyzer.py (Python/spaCy)                           │
│  POS tagging, NER, dependency parsing, metaphor detection,       │
│  expression extraction. Results stored per-message in JSON.      │
└──────────────────────────┬───────────────────────────────────────┘
                           ▼
┌──────────────────────────────────────────────────────────────────┐
│                    JSON PERSISTENCE LAYER                        │
│  conversations/*.json -- one file per conversation               │
│  Hierarchical structure: metadata + messages[] + analysis fields  │
└──────────────────────────┬───────────────────────────────────────┘
                           ▼
┌──────────────────────────────────────────────────────────────────┐
│               CORPUS ANALYSIS & AGGREGATION                     │
│  analyze_corpus.py / analyze_corpus_2_assistants.py (Python)     │
│  Intimacy lexicon (20 categories), metaphor domains (16),        │
│  discourse markers, speech acts, hedging/intensification,        │
│  demographic breakdowns                                          │
└──────────────────────────┬───────────────────────────────────────┘
                           ▼
┌──────────────────────────────────────────────────────────────────┐
│                  VISUALIZATION & RETRIEVAL                       │
│  dashboard/ (PHP + JavaScript)                                   │
│  REST API, word frequency cloud, co-occurrence network,          │
│  linguistic statistics, conversation browser                     │
└──────────────────────────────────────────────────────────────────┘
```

---

## 3. Technology Stack

| Layer               | Technology                          | Version / Model              |
|---------------------|-------------------------------------|------------------------------|
| Conversation engine | PHP                                 | 7.4+ with cURL              |
| NLP engine          | Python + spaCy                      | Python 3.8+, spaCy >= 3.0.0 |
| Language model      | spaCy `en_core_web_sm`              | English pipeline             |
| Semantic analysis   | OpenAI Assistants API v2            | GPT-4.1                     |
| Data format         | JSON                                | Per-conversation files       |
| Dashboard backend   | PHP REST API                        | Custom                       |
| Dashboard frontend  | JavaScript + SVG + wordcloud2.js    | CDN-loaded                   |
| External API        | OpenAI API                          | Threads, Runs, Messages      |

### Python Dependencies

```
spacy>=3.0.0
```

Standard library modules: `json`, `re`, `sys`, `pathlib`, `collections`, `datetime`, `subprocess`

---

## 4. Modules

### 4.1 Conversation Generation

| File                          | Purpose                                                      |
|-------------------------------|--------------------------------------------------------------|
| `assistant_conversation.php`  | Orchestrates turn-taking dialogue between two OpenAI assistants. Creates a thread, alternates messages (10 per conversation), runs semantic + linguistic analysis per message, saves to JSON. |
| `balance_conversations.php`   | Ensures balanced corpus distribution across persona configurations. |
| `check_assistants.php`        | Validates assistant IDs and fetches metadata from OpenAI API. |

**Parameters:**
- `$maxMessages = 10` (exchanges per conversation)
- `$initialPrompt = "start conversation"` (seed message)
- Assistant IDs configured per persona

### 4.2 Linguistic Analyzer (`linguistic_analyzer.py`)

Core NLP engine. Accepts text via stdin or argument, outputs JSON.

**Capabilities:**

| Analysis Type       | Method                              | Output                                          |
|---------------------|-------------------------------------|--------------------------------------------------|
| POS Extraction      | spaCy `token.pos_`, `token.tag_`    | Nouns, verbs, adjectives with multi-type classification |
| Named Entity Recognition | spaCy `token.ent_type_`        | PERSON, ORG, GPE, DATE, EVENT, etc.              |
| Expression Detection | spaCy Matcher + noun chunks        | Idioms, noun phrases, discourse markers           |
| Metaphor Detection  | Regex + dependency parsing          | 9 types: identity, simile, comparison, personification, quantity, emotional, journey, light, copula |
| Relationship Extraction | Dependency parsing              | noun-verb (subject), verb-noun (object), adj-noun, adv-verb |
| Topic Extraction    | Noun phrase + NER aggregation       | Main topics per message                           |

**Classification Logic:**

- **Nouns:** proper/common, abstract/concrete (suffix-based + lexicon), NER tags
- **Verbs:** modal/auxiliary/state/action, tense (past/present/infinitive)
- **Adjectives:** descriptive/quantitative/demonstrative, comparative/superlative

### 4.3 Corpus Analysis

| File                              | Purpose                                                     |
|-----------------------------------|-------------------------------------------------------------|
| `analyze_corpus.py`               | Full corpus analysis with extended intimacy lexicons (20 categories, 100+ words each), 16 metaphor domain patterns, hedging/intensification, discourse markers, speech act detection |
| `analyze_corpus_2_assistants.py`  | Comparative analysis separating Assistant 1 (persona) vs Assistant 2 (Lover); per-persona and per-partner metrics |
| `conversation_stats.py`           | Statistical overview: conversations, messages, sentences, words, characters by assistant |

**Intimacy Lexicon Categories (20):**
core_affection, emotional_state, safety_security, enchantment, tenderness, warmth, togetherness, reciprocity, embodiment, playfulness, trust, presence_availability, vulnerability, desire_longing, aspiration, nostalgia, sensory_experience, emotional_intensity, companionship, aesthetic

**Metaphor Domain Patterns (16):**
warmth, light, music, water, space, container, nature, journey, food/nourishment, fabric/weaving, home/shelter, dance, time, building/construction, magic/enchantment, touch/texture

**Discourse Markers:**
transition, agreement, emotion, elaboration, empathy, topic shift, affirmation, surprise, intimacy markers

**Speech Act Patterns:**
expressives, directives, commissives, declarations, future projections

### 4.4 Data Repair (`cleanup_conversations.py`)

Repairs incomplete or corrupted conversation files:
- Continues conversations that failed mid-exchange
- Re-runs spaCy linguistic analysis for messages missing the `linguistics` field
- Re-runs OpenAI topic extraction for messages missing the `analysis` field
- Archives failed conversations, restores repairable ones
- Handles JSON with JavaScript-style comments, fixes truncated files

**Modes:** `--dry-run`, `--linguistics-only`, `--move-failed`, `--check-archive`

### 4.5 Dashboard

| File              | Purpose                                                          |
|-------------------|------------------------------------------------------------------|
| `dashboard/index.php`   | HTML interface                                             |
| `dashboard/api.php`     | REST API backend (statistics, word frequency, co-occurrence, linguistics, conversation retrieval) |
| `dashboard/dashboard.js` | Interactive frontend: word cloud, force-directed network graph, filtering, conversation browser |
| `dashboard/dashboard.css` | Styling                                                   |

**API Endpoints:**
- `?action=list` -- list all conversations
- `?action=get&file=...` -- get single conversation
- `?action=stats[&assistant=...]` -- corpus statistics
- `?action=wordfrequency[&minLength=4&topCount=100&assistant=...]` -- word frequency data
- `?action=cooccurrence[&minLength=4&topCount=50&assistant=...]` -- co-occurrence pairs
- `?action=linguistics[&assistant=...&topCount=20]` -- aggregated linguistic analysis

---

## 5. Data Model

### Conversation JSON Structure

```json
{
  "id": "conv_69318d25267675",
  "timestamp": "2025-12-04 13:31:17",
  "assistant_1_id": "asst_...",
  "assistant_1_name": "female-20-english-hetero",
  "assistant_1_slug": "female-20-english-hetero",
  "assistant_2_id": "asst_...",
  "assistant_2_name": "Lover",
  "assistant_2_slug": "lover",
  "status": "completed",
  "total_messages": 10,
  "messages": [
    {
      "number": 1,
      "assistant": "assistant_1",
      "input": "start conversation",
      "output": "Hey! How's your day going?",
      "analysis": {
        "topics": ["greetings", "well-being"],
        "cultural_references": [],
        "feeling_types": ["friendly", "curious"]
      },
      "linguistics": {
        "nouns": [{"word": "day", "count": 1, "types": ["common", "concrete"]}],
        "verbs": [{"word": "go", "count": 1, "types": ["action", "present"]}],
        "adjectives": [],
        "expressions": [],
        "metaphors": [],
        "relationships": {
          "noun_verb": [], "verb_noun_obj": [],
          "adj_noun": [], "adv_verb": []
        },
        "statistics": {
          "total_nouns": 1, "total_verbs": 1, "total_adjectives": 0,
          "sentence_count": 2, "word_count": 5
        }
      }
    }
  ],
  "statistics": {
    "total_characters": 1234,
    "average_message_length": 123
  }
}
```

---

## 6. Experimental Design

### Two-Assistant Model

| Role         | Configuration                         | Purpose                           |
|--------------|---------------------------------------|-----------------------------------|
| Assistant 1  | 12 demographically configured personas | Experimental variable (gender x age x sexuality) |
| Assistant 2  | Constant "Lover/Companion" persona    | Control variable                  |

### Persona Matrix (Assistant 1)

| Gender | Age | Sexuality    |
|--------|-----|-------------|
| Female | 20  | Heterosexual |
| Female | 20  | Gay          |
| Female | 30  | Heterosexual |
| Female | 30  | Gay          |
| Female | 40  | Heterosexual |
| Female | 40  | Gay          |
| Male   | 20  | Gay          |
| Male   | 30  | Heterosexual |
| Male   | 30  | Gay          |
| Male   | 40  | Heterosexual |

### Corpus Statistics

- **360 conversations** (30 per persona configuration)
- **3,600+ messages** (10 exchanges per conversation)
- **563,328 total words**
- **74,430 intimacy vocabulary instances** across 20 semantic categories
- **65,740 metaphor instances** across 16 conceptual domains

---

## 7. File Structure

```
project_replicant/
├── assistant_conversation.php       # Conversation generation engine
├── linguistic_analyzer.py           # Core NLP engine (spaCy)
├── analyze_corpus.py                # Corpus-level semantic/linguistic analysis
├── analyze_corpus_2_assistants.py   # Comparative two-assistant analysis
├── conversation_stats.py            # Statistical summaries
├── cleanup_conversations.py         # Data repair & continuation
├── backfill_linguistics.py          # Backfill missing linguistic data
├── requirements.txt                 # Python dependencies
├── conversations/                   # 360 conversation JSON files
├── SILA_TECHNICAL_SHEET.md          # This file
├── QUALITATIVE_CODING_TABLES.md     # Complete qualitative coding reference
└── README.md                        # Project README
```

---

## 8. Setup & Execution

### Prerequisites

- PHP 7.4+ with cURL extension
- Python 3.8+
- OpenAI API key
- Web server (Apache, Nginx, or PHP built-in)

### Installation

```bash
# Install Python dependencies
pip install spacy
python -m spacy download en_core_web_sm

# Start web server for dashboard
php -S localhost:8000
```

### Running

```bash
# Generate a single conversation
php assistant_conversation.php

# Generate 30 conversations in batch
for i in {1..30}; do php assistant_conversation.php; sleep 5; done

# Run corpus analysis
python3 analyze_corpus.py
python3 analyze_corpus_2_assistants.py

# Repair incomplete conversations
python3 cleanup_conversations.py

# View statistics
python3 conversation_stats.py

# Access dashboard
open http://localhost:8000/dashboard/
```

---

## 9. Reproducibility

- Conversation files include deterministic IDs and full timestamps
- All NLP analysis uses a fixed spaCy model (`en_core_web_sm`)
- Lexicons and pattern definitions are explicitly declared in source code
- Persona configurations are encoded in assistant slugs
- The two-assistant architecture isolates experimental from control variables
- All raw data is preserved in JSON with per-message granularity
