#!/usr/bin/env python3
"""
Backfill Linguistic Analysis for Existing Conversations

This script runs spaCy linguistic analysis on conversation files that were
created before the linguistic analyzer was integrated.

Usage:
    python backfill_linguistics.py [--force] [--dry-run] [--file FILENAME]

Options:
    --force     Re-analyze messages that already have linguistics data
    --dry-run   Show what would be done without making changes
    --file      Process only a specific conversation file
"""

import os
import sys
import json
import glob
import argparse
from datetime import datetime

# Import the linguistic analyzer
try:
    from linguistic_analyzer import analyze_text
except ImportError:
    print("Error: linguistic_analyzer.py not found in the current directory")
    print("Make sure you run this script from the project root directory")
    sys.exit(1)


def get_conversation_files(conversations_dir, specific_file=None):
    """Get list of conversation JSON files to process."""
    if specific_file:
        path = os.path.join(conversations_dir, specific_file)
        if os.path.exists(path):
            return [path]
        else:
            print(f"Error: File not found: {path}")
            return []

    pattern = os.path.join(conversations_dir, "conversation_*.json")
    files = glob.glob(pattern)
    return sorted(files)


def needs_analysis(message, force=False):
    """Check if a message needs linguistic analysis."""
    if force:
        return True
    return 'linguistics' not in message or message['linguistics'] is None


def process_conversation(filepath, force=False, dry_run=False):
    """Process a single conversation file and add linguistic analysis."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        print(f"  Error: Invalid JSON in {filepath}: {e}")
        return {'processed': 0, 'skipped': 0, 'errors': 1}
    except Exception as e:
        print(f"  Error reading {filepath}: {e}")
        return {'processed': 0, 'skipped': 0, 'errors': 1}

    if 'messages' not in data:
        print(f"  Warning: No messages found in {filepath}")
        return {'processed': 0, 'skipped': 0, 'errors': 0}

    stats = {'processed': 0, 'skipped': 0, 'errors': 0}
    modified = False

    for i, message in enumerate(data['messages']):
        # Get the text to analyze (prefer output, fallback to input)
        text = message.get('output', '') or message.get('input', '')

        if not text or len(text.strip()) < 10:
            stats['skipped'] += 1
            continue

        if not needs_analysis(message, force):
            stats['skipped'] += 1
            continue

        if dry_run:
            print(f"    Would analyze message #{message.get('number', i+1)} ({len(text)} chars)")
            stats['processed'] += 1
            continue

        try:
            # Run linguistic analysis
            linguistics = analyze_text(text)

            if linguistics:
                message['linguistics'] = linguistics
                modified = True
                stats['processed'] += 1
                print(f"    Analyzed message #{message.get('number', i+1)}: "
                      f"{linguistics['statistics']['total_nouns']} nouns, "
                      f"{linguistics['statistics']['total_verbs']} verbs, "
                      f"{len(linguistics.get('relationships', {}).get('noun_verb', []))} relationships")
            else:
                print(f"    Warning: No analysis result for message #{message.get('number', i+1)}")
                stats['errors'] += 1

        except Exception as e:
            print(f"    Error analyzing message #{message.get('number', i+1)}: {e}")
            stats['errors'] += 1

    # Save the modified file
    if modified and not dry_run:
        try:
            # Add backfill timestamp
            data['linguistics_backfilled_at'] = datetime.now().isoformat()

            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            print(f"  Saved updates to {os.path.basename(filepath)}")
        except Exception as e:
            print(f"  Error saving {filepath}: {e}")
            stats['errors'] += 1

    return stats


def main():
    parser = argparse.ArgumentParser(
        description='Backfill linguistic analysis for existing conversations'
    )
    parser.add_argument('--force', action='store_true',
                        help='Re-analyze messages that already have linguistics data')
    parser.add_argument('--dry-run', action='store_true',
                        help='Show what would be done without making changes')
    parser.add_argument('--file', type=str,
                        help='Process only a specific conversation file')
    parser.add_argument('--dir', type=str, default='conversations',
                        help='Directory containing conversation files (default: conversations)')

    args = parser.parse_args()

    # Determine conversations directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    conversations_dir = os.path.join(script_dir, args.dir)

    if not os.path.isdir(conversations_dir):
        print(f"Error: Conversations directory not found: {conversations_dir}")
        sys.exit(1)

    print("=" * 60)
    print("Linguistic Analysis Backfill Script")
    print("=" * 60)
    print(f"Conversations directory: {conversations_dir}")
    print(f"Force re-analysis: {args.force}")
    print(f"Dry run: {args.dry_run}")
    print()

    # Get files to process
    files = get_conversation_files(conversations_dir, args.file)

    if not files:
        print("No conversation files found to process")
        sys.exit(0)

    print(f"Found {len(files)} conversation file(s) to process")
    print()

    # Process each file
    total_stats = {'processed': 0, 'skipped': 0, 'errors': 0}

    for filepath in files:
        filename = os.path.basename(filepath)
        print(f"Processing: {filename}")

        stats = process_conversation(filepath, args.force, args.dry_run)

        total_stats['processed'] += stats['processed']
        total_stats['skipped'] += stats['skipped']
        total_stats['errors'] += stats['errors']

        if stats['processed'] == 0 and stats['skipped'] > 0:
            print(f"  Skipped (already analyzed): {stats['skipped']} messages")
        print()

    # Summary
    print("=" * 60)
    print("Summary")
    print("=" * 60)
    print(f"Files processed: {len(files)}")
    print(f"Messages analyzed: {total_stats['processed']}")
    print(f"Messages skipped: {total_stats['skipped']}")
    print(f"Errors: {total_stats['errors']}")

    if args.dry_run:
        print()
        print("(Dry run - no changes were made)")


if __name__ == '__main__':
    main()
