#!/usr/bin/env python3
"""
Repair script for incomplete conversation JSON files.

Re-runs linguistic analysis and topic extraction for messages missing data.
Continues incomplete conversations that didn't reach the expected message count.

Usage:
    python cleanup_conversations.py                  # Repair linguistics and topics
    python cleanup_conversations.py --dry-run        # Preview without making changes
    python cleanup_conversations.py --move-failed    # Move truly failed conversations to archive
    python cleanup_conversations.py --check-archive  # Check/repair archived files and restore if fixed
    python cleanup_conversations.py --linguistics-only  # Only repair linguistics (no API needed)
"""

import json
import subprocess
import sys
import shutil
import argparse
import re
import time
import os
import datetime
from pathlib import Path

# Directories
SCRIPT_DIR = Path(__file__).parent
CONVERSATIONS_DIR = SCRIPT_DIR / "conversations"
OLD_DIR = SCRIPT_DIR / "conversations-old"
LINGUISTIC_ANALYZER = SCRIPT_DIR / "linguistic_analyzer.py"

# OpenAI API configuration
API_KEY = os.environ.get('OPENAI_API_KEY', '')
TOPIC_EXTRACTOR_ID = os.environ.get('TOPIC_EXTRACTOR_ID', '')

# Try to import requests, fall back to urllib if not available
try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    import urllib.request
    import urllib.error
    HAS_REQUESTS = False


def make_api_request(url: str, method: str = 'GET', data: dict = None) -> dict:
    """Make a request to the OpenAI API."""
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {API_KEY}',
        'OpenAI-Beta': 'assistants=v2'
    }

    if HAS_REQUESTS:
        if method == 'POST':
            response = requests.post(url, headers=headers, json=data, timeout=120)
        else:
            response = requests.get(url, headers=headers, timeout=60)
        response.raise_for_status()
        return response.json()
    else:
        req = urllib.request.Request(url, headers=headers)
        if method == 'POST' and data:
            req.data = json.dumps(data).encode('utf-8')
        timeout = 120 if method == 'POST' else 60
        with urllib.request.urlopen(req, timeout=timeout) as response:
            return json.loads(response.read().decode('utf-8'))


def create_thread() -> str:
    """Create a new thread."""
    url = 'https://api.openai.com/v1/threads'
    result = make_api_request(url, 'POST', {})
    return result['id']


def add_message(thread_id: str, content: str) -> None:
    """Add a message to a thread."""
    url = f'https://api.openai.com/v1/threads/{thread_id}/messages'
    make_api_request(url, 'POST', {'role': 'user', 'content': content})


def run_assistant(thread_id: str, assistant_id: str) -> str:
    """Run an assistant on a thread and return the run ID."""
    url = f'https://api.openai.com/v1/threads/{thread_id}/runs'
    result = make_api_request(url, 'POST', {'assistant_id': assistant_id})
    return result['id']


def wait_for_completion(thread_id: str, run_id: str, max_wait: int = 60) -> bool:
    """Wait for a run to complete."""
    url = f'https://api.openai.com/v1/threads/{thread_id}/runs/{run_id}'
    start_time = time.time()

    while True:
        result = make_api_request(url, 'GET')
        status = result['status']

        if status == 'completed':
            return True
        elif status in ['failed', 'cancelled', 'expired']:
            return False

        if time.time() - start_time > max_wait:
            return False

        time.sleep(1)


def get_latest_response(thread_id: str) -> str:
    """Get the latest assistant response from a thread."""
    url = f'https://api.openai.com/v1/threads/{thread_id}/messages?limit=1'
    result = make_api_request(url, 'GET')

    if not result.get('data'):
        return None

    message = result['data'][0]
    return message['content'][0]['text']['value']


def get_assistant_response(thread_id: str, assistant_id: str, message: str) -> str | None:
    """Send a message to an assistant and get the response."""
    try:
        add_message(thread_id, message)
        run_id = run_assistant(thread_id, assistant_id)

        if not wait_for_completion(thread_id, run_id):
            return None

        return get_latest_response(thread_id)
    except Exception as e:
        print(f"    Warning: Failed to get assistant response: {e}")
        return None


