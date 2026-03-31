#!/usr/bin/env python3
"""
Linguistic Analyzer for Project Replicant
Uses spaCy for NLP analysis including:
- Nouns (with types: common, proper, abstract, concrete)
- Verbs (with types: action, state, modal, auxiliary)
- Adjectives (with types: descriptive, quantitative, demonstrative)
- Expressions (idioms, phrases, collocations)
- Topics (key noun phrases)
- Metaphors and analogies (pattern-based detection)
"""

import sys
import json
import re
from collections import Counter

try:
    import spacy
    from spacy.matcher import Matcher
except ImportError:
    print(json.dumps({
        "error": "spaCy not installed. Run: pip install spacy && python -m spacy download en_core_web_sm"
    }))
    sys.exit(1)

# Load spaCy model
try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    print(json.dumps({
        "error": "spaCy English model not found. Run: python -m spacy download en_core_web_sm"
    }))
    sys.exit(1)

# Abstract noun indicators (common suffixes and words)
ABSTRACT_SUFFIXES = ('tion', 'sion', 'ness', 'ment', 'ity', 'ance', 'ence', 'dom', 'ship', 'hood', 'ism')
ABSTRACT_NOUNS = {
    'love', 'hate', 'fear', 'joy', 'anger', 'happiness', 'sadness', 'peace', 'hope', 'faith',
    'trust', 'freedom', 'beauty', 'truth', 'wisdom', 'knowledge', 'time', 'life', 'death',
    'dream', 'memory', 'thought', 'idea', 'feeling', 'emotion', 'soul', 'spirit', 'mind',
    'heart', 'courage', 'strength', 'power', 'energy', 'magic', 'wonder', 'comfort', 'warmth'
}

# State verbs (non-action verbs)
STATE_VERBS = {
    'be', 'am', 'is', 'are', 'was', 'were', 'been', 'being',
    'have', 'has', 'had', 'seem', 'appear', 'look', 'feel', 'sound', 'taste', 'smell',
    'know', 'believe', 'think', 'understand', 'remember', 'forget', 'recognize',
    'love', 'like', 'hate', 'want', 'need', 'prefer', 'wish', 'desire',
    'own', 'possess', 'belong', 'contain', 'consist', 'include',
    'exist', 'matter', 'mean', 'deserve', 'fit', 'suit', 'resemble'
}

# Modal verbs
MODAL_VERBS = {'can', 'could', 'may', 'might', 'must', 'shall', 'should', 'will', 'would', 'ought'}

# Auxiliary verbs
AUXILIARY_VERBS = {'be', 'am', 'is', 'are', 'was', 'were', 'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did'}

# Quantitative adjectives
QUANTITATIVE_ADJECTIVES = {
    'many', 'much', 'few', 'little', 'some', 'any', 'several', 'all', 'most', 'more',
    'less', 'enough', 'no', 'every', 'each', 'whole', 'half', 'both', 'either', 'neither',
    'first', 'second', 'third', 'last', 'next', 'other', 'another', 'one', 'two', 'three'
}

# Demonstrative adjectives
DEMONSTRATIVE_ADJECTIVES = {'this', 'that', 'these', 'those', 'such', 'same', 'certain'}

# Common expressions/idioms patterns
EXPRESSION_PATTERNS = [
    # Similes
    [{"LOWER": "as"}, {"POS": "ADJ"}, {"LOWER": "as"}],
    [{"LOWER": "like"}, {"POS": "DET", "OP": "?"}, {"POS": "NOUN"}],

    # Common phrases
    [{"LOWER": "kind"}, {"LOWER": "of"}],
    [{"LOWER": "sort"}, {"LOWER": "of"}],
    [{"LOWER": "a"}, {"LOWER": "lot"}, {"LOWER": "of"}],
    [{"LOWER": "in"}, {"LOWER": "terms"}, {"LOWER": "of"}],
    [{"LOWER": "at"}, {"LOWER": "the"}, {"LOWER": "end"}, {"LOWER": "of"}],
    [{"LOWER": "on"}, {"LOWER": "top"}, {"LOWER": "of"}],

    # Emotional expressions
    [{"LOWER": "i"}, {"LOWER": "feel"}, {"LOWER": "like"}],
    [{"LOWER": "it"}, {"LOWER": "feels"}, {"LOWER": "like"}],
    [{"LOWER": "makes"}, {"POS": "PRON", "OP": "?"}, {"LOWER": "feel"}],
]

