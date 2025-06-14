"""
Voice Recognition Test Script
Tests the VoiceHandler class with various speech recognition scenarios
"""
import sys

sys.path.append('src')

import time
from core.voice_handler import VoiceHandler, VoiceState


def test_microphone_setup():
    """Test basic microphone functionality"""
    print("=== Microphone Setup Test ===")

    try:
        voice_handler = VoiceHandler()
        print("✅ VoiceHandler created successfully")

        # Test microphone
        result = voice_handler.test_microphone()
        print(f"Microphone test result: {result}")

        if result['status'] == 'success':
            print("✅ Microphone is working correctly")
            return voice_handler
        elif result['status'] == 'warning':
            print("⚠️ Microphone works but may need adjustment")
            return voice_handler
        else:
            print("❌ Microphone test failed")
            return None

    except Exception as e:
        print(f"❌ Failed to create VoiceHandler: {e}")
        return None


def test_single_command(voice_handler):
    """Test listening for a single voice command"""
    print("\n=== Single Command Test ===")
    print("Say one of these commands:")
    print("- next page")
    print("- previous page")
    print("- zoom in")
    print("- zoom out")
    print("- go to page 5")
    print("- set zoom to 90%")

    try:
        result = voice_handler.listen_once(timeout=10)

        if result:
            text, confidence = result
            print(f"✅ Command recognized: '{text}'")
            print(f"   Confidence: {confidence:.2f}")
            return True
        else:
            print("❌ No command recognized")
            return False

    except Exception as e:
        print(f"❌ Error during single command test: {e}")
        return False


def test_continuous_listening(voice_handler):
    """Test continuous voice recognition"""
    print("\n=== Continuous Listening Test ===")
    print("Starting continuous listening for 30 seconds...")
    print("Say multiple commands. Press Ctrl+C to stop early.")

    # Set up callbacks
    commands_received = []

    def on_command(text, confidence):
        commands_received.append((text, confidence, time.time()))
        print(f"🗣️ Heard: '{text}' (confidence: {confidence:.2f})")

    def on_error(error_msg):
        print(f"❌ Error: {error_msg}")

    def on_state_change(state):
        if state == VoiceState.LISTENING:
            print("👂 Listening...")
        elif state == VoiceState.PROCESSING:
            print("🔄 Processing...")

    voice_handler.set_callbacks(
        on_command=on_command,
        on_error=on_error,
        on_state_change=on_state_change
    )

    try:
        # Start listening
        voice_handler.start_listening()

        # Listen for 30 seconds
        time.sleep(30)

        # Stop listening
        voice_handler.stop_listening()

        print(f"\n📊 Continuous listening results:")
        print(f"Commands received: {len(commands_received)}")

        for i, (text, conf, timestamp) in enumerate(commands_received, 1):
            print(f"  {i}. '{text}' (confidence: {conf:.2f})")

        return len(commands_received) > 0

    except KeyboardInterrupt:
        print("\n⏹️ Stopped by user")
        voice_handler.stop_listening()
        return True
    except Exception as e:
        print(f"❌ Error during continuous listening: {e}")
        voice_handler.stop_listening()
        return False


def test_command_variations(voice_handler):
    """Test recognition of different command variations"""
    print("\n=== Command Variations Test ===")

    test_commands = [
        "next page",
        "go to next page",
        "turn the page",
        "zoom in",
        "make it bigger",
        "enlarge",
        "zoom out",
        "make it smaller",
        "previous page",
        "go back",
        "go to page 5",
        "page 10",
        "zoom to 90%",
        "set zoom 150%"
    ]

    print("Say each of these commands when prompted:")
    recognized_commands = []

    for i, expected_command in enumerate(test_commands, 1):
        print(f"\n{i}/{len(test_commands)}: Say '{expected_command}'")
        print("(Press Enter to skip)")

        # Allow user to skip
        import select
        import sys

        try:
            result = voice_handler.listen_once(timeout=8)

            if result:
                text, confidence = result
                recognized_commands.append({
                    'expected': expected_command,
                    'recognized': text,
                    'confidence': confidence,
                    'match': expected_command.lower() in text.lower() or text.lower() in expected_command.lower()
                })

                if recognized_commands[-1]['match']:
                    print(f"✅ Match: '{text}'")
                else:
                    print(f"❓ Different: '{text}' (expected: '{expected_command}')")
            else:
                print("❌ Not recognized")
                recognized_commands.append({
                    'expected': expected_command,
                    'recognized': None,
                    'confidence': 0,
                    'match': False
                })

        except Exception as e:
            print(f"❌ Error: {e}")

    # Show results
    print(f"\n📊 Command Variations Results:")
    matches = sum(1 for cmd in recognized_commands if cmd['match'])
    total = len(recognized_commands)
    accuracy = matches / total if total > 0 else 0

    print(f"Accuracy: {accuracy:.1%} ({matches}/{total})")

    print(f"\nMismatches:")
    for cmd in recognized_commands:
        if not cmd['match'] and cmd['recognized']:
            print(f"  Expected: '{cmd['expected']}'")
            print(f"  Got: '{cmd['recognized']}' ({cmd['confidence']:.2f})")

    return accuracy > 0.7


