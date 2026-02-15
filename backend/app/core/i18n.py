import os
import json
from typing import Dict, Any, Optional

class TranslationManager:
    """
    Manages multi-language support for the Studio UI and System.
    Loads JSON localization files and provides translation lookups.
    """
    _locales: Dict[str, Dict[str, str]] = {}
    _default_locale = "en"

    @classmethod
    def load_locales(cls):
        """Loads all available .json files from the locales directory."""
        locales_dir = os.path.join(os.path.dirname(__file__), "..", "..", "locales")
        if not os.path.exists(locales_dir):
            os.makedirs(locales_dir, exist_ok=True)
            # Create default EN file if missing
            default_en = {
                "welcome": "Welcome to Studio",
                "workflow_started": "Workflow execution started",
                "workflow_completed": "Workflow completed successfully",
                "node_error": "Error in node {node_id}: {error}",
                "scheduled_task": "Scheduled Execution"
            }
            with open(os.path.join(locales_dir, "en.json"), "w") as f:
                json.dump(default_en, f, indent=2)

        for filename in os.listdir(locales_dir):
            if filename.endswith(".json"):
                locale_code = filename.replace(".json", "")
                with open(os.path.join(locales_dir, filename), "r", encoding="utf-8") as f:
                    cls._locales[locale_code] = json.load(f)

    @classmethod
    def translate(cls, key: str, locale: str = "en", **kwargs) -> str:
        """
        Retrieves a translated string for the given key and locale.
        Supports variable substitution using **kwargs.
        """
        if not cls._locales:
            cls.load_locales()
            
        locale_data = cls._locales.get(locale, cls._locales.get(cls._default_locale, {}))
        text = locale_data.get(key, cls._locales.get(cls._default_locale, {}).get(key, key))
        
        try:
            return text.format(**kwargs)
        except KeyError:
            return text

i18n = TranslationManager()

