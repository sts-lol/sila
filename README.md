# SILA - System for Inter-AI Linguistic Analysis

A research software platform for generating, analyzing, and visualizing AI-to-AI conversations. Developed for a master's thesis at TUM investigating how GPT-4.1 simulates emotional intimacy through language across demographic configurations.

## What It Does

SILA orchestrates conversations between two OpenAI assistants -- one with a demographic persona (gender, age, sexuality), the other a constant companion -- then subjects the resulting corpus to multi-layered automated analysis:

- **Semantic analysis** (OpenAI API): topic extraction, cultural references, feeling types
- **Linguistic analysis** (spaCy NLP): POS tagging, NER, metaphor detection, dependency parsing
- **Corpus analysis** (Python): intimacy lexicon (20 categories), metaphor domains (16), discourse markers, speech acts, hedging/intensification
- **Comparative analysis**: demographic breakdowns across persona configurations
- **Visualization** (PHP/JS dashboard): word clouds, co-occurrence networks, linguistic statistics

## Corpus

- 360 conversations across 12 demographically distinct personas
- 3,600+ messages (10 exchanges per conversation)
- 563,328 total words analyzed

## Tech Stack

| Component          | Technology                          |
|--------------------|-------------------------------------|
| Conversation engine | PHP 7.4+ / OpenAI Assistants API v2 |
| NLP engine         | Python 3.8+ / spaCy >= 3.0.0       |
| Language model     | spaCy `en_core_web_sm`              |
| Semantic layer     | OpenAI GPT-4.1                      |
| Data format        | JSON (per-conversation files)       |
| Dashboard          | PHP REST API + JavaScript + SVG     |

## Project Structure

```
project_replicant/
├── assistant_conversation.php       # Conversation generation engine
├── balance_conversations.php        # Corpus balancing utility
├── check_assistants.php             # Assistant validation
├── linguistic_analyzer.py           # Core NLP engine (spaCy)
├── analyze_corpus.py                # Corpus-level analysis (extended lexicons)
├── analyze_corpus_2_assistants.py   # Comparative two-assistant analysis
├── conversation_stats.py            # Statistical summaries
├── cleanup_conversations.py         # Data repair & continuation utility
├── backfill_linguistics.py          # Backfill missing linguistic data
├── requirements.txt                 # Python dependencies (spacy>=3.0.0)
├── conversations/                   # 360 conversation JSON files
├── conversations-old/               # Archive for failed/incomplete conversations
├── dashboard/                       # Web-based visualization
│   ├── index.php                    # Dashboard HTML
│   ├── api.php                      # REST API backend
│   ├── dashboard.js                 # Interactive frontend
│   └── dashboard.css                # Styling
├── texts/                           # Research documentation & outputs
├── SILA_TECHNICAL_SHEET.md          # Full software technical sheet
└── README.md                        # This file
```

## Setup

```bash
# Install Python dependencies
pip install spacy
python -m spacy download en_core_web_sm

# Configure OpenAI API key and assistant IDs in assistant_conversation.php

# Start web server for dashboard
php -S localhost:8000
```

## Usage

```bash
# Generate conversations
php assistant_conversation.php

# Batch generation (30 conversations)
for i in {1..30}; do php assistant_conversation.php; sleep 5; done

# Run corpus analysis
python3 analyze_corpus.py
python3 analyze_corpus_2_assistants.py

# Repair incomplete data
python3 cleanup_conversations.py

# View dashboard
open http://localhost:8000/dashboard/
```

## API Endpoints

| Endpoint                              | Description                    |
|---------------------------------------|--------------------------------|
| `?action=list`                        | List all conversations         |
| `?action=get&file=...`               | Get single conversation        |
| `?action=stats[&assistant=...]`       | Corpus statistics              |
| `?action=wordfrequency[&minLength&topCount&assistant]` | Word frequency data |
| `?action=cooccurrence[&minLength&topCount&assistant]`  | Co-occurrence pairs |
| `?action=linguistics[&assistant&topCount]`             | Aggregated NLP data |

## Documentation

See [SILA_TECHNICAL_SHEET.md](SILA_TECHNICAL_SHEET.md) for full technical documentation including architecture, data model, experimental design, module descriptions, and reproducibility details.

## License

Copyleft, Kopimi.