# Metaphor patterns
METAPHOR_PATTERNS = [
    # "X is Y" pattern (noun is noun, where they're different categories)
    [{"POS": "NOUN"}, {"LEMMA": "be"}, {"POS": "DET", "OP": "?"}, {"POS": "ADJ", "OP": "?"}, {"POS": "NOUN"}],

    # "X is like Y" simile
    [{"POS": "NOUN"}, {"LEMMA": "be"}, {"LOWER": "like"}, {"POS": "DET", "OP": "?"}, {"POS": "NOUN"}],

    # "as X as Y" pattern
    [{"LOWER": "as"}, {"POS": "ADJ"}, {"LOWER": "as"}, {"POS": "DET", "OP": "?"}, {"POS": "NOUN"}],

    # "like a/an X" pattern
    [{"LOWER": "like"}, {"POS": "DET"}, {"POS": "ADJ", "OP": "?"}, {"POS": "NOUN"}],

    # Verb-based metaphors "swimming in", "drowning in", "burning with"
    [{"POS": "VERB"}, {"LOWER": {"IN": ["in", "with", "through", "into"]}}],
]

def classify_noun(token, lemma):
    """Classify a noun into types."""
    types = []

    # Proper noun
    if token.pos_ == "PROPN":
        types.append("proper")
    else:
        types.append("common")

    # Abstract vs concrete
    if (lemma in ABSTRACT_NOUNS or
        any(lemma.endswith(suffix) for suffix in ABSTRACT_SUFFIXES)):
        types.append("abstract")
    else:
        types.append("concrete")

    # Named entity type
    if token.ent_type_:
        types.append(token.ent_type_.lower())

    return types

def classify_verb(token, lemma):
    """Classify a verb into types."""
    types = []

    if lemma in MODAL_VERBS:
        types.append("modal")
    elif token.dep_ == "aux" or lemma in AUXILIARY_VERBS:
        types.append("auxiliary")
    elif lemma in STATE_VERBS:
        types.append("state")
    else:
        types.append("action")

    # Tense
    if token.tag_ in ("VBD", "VBN"):
        types.append("past")
    elif token.tag_ in ("VBZ", "VBP", "VBG"):
        types.append("present")
    elif token.tag_ == "VB":
        types.append("infinitive")

    return types

def classify_adjective(token, lemma):
    """Classify an adjective into types."""
    types = []

    if lemma in QUANTITATIVE_ADJECTIVES:
        types.append("quantitative")
    elif lemma in DEMONSTRATIVE_ADJECTIVES:
        types.append("demonstrative")
    else:
        types.append("descriptive")

    # Comparative/superlative
    if token.tag_ == "JJR":
        types.append("comparative")
    elif token.tag_ == "JJS":
        types.append("superlative")

    return types

def extract_expressions(doc, matcher):
    """Extract expressions and idioms from text."""
    expressions = []
    matches = matcher(doc)

    for match_id, start, end in matches:
        span = doc[start:end]
        expression_type = nlp.vocab.strings[match_id]
        expressions.append({
            "text": span.text,
            "type": expression_type
        })

    # Also extract common collocations (frequently co-occurring words)
    # Using noun chunks as expressions
    for chunk in doc.noun_chunks:
        if len(chunk) > 1:
            expressions.append({
                "text": chunk.text,
                "type": "noun_phrase"
            })

    return expressions

