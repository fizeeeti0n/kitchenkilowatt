# Agent Log Extractor for Antigravity IDE -> .agent-logs/ format.
#
# Reads the auto-generated transcript JSONL file and extracts prompt/response pairs
# into the 8x assignment log format. Designed to be run repeatedly (idempotent).
# It tracks the last-processed step index so it only appends new entries on re-run.

import json
import os
import re
from datetime import datetime, timezone

# -- Config --
CONVERSATION_ID = "26fa61fc-f589-410f-8a63-dacfec135978"
APP_DATA = r"C:\Users\Admin\.gemini\antigravity-ide"
TRANSCRIPT_PATH = os.path.join(
    APP_DATA, "brain", CONVERSATION_ID, ".system_generated", "logs", "transcript.jsonl"
)
TRANSCRIPT_FULL_PATH = os.path.join(
    APP_DATA, "brain", CONVERSATION_ID, ".system_generated", "logs", "transcript_full.jsonl"
)
OUTPUT_DIR = os.path.join(r"g:\kitchen", ".agent-logs")
STATE_FILE = os.path.join(OUTPUT_DIR, ".last_processed_step")

SESSION_ID = CONVERSATION_ID[:8]  # "26fa61fc"
PROJECT = "kitchen-kilowatt"
AUTHOR = "ahanaf-nafiz"
TOOL = "antigravity-ide"
MODEL = "claude-opus-4.6-thinking"


def load_last_processed():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r") as f:
            return int(f.read().strip())
    return -1


def save_last_processed(step_index):
    with open(STATE_FILE, "w") as f:
        f.write(str(step_index))


def get_log_filename():
    """One file per date, named per the 8x format."""
    now = datetime.now(timezone.utc)
    date_str = now.strftime("%Y-%m-%d")
    for fname in os.listdir(OUTPUT_DIR):
        if fname.startswith(date_str) and fname.endswith(".md"):
            return os.path.join(OUTPUT_DIR, fname)
    # Create new file with header
    time_str = now.strftime("%H-%M-%S")
    filename = f"{date_str}_{time_str}_{SESSION_ID}.md"
    filepath = os.path.join(OUTPUT_DIR, filename)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(f"---\n")
        f.write(f"session_id: {CONVERSATION_ID}\n")
        f.write(f"date: {date_str}\n")
        f.write(f"author: {AUTHOR}\n")
        f.write(f"model: {MODEL}\n")
        f.write(f"tool: {TOOL}\n")
        f.write(f"project: {PROJECT}\n")
        f.write(f"total_exchanges: 0\n")
        f.write(f"first_prompt_time: {now.isoformat()}\n")
        f.write(f"last_prompt_time: {now.isoformat()}\n")
        f.write(f"---\n\n")
        f.write(f"# Session Log - {date_str}\n\n")
        f.write(f"Session: `{SESSION_ID}` | Project: `{PROJECT}` | Author: `{AUTHOR}`\n\n")
        f.write(f"---\n\n")
    return filepath


def strip_xml_wrapper(text):
    """Strip <USER_REQUEST>, <ADDITIONAL_METADATA>, <USER_SETTINGS_CHANGE> wrappers
    to get the raw user prompt."""
    # Extract content inside <USER_REQUEST> tags
    match = re.search(r'<USER_REQUEST>\s*(.*?)\s*</USER_REQUEST>', text, re.DOTALL)
    if match:
        return match.group(1).strip()
    return text.strip()


def read_transcript():
    """Read the compact transcript."""
    path = TRANSCRIPT_PATH
    if not os.path.exists(path):
        path = TRANSCRIPT_FULL_PATH
    if not os.path.exists(path):
        print(f"Transcript not found.")
        return []
    steps = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    steps.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    return steps


