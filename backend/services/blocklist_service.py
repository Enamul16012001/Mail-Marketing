import re
import json
from typing import List, Dict, Optional

from database import get_database


class BlocklistService:
    """Manages sender filtering / blocklist rules."""

    DEFAULT_RULES = [
        {"type": "regex", "value": r"^noreply@", "label": "noreply addresses"},
        {"type": "regex", "value": r"^no-reply@", "label": "no-reply addresses"},
        {"type": "regex", "value": r"^mailer-daemon@", "label": "mailer daemon"},
        {"type": "regex", "value": r"^postmaster@", "label": "postmaster"},
        {"type": "domain", "value": "@newsletter.", "label": "newsletter domains"},
    ]

    SETTING_KEY = "sender_blocklist"

    def __init__(self):
        self.db = get_database()
        self._cache: Optional[List[Dict]] = None

    def _load_rules(self) -> List[Dict]:
        raw = self.db.get_setting(self.SETTING_KEY)
        if raw:
            return json.loads(raw)
        # First time: initialize with defaults
        self._save_rules(self.DEFAULT_RULES)
        return list(self.DEFAULT_RULES)

    def _save_rules(self, rules: List[Dict]):
        self.db.set_setting(self.SETTING_KEY, json.dumps(rules))
        self._cache = None

    def get_rules(self) -> List[Dict]:
        if self._cache is None:
            self._cache = self._load_rules()
        return self._cache

    def add_rule(self, rule_type: str, value: str, label: str = "") -> List[Dict]:
        rules = self._load_rules()
        rules.append({"type": rule_type, "value": value, "label": label})
        self._save_rules(rules)
        return self.get_rules()

    def remove_rule(self, index: int) -> List[Dict]:
        rules = self._load_rules()
        if 0 <= index < len(rules):
            rules.pop(index)
            self._save_rules(rules)
        return self.get_rules()

    def should_block(self, sender_email: str) -> bool:
        """Check if sender should be blocked."""
        sender_lower = sender_email.lower().strip()
        for rule in self.get_rules():
            try:
                if rule["type"] == "exact" and sender_lower == rule["value"].lower():
                    return True
                elif rule["type"] == "domain" and sender_lower.endswith(rule["value"].lower()):
                    return True
                elif rule["type"] == "regex":
                    if re.search(rule["value"], sender_lower, re.IGNORECASE):
                        return True
            except re.error:
                continue
        return False


# Singleton
_blocklist_service: Optional[BlocklistService] = None


def get_blocklist_service() -> BlocklistService:
    global _blocklist_service
    if _blocklist_service is None:
        _blocklist_service = BlocklistService()
    return _blocklist_service