def extract_metaphors(doc, text):
    """Extract metaphors and analogies using pattern matching."""
    metaphors = []

    # Pattern-based detection
    patterns = [
        # "X is Y" metaphor pattern
        (r'\b(\w+)\s+(?:is|are|was|were)\s+(?:a|an|the)?\s*(\w+)\b', 'identity_metaphor'),
        # "like a X" simile
        (r'\blike\s+(?:a|an|the)?\s*(\w+(?:\s+\w+)?)\b', 'simile'),
        # "as X as Y" comparison
        (r'\bas\s+(\w+)\s+as\s+(?:a|an|the)?\s*(\w+)\b', 'comparison'),
        # Personification patterns
        (r'\b(?:the\s+)?(\w+)\s+(?:whispered|screamed|danced|sang|laughed|cried|smiled|frowned)\b', 'personification'),
        # "sea of X", "ocean of X", "mountain of X" etc.
        (r'\b(?:sea|ocean|mountain|river|flood|wave|storm)\s+of\s+(\w+)\b', 'quantity_metaphor'),
        # "X in my heart/soul/mind"
        (r'\b(\w+)\s+in\s+(?:my|your|the)\s+(?:heart|soul|mind|head)\b', 'emotional_metaphor'),
        # Journey/path metaphors
        (r'\b(?:journey|path|road|way)\s+(?:of|to|through)\s+(\w+)\b', 'journey_metaphor'),
        # Light/dark metaphors
        (r'\b(?:light|dark|bright|shadow|glow|shine)\s+(?:of|in)\s+(\w+)\b', 'light_metaphor'),
    ]

    for pattern, metaphor_type in patterns:
        matches = re.finditer(pattern, text, re.IGNORECASE)
        for match in matches:
            metaphors.append({
                "text": match.group(0),
                "type": metaphor_type
            })

    # Use spaCy's dependency parsing for more complex patterns
    for sent in doc.sents:
        # Look for "X is Y" where X and Y are different semantic categories
        for token in sent:
            if token.lemma_ == "be" and token.dep_ == "ROOT":
                subject = None
                complement = None
                for child in token.children:
                    if child.dep_ == "nsubj":
                        subject = child
                    elif child.dep_ == "attr":
                        complement = child

                if subject and complement:
                    # Check if they're semantically different (potential metaphor)
                    if (subject.pos_ == "NOUN" and complement.pos_ == "NOUN" and
                        subject.lemma_ != complement.lemma_):
                        metaphors.append({
                            "text": f"{subject.text} is {complement.text}",
                            "type": "copula_metaphor"
                        })

    # Deduplicate
    seen = set()
    unique_metaphors = []
    for m in metaphors:
        key = m["text"].lower()
        if key not in seen:
            seen.add(key)
            unique_metaphors.append(m)

    return unique_metaphors

def extract_topics(doc):
    """Extract main topics from text using noun phrases and entities."""
    topics = []

    # Collect noun chunks as potential topics
    chunk_counts = Counter()
    for chunk in doc.noun_chunks:
        # Filter out pronouns and very short chunks
        if chunk.root.pos_ != "PRON" and len(chunk.text) > 2:
            # Use the root noun of the chunk
            chunk_counts[chunk.root.lemma_] += 1

    # Collect named entities
    entity_counts = Counter()
    for ent in doc.ents:
        entity_counts[ent.text] += 1

    # Combine and rank topics
    for noun, count in chunk_counts.most_common(10):
        topics.append({
            "text": noun,
            "type": "noun_topic",
            "count": count
        })

    for entity, count in entity_counts.most_common(5):
        topics.append({
            "text": entity,
            "type": "entity_topic",
            "count": count
        })

    return topics


