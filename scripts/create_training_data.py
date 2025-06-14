"""
Generate separate JSON training data files for PDF Voice Editor
Creates individual files for each intent: {intent_lowercase}_commands.json
"""

import json
import os
from datetime import datetime
from pathlib import Path


def create_all_training_files():
    """Create separate JSON files for each intent"""

    # Create data/training directory if it doesn't exist
    data_dir = Path("data/training")
    data_dir.mkdir(parents=True, exist_ok=True)

    # NEXT_PAGE intent training data
    next_page_data = {
        "intent": "NEXT_PAGE",
        "examples": [
            "next page",
            "go forward",
            "page forward",
            "turn the page",
            "continue",
            "advance page",
            "go to next page",
            "move to next page",
            "forward one page",
            "next",
            "proceed",
            "advance",
            "go ahead",
            "keep going",
            "move forward",
            "page up",
            "turn page",
            "flip page",
            "go on",
            "continue forward",
            "next page please",
            "can you go to the next page",
            "please turn the page",
            "move to the next page",
            "advance to next page",
            "go forward one page",
            "take me to the next page",
            "show me the next page",
            "display next page",
            "forward",
            "onward",
            "proceed to next",
            "go to following page",
            "turn to next page",
            "flip to next page",
            "move ahead",
            "step forward",
            "progress forward",
            "advance one page",
            "next document page",
            "forward in document"
        ],
        "count": 40,
        "last_updated": datetime.now().isoformat()
    }

    # PREV_PAGE intent training data
    prev_page_data = {
        "intent": "PREV_PAGE",
        "examples": [
            "previous page",
            "go back",
            "page back",
            "back one page",
            "return",
            "last page",
            "go to previous page",
            "move to previous page",
            "backward one page",
            "previous",
            "back",
            "retreat",
            "go backward",
            "move back",
            "page down",
            "flip back",
            "go backwards",
            "step back",
            "return to previous",
            "previous page please",
            "can you go back",
            "please go to previous page",
            "move to the previous page",
            "go back one page",
            "take me to the previous page",
            "show me the previous page",
            "display previous page",
            "backward",
            "rewind",
            "go to prior page",
            "prior page",
            "preceding page",
            "flip to previous page",
            "move backward",
            "step backward",
            "regress",
            "backtrack",
            "previous document page",
            "backward in document",
            "reverse one page"
        ],
        "count": 40,
        "last_updated": datetime.now().isoformat()
    }

    # GOTO_PAGE intent training data
    goto_page_data = {
        "intent": "GOTO_PAGE",
        "examples": [
            "go to page 5",
            "page 5",
            "navigate to page 10",
            "jump to page 3",
            "show page 7",
            "page number 2",
            "go to page 1",
            "page 15",
            "jump to page 25",
            "navigate to page 8",
            "show page 12",
            "display page 6",
            "open page 9",
            "view page 4",
            "turn to page 11",
            "flip to page 20",
            "move to page 14",
            "switch to page 18",
            "go to page number 13",
            "take me to page 16",
            "show me page 17",
            "display page number 19",
            "navigate to page number 22",
            "jump to page number 21",
            "go to the first page",
            "go to the last page",
            "page one",
            "page two",
            "page three",
            "page four",
            "page five",
            "first page",
            "last page",
            "final page",
            "beginning page",
            "end page",
            "start page",
            "page ten",
            "page twenty",
            "page fifty"
        ],
        "count": 40,
        "last_updated": datetime.now().isoformat()
    }

    # ZOOM_IN intent training data
    zoom_in_data = {
        "intent": "ZOOM_IN",
        "examples": [
            "zoom in",
            "make bigger",
            "enlarge",
            "magnify",
            "increase zoom",
            "bigger view",
            "zoom up",
            "scale up",
            "make larger",
            "blow up",
            "expand view",
            "increase magnification",
            "make it bigger",
            "zoom closer",
            "get closer",
            "increase size",
            "make text larger",
            "enlarge view",
            "magnify view",
            "zoom in please",
            "can you zoom in",
            "please make it bigger",
            "make this larger",
            "increase the zoom",
            "zoom in a bit",
            "zoom in more",
            "make it much bigger",
            "enlarge this",
            "magnify this",
            "blow this up",
            "scale this up",
            "increase view size",
            "make view bigger",
            "zoom in on this",
            "get a closer look",
            "see it bigger",
            "make font bigger",
            "larger view",
            "bigger magnification",
            "zoom inward"
        ],
        "count": 40,
        "last_updated": datetime.now().isoformat()
    }

    # ZOOM_OUT intent training data
    zoom_out_data = {
        "intent": "ZOOM_OUT",
        "examples": [
            "zoom out",
            "make smaller",
            "shrink",
            "reduce",
            "decrease zoom",
            "smaller view",
            "zoom down",
            "scale down",
            "make tinier",
            "contract view",
            "decrease magnification",
            "make it smaller",
            "zoom further",
            "get further away",
            "decrease size",
            "make text smaller",
            "shrink view",
            "reduce view",
            "zoom out please",
            "can you zoom out",
            "please make it smaller",
            "make this smaller",
            "decrease the zoom",
            "zoom out a bit",
            "zoom out more",
            "make it much smaller",
            "shrink this",
            "reduce this",
            "scale this down",
            "decrease view size",
            "make view smaller",
            "zoom out from this",
            "get a wider view",
            "see more of the page",
            "make font smaller",
            "smaller view",
            "less magnification",
            "zoom outward",
            "pull back",
            "step back",
            "wider perspective"
        ],
        "count": 40,
        "last_updated": datetime.now().isoformat()
    }

    # SET_ZOOM intent training data
    set_zoom_data = {
        "intent": "SET_ZOOM",
        "examples": [
            "zoom to 90%",
            "set zoom 150%",
            "zoom level 75%",
            "magnify to 200%",
            "scale to 50%",
            "zoom 100%",
            "set zoom to 90 percent",
            "zoom to 150 percent",
            "magnification 75%",
            "zoom factor 200%",
            "set magnification to 50%",
            "zoom level 125%",
            "scale to 175%",
            "set zoom level to 80%",
            "zoom to ninety percent",
            "set zoom 0.9",
            "zoom 90",
            "90% zoom",
            "zoom: 90%",
            "make it 90% size",
            "adjust zoom to 90%",
            "resize to 90 percent",
            "zoom factor 90%",
            "set scale 90%",
            "view at 90% size",
            "display at 90%",
            "zoom to fifty percent",
            "set zoom to 50%",
            "magnify to 150%",
            "scale to 200%",
            "zoom level should be 85%",
            "i want 200% magnification",
            "set the zoom to 60 percent please",
            "can you zoom to 90 percent",
            "please set the zoom to 90%",
            "change zoom level to 90",
            "make zoom 90 percent",
            "zoom level 90%",
            "set magnification to 90%",
            "magnify to 90 percent"
        ],
        "count": 40,
        "last_updated": datetime.now().isoformat()
    }

    # Dictionary of all training data
    all_training_data = {
        "next_page_commands.json": next_page_data,
        "prev_page_commands.json": prev_page_data,
        "goto_page_commands.json": goto_page_data,
        "zoom_in_commands.json": zoom_in_data,
        "zoom_out_commands.json": zoom_out_data,
        "set_zoom_commands.json": set_zoom_data
    }

    # Create each JSON file
    created_files = []
    for filename, data in all_training_data.items():
        filepath = data_dir / filename

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        created_files.append(str(filepath))
        print(f"Created: {filepath} ({data['count']} examples)")

    # Create metadata file
    metadata = {
        "version": "1.0",
        "created": datetime.now().isoformat(),
        "total_files": len(all_training_data),
        "total_examples": sum(data["count"] for data in all_training_data.values()),
        "intents": [data["intent"] for data in all_training_data.values()],
        "intent_counts": {data["intent"]: data["count"] for data in all_training_data.values()},
        "files": list(all_training_data.keys())
    }

    metadata_path = data_dir / "metadata.json"
    with open(metadata_path, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)

    created_files.append(str(metadata_path))
    print(f"Created: {metadata_path}")

    return created_files