def strip_json_comments(json_str: str) -> str:
    """Remove JavaScript-style comments from JSON string, preserving strings."""
    result = []
    i = 0
    in_string = False
    escape_next = False

    while i < len(json_str):
        char = json_str[i]

        if escape_next:
            result.append(char)
            escape_next = False
            i += 1
            continue

        if char == '\\' and in_string:
            result.append(char)
            escape_next = True
            i += 1
            continue

        if char == '"' and not escape_next:
            in_string = not in_string
            result.append(char)
            i += 1
            continue

        if not in_string:
            # Check for single-line comment
            if char == '/' and i + 1 < len(json_str) and json_str[i + 1] == '/':
                # Skip until end of line
                while i < len(json_str) and json_str[i] != '\n':
                    i += 1
                continue
            # Check for multi-line comment
            if char == '/' and i + 1 < len(json_str) and json_str[i + 1] == '*':
                i += 2
                while i + 1 < len(json_str) and not (json_str[i] == '*' and json_str[i + 1] == '/'):
                    i += 1
                i += 2  # Skip */
                continue

        result.append(char)
        i += 1

    # Remove trailing commas (invalid in JSON but left after comment removal)
    cleaned = ''.join(result)
    # Remove trailing commas before ] or }
    cleaned = re.sub(r',(\s*[\]\}])', r'\1', cleaned)
    # Remove parenthetical explanations after string values: "value" (explanation)
    cleaned = re.sub(r'"\s*\([^)]*\)', '"', cleaned)
    return cleaned


def try_fix_truncated_json(json_str: str) -> str:
    """Attempt to fix truncated JSON by closing open brackets and removing trailing content."""
    # Remove any trailing incomplete string (after last complete value)
    # Find last complete array item or object property
    lines = json_str.split('\n')
    fixed_lines = []

    for line in lines:
        # Skip lines that look truncated (end with ... or incomplete quotes)
        stripped = line.rstrip()
        if stripped.endswith('...') or (stripped.count('"') % 2 == 1 and not stripped.endswith(',')):
            # Try to salvage by removing the incomplete part
            if '// ' in line:
                # Line has a comment, take everything before it
                line = line.split('// ')[0].rstrip()
                if line.endswith(','):
                    fixed_lines.append(line)
                continue
            break
        fixed_lines.append(line)

    result = '\n'.join(fixed_lines)

    # Count open brackets
    open_braces = result.count('{') - result.count('}')
    open_brackets = result.count('[') - result.count(']')

    # Remove trailing comma if present
    result = result.rstrip()
    if result.endswith(','):
        result = result[:-1]

    # Close any open brackets
    result += ']' * open_brackets + '}' * open_braces

    return result