def extract_relationships(doc):
    """
    Extract cross-category relationships using dependency parsing:
    - Noun-Verb relationships (subject-verb, verb-object)
    - Adjective-Noun relationships (amod)
    - Adverb-Verb relationships (advmod)
    """
    relationships = {
        'noun_verb': [],      # e.g., "music" -> "play"
        'adj_noun': [],       # e.g., "beautiful" -> "moment"
        'adv_verb': [],       # e.g., "slowly" -> "walk"
        'verb_noun_obj': [],  # e.g., "feel" -> "emotion" (verb-object)
    }

    seen = {
        'noun_verb': set(),
        'adj_noun': set(),
        'adv_verb': set(),
        'verb_noun_obj': set(),
    }

    for token in doc:
        # Skip punctuation and short words
        if token.is_punct or token.is_space or len(token.lemma_) < 2:
            continue

        # Noun-Verb: Subject relationships (nsubj, nsubjpass)
        if token.dep_ in ('nsubj', 'nsubjpass') and token.pos_ in ('NOUN', 'PROPN'):
            verb = token.head
            if verb.pos_ in ('VERB', 'AUX') and len(verb.lemma_) >= 2:
                key = (token.lemma_.lower(), verb.lemma_.lower())
                if key not in seen['noun_verb']:
                    seen['noun_verb'].add(key)
                    relationships['noun_verb'].append({
                        'noun': token.lemma_.lower(),
                        'verb': verb.lemma_.lower(),
                        'relation': 'subject'
                    })

        # Verb-Noun: Object relationships (dobj, pobj)
        if token.dep_ in ('dobj', 'pobj') and token.pos_ in ('NOUN', 'PROPN'):
            # Find the governing verb
            verb = token.head
            # For pobj, go up one more level
            if token.dep_ == 'pobj' and verb.dep_ == 'prep':
                verb = verb.head
            if verb.pos_ in ('VERB', 'AUX') and len(verb.lemma_) >= 2:
                key = (verb.lemma_.lower(), token.lemma_.lower())
                if key not in seen['verb_noun_obj']:
                    seen['verb_noun_obj'].add(key)
                    relationships['verb_noun_obj'].append({
                        'verb': verb.lemma_.lower(),
                        'noun': token.lemma_.lower(),
                        'relation': 'object'
                    })

        # Adjective-Noun: amod relationships
        if token.dep_ == 'amod' and token.pos_ == 'ADJ':
            noun = token.head
            if noun.pos_ in ('NOUN', 'PROPN') and len(noun.lemma_) >= 2:
                key = (token.lemma_.lower(), noun.lemma_.lower())
                if key not in seen['adj_noun']:
                    seen['adj_noun'].add(key)
                    relationships['adj_noun'].append({
                        'adjective': token.lemma_.lower(),
                        'noun': noun.lemma_.lower()
                    })

        # Adverb-Verb: advmod relationships
        if token.dep_ == 'advmod' and token.pos_ == 'ADV':
            verb = token.head
            if verb.pos_ in ('VERB', 'AUX') and len(verb.lemma_) >= 2:
                key = (token.lemma_.lower(), verb.lemma_.lower())
                if key not in seen['adv_verb']:
                    seen['adv_verb'].add(key)
                    relationships['adv_verb'].append({
                        'adverb': token.lemma_.lower(),
                        'verb': verb.lemma_.lower()
                    })

    return relationships


def link_words_to_context(nouns, verbs, adjectives, doc):
    """
    Create contextual links - which words appear in which sentence contexts.
    Returns sentence-level co-occurrences for context analysis.
    """
    sentence_contexts = []

    for sent in doc.sents:
        sent_nouns = []
        sent_verbs = []
        sent_adjs = []

        for token in sent:
            if token.is_punct or token.is_space or len(token.lemma_) < 2:
                continue

            lemma = token.lemma_.lower()

            if token.pos_ in ('NOUN', 'PROPN'):
                sent_nouns.append(lemma)
            elif token.pos_ in ('VERB', 'AUX'):
                sent_verbs.append(lemma)
            elif token.pos_ == 'ADJ':
                sent_adjs.append(lemma)

        if sent_nouns or sent_verbs or sent_adjs:
            sentence_contexts.append({
                'nouns': list(set(sent_nouns)),
                'verbs': list(set(sent_verbs)),
                'adjectives': list(set(sent_adjs))
            })

    return sentence_contexts