def read_full_step(step_index):
    """Read a specific step from transcript_full.jsonl to get untruncated content."""
    if not os.path.exists(TRANSCRIPT_FULL_PATH):
        return None
    with open(TRANSCRIPT_FULL_PATH, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                step = json.loads(line)
                if step.get("step_index") == step_index:
                    return step
            except json.JSONDecodeError:
                continue
    return None


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    last_processed = load_last_processed()
    steps = read_transcript()

    if not steps:
        print("No transcript data found.")
        return

    # Strategy: walk through steps and collect (USER_INPUT, last-non-empty PLANNER_RESPONSE) pairs
    # A "turn" is: one USER_INPUT followed by N PLANNER_RESPONSE steps.
    # The FINAL response text is the last PLANNER_RESPONSE with non-empty content
    # before the next USER_INPUT (or end of transcript).

    # First, group into turns
    turns = []
    current_turn = None

    for step in steps:
        step_type = step.get("type", "")
        source = step.get("source", "")
        step_index = step.get("step_index", 0)

        if step_type == "USER_INPUT" and source == "USER_EXPLICIT":
            if current_turn:
                turns.append(current_turn)
            current_turn = {
                "prompt_step": step,
                "response_steps": [],
            }
        elif step_type == "PLANNER_RESPONSE" and source == "MODEL":
            if current_turn:
                current_turn["response_steps"].append(step)

    if current_turn:
        turns.append(current_turn)

    # Now extract pairs, filtering by last_processed
    pairs = []
    for turn in turns:
        prompt_step = turn["prompt_step"]
        prompt_index = prompt_step.get("step_index", 0)

        # Find the last PLANNER_RESPONSE with non-empty content
        final_response = None
        for resp in reversed(turn["response_steps"]):
            content = resp.get("content", "")
            if content and content.strip():
                final_response = resp
                break

        if not final_response:
            continue

        resp_index = final_response.get("step_index", 0)
        max_index = max(prompt_index, resp_index)

        if max_index <= last_processed:
            continue

        # Get full content if truncated
        prompt_content = prompt_step.get("content", "")
        if prompt_step.get("is_truncated"):
            full_step = read_full_step(prompt_index)
            if full_step:
                prompt_content = full_step.get("content", prompt_content)

        resp_content = final_response.get("content", "")
        if final_response.get("is_truncated"):
            full_step = read_full_step(resp_index)
            if full_step:
                resp_content = full_step.get("content", resp_content)

        pairs.append({
            "prompt": {
                "step_index": prompt_index,
                "content": strip_xml_wrapper(prompt_content),
                "timestamp": prompt_step.get("created_at",
                    datetime.now(timezone.utc).isoformat()),
            },
            "response": {
                "step_index": resp_index,
                "content": resp_content.strip(),
                "timestamp": final_response.get("created_at",
                    datetime.now(timezone.utc).isoformat()),
            },
            "max_index": max_index,
        })

    if not pairs:
        print(f"No new prompt/response pairs found (last processed: step {last_processed}).")
        return

    log_file = get_log_filename()

    # Count existing entries
    existing_count = 0
    if os.path.exists(log_file):
        with open(log_file, "r", encoding="utf-8") as f:
            existing_count = f.read().count("[LOG_ENTRY type=PROMPT")

    with open(log_file, "a", encoding="utf-8") as f:
        for i, pair in enumerate(pairs):
            num = existing_count + i + 1
            p = pair["prompt"]
            r = pair["response"]

            f.write(f"\n[LOG_ENTRY type=PROMPT num={num} session={SESSION_ID}]\n")
            f.write(f"timestamp: {p['timestamp']}\n")
            f.write(f"model: {MODEL}\n\n")
            f.write(p["content"])
            f.write("\n\n\n")

            f.write(f"[LOG_ENTRY type=RESPONSE num={num} session={SESSION_ID}]\n")
            f.write(f"timestamp: {r['timestamp']}\n")
            f.write(f"model: {MODEL}\n\n")
            f.write(r["content"])
            f.write("\n\n\n")

    # Update header
    with open(log_file, "r", encoding="utf-8") as f:
        content = f.read()

    total = existing_count + len(pairs)
    content = re.sub(r"total_exchanges: \d+", f"total_exchanges: {total}", content, count=1)
    last_ts = pairs[-1]["response"]["timestamp"]
    content = re.sub(r"last_prompt_time: .+", f"last_prompt_time: {last_ts}", content, count=1)

    with open(log_file, "w", encoding="utf-8") as f:
        f.write(content)

    # Save state
    max_step = max(p["max_index"] for p in pairs)
    save_last_processed(max_step)

    print(f"Extracted {len(pairs)} new exchange(s) -> {log_file}")
    print(f"Total exchanges in log: {total}")


if __name__ == "__main__":
    main()