def parse_json_response(response: str) -> dict | None:
    """Parse JSON from API response, handling comments and code blocks."""
    if not response:
        return None

    # Strip comments from the response
    cleaned = strip_json_comments(response)

    # Try to extract JSON object from response
    json_pattern = r'\{(?:[^{}]|(?:\{(?:[^{}]|(?:\{[^{}]*\}))*\}))*\}'
    match = re.search(json_pattern, cleaned, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass

    # Try direct JSON parse
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass

    # Try to fix truncated JSON
    try:
        fixed = try_fix_truncated_json(cleaned)
        return json.loads(fixed)
    except json.JSONDecodeError:
        return None


def extract_topics(text: str, thread_id: str = None) -> dict | None:
    """Extract topics from text using the OpenAI topic extractor assistant."""
    response = None
    try:
        # Create a new thread if not provided
        if not thread_id:
            thread_id = create_thread()

        # Add message and run assistant
        add_message(thread_id, text)
        run_id = run_assistant(thread_id, TOPIC_EXTRACTOR_ID)

        # Wait for completion
        if not wait_for_completion(thread_id, run_id):
            print("    Warning: Topic extraction timed out or failed")
            return None

        # Get response
        response = get_latest_response(thread_id)
        if not response:
            print("    Warning: Empty response from topic extractor")
            return None

        # Parse JSON from response
        result = parse_json_response(response)
        if result:
            return result

        print(f"    Warning: Could not parse topic extraction response")
        print(f"    API Response: {response[:500]}..." if len(response) > 500 else f"    API Response: {response}")
        return None

    except Exception as e:
        print(f"    Warning: Topic extraction failed: {e}")
        if response:
            print(f"    API Response: {response[:500]}..." if len(response) > 500 else f"    API Response: {response}")
        return None


def analyze_linguistics(text: str) -> dict | None:
    """Run linguistic analysis on text using the Python spaCy analyzer."""
    if not LINGUISTIC_ANALYZER.exists():
        print(f"  Warning: Linguistic analyzer not found at {LINGUISTIC_ANALYZER}")
        return None

    try:
        result = subprocess.run(
            ['python3', str(LINGUISTIC_ANALYZER)],
            input=text,
            capture_output=True,
            text=True,
            timeout=30
        )

        if result.returncode != 0:
            print(f"  Warning: Linguistic analyzer failed: {result.stderr[:100]}")
            return None

        output = result.stdout.strip()
        if not output:
            print("  Warning: Linguistic analyzer returned empty output")
            return None

        data = json.loads(output)
        if 'error' in data:
            print(f"  Warning: Linguistic analyzer error: {data['error']}")
            return None

        return data

    except subprocess.TimeoutExpired:
        print("  Warning: Linguistic analysis timed out")
        return None
    except json.JSONDecodeError as e:
        print(f"  Warning: Failed to parse linguistic analysis output: {e}")
        return None
    except Exception as e:
        print(f"  Warning: Linguistic analysis failed: {e}")
        return None


def continue_conversation(file_path: Path, dry_run: bool = False) -> dict:
    """
    Continue an incomplete conversation that didn't reach the expected message count.

    Returns:
        dict with continuation stats
    """
    stats = {
        'messages_added': 0,
        'messages_failed': 0,
        'modified': False
    }

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"  Error reading file: {e}")
        return stats

    messages = data.get('messages', [])
    total_expected = data.get('total_messages', 10)
    current_count = len(messages)

    if current_count >= total_expected:
        return stats

    messages_needed = total_expected - current_count
    print(f"  Need to add {messages_needed} more messages ({current_count}/{total_expected})")

    if dry_run:
        print(f"    [DRY RUN] Would continue conversation")
        stats['messages_added'] = messages_needed
        stats['modified'] = True
        return stats

    # Get assistant info from the conversation
    assistant_1_id = data.get('assistant_1_id')
    assistant_1_name = data.get('assistant_1_name', 'Assistant 1')
    assistant_1_slug = data.get('assistant_1_slug', 'assistant-1')
    assistant_2_id = data.get('assistant_2_id')
    assistant_2_name = data.get('assistant_2_name', 'Assistant 2')
    assistant_2_slug = data.get('assistant_2_slug', 'assistant-2')

    if not assistant_1_id or not assistant_2_id:
        print("  Error: Missing assistant IDs in conversation")
        return stats

    # Create new threads for continuing the conversation
    try:
        thread_1_id = create_thread()
        thread_2_id = create_thread()
        topic_thread_id = create_thread()
    except Exception as e:
        print(f"  Error creating threads: {e}")
        return stats

    # Get the last message to continue from
    if messages:
        last_message = messages[-1]
        current_message = last_message.get('output', '')
        last_assistant = last_message.get('assistant', 'assistant_1')
    else:
        current_message = "start conversation"
        last_assistant = 'assistant_2'  # So we start with assistant_1

    # Continue the conversation
    for i in range(messages_needed):
        msg_num = current_count + i + 1

        # Alternate between assistants
        if last_assistant == 'assistant_2':
            # Assistant 1's turn
            current_assistant = 'assistant_1'
            assistant_id = assistant_1_id
            assistant_name = assistant_1_name
            assistant_slug = assistant_1_slug
            thread_id = thread_1_id
        else:
            # Assistant 2's turn
            current_assistant = 'assistant_2'
            assistant_id = assistant_2_id
            assistant_name = assistant_2_name
            assistant_slug = assistant_2_slug
            thread_id = thread_2_id

        print(f"  Message {msg_num}: Getting response from {assistant_name}...")

        response = get_assistant_response(thread_id, assistant_id, current_message)

        if not response:
            print(f"    Failed to get response")
            stats['messages_failed'] += 1
            break

        print(f"    Got response ({len(response)} chars)")

        # Extract topics
        print(f"    Extracting topics...")
        analysis = extract_topics(response, topic_thread_id)

        # Analyze linguistics
        print(f"    Analyzing linguistics...")
        linguistics = analyze_linguistics(response)

        # Create message data
        message_data = {
            'number': msg_num,
            'assistant': current_assistant,
            'assistant_id': assistant_id,
            'assistant_name': assistant_name,
            'assistant_slug': assistant_slug,
            'input': current_message,
            'output': response
        }

        if analysis:
            message_data['analysis'] = analysis
        if linguistics:
            message_data['linguistics'] = linguistics

        messages.append(message_data)
        stats['messages_added'] += 1
        stats['modified'] = True

        # Update for next iteration
        current_message = response
        last_assistant = current_assistant

    # Save the updated conversation
    if stats['modified']:
        # Check if conversation is now complete
        if len(messages) >= total_expected:
            data['status'] = 'completed'
            data['completed_at'] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            if 'error' in data:
                del data['error']
            if 'failed_at' in data:
                del data['failed_at']

        # Update statistics
        total_chars = sum(len(msg.get('output', '')) for msg in messages)
        data['statistics'] = {
            'total_characters': total_chars,
            'average_message_length': round(total_chars / len(messages)) if messages else 0
        }

        data['messages'] = messages
        data['continued_at'] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

    return stats