def validate_training_files():
    """Validate that all training files are properly formatted"""
    data_dir = Path("data/training")

    if not data_dir.exists():
        print("Error: data/training directory does not exist")
        return False

    expected_files = [
        "next_page_commands.json",
        "prev_page_commands.json",
        "goto_page_commands.json",
        "zoom_in_commands.json",
        "zoom_out_commands.json",
        "set_zoom_commands.json",
        "metadata.json"
    ]

    all_valid = True

    for filename in expected_files:
        filepath = data_dir / filename

        if not filepath.exists():
            print(f"Error: Missing file {filepath}")
            all_valid = False
            continue

        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)

            if filename != "metadata.json":
                # Validate training data file structure
                required_keys = ["intent", "examples", "count", "last_updated"]
                for key in required_keys:
                    if key not in data:
                        print(f"Error: {filepath} missing required key: {key}")
                        all_valid = False

                if len(data["examples"]) != data["count"]:
                    print(f"Warning: {filepath} count mismatch: {len(data['examples'])} vs {data['count']}")

            print(f"✓ Valid: {filepath}")

        except json.JSONDecodeError as e:
            print(f"Error: Invalid JSON in {filepath}: {e}")
            all_valid = False
        except Exception as e:
            print(f"Error: Could not read {filepath}: {e}")
            all_valid = False

    return all_valid


def test_training_data_manager():
    """Test loading the created files with TrainingDataManager"""
    try:
        # Import TrainingDataManager (adjust path as needed)
        import sys
        sys.path.append('src')
        from training.training_data import TrainingDataManager

        manager = TrainingDataManager("data/training")

        # Test loading all data
        print("\n=== Testing TrainingDataManager ===")
        all_data = manager.load_training_data_split()

        print(f"Loaded {len(all_data)} intents:")
        for intent, examples in all_data.items():
            print(f"  {intent}: {len(examples)} examples")

        # Test loading specific intent
        zoom_in_data = manager.load_intent_incrementally("ZOOM_IN", max_examples=5)
        print(f"\nSample ZOOM_IN examples (limited to 5):")
        for i, example in enumerate(zoom_in_data, 1):
            print(f"  {i}. {example}")

        # Test statistics
        stats = manager.get_training_stats()
        print(f"\nTraining data statistics:")
        print(f"  Total examples: {stats.get('total_examples', 'N/A')}")
        print(f"  Total intents: {len(stats.get('intents', []))}")

        return True

    except ImportError:
        print("Note: Could not import TrainingDataManager - create it first")
        return False
    except Exception as e:
        print(f"Error testing TrainingDataManager: {e}")
        return False


if __name__ == "__main__":
    print("Creating training data files...")
    created_files = create_all_training_files()

    print(f"\n=== Summary ===")
    print(f"Created {len(created_files)} files in data/training/:")
    for file in created_files:
        print(f"  - {file}")

    print(f"\n=== Validation ===")
    if validate_training_files():
        print("✓ All training files are valid")
    else:
        print("✗ Some training files have errors")

    print(f"\n=== Testing with TrainingDataManager ===")
    test_training_data_manager()

    print(f"\n=== Next Steps ===")
    print("1. Run this script to create the training data files")
    print("2. Create src/training/training_data.py with TrainingDataManager class")
    print("3. Test loading: manager.load_training_data_split()")
    print("4. Use the data to train your intent classification model")