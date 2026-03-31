#!/usr/bin/env python3
"""
Display conversation statistics grouped by assistant type.

Usage:
    python conversation_stats.py
    python conversation_stats.py --detailed
"""

import json
import argparse
from pathlib import Path
from collections import defaultdict

SCRIPT_DIR = Path(__file__).parent
CONVERSATIONS_DIR = SCRIPT_DIR / "conversations"


def get_stats(detailed: bool = False):
    """Get conversation statistics grouped by assistant."""
    if not CONVERSATIONS_DIR.exists():
        print(f"Error: Conversations directory not found: {CONVERSATIONS_DIR}")
        return

    files = list(CONVERSATIONS_DIR.glob("*.json"))

    # Stats per assistant
    assistant_stats = defaultdict(lambda: {
        'total': 0,
        'completed': 0,
        'failed': 0,
        'in_progress': 0,
        'total_messages': 0,
        'total_chars': 0,
        'total_words': 0,
        'total_sentences': 0
    })

    # Overall stats
    total_conversations = 0
    total_completed = 0
    total_failed = 0

    for file_path in files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except:
            continue

        total_conversations += 1

        # Get assistant info
        assistant_name = data.get('assistant_1_name', 'Unknown')
        assistant_slug = data.get('assistant_1_slug', 'unknown')
        status = data.get('status', 'unknown')
        messages = data.get('messages', [])

        # Update stats
        stats = assistant_stats[assistant_slug]
        stats['name'] = assistant_name
        stats['total'] += 1

        if status == 'completed':
            stats['completed'] += 1
            total_completed += 1
        elif status == 'failed':
            stats['failed'] += 1
            total_failed += 1
        else:
            stats['in_progress'] += 1

        stats['total_messages'] += len(messages)
        for msg in messages:
            output = msg.get('output', '')
            stats['total_chars'] += len(output)
            stats['total_words'] += len(output.split())
            # Count sentences (ending with . ! or ?)
            stats['total_sentences'] += output.count('.') + output.count('!') + output.count('?')

    # Print results
    print("=" * 70)
    print("CONVERSATION STATISTICS BY ASSISTANT")
    print("=" * 70)
    print()

    # Sort by total conversations (descending)
    sorted_assistants = sorted(
        assistant_stats.items(),
        key=lambda x: x[1]['total'],
        reverse=True
    )

    # Calculate column width based on longest name
    max_name_len = max(len(stats['name']) for _, stats in sorted_assistants) if sorted_assistants else 20
    max_name_len = max(max_name_len, 20)

    # Calculate totals for footer
    total_words = sum(s['total_words'] for _, s in sorted_assistants)
    total_chars = sum(s['total_chars'] for _, s in sorted_assistants)
    total_sentences = sum(s['total_sentences'] for _, s in sorted_assistants)

    # Header
    print(f"{'Assistant':<{max_name_len}}  {'Conv':>5}  {'Done':>5}  {'Msgs':>6}  {'Sents':>7}  {'Words':>9}  {'Chars':>11}")
    print("-" * (max_name_len + 52))

    for slug, stats in sorted_assistants:
        name = stats['name']
        print(f"{name:<{max_name_len}}  {stats['total']:>5}  {stats['completed']:>5}  {stats['total_messages']:>6,}  {stats['total_sentences']:>7,}  {stats['total_words']:>9,}  {stats['total_chars']:>11,}")

    print("-" * (max_name_len + 52))
    total_msgs = sum(s['total_messages'] for _, s in sorted_assistants)
    print(f"{'TOTAL':<{max_name_len}}  {total_conversations:>5}  {total_completed:>5}  {total_msgs:>6,}  {total_sentences:>7,}  {total_words:>9,}  {total_chars:>11,}")
    print()

    if detailed:
        print()
        print("DETAILED STATISTICS")
        print("-" * 70)
        for slug, stats in sorted_assistants:
            avg_msgs = stats['total_messages'] / stats['total'] if stats['total'] > 0 else 0
            avg_chars = stats['total_chars'] / stats['total_messages'] if stats['total_messages'] > 0 else 0
            print(f"\n{stats['name']} ({slug})")
            print(f"  Conversations: {stats['total']} (completed: {stats['completed']}, failed: {stats['failed']})")
            print(f"  Total messages: {stats['total_messages']} (avg: {avg_msgs:.1f} per conversation)")
            print(f"  Total characters: {stats['total_chars']:,} (avg: {avg_chars:.0f} per message)")

    print()
    print(f"Total conversation files: {len(files)}")


def main():
    parser = argparse.ArgumentParser(description='Display conversation statistics by assistant.')
    parser.add_argument('--detailed', '-d', action='store_true', help='Show detailed statistics')
    args = parser.parse_args()

    get_stats(detailed=args.detailed)


if __name__ == '__main__':
    main()