def repair_conversation(file_path: Path, dry_run: bool = False, linguistics_only: bool = False) -> dict:
    """
    Repair a conversation file by re-running missing analysis.

    Returns:
        dict with repair stats
    """
    stats = {
        'linguistics_repaired': 0,
        'linguistics_failed': 0,
        'topics_repaired': 0,
        'topics_failed': 0,
        'already_complete': 0,
        'modified': False
    }

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"  Error reading file: {e}")
        return stats

    messages = data.get('messages', [])
    if not messages:
        return stats

    # Create a thread for topic extraction (reuse for all messages)
    topic_thread_id = None
    if not linguistics_only and not dry_run:
        try:
            topic_thread_id = create_thread()
        except Exception as e:
            print(f"  Warning: Could not create topic extraction thread: {e}")

    for i, msg in enumerate(messages):
        msg_num = msg.get('number', i + 1)
        output_text = msg.get('output', '')

        if not output_text:
            continue

        # Check if linguistics is missing
        if 'linguistics' not in msg:
            print(f"  Message {msg_num}: Missing linguistics, analyzing...")

            if dry_run:
                print(f"    [DRY RUN] Would analyze linguistics")
                stats['linguistics_repaired'] += 1
                stats['modified'] = True
            else:
                linguistics = analyze_linguistics(output_text)
                if linguistics:
                    msg['linguistics'] = linguistics
                    stats['linguistics_repaired'] += 1
                    stats['modified'] = True
                    print(f"    Linguistics repaired")
                else:
                    stats['linguistics_failed'] += 1
                    print(f"    Linguistics failed")

        # Check if analysis (topics) is missing
        if 'analysis' not in msg and not linguistics_only:
            print(f"  Message {msg_num}: Missing analysis, extracting topics...")

            if dry_run:
                print(f"    [DRY RUN] Would extract topics")
                stats['topics_repaired'] += 1
                stats['modified'] = True
            else:
                analysis = extract_topics(output_text, topic_thread_id)
                if analysis:
                    msg['analysis'] = analysis
                    stats['topics_repaired'] += 1
                    stats['modified'] = True
                    print(f"    Topics extracted")
                else:
                    stats['topics_failed'] += 1
                    print(f"    Topics failed")

        # Count complete messages
        if 'linguistics' in msg and ('analysis' in msg or linguistics_only):
            stats['already_complete'] += 1

    # Save the repaired file
    if stats['modified'] and not dry_run:
        # Update status if all messages are now complete
        all_complete = all(
            'linguistics' in msg and ('analysis' in msg or linguistics_only)
            for msg in messages
        )

        if all_complete:
            data['status'] = 'completed'
            if 'error' in data:
                del data['error']
            if 'failed_at' in data:
                del data['failed_at']
            data['repaired_at'] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

    return stats


