"""
Intent Classifier for PDF Voice Editor
Trains ML model to classify voice commands into intents
Uses TF-IDF + SVM for robust text classification
"""

import os
import joblib
import numpy as np
import pandas as pd
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Optional

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.svm import SVC
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score
from sklearn.pipeline import Pipeline

# Import our training data manager
from training_data import TrainingDataManager


class IntentClassifier:
    """
    ML-based intent classifier for voice commands
    Supports training, prediction, and model persistence
    """

    def __init__(self, data_dir: str = "data/training", models_dir: str = "data/models"):
        self.data_dir = data_dir
        self.models_dir = Path(models_dir)
        self.models_dir.mkdir(parents=True, exist_ok=True)

        # Initialize components
        self.data_manager = TrainingDataManager(data_dir)
        self.pipeline = None
        self.is_trained = False
        self.intent_labels = []
        self.training_stats = {}

        # Model configuration
        self.model_config = {
            'vectorizer': {
                'ngram_range': (1, 2),
                'max_features': 500,
                'min_df': 2,
                'max_df': 0.8,
                'sublinear_tf': True,
                'lowercase': True,
                'stop_words': None  # Keep stop words for command parsing
            },
            'classifier': {
                'kernel': 'linear',
                'probability': True,
                'C': 1.0,
                'random_state': 42
            }
        }

    def load_training_data(self) -> Tuple[List[str], List[str]]:
        """Load and prepare training data for sklearn"""
        print("Loading training data...")

        # Load data using TrainingDataManager
        training_by_intent = self.data_manager.load_training_data_split()

        if not training_by_intent:
            raise ValueError("No training data found. Run create_training_data.py first.")

        # Convert to lists for sklearn
        texts = []
        labels = []

        for intent, examples in training_by_intent.items():
            for example in examples:
                texts.append(self._preprocess_text(example))
                labels.append(intent)

        self.intent_labels = list(set(labels))

        print(f"Loaded {len(texts)} training examples across {len(self.intent_labels)} intents:")
        for intent in self.intent_labels:
            count = labels.count(intent)
            print(f"  {intent}: {count} examples")

        return texts, labels

    def _preprocess_text(self, text: str) -> str:
        """Preprocess text for better classification"""
        # Convert to lowercase
        text = text.lower().strip()

        # Remove extra whitespace
        text = ' '.join(text.split())

        # Optional: normalize numbers (uncomment if needed)
        # import re
        # text = re.sub(r'\d+', 'NUMBER', text)

        return text

    def train(self, test_size: float = 0.2, cv_folds: int = 5) -> Dict:
        """
        Train the intent classification model

        Args:
            test_size: Fraction of data to use for testing
            cv_folds: Number of cross-validation folds

        Returns:
            Dictionary with training statistics
        """
        print("=== Training Intent Classifier ===")

        # Load training data
        texts, labels = self.load_training_data()

        # Split into train/test sets
        X_train, X_test, y_train, y_test = train_test_split(
            texts, labels,
            test_size=test_size,
            random_state=42,
            stratify=labels  # Ensure balanced split
        )

        print(f"Training set: {len(X_train)} examples")
        print(f"Test set: {len(X_test)} examples")

        # Create ML pipeline
        self.pipeline = Pipeline([
            ('tfidf', TfidfVectorizer(**self.model_config['vectorizer'])),
            ('classifier', SVC(**self.model_config['classifier']))
        ])

        # Train the model
        print("Training TF-IDF vectorizer and SVM classifier...")
        self.pipeline.fit(X_train, y_train)

        # Evaluate performance
        print("Evaluating model performance...")

        # Test set accuracy
        test_predictions = self.pipeline.predict(X_test)
        test_accuracy = accuracy_score(y_test, test_predictions)

        # Cross-validation score
        cv_scores = cross_val_score(self.pipeline, texts, labels, cv=cv_folds)
        cv_mean = cv_scores.mean()
        cv_std = cv_scores.std()

        # Detailed classification report
        class_report = classification_report(y_test, test_predictions, output_dict=True)

        # Store training statistics
        self.training_stats = {
            'test_accuracy': test_accuracy,
            'cv_mean': cv_mean,
            'cv_std': cv_std,
            'total_examples': len(texts),
            'train_examples': len(X_train),
            'test_examples': len(X_test),
            'num_intents': len(self.intent_labels),
            'intents': self.intent_labels,
            'trained_at': datetime.now().isoformat(),
            'classification_report': class_report
        }

        self.is_trained = True

        # Print results
        print(f"\n=== Training Results ===")
        print(f"Test Accuracy: {test_accuracy:.3f}")
        print(f"Cross-validation: {cv_mean:.3f} (+/- {cv_std * 2:.3f})")
        print(f"\nClassification Report:")
        print(classification_report(y_test, test_predictions))

        # Show confusion matrix
        print("Confusion Matrix:")
        cm = confusion_matrix(y_test, test_predictions, labels=self.intent_labels)
        self._print_confusion_matrix(cm, self.intent_labels)

        return self.training_stats

    def _print_confusion_matrix(self, cm: np.ndarray, labels: List[str]):
        """Print confusion matrix in readable format"""
        print("\nPredicted →")
        print("Actual ↓   ", end="")
        for label in labels:
            print(f"{label[:8]:>8}", end="")
        print()

        for i, actual_label in enumerate(labels):
            print(f"{actual_label[:10]:10}", end="")
            for j in range(len(labels)):
                print(f"{cm[i][j]:8}", end="")
            print()

    def predict(self, text: str) -> Tuple[str, float]:
        """
        Predict intent for a single text input

        Args:
            text: Input text to classify

        Returns:
            Tuple of (predicted_intent, confidence)
        """
        if not self.is_trained:
            raise ValueError("Model not trained. Call train() first.")

        # Preprocess text
        processed_text = self._preprocess_text(text)

        # Get prediction and probability
        prediction = self.pipeline.predict([processed_text])[0]
        probabilities = self.pipeline.predict_proba([processed_text])[0]
        confidence = max(probabilities)

        return prediction, confidence

    def predict_batch(self, texts: List[str]) -> List[Tuple[str, float]]:
        """
        Predict intents for multiple texts

        Args:
            texts: List of input texts

        Returns:
            List of (intent, confidence) tuples
        """
        if not self.is_trained:
            raise ValueError("Model not trained. Call train() first.")

        # Preprocess all texts
        processed_texts = [self._preprocess_text(text) for text in texts]

        # Get predictions and probabilities
        predictions = self.pipeline.predict(processed_texts)
        probabilities = self.pipeline.predict_proba(processed_texts)
        confidences = [max(probs) for probs in probabilities]

        return list(zip(predictions, confidences))

    def get_intent_probabilities(self, text: str) -> Dict[str, float]:
        """
        Get probability scores for all intents

        Args:
            text: Input text to analyze

        Returns:
            Dictionary mapping intent names to probabilities
        """
        if not self.is_trained:
            raise ValueError("Model not trained. Call train() first.")

        processed_text = self._preprocess_text(text)
        probabilities = self.pipeline.predict_proba([processed_text])[0]

        # Get class labels from the classifier
        class_labels = self.pipeline.named_steps['classifier'].classes_

        return dict(zip(class_labels, probabilities))

    def save_model(self, filename: str = "intent_classifier.pkl"):
        """Save trained model to disk"""
        if not self.is_trained:
            raise ValueError("No trained model to save. Call train() first.")

        model_path = self.models_dir / filename

        # Create model data
        model_data = {
            'pipeline': self.pipeline,
            'intent_labels': self.intent_labels,
            'training_stats': self.training_stats,
            'model_config': self.model_config,
            'is_trained': self.is_trained
        }

        # Save to disk
        joblib.dump(model_data, model_path)
        print(f"Model saved to: {model_path}")

        return model_path

    def load_model(self, filename: str = "intent_classifier.pkl"):
        """Load trained model from disk"""
        model_path = self.models_dir / filename

        if not model_path.exists():
            raise FileNotFoundError(f"Model file not found: {model_path}")

        # Load model data
        model_data = joblib.load(model_path)

        # Restore model state
        self.pipeline = model_data['pipeline']
        self.intent_labels = model_data['intent_labels']
        self.training_stats = model_data.get('training_stats', {})
        self.model_config = model_data.get('model_config', self.model_config)
        self.is_trained = model_data.get('is_trained', True)

        print(f"Model loaded from: {model_path}")
        print(f"Intents: {self.intent_labels}")

        if 'test_accuracy' in self.training_stats:
            print(f"Model accuracy: {self.training_stats['test_accuracy']:.3f}")

    def evaluate_on_examples(self, test_examples: Dict[str, List[str]]) -> Dict:
        """
        Evaluate model on custom test examples

        Args:
            test_examples: Dict mapping intent names to example texts

        Returns:
            Evaluation results
        """
        if not self.is_trained:
            raise ValueError("Model not trained. Call train() first.")

        results = {
            'correct': 0,
            'total': 0,
            'per_intent': {},
            'errors': []
        }

        for true_intent, examples in test_examples.items():
            intent_correct = 0
            intent_total = len(examples)

            for example in examples:
                predicted_intent, confidence = self.predict(example)

                if predicted_intent == true_intent:
                    intent_correct += 1
                    results['correct'] += 1
                else:
                    results['errors'].append({
                        'text': example,
                        'true_intent': true_intent,
                        'predicted_intent': predicted_intent,
                        'confidence': confidence
                    })

                results['total'] += 1

            results['per_intent'][true_intent] = {
                'correct': intent_correct,
                'total': intent_total,
                'accuracy': intent_correct / intent_total if intent_total > 0 else 0
            }

        results['overall_accuracy'] = results['correct'] / results['total'] if results['total'] > 0 else 0

        return results

    def get_feature_importance(self, top_n: int = 10) -> Dict[str, List[Tuple[str, float]]]:
        """
        Get most important features (words/phrases) for each intent

        Args:
            top_n: Number of top features to return per intent

        Returns:
            Dictionary mapping intent names to list of (feature, importance) tuples
        """
        if not self.is_trained:
            raise ValueError("Model not trained. Call train() first.")

        # Get feature names from TF-IDF vectorizer
        vectorizer = self.pipeline.named_steps['tfidf']
        classifier = self.pipeline.named_steps['classifier']
        feature_names = vectorizer.get_feature_names_out()

        # Get feature weights for each class
        intent_features = {}

        for i, intent in enumerate(classifier.classes_):
            # Get coefficients for this class
            if hasattr(classifier, 'coef_'):
                coefficients = classifier.coef_[i]

                # Get top positive features (most important for this class)
                top_indices = coefficients.argsort()[-top_n:][::-1]
                top_features = [(feature_names[idx], coefficients[idx]) for idx in top_indices]

                intent_features[intent] = top_features

        return intent_features


