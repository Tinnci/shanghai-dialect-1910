#!/usr/bin/env python
"""
End-to-End Test: Shanghai Dialect Text-to-Sequence Pipeline

This script validates the complete frontend pipeline:
1. Pott Romanization -> IPA (via PottToIPA)
2. IPA -> Model Sequence IDs (via text_to_sequence with shanghai_cleaners)

Usage:
    uv run python tests/test_shanghai_frontend.py
"""

import sys
from pathlib import Path

# Ensure project root is in path
_project_root = Path(__file__).resolve().parents[1]
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))


def test_pott_to_ipa():
    """Test the Pott-to-IPA conversion."""
    from src.pott_g2p import PottToIPA

    converter = PottToIPA()

    test_cases = [
        # (input, expected_ipa_initial, expected_ipa_final)
        ("ngoo", "ŋ", "u"),  # ng-oo
        ("tshang", "tsʰ", "ɑ̃"),  # tsh-ang
        ("nyih", "ɲ", "iʔ"),  # ny-ih (checked tone)
        ("kuh", "k", "uʔ"),  # k-uh (checked tone)
        ("dzi", "dz", "z̩"),  # dz-i (apical vowel after sibilant)
        ("vaung", "v", "ɑ̃"),  # v-aung (voiced initial)
    ]

    print("=" * 60)
    print("TEST 1: Pott -> IPA Conversion")
    print("=" * 60)

    all_passed = True
    for pott, expected_init, expected_final in test_cases:
        ipa, wugniu, conf = converter.convert_syllable(pott)
        # Simple check: the IPA should contain the expected parts
        has_init = expected_init in ipa or expected_init == ""
        has_final = expected_final in ipa

        status = "✓" if (has_init and has_final) else "✗"
        if not (has_init and has_final):
            all_passed = False

        print(f"  {status} {pott:10} -> {ipa:15} (expect: {expected_init}+{expected_final})")

    return all_passed


def test_shanghai_cleaners():
    """Test the shanghai_cleaners function."""
    from matcha.text.shanghai_cleaners import shanghai_cleaners

    test_cases = [
        "Ngoo yiao mah dzi.",
        "Nong hau vau?",
        "Tsh-tsiang kuh.",
    ]

    print("\n" + "=" * 60)
    print("TEST 2: Shanghai Cleaners (Full Text)")
    print("=" * 60)

    for text in test_cases:
        ipa = shanghai_cleaners(text)
        print(f"  Pott: {text}")
        print(f"  IPA:  {ipa}")
        print()

    return True  # Visual inspection for now


def test_text_to_sequence():
    """Test the text_to_sequence function with shanghai_cleaners."""
    from matcha.text import text_to_sequence, sequence_to_text

    test_input = "Ngoo yiao mah"

    print("=" * 60)
    print("TEST 3: text_to_sequence with shanghai_cleaners")
    print("=" * 60)

    try:
        sequence, clean_text = text_to_sequence(test_input, ["shanghai_cleaners"])
        recovered = sequence_to_text(sequence)

        print(f"  Input (Pott):    {test_input}")
        print(f"  Clean (IPA):     {clean_text}")
        print(f"  Sequence IDs:    {sequence[:20]}..." if len(sequence) > 20 else f"  Sequence IDs:    {sequence}")
        print(f"  Recovered Text:  {recovered}")
        print(f"  Sequence Length: {len(sequence)}")

        # Basic validation
        if len(sequence) > 0 and len(clean_text) > 0:
            print("  Status: ✓ PASSED")
            return True
        else:
            print("  Status: ✗ FAILED (empty output)")
            return False

    except KeyError as e:
        print(f"  Status: ✗ FAILED - Symbol not in vocabulary: {e}")
        print("  This indicates the IPA symbols are not yet in symbols.py")
        print("  You may need to use shanghai_symbols.py instead of the default symbols")
        return False
    except Exception as e:
        print(f"  Status: ✗ FAILED - {type(e).__name__}: {e}")
        return False


def main():
    """Run all tests."""
    print("\n" + "#" * 60)
    print("# Shanghai Dialect Frontend E2E Test Suite")
    print("#" * 60 + "\n")

    results = {
        "Pott -> IPA": test_pott_to_ipa(),
        "Shanghai Cleaners": test_shanghai_cleaners(),
        "text_to_sequence": test_text_to_sequence(),
    }

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    for name, passed in results.items():
        status = "✓ PASSED" if passed else "✗ FAILED"
        print(f"  {name}: {status}")

    all_passed = all(results.values())
    print("\n" + ("All tests passed!" if all_passed else "Some tests failed."))
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
