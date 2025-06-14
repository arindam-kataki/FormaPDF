"""
Train Intent Classification Model
Script to train and save the intent classifier
"""
import sys

sys.path.append('src')

from training.intent_classifier import IntentClassifier


def main():
    print("=== PDF Voice Editor - Intent Model Training ===")

    # Create classifier
    classifier = IntentClassifier()

    # Train model
    print("Starting training...")
    stats = classifier.train()

    # Save trained model
    model_path = classifier.save_model()

    print(f"\n🎉 Training Complete!")
    print(f"Model saved to: {model_path}")
    print(f"Test accuracy: {stats['test_accuracy']:.1%}")
    print(f"Cross-validation: {stats['cv_mean']:.1%} (+/- {stats['cv_std'] * 2:.1%})")

    # Test with sample commands
    test_commands = [
        "go to the next page",
        "zoom in please",
        "set zoom to 90 percent",
        "previous page",
        "make it bigger",
        "page 5",
        "turn the page",
        "magnify this",
        "zoom out",
        "go back"
    ]

    print(f"\n=== Sample Predictions ===")
    for command in test_commands:
        intent, confidence = classifier.predict(command)
        print(f"'{command}' → {intent} ({confidence:.2f})")

    # Show feature importance
    print(f"\n=== Top Features per Intent ===")
    try:
        feature_importance = classifier.get_feature_importance(top_n=5)
        for intent, features in feature_importance.items():
            print(f"\n{intent}:")
            for feature, weight in features:
                print(f"  {feature}: {weight:.3f}")
    except Exception as e:
        print(f"Could not show feature importance: {e}")

    print(f"\n=== Next Steps ===")
    print("1. ✓ Intent classifier trained successfully")
    print("2. Test predictions with: scripts/test_intent_model.py")
    print("3. Create voice recognition integration")
    print("4. Build PDF viewer with voice controls")


if __name__ == "__main__":
    main()