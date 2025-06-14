"""
Test Intent Classification Model
Script to test and validate the trained intent classifier
"""
import sys

sys.path.append('src')

from training.intent_classifier import IntentClassifier


def test_basic_predictions():
    """Test basic intent predictions"""
    print("=== Basic Intent Predictions ===")

    # Load trained model
    classifier = IntentClassifier()

    try:
        classifier.load_model()
        print("✓ Model loaded successfully")
    except FileNotFoundError:
        print("✗ Model not found. Train model first with: python scripts/train_intent_model.py")
        return False

    # Test commands for each intent
    test_cases = {
        "NEXT_PAGE": [
            "next page",
            "go forward",
            "turn the page",
            "advance page",
            "continue to next",
            "move to next page"
        ],
        "PREV_PAGE": [
            "previous page",
            "go back",
            "back one page",
            "return to previous",
            "move backward",
            "step back"
        ],
        "GOTO_PAGE": [
            "go to page 5",
            "page 10",
            "jump to page 3",
            "show page 7",
            "navigate to page 15",
            "take me to page 2"
        ],
        "ZOOM_IN": [
            "zoom in",
            "make bigger",
            "enlarge view",
            "magnify this",
            "increase zoom",
            "bigger view"
        ],
        "ZOOM_OUT": [
            "zoom out",
            "make smaller",
            "shrink view",
            "reduce zoom",
            "smaller view",
            "decrease magnification"
        ],
        "SET_ZOOM": [
            "zoom to 90%",
            "set zoom 150%",
            "magnify to 200%",
            "scale to 75%",
            "zoom level 50%",
            "set magnification to 125%"
        ]
    }

    correct_predictions = 0
    total_predictions = 0
    errors = []

    for expected_intent, commands in test_cases.items():
        print(f"\n--- Testing {expected_intent} ---")

        for command in commands:
            predicted_intent, confidence = classifier.predict(command)
            total_predictions += 1

            if predicted_intent == expected_intent:
                correct_predictions += 1
                status = "✓"
            else:
                errors.append({
                    'command': command,
                    'expected': expected_intent,
                    'predicted': predicted_intent,
                    'confidence': confidence
                })
                status = "✗"

            print(f"  {status} '{command}' → {predicted_intent} ({confidence:.2f})")

    accuracy = correct_predictions / total_predictions
    print(f"\n=== Test Results ===")
    print(f"Accuracy: {accuracy:.1%} ({correct_predictions}/{total_predictions})")

    if errors:
        print(f"\n=== Errors ({len(errors)}) ===")
        for error in errors:
            print(f"'{error['command']}'")
            print(f"  Expected: {error['expected']}")
            print(f"  Got: {error['predicted']} ({error['confidence']:.2f})")

    return accuracy > 0.9


def test_edge_cases():
    """Test edge cases and challenging inputs"""
    print("\n=== Edge Case Testing ===")

    classifier = IntentClassifier()
    classifier.load_model()

    edge_cases = [
        # Typos and variations
        ("nxt page", "Should handle typos"),
        ("go forwrd", "Should handle misspellings"),
        ("zoom inn", "Should handle typos in zoom"),

        # Very short commands
        ("next", "Very short command"),
        ("back", "Very short command"),
        ("zoom", "Ambiguous zoom command"),

        # Conversational
        ("can you go to the next page please", "Polite conversational"),
        ("i want to zoom in", "Natural language"),
        ("let me see page 5", "Casual phrasing"),

        # Numbers written out
        ("go to page five", "Written number"),
        ("zoom to ninety percent", "Written percentage"),

        # Unusual phrasing
        ("advance to the following page", "Formal language"),
        ("make the document larger", "Alternative phrasing"),
        ("navigate backwards", "Different terminology"),

        # Ambiguous cases
        ("make it bigger", "Could be zoom in"),
        ("go forward", "Could be navigation"),
        ("show me more", "Vague command")
    ]

    print("Testing challenging inputs...")

    for command, description in edge_cases:
        intent, confidence = classifier.predict(command)

        # Color code by confidence
        if confidence > 0.8:
            conf_symbol = "🟢"  # High confidence
        elif confidence > 0.6:
            conf_symbol = "🟡"  # Medium confidence
        else:
            conf_symbol = "🔴"  # Low confidence

        print(f"{conf_symbol} '{command}' → {intent} ({confidence:.2f}) - {description}")