def analyze_text(text):
    """Main analysis function."""
    doc = nlp(text)

    # Initialize matcher for expressions
    matcher = Matcher(nlp.vocab)
    for i, pattern in enumerate(EXPRESSION_PATTERNS):
        matcher.add(f"EXPR_{i}", [pattern])

    # Extract linguistic features
    nouns = []
    verbs = []
    adjectives = []

    for token in doc:
        lemma = token.lemma_.lower()

        # Skip punctuation, spaces, and very short words
        if token.is_punct or token.is_space or len(lemma) < 2:
            continue

        if token.pos_ in ("NOUN", "PROPN"):
            types = classify_noun(token, lemma)
            nouns.append({
                "text": token.text,
                "lemma": lemma,
                "types": types
            })

        elif token.pos_ in ("VERB", "AUX"):
            types = classify_verb(token, lemma)
            verbs.append({
                "text": token.text,
                "lemma": lemma,
                "types": types
            })

        elif token.pos_ == "ADJ":
            types = classify_adjective(token, lemma)
            adjectives.append({
                "text": token.text,
                "lemma": lemma,
                "types": types
            })

    # Extract expressions
    expressions = extract_expressions(doc, matcher)

    # Extract metaphors
    metaphors = extract_metaphors(doc, text)

    # Extract topics
    topics = extract_topics(doc)

    # Extract cross-category relationships
    relationships = extract_relationships(doc)

    # Extract sentence contexts for word-topic linking
    sentence_contexts = link_words_to_context(nouns, verbs, adjectives, doc)

    # Aggregate by lemma and count
    noun_counts = Counter()
    noun_types = {}
    for n in nouns:
        noun_counts[n["lemma"]] += 1
        if n["lemma"] not in noun_types:
            noun_types[n["lemma"]] = n["types"]

    verb_counts = Counter()
    verb_types = {}
    for v in verbs:
        verb_counts[v["lemma"]] += 1
        if v["lemma"] not in verb_types:
            verb_types[v["lemma"]] = v["types"]

    adj_counts = Counter()
    adj_types = {}
    for a in adjectives:
        adj_counts[a["lemma"]] += 1
        if a["lemma"] not in adj_types:
            adj_types[a["lemma"]] = a["types"]

    # Format output
    result = {
        "nouns": [
            {"word": word, "count": count, "types": noun_types.get(word, [])}
            for word, count in noun_counts.most_common(20)
        ],
        "verbs": [
            {"word": word, "count": count, "types": verb_types.get(word, [])}
            for word, count in verb_counts.most_common(20)
        ],
        "adjectives": [
            {"word": word, "count": count, "types": adj_types.get(word, [])}
            for word, count in adj_counts.most_common(20)
        ],
        "expressions": expressions[:20],
        "topics": topics[:10],
        "metaphors": metaphors[:10],
        "relationships": {
            "noun_verb": relationships['noun_verb'][:30],
            "verb_noun_obj": relationships['verb_noun_obj'][:30],
            "adj_noun": relationships['adj_noun'][:30],
            "adv_verb": relationships['adv_verb'][:30]
        },
        "sentence_contexts": sentence_contexts[:50],
        "statistics": {
            "total_nouns": len(nouns),
            "total_verbs": len(verbs),
            "total_adjectives": len(adjectives),
            "total_expressions": len(expressions),
            "total_metaphors": len(metaphors),
            "total_noun_verb_relations": len(relationships['noun_verb']),
            "total_adj_noun_relations": len(relationships['adj_noun']),
            "total_adv_verb_relations": len(relationships['adv_verb']),
            "sentence_count": len(list(doc.sents)),
            "word_count": len([t for t in doc if not t.is_punct and not t.is_space])
        }
    }

    return result

def main():
    """Main entry point - reads text from stdin or command line argument."""
    if len(sys.argv) > 1:
        # Text passed as argument
        text = sys.argv[1]
    else:
        # Read from stdin
        text = sys.stdin.read()

    if not text.strip():
        print(json.dumps({"error": "No text provided"}))
        sys.exit(1)

    try:
        result = analyze_text(text)
        print(json.dumps(result, ensure_ascii=False))
    except Exception as e:
        print(json.dumps({"error": str(e)}))
        sys.exit(1)

if __name__ == "__main__":
    main()