def check_conversation(file_path: Path, linguistics_only: bool = False) -> tuple[bool, list[str], bool, bool]:
    """
    Check if a conversation file needs repair or should be archived.

    Returns:
        tuple: (needs_repair, list of issues, should_archive, needs_continuation)
    """
    issues = []
    should_archive = False
    needs_continuation = False

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        return False, [f"invalid JSON: {e}"], True, False
    except Exception as e:
        return False, [f"error reading file: {e}"], True, False

    # Check for incomplete message count
    messages = data.get('messages', [])
    total_expected = data.get('total_messages', 10)

    if len(messages) < total_expected and len(messages) > 0:
        issues.append(f"incomplete: {len(messages)}/{total_expected} messages")
        needs_continuation = True

    # Check for fatal errors that can't be repaired (only if no messages at all)
    if data.get('status') == 'failed' and len(messages) == 0:
        error = data.get('error', '')
        issues.append(f"failed with no messages: {error[:50]}")
        should_archive = True

    # Check messages for missing fields
    if len(messages) == 0:
        issues.append("empty messages array")
        should_archive = True
    else:
        missing_linguistics = 0
        missing_analysis = 0

        for msg in messages:
            if 'linguistics' not in msg:
                missing_linguistics += 1
            if 'analysis' not in msg:
                missing_analysis += 1

        if missing_linguistics > 0:
            issues.append(f"{missing_linguistics} messages missing linguistics")
        if missing_analysis > 0 and not linguistics_only:
            issues.append(f"{missing_analysis} messages missing analysis")

    needs_repair = len(issues) > 0 and not should_archive
    return needs_repair, issues, should_archive, needs_continuation