def test_noise_adjustment(voice_handler):
    """Test ambient noise adjustment"""
    print("\n=== Noise Adjustment Test ===")

    # Get initial energy threshold
    initial_stats = voice_handler.get_statistics()
    initial_threshold = initial_stats.get('energy_threshold', 0)

    print(f"Initial energy threshold: {initial_threshold}")

    # Adjust for current noise
    voice_handler.adjust_for_noise(duration=2)

    # Get new threshold
    new_stats = voice_handler.get_statistics()
    new_threshold = new_stats.get('energy_threshold', 0)

    print(f"New energy threshold: {new_threshold}")

    # Test recognition with new threshold
    print("Test recognition with adjusted threshold:")
    print("Say: 'test noise adjustment'")

    result = voice_handler.listen_once(timeout=5)

    if result:
        text, confidence = result
        print(f"✅ Recognition after adjustment: '{text}' ({confidence:.2f})")
        return True
    else:
        print("❌ Recognition failed after adjustment")
        return False


def show_statistics(voice_handler):
    """Display voice handler statistics"""
    print("\n=== Voice Handler Statistics ===")

    stats = voice_handler.get_statistics()

    for key, value in stats.items():
        if key == 'last_command_time' and value:
            # Convert timestamp to readable format
            import datetime
            readable_time = datetime.datetime.fromtimestamp(value).strftime('%H:%M:%S')
            print(f"{key}: {readable_time}")
        else:
            print(f"{key}: {value}")


def main():
    """Run all voice recognition tests"""
    print("🎤 PDF Voice Editor - Voice Recognition Testing")
    print("=" * 50)

    # Test 1: Microphone setup
    voice_handler = test_microphone_setup()
    if not voice_handler:
        print("❌ Cannot proceed without working microphone")
        return

    # Test 2: Single command
    print("\n" + "=" * 50)
    single_success = test_single_command(voice_handler)

    if not single_success:
        print("❌ Single command test failed. Check microphone and try again.")
        return

    # Test 3: Noise adjustment
    print("\n" + "=" * 50)
    test_noise_adjustment(voice_handler)

    # Test 4: Command variations
    print("\n" + "=" * 50)
    variations_success = test_command_variations(voice_handler)

    # Test 5: Continuous listening (optional)
    print("\n" + "=" * 50)
    response = input("Run continuous listening test? (y/n): ").strip().lower()
    if response in ['y', 'yes']:
        continuous_success = test_continuous_listening(voice_handler)
    else:
        continuous_success = True

    # Show final statistics
    show_statistics(voice_handler)

    # Summary
    print("\n" + "=" * 50)
    print("🏁 Test Summary:")
    print(f"✅ Microphone: Working")
    print(f"{'✅' if single_success else '❌'} Single commands: {'Working' if single_success else 'Failed'}")
    print(
        f"{'✅' if variations_success else '❌'} Command variations: {'Good' if variations_success else 'Needs improvement'}")
    print(f"{'✅' if continuous_success else '❌'} Continuous listening: {'Working' if continuous_success else 'Failed'}")

    if single_success and variations_success:
        print("\n🎉 Voice recognition is ready for integration!")
        print("Next step: Create command processor to handle recognized text")
    else:
        print("\n⚠️ Voice recognition needs improvement before integration")
        print("Try adjusting microphone settings or using a different recognition engine")


if __name__ == "__main__":
    main()