def create_training_script():
    """Helper function to create a training script"""
    script_content = '''
"""
Train Intent Classification Model
"""
import sys
sys.path.append('src')

from training.intent_classifier import IntentClassifier

def main():
    # Create and train classifier
    classifier = IntentClassifier()

    # Train model
    stats = classifier.train()

    # Save trained model
    model_path = classifier.save_model()

    print(f"\\n=== Training Complete ===")
    print(f"Model saved to: {model_path}")
    print(f"Test accuracy: {stats['test_accuracy']:.3f}")

    # Test with sample commands
    test_commands = [
        "go to the next page",
        "zoom in please", 
        "set zoom to 90%",
        "previous page",
        "make it bigger",
        "page 5"
    ]

    print(f"\\n=== Sample Predictions ===")
    for command in test_commands:
        intent, confidence = classifier.predict(command)
        print(f"'{command}' → {intent} ({confidence:.2f})")

if __name__ == "__main__":
    main()
'''

    return script_content


# Example usage and testing
if __name__ == "__main__":
    # This code runs when script is executed directly
    print("Intent Classifier Module")
    print("Import this module and create IntentClassifier() to use")
    print("\nExample usage:")
    print("classifier = IntentClassifier()")
    print("classifier.train()")
    print("intent, conf = classifier.predict('next page')")