def main():
    parser = argparse.ArgumentParser(
        description='Repair incomplete conversation JSON files by re-running analysis.'
    )
    parser.add_argument(
        '--dry-run', '-n',
        action='store_true',
        help='Preview what would be done without making changes'
    )
    parser.add_argument(
        '--move-failed',
        action='store_true',
        help='Move truly failed conversations (API errors, timeouts) to archive'
    )
    parser.add_argument(
        '--check-archive',
        action='store_true',
        help='Check archived files in conversations-old/ and restore any that can be repaired'
    )
    parser.add_argument(
        '--linguistics-only',
        action='store_true',
        help='Only repair linguistics (no API calls for topic extraction or continuation)'
    )

    args = parser.parse_args()

    if not CONVERSATIONS_DIR.exists():
        print(f"Error: Conversations directory not found: {CONVERSATIONS_DIR}")
        sys.exit(1)

    # Check linguistic analyzer exists
    if not LINGUISTIC_ANALYZER.exists():
        print(f"Warning: Linguistic analyzer not found at {LINGUISTIC_ANALYZER}")
        print("Linguistic repair will not work without it.\n")

    print(f"{'[DRY RUN] ' if args.dry_run else ''}Conversation Repair Tool")
    print("=" * 60)
    if args.linguistics_only:
        print("Mode: Linguistics only (no API calls)")
    else:
        print("Mode: Full repair (linguistics + topics + continuation)")
    print()

    needs_repair = []
    needs_continuation = []
    complete = []
    to_archive = []

    # Scan all conversations
    for json_file in sorted(CONVERSATIONS_DIR.glob("*.json")):
        needs_fix, issues, should_archive, needs_cont = check_conversation(json_file, args.linguistics_only)

        if should_archive:
            to_archive.append((json_file, issues))
        elif needs_fix:
            needs_repair.append((json_file, issues, needs_cont))
        else:
            complete.append(json_file)

    # Separate continuation needs
    needs_continuation = [(f, i) for f, i, c in needs_repair if c]
    needs_repair_only = [(f, i) for f, i, c in needs_repair if not c]

    print(f"Complete conversations: {len(complete)}")
    print(f"Need continuation: {len(needs_continuation)}")
    print(f"Need repair only: {len(needs_repair_only)}")
    print(f"Should archive (unrecoverable): {len(to_archive)}")
    print()

    # Continue incomplete conversations first
    total_messages_added = 0
    total_messages_failed = 0

    if needs_continuation and not args.linguistics_only:
        print("Continuing incomplete conversations...")
        print("-" * 60)

        for file_path, issues in needs_continuation:
            print(f"\n{file_path.name}")
            print(f"  Issues: {', '.join(issues)}")

            stats = continue_conversation(file_path, dry_run=args.dry_run)
            total_messages_added += stats['messages_added']
            total_messages_failed += stats['messages_failed']

        print()
        print("-" * 60)
        if args.dry_run:
            print(f"[DRY RUN] Would add {total_messages_added} messages")
        else:
            print(f"Added {total_messages_added} messages, {total_messages_failed} failed")

    # Repair conversations (including the ones we just continued)
    total_linguistics_repaired = 0
    total_linguistics_failed = 0
    total_topics_repaired = 0
    total_topics_failed = 0

    all_needs_repair = needs_repair_only + needs_continuation
    if all_needs_repair:
        print()
        print("Repairing missing analysis...")
        print("-" * 60)

        for file_path, issues in all_needs_repair:
            print(f"\n{file_path.name}")

            stats = repair_conversation(file_path, dry_run=args.dry_run, linguistics_only=args.linguistics_only)
            total_linguistics_repaired += stats['linguistics_repaired']
            total_linguistics_failed += stats['linguistics_failed']
            total_topics_repaired += stats['topics_repaired']
            total_topics_failed += stats['topics_failed']

        print()
        print("-" * 60)
        if args.dry_run:
            print(f"[DRY RUN] Would repair:")
            print(f"  Linguistics: {total_linguistics_repaired} messages")
            if not args.linguistics_only:
                print(f"  Topics: {total_topics_repaired} messages")
        else:
            print(f"Repaired:")
            print(f"  Linguistics: {total_linguistics_repaired} succeeded, {total_linguistics_failed} failed")
            if not args.linguistics_only:
                print(f"  Topics: {total_topics_repaired} succeeded, {total_topics_failed} failed")

    # Archive failed conversations
    if to_archive and args.move_failed:
        print()
        print("Archiving unrecoverable conversations...")
        print("-" * 60)

        if not args.dry_run:
            OLD_DIR.mkdir(exist_ok=True)

        for file_path, issues in to_archive:
            dest = OLD_DIR / file_path.name
            if args.dry_run:
                print(f"  [DRY RUN] Would move: {file_path.name}")
            else:
                shutil.move(str(file_path), str(dest))
                print(f"  Moved: {file_path.name}")
            print(f"    Reason: {', '.join(issues[:2])}")

        print()
        if args.dry_run:
            print(f"[DRY RUN] Would archive {len(to_archive)} files")
        else:
            print(f"Archived {len(to_archive)} files to {OLD_DIR}")

    elif to_archive and not args.move_failed:
        print()
        print(f"Found {len(to_archive)} unrecoverable conversations.")
        print("Use --move-failed to archive them.")

    if not all_needs_repair and not to_archive and not needs_continuation:
        print("All conversations are complete. Nothing to do.")

    # Check and repair archived files
    if args.check_archive and OLD_DIR.exists():
        print()
        print("Checking archived conversations...")
        print("=" * 60)

        archived_files = list(OLD_DIR.glob("*.json"))
        if not archived_files:
            print("No archived files found.")
        else:
            repairable = []
            unrecoverable = []

            for json_file in sorted(archived_files):
                needs_fix, issues, should_archive, needs_cont = check_conversation(json_file, args.linguistics_only)

                # If it was archived but could now be repaired
                if needs_fix or (not should_archive and not needs_fix):
                    repairable.append((json_file, issues, needs_cont))
                else:
                    unrecoverable.append((json_file, issues))

            print(f"Repairable: {len(repairable)}")
            print(f"Unrecoverable: {len(unrecoverable)}")

            if repairable:
                print()
                print("Repairing and restoring archived conversations...")
                print("-" * 60)

                restored = 0
                for file_path, issues, needs_cont in repairable:
                    print(f"\n{file_path.name}")
                    if issues:
                        print(f"  Issues: {', '.join(issues)}")

                    # Continue if needed
                    if needs_cont and not args.linguistics_only:
                        continue_conversation(file_path, dry_run=args.dry_run)

                    # Repair analysis
                    repair_conversation(file_path, dry_run=args.dry_run, linguistics_only=args.linguistics_only)

                    # Check if now complete
                    _, remaining_issues, still_failed, _ = check_conversation(file_path, args.linguistics_only)

                    if not still_failed:
                        dest = CONVERSATIONS_DIR / file_path.name
                        if args.dry_run:
                            print(f"  [DRY RUN] Would restore")
                        else:
                            shutil.move(str(file_path), str(dest))
                            print(f"  Restored")
                        restored += 1

                print()
                print("-" * 60)
                if args.dry_run:
                    print(f"[DRY RUN] Would restore {restored} conversations")
                else:
                    print(f"Restored {restored} conversations to conversations/")

    print()
    print("Done!")


if __name__ == '__main__':
    main()