def test_probability_distributions():
    """Test probability distributions for ambiguous commands"""
    print("\n=== Probability Distribution Analysis ===")

    classifier = IntentClassifier()
    classifier.load_model()

    ambiguous_commands = [
        "go forward",  # Could be NEXT_PAGE
        "make bigger",  # Could be ZOOM_IN
        "page",  # Could be GOTO_PAGE or NEXT_PAGE
        "zoom",  # Could be any zoom intent
        "back"  # Could be PREV_PAGE
    ]

    for command in ambiguous_commands:
        print(f"\n'{command}':")
        probabilities = classifier.get_intent_probabilities(command)

        # Sort by probability (highest first)
        sorted_probs = sorted(probabilities.items(), key=lambda x: x[1], reverse=True)

        for intent, prob in sorted_probs:
            bar_length = int(prob * 20)  # Scale to 20 characters
            bar = "█" * bar_length + "░" * (20 - bar_length)
            print(f"  {intent:12} {bar} {prob:.3f}")


def test_batch_predictions():
    """Test batch prediction functionality"""
    print("\n=== Batch Prediction Test ===")

    classifier = IntentClassifier()
    classifier.load_model()

    batch_commands = [
        "next page",
        "zoom in",
        "go to page 10",
        "previous page",
        "make smaller",
        "set zoom to 150%"
    ]

    print("Testing batch predictions...")
    results = classifier.predict_batch(batch_commands)

    for i, (command, (intent, confidence)) in enumerate(zip(batch_commands, results)):
        print(f"{i + 1}. '{command}' → {intent} ({confidence:.2f})")


def interactive_test():
    """Interactive testing - user can type commands"""
    print("\n=== Interactive Testing ===")
    print("Type voice commands to test classification (or 'quit' to exit)")

    classifier = IntentClassifier()
    classifier.load_model()

    while True:
        try:
            user_input = input("\nEnter command: ").strip()

            if user_input.lower() in ['quit', 'exit', 'q']:
                print("Goodbye!")
                break

            if not user_input:
                continue

            intent, confidence = classifier.predict(user_input)

            # Show prediction
            print(f"Intent: {intent}")
            print(f"Confidence: {confidence:.2f}")

            # Show top 3 probabilities
            probabilities = classifier.get_intent_probabilities(user_input)
            sorted_probs = sorted(probabilities.items(), key=lambda x: x[1], reverse=True)[:3]

            print("Top 3 possibilities:")
            for i, (intent_name, prob) in enumerate(sorted_probs, 1):
                print(f"  {i}. {intent_name}: {prob:.3f}")

        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except Exception as e:
            print(f"Error: {e}")


def main():
    """Run all tests"""
    print("=== PDF Voice Editor - Intent Classifier Testing ===")

    # Test basic predictions
    basic_success = test_basic_predictions()

    if basic_success:
        print("\n✓ Basic tests passed!")

        # Run additional tests
        test_edge_cases()
        test_probability_distributions()
        test_batch_predictions()

        # Offer interactive testing
        print("\n" + "=" * 50)
        response = input("Run interactive testing? (y/n): ").strip().lower()
        if response in ['y', 'yes']:
            interactive_test()

        print(f"\n=== Summary ===")
        print("✓ Intent classifier is working correctly")
        print("✓ Ready for voice recognition integration")
        print("✓ Next step: Create voice handler and PDF viewer")

    else:
        print("\n✗ Basic tests failed!")
        print("Check training data and retrain model")
        print("Run: python scripts/train_intent_model.py")


if __name__ == "__main__":
    main()