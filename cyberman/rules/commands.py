from __future__ import annotations







import re



from dataclasses import dataclass











@dataclass(frozen=True)



class ParsedCommand:



    action: str



    args: tuple[str, ...] = ()











def parse(text: str) -> ParsedCommand | None:



    cleaned = text.strip()



    lower = cleaned.lower()







    quick_commands = {



        "help": "help",



        "what can you do": "help",



        "about": "about",



        "battery": "battery_status",



        "battery status": "battery_status",



        "volume up": "volume_up",



        "volume down": "volume_down",



        "mute": "volume_mute",



        "unmute": "volume_mute",



        "brightness up": "brightness_up",



        "brightness down": "brightness_down",



        "shutdown": "shutdown",



        "restart": "restart",



        "sleep": "sleep",
        "voice status": "voice_status",
        "audio status": "voice_status",
        "mic status": "voice_status",
        "wake word status": "voice_status",



    }



    if lower in quick_commands:



        return ParsedCommand(quick_commands[lower])







    type_context_match = re.match(
        r"^(?:type|dictate|write|insert)(?:\s+text)?\s+(.+?)\s+(?:into|in|on|inside)\s+(?:the\s+)?(.+)$",
        cleaned,
        flags=re.IGNORECASE,
    )
    if type_context_match:
        typed = type_context_match.group(1).strip()
        target = type_context_match.group(2).strip()
        if typed and target:
            target = re.sub(r"^(?:the|a|an|my)\s+", "", target, flags=re.IGNORECASE).strip()
            if typed and target:
                return ParsedCommand("type_text_in_app", (typed, target))

    type_match = re.match(r"^(?:type|dictate|write|insert)(?:\s+text)?\s+(.+)$", cleaned, flags=re.IGNORECASE)
    if type_match:
        typed = type_match.group(1).strip()
        typed = re.sub(
            r"\s+(?:into|in|on|inside)\s+(?:the\s+)?(?:notepad|word|excel|chrome|edge|file manager|file explorer|explorer|document|sheet|spreadsheet|window|app|application)$",
            "",
            typed,
            flags=re.IGNORECASE,
        ).strip()
        if typed:
            return ParsedCommand("type_text", (typed,))
    if lower.startswith("open "):



        target = cleaned[5:].strip()



        if target.startswith("http://") or target.startswith("https://"):



            return ParsedCommand("open_url", (target,))



        return ParsedCommand("open_app", (target,))







    patterns = [



        (r"^copy (.+?) to (.+)$", "copy_path"),



        (r"^move (.+?) to (.+)$", "move_path"),



        (r"^rename (.+?) to (.+)$", "rename_path"),



        (r"^delete (.+)$", "delete_path"),



        (r"^search (.+?) in (.+)$", "search_files"),



        (r"^list files(?: in (.+))?$", "list_files"),



        (r"^(?:make|create) folder (.+)$", "create_folder"),



        (r"^create file (.+?) with (.+)$", "create_file"),



        (r"^read file (.+?)(?: aloud)?$", "read_file"),



        (r"^(?:type|dictate|write|insert)(?:\s+text)?\s+(.+?)\s+(?:into|in|on|inside)\s+(?:the\s+)?(.+)$", "type_text_in_app"),
        (r"^(?:type|dictate|write|insert)(?:\s+text)?\s+(.+)$", "type_text"),

        (r"^volume up$", "volume_up"),



        (r"^volume down$", "volume_down"),



        (r"^mute$", "volume_mute"),



        (r"^unmute$", "volume_mute"),



        (r"^brightness up$", "brightness_up"),



        (r"^brightness down$", "brightness_down"),



        (r"^battery status$", "battery_status"),



        (r"^shutdown$", "shutdown"),



        (r"^restart$", "restart"),



        (r"^sleep$", "sleep"),



    ]



    for pattern, action in patterns:



        match = re.match(pattern, cleaned, flags=re.IGNORECASE)



        if match:



            args = tuple(part.strip() if part is not None else "" for part in match.groups())

            return ParsedCommand(action, args)







    return None






