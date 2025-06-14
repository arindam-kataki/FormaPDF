"""
Verify that training data files load correctly
"""
from pathlib import Path
import sys

# Add src to path so we can import our modules
sys.path.append('src')


def verify_training_data():
    """Test loading training data from JSON files"""

    # Check if TrainingDataManager exists
    try:
        from training.training_data import TrainingDataManager
        print("✓ TrainingDataManager imported successfully")
    except ImportError as e:
        print(f"✗ Error importing TrainingDataManager: {e}")
        print("Create src/training/training_data.py first!")
        return False

    # Check if training data files exist
    data_dir = Path("data/training")
    if not data_dir.exists():
        print(f"✗ Training data directory not found: {data_dir}")
        return False

    expected_files = [
        "next_page_commands.json",
        "prev_page_commands.json",
        "goto_page_commands.json",
        "zoom_in_commands.json",
        "zoom_out_commands.json",
        "set_zoom_commands.json"
    ]

    missing_files = []
    for filename in expected_files:
        if not (data_dir / filename).exists():
            missing_files.append(filename)

    if missing_files:
        print(f"✗ Missing training files: {missing_files}")
        return False

    print("✓ All training data files found")

    # Test loading data
    try:
        manager = TrainingDataManager("data/training")
        print("✓ TrainingDataManager created successfully")

        # Load all training data
        all_data = manager.load_training_data_split()
        print(f"✓ Loaded training data for {len(all_data)} intents:")

        total_examples = 0
        for intent, examples in all_data.items():
            print(f"    {intent}: {len(examples)} examples")
            total_examples += len(examples)

        print(f"✓ Total training examples: {total_examples}")

        # Test loading specific intent
        if "ZOOM_IN" in all_data:
            zoom_examples = manager.load_intent_incrementally("ZOOM_IN", max_examples=3)
            print(f"✓ Sample ZOOM_IN examples:")
            for i, example in enumerate(zoom_examples, 1):
                print(f"      {i}. {example}")

        print("\n🎉 All tests passed! Training data is ready to use.")
        return True

    except Exception as e:
        print(f"✗ Error loading training data: {e}")
        return False


def main():
    print("=== Training Data Verification ===")
    success = verify_training_data()

    if success:
        print("\n=== Next Steps ===")
        print("1. Training data is loading correctly")
        print("2. Create intent classifier: src/training/intent_classifier.py")
        print("3. Train your first ML model!")
    else:
        print("\n=== Fix Required ===")
        print("1. Create src/training/training_data.py with TrainingDataManager")
        print("2. Ensure all training JSON files exist")
        print("3. Run this script again")


if __name__ == "__main__":
    main()