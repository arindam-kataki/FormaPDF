"""
Voice Handler for PDF Voice Editor
Handles speech recognition and voice command capture
Uses SpeechRecognition library with multiple backend support
"""

import speech_recognition as sr
import threading
import time
import queue
from typing import Optional, Callable, Dict, Any
from enum import Enum
import logging


class VoiceState(Enum):
    """Voice handler states"""
    IDLE = "idle"
    LISTENING = "listening"
    PROCESSING = "processing"
    ERROR = "error"


class VoiceHandler:
    """
    Handles voice recognition and speech-to-text conversion
    Supports continuous listening and command detection
    """

    def __init__(self,
                 recognition_engine: str = "google",
                 language: str = "en-US",
                 timeout: float = 5.0,
                 phrase_timeout: float = 0.3,
                 energy_threshold: int = 4000):
        """
        Initialize voice handler

        Args:
            recognition_engine: Speech recognition engine ("google", "sphinx", "azure", etc.)
            language: Language code for recognition
            timeout: Seconds to wait for phrase start
            phrase_timeout: Seconds of silence to end phrase
            energy_threshold: Minimum audio energy to trigger recognition
        """
        self.recognition_engine = recognition_engine
        self.language = language
        self.timeout = timeout
        self.phrase_timeout = phrase_timeout
        self.energy_threshold = energy_threshold

        # Initialize speech recognition components
        self.recognizer = sr.Recognizer()
        self.microphone = None
        self.is_listening = False
        self.state = VoiceState.IDLE

        # Threading components
        self.listen_thread = None
        self.command_queue = queue.Queue()

        # Callback functions
        self.on_command_callback = None
        self.on_error_callback = None
        self.on_state_change_callback = None

        # Statistics
        self.stats = {
            'commands_recognized': 0,
            'recognition_errors': 0,
            'audio_errors': 0,
            'last_command_time': None
        }

        # Configure logging
        self.logger = logging.getLogger(__name__)

        # Initialize microphone
        self._initialize_microphone()

    def _initialize_microphone(self):
        """Initialize and configure microphone"""
        try:
            self.microphone = sr.Microphone()

            # Adjust for ambient noise
            print("Calibrating microphone for ambient noise...")
            with self.microphone as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=1)

            # Set energy threshold
            self.recognizer.energy_threshold = self.energy_threshold
            self.recognizer.timeout = self.timeout
            self.recognizer.phrase_threshold = self.phrase_timeout

            print(f"Microphone initialized. Energy threshold: {self.recognizer.energy_threshold}")

        except Exception as e:
            self.logger.error(f"Failed to initialize microphone: {e}")
            raise RuntimeError(f"Microphone initialization failed: {e}")

    def set_callbacks(self,
                      on_command: Optional[Callable[[str, float], None]] = None,
                      on_error: Optional[Callable[[str], None]] = None,
                      on_state_change: Optional[Callable[[VoiceState], None]] = None):
        """
        Set callback functions for voice events

        Args:
            on_command: Called when command is recognized (text, confidence)
            on_error: Called when error occurs (error_message)
            on_state_change: Called when voice state changes (new_state)
        """
        self.on_command_callback = on_command
        self.on_error_callback = on_error
        self.on_state_change_callback = on_state_change

    def _set_state(self, new_state: VoiceState):
        """Update voice handler state and notify callback"""
        if self.state != new_state:
            self.state = new_state
            if self.on_state_change_callback:
                self.on_state_change_callback(new_state)

    def _recognize_speech(self, audio_data) -> Optional[tuple]:
        """
        Recognize speech from audio data

        Args:
            audio_data: Audio data from microphone

        Returns:
            Tuple of (recognized_text, confidence) or None if failed
        """
        try:
            # Choose recognition engine
            if self.recognition_engine == "google":
                text = self.recognizer.recognize_google(audio_data, language=self.language)
                confidence = 0.9  # Google doesn't provide confidence, estimate high

            elif self.recognition_engine == "sphinx":
                text = self.recognizer.recognize_sphinx(audio_data, language=self.language)
                confidence = 0.7  # Sphinx generally less accurate

            elif self.recognition_engine == "azure":
                # Azure Cognitive Services (requires API key)
                text = self.recognizer.recognize_azure(audio_data,
                                                       language=self.language)
                confidence = 0.9

            else:
                # Default to Google
                text = self.recognizer.recognize_google(audio_data, language=self.language)
                confidence = 0.9

            return text.lower().strip(), confidence

        except sr.UnknownValueError:
            # Could not understand audio
            return None
        except sr.RequestError as e:
            # API request failed
            self.logger.error(f"Recognition service error: {e}")
            if self.on_error_callback:
                self.on_error_callback(f"Recognition service unavailable: {e}")
            return None
        except Exception as e:
            # Other recognition errors
            self.logger.error(f"Recognition error: {e}")
            if self.on_error_callback:
                self.on_error_callback(f"Recognition failed: {e}")
            return None

    def _listen_continuously(self):
        """Continuous listening loop (runs in separate thread)"""
        self.logger.info("Starting continuous listening...")

        while self.is_listening:
            try:
                self._set_state(VoiceState.LISTENING)

                # Listen for audio
                with self.microphone as source:
                    # Wait for audio input
                    audio = self.recognizer.listen(source,
                                                   timeout=self.timeout,
                                                   phrase_time_limit=5)

                if not self.is_listening:
                    break

                self._set_state(VoiceState.PROCESSING)

                # Recognize speech
                result = self._recognize_speech(audio)

                if result:
                    text, confidence = result
                    self.stats['commands_recognized'] += 1
                    self.stats['last_command_time'] = time.time()

                    self.logger.info(f"Recognized command: '{text}' (confidence: {confidence:.2f})")

                    # Add to queue and notify callback
                    self.command_queue.put((text, confidence))
                    if self.on_command_callback:
                        self.on_command_callback(text, confidence)
                else:
                    self.stats['recognition_errors'] += 1

            except sr.WaitTimeoutError:
                # No speech detected, continue listening
                continue
            except Exception as e:
                self.stats['audio_errors'] += 1
                self.logger.error(f"Listening error: {e}")
                self._set_state(VoiceState.ERROR)

                if self.on_error_callback:
                    self.on_error_callback(f"Audio error: {e}")

                # Brief pause before retrying
                time.sleep(1)

        self._set_state(VoiceState.IDLE)
        self.logger.info("Stopped continuous listening")

    def start_listening(self):
        """Start continuous voice recognition"""
        if self.is_listening:
            self.logger.warning("Already listening")
            return

        if not self.microphone:
            raise RuntimeError("Microphone not initialized")

        self.is_listening = True
        self.listen_thread = threading.Thread(target=self._listen_continuously)
        self.listen_thread.daemon = True
        self.listen_thread.start()

        print("🎤 Voice recognition started. Say a command...")

    def stop_listening(self):
        """Stop continuous voice recognition"""
        if not self.is_listening:
            return

        print("🔇 Stopping voice recognition...")
        self.is_listening = False

        if self.listen_thread and self.listen_thread.is_alive():
            self.listen_thread.join(timeout=2)

        self._set_state(VoiceState.IDLE)
        print("Voice recognition stopped")

    def listen_once(self, timeout: Optional[float] = None) -> Optional[tuple]:
        """
        Listen for a single command (blocking)

        Args:
            timeout: Maximum time to wait for command

        Returns:
            Tuple of (text, confidence) or None if failed
        """
        if not self.microphone:
            raise RuntimeError("Microphone not initialized")

        timeout = timeout or self.timeout

        try:
            self._set_state(VoiceState.LISTENING)
            print("🎤 Listening for command...")

            with self.microphone as source:
                audio = self.recognizer.listen(source, timeout=timeout)

            self._set_state(VoiceState.PROCESSING)
            print("🔄 Processing speech...")

            result = self._recognize_speech(audio)

            if result:
                text, confidence = result
                self.stats['commands_recognized'] += 1
                self.stats['last_command_time'] = time.time()
                print(f"✅ Recognized: '{text}' (confidence: {confidence:.2f})")
                self._set_state(VoiceState.IDLE)
                return result
            else:
                self.stats['recognition_errors'] += 1
                print("❌ Could not understand command")
                self._set_state(VoiceState.ERROR)
                return None

        except sr.WaitTimeoutError:
            print("⏰ No speech detected within timeout")
            self._set_state(VoiceState.IDLE)
            return None
        except Exception as e:
            self.stats['audio_errors'] += 1
            self.logger.error(f"Single listen error: {e}")
            self._set_state(VoiceState.ERROR)
            if self.on_error_callback:
                self.on_error_callback(f"Listen error: {e}")
            return None

    def get_pending_commands(self) -> list:
        """Get all pending commands from queue"""
        commands = []
        while not self.command_queue.empty():
            try:
                commands.append(self.command_queue.get_nowait())
            except queue.Empty:
                break
        return commands

    def test_microphone(self) -> Dict[str, Any]:
        """Test microphone and return diagnostic information"""
        if not self.microphone:
            return {"status": "error", "message": "Microphone not initialized"}

        try:
            # Test audio input
            print("🎤 Testing microphone... Say something!")

            with self.microphone as source:
                # Record brief audio sample
                audio = self.recognizer.listen(source, timeout=3, phrase_time_limit=3)

            # Test recognition
            result = self._recognize_speech(audio)

            if result:
                text, confidence = result
                return {
                    "status": "success",
                    "message": f"Microphone working. Heard: '{text}'",
                    "text": text,
                    "confidence": confidence,
                    "energy_threshold": self.recognizer.energy_threshold
                }
            else:
                return {
                    "status": "warning",
                    "message": "Microphone working but could not understand speech",
                    "energy_threshold": self.recognizer.energy_threshold
                }

        except sr.WaitTimeoutError:
            return {
                "status": "warning",
                "message": "Microphone working but no speech detected",
                "energy_threshold": self.recognizer.energy_threshold
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Microphone test failed: {e}",
                "error": str(e)
            }

    def get_statistics(self) -> Dict[str, Any]:
        """Get voice recognition statistics"""
        return {
            "state": self.state.value,
            "is_listening": self.is_listening,
            "commands_recognized": self.stats['commands_recognized'],
            "recognition_errors": self.stats['recognition_errors'],
            "audio_errors": self.stats['audio_errors'],
            "last_command_time": self.stats['last_command_time'],
            "energy_threshold": self.recognizer.energy_threshold if self.recognizer else None,
            "recognition_engine": self.recognition_engine,
            "language": self.language
        }

    def adjust_for_noise(self, duration: float = 1.0):
        """Adjust microphone sensitivity for current noise level"""
        if not self.microphone:
            return

        try:
            print(f"🔧 Adjusting for ambient noise ({duration}s)...")
            with self.microphone as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=duration)

            print(f"✅ Adjusted. New energy threshold: {self.recognizer.energy_threshold}")

        except Exception as e:
            self.logger.error(f"Noise adjustment failed: {e}")
            if self.on_error_callback:
                self.on_error_callback(f"Noise adjustment failed: {e}")

    def __del__(self):
        """Cleanup when object is destroyed"""
        if self.is_listening:
            self.stop_listening()


# Example callback functions
def on_command_received(text: str, confidence: float):
    """Example callback for when command is recognized"""
    print(f"📢 Command: '{text}' (confidence: {confidence:.2f})")


def on_voice_error(error_message: str):
    """Example callback for voice errors"""
    print(f"❌ Voice Error: {error_message}")


def on_state_changed(new_state: VoiceState):
    """Example callback for state changes"""
    print(f"🔄 Voice State: {new_state.value}")


# Example usage and testing
if __name__ == "__main__":
    # This code runs when script is executed directly
    print("Voice Handler Module")
    print("Example usage:")
    print()
    print("# Create voice handler")
    print("voice_handler = VoiceHandler()")
    print()
    print("# Set up callbacks")
    print("voice_handler.set_callbacks(")
    print("    on_command=on_command_received,")
    print("    on_error=on_voice_error,")
    print("    on_state_change=on_state_changed")
    print(")")
    print()
    print("# Test microphone")
    print("result = voice_handler.test_microphone()")
    print("print(result)")
    print()
    print("# Listen for single command")
    print("command = voice_handler.listen_once()")
    print("if command:")
    print("    text, confidence = command")
    print("    print(f'You said: {text}')")