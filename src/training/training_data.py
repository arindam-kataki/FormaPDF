"""
Training Data Manager for PDF Voice Editor
Supports file-based storage and incremental loading of training data
"""

import json
import csv
import os
import glob
from datetime import datetime
from typing import Dict, List, Tuple, Optional
from pathlib import Path


class TrainingDataManager:
    """Manages training data loading, saving, and incremental updates"""

    def __init__(self, data_dir: str = "data/training"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.training_data = {}
        self.metadata = {}

    # METHOD 1: JSON-based storage (recommended)

    def save_training_data_json(self, training_by_intent: Dict[str, List[str]],
                                filename: str = "voice_commands.json"):
        """Save training data to single JSON file"""
        filepath = self.data_dir / filename

        data = {
            "metadata": {
                "version": "1.0",
                "created": datetime.now().isoformat(),
                "total_examples": sum(len(examples) for examples in training_by_intent.values()),
                "intents": list(training_by_intent.keys()),
                "intent_counts": {intent: len(examples) for intent, examples in training_by_intent.items()}
            },
            "training_data": training_by_intent
        }

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        print(f"Training data saved to {filepath}")
        return filepath

    def load_training_data_json(self, filename: str = "voice_commands.json") -> Dict[str, List[str]]:
        """Load training data from single JSON file"""
        filepath = self.data_dir / filename

        if not filepath.exists():
            print(f"Training data file not found: {filepath}")
            return {}

        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)

        self.metadata = data.get("metadata", {})
        training_data = data.get("training_data", {})

        print(f"Loaded {self.metadata.get('total_examples', 0)} examples from {filepath}")
        return training_data

    # METHOD 2: Multiple JSON files (better for incremental loading)

    def save_training_data_split(self, training_by_intent: Dict[str, List[str]]):
        """Save each intent to separate JSON file"""
        for intent, examples in training_by_intent.items():
            filename = f"{intent.lower()}_commands.json"
            filepath = self.data_dir / filename

            intent_data = {
                "intent": intent,
                "examples": examples,
                "count": len(examples),
                "last_updated": datetime.now().isoformat()
            }

            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(intent_data, f, indent=2, ensure_ascii=False)

        # Save metadata
        self._save_metadata(training_by_intent)
        print(f"Training data split into {len(training_by_intent)} files")

    def load_training_data_split(self, intents: Optional[List[str]] = None) -> Dict[str, List[str]]:
        """Load training data from multiple JSON files"""
        training_data = {}

        # Get all intent files if no specific intents requested
        if intents is None:
            pattern = str(self.data_dir / "*_commands.json")
            intent_files = glob.glob(pattern)
        else:
            intent_files = [str(self.data_dir / f"{intent.lower()}_commands.json")
                            for intent in intents]

        for filepath in intent_files:
            if os.path.exists(filepath):
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                intent = data.get("intent")
                examples = data.get("examples", [])
                training_data[intent] = examples
                print(f"Loaded {len(examples)} examples for {intent}")

        return training_data

    # METHOD 3: Incremental loading

    def add_training_examples(self, intent: str, new_examples: List[str],
                              save_immediately: bool = True):
        """Add new training examples to existing intent"""
        filename = f"{intent.lower()}_commands.json"
        filepath = self.data_dir / filename

        # Load existing data
        existing_examples = []
        if filepath.exists():
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                existing_examples = data.get("examples", [])

        # Add new examples (avoid duplicates)
        existing_set = set(existing_examples)
        unique_new = [ex for ex in new_examples if ex not in existing_set]
        all_examples = existing_examples + unique_new

        if save_immediately:
            intent_data = {
                "intent": intent,
                "examples": all_examples,
                "count": len(all_examples),
                "last_updated": datetime.now().isoformat()
            }

            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(intent_data, f, indent=2, ensure_ascii=False)

            print(f"Added {len(unique_new)} new examples to {intent}")

        return all_examples

    def load_intent_incrementally(self, intent: str, max_examples: Optional[int] = None) -> List[str]:
        """Load examples for specific intent with optional limit"""
        filename = f"{intent.lower()}_commands.json"
        filepath = self.data_dir / filename

        if not filepath.exists():
            print(f"No training data found for intent: {intent}")
            return []

        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)

        examples = data.get("examples", [])

        if max_examples and len(examples) > max_examples:
            examples = examples[:max_examples]
            print(f"Loaded {max_examples} examples for {intent} (limited)")
        else:
            print(f"Loaded {len(examples)} examples for {intent}")

        return examples

    # METHOD 4: CSV support (for non-programmers)

    def save_training_data_csv(self, training_by_intent: Dict[str, List[str]],
                               filename: str = "voice_commands.csv"):
        """Save training data to CSV file"""
        filepath = self.data_dir / filename

        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['command', 'intent'])  # Header

            for intent, examples in training_by_intent.items():
                for example in examples:
                    writer.writerow([example, intent])

        print(f"Training data saved to CSV: {filepath}")

    def load_training_data_csv(self, filename: str = "voice_commands.csv") -> Dict[str, List[str]]:
        """Load training data from CSV file"""
        filepath = self.data_dir / filename

        if not filepath.exists():
            print(f"CSV file not found: {filepath}")
            return {}

        training_data = {}

        with open(filepath, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                command = row['command'].strip()
                intent = row['intent'].strip()

                if intent not in training_data:
                    training_data[intent] = []
                training_data[intent].append(command)

        print(f"Loaded training data from CSV: {filepath}")
        return training_data

    # UTILITY METHODS

    def _save_metadata(self, training_by_intent: Dict[str, List[str]]):
        """Save metadata about training data"""
        metadata = {
            "version": "1.0",
            "last_updated": datetime.now().isoformat(),
            "total_examples": sum(len(examples) for examples in training_by_intent.values()),
            "intents": list(training_by_intent.keys()),
            "intent_counts": {intent: len(examples) for intent, examples in training_by_intent.items()}
        }

        metadata_path = self.data_dir / "metadata.json"
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2)

    def get_training_stats(self) -> Dict:
        """Get statistics about current training data"""
        metadata_path = self.data_dir / "metadata.json"

        if metadata_path.exists():
            with open(metadata_path, 'r', encoding='utf-8') as f:
                return json.load(f)

        # Calculate stats from files
        training_data = self.load_training_data_split()
        return {
            "total_examples": sum(len(examples) for examples in training_data.values()),
            "intents": list(training_data.keys()),
            "intent_counts": {intent: len(examples) for intent, examples in training_data.items()}
        }

    def validate_training_data(self, training_data: Dict[str, List[str]]) -> Dict:
        """Validate training data quality"""
        issues = {
            "duplicates": {},
            "empty_intents": [],
            "short_commands": {},
            "similar_commands": {}
        }

        for intent, examples in training_data.items():
            if not examples:
                issues["empty_intents"].append(intent)
                continue

            # Check for duplicates
            unique_examples = set(examples)
            if len(unique_examples) < len(examples):
                issues["duplicates"][intent] = len(examples) - len(unique_examples)

            # Check for very short commands
            short_commands = [ex for ex in examples if len(ex.split()) < 2]
            if short_commands:
                issues["short_commands"][intent] = short_commands

        return issues


# USAGE EXAMPLES

def example_usage():
    """Demonstrate how to use the TrainingDataManager"""

    # Initialize manager
    manager = TrainingDataManager("data/training")

    # Example 1: Save training data to multiple files
    training_data = {
        "ZOOM": ["zoom to 90%", "magnify to 150%", "scale to 75%"],
        "PAN": ["move view left", "scroll up", "pan right"],
        "GRID": ["show grid", "hide grid", "toggle grid"]
    }

    manager.save_training_data_split(training_data)

    # Example 2: Load specific intents
    zoom_data = manager.load_training_data_split(["ZOOM"])

    # Example 3: Add new examples incrementally
    new_zoom_examples = ["enlarge to 200%", "shrink to 50%"]
    manager.add_training_examples("ZOOM", new_zoom_examples)

    # Example 4: Load with limits
    limited_examples = manager.load_intent_incrementally("ZOOM", max_examples=5)

    # Example 5: Get statistics
    stats = manager.get_training_stats()
    print(f"Training data stats: {stats}")

    # Example 6: CSV export for editing
    all_data = manager.load_training_data_split()
    manager.save_training_data_csv(all_data)


if __name__ == "__main__":
    example_usage()