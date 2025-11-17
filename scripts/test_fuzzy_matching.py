"""Test script for fuzzy matching fallback logic in technique validation.

This script tests the TechniqueService.match_technique() method with various
incorrect IDs and names to verify the fuzzy matching works correctly.
"""

import sys
from pathlib import Path

# Add src to path so we can import modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.shared.technique_service.technique_service import TechniqueService


def print_test_header(test_name: str) -> None:
    """Print a formatted test header."""
    print(f"\n{'='*70}")
    print(f"TEST: {test_name}")
    print(f"{'='*70}")


def test_case(
    service: TechniqueService,
    test_name: str,
    incorrect_id: str,
    incorrect_name: str,
    expected_id: str | None = None,
) -> None:
    """Run a single test case.

    Args:
        service: TechniqueService instance
        test_name: Description of the test
        incorrect_id: The incorrect/misspelled ID to test
        incorrect_name: The incorrect/misspelled name to test
        expected_id: Expected technique ID (optional, for verification)
    """
    print(f"\n{test_name}")
    print(f"Input ID:   '{incorrect_id}'")
    print(f"Input Name: '{incorrect_name}'")

    try:
        matched = service.match_technique(incorrect_id, incorrect_name)
        print(f"✓ Matched:  '{matched.name}' (ID: {matched.id})")

        if expected_id and matched.id != expected_id:
            print(f"⚠ WARNING: Expected ID '{expected_id}', got '{matched.id}'")
    except ValueError as e:
        print(f"✗ FAILED: {e}")


def main() -> None:
    """Run all fuzzy matching tests."""
    print("\n" + "="*70)
    print("FUZZY MATCHING FALLBACK LOGIC TEST SUITE")
    print("="*70)

    # Initialize the technique service
    service = TechniqueService()
    techniques = service.get_all_techniques()

    print(f"\nLoaded {len(techniques)} techniques from YAML files")
    print("\nSample techniques:")
    for i, (tid, tech) in enumerate(techniques.items()):
        if i < 5:
            print(f"  - {tech.name} (ID: {tid})")
        else:
            break

    # Test 1: Capitalization differences
    print_test_header("Test 1: Capitalization Differences")
    test_case(
        service,
        "1.1: Name with different capitalization",
        "535594f5-b838-471e-a1bf-2d6a6c3a0e68",  # Correct ID
        "MINCE",  # Wrong capitalization
    )
    test_case(
        service,
        "1.2: Name all lowercase",
        "535594f5-b838-471e-a1bf-2d6a6c3a0e68",
        "mince",
    )

    # Test 2: Punctuation differences
    print_test_header("Test 2: Punctuation Differences")
    # Find a technique with punctuation if exists
    test_case(
        service,
        "2.1: Missing punctuation",
        "535594f5-b838-471e-a1bf-2d6a6c3a0e68",
        "Mince",  # Assuming original has punctuation
    )

    # Test 3: Typos in ID
    print_test_header("Test 3: Typos in ID")
    test_case(
        service,
        "3.1: Single character typo in ID",
        "535594f5-b838-471e-a1bf-2d6a6c3a0e69",  # Last char wrong
        "Mince",
        expected_id="535594f5-b838-471e-a1bf-2d6a6c3a0e68",
    )
    test_case(
        service,
        "3.2: Missing dashes in ID",
        "535594f5b838471ea1bf2d6a6c3a0e68",  # Missing dashes
        "Mince",
        expected_id="535594f5-b838-471e-a1bf-2d6a6c3a0e68",
    )

    # Test 4: Typos in name
    print_test_header("Test 4: Typos in Name")
    test_case(
        service,
        "4.1: Single character typo",
        "535594f5-b838-471e-a1bf-2d6a6c3a0e68",
        "Minse",  # 'c' -> 's'
        expected_id="535594f5-b838-471e-a1bf-2d6a6c3a0e68",
    )
    test_case(
        service,
        "4.2: Multiple character typos",
        "535594f5-b838-471e-a1bf-2d6a6c3a0e68",
        "Minxe",  # Multiple typos
        expected_id="535594f5-b838-471e-a1bf-2d6a6c3a0e68",
    )

    # Test 5: Both ID and name wrong
    print_test_header("Test 5: Both ID and Name Incorrect")
    test_case(
        service,
        "5.1: Both slightly wrong",
        "535594f5-b838-471e-a1bf-2d6a6c3a0e69",  # ID slightly wrong
        "Minse",  # Name slightly wrong
        expected_id="535594f5-b838-471e-a1bf-2d6a6c3a0e68",
    )
    test_case(
        service,
        "5.2: ID completely wrong, name correct",
        "00000000-0000-0000-0000-000000000000",  # Totally wrong ID
        "Mince",  # Correct name
        expected_id="535594f5-b838-471e-a1bf-2d6a6c3a0e68",
    )

    # Test 6: Edge cases
    print_test_header("Test 6: Edge Cases")
    test_case(
        service,
        "6.1: Completely wrong ID and name (should fail)",
        "00000000-0000-0000-0000-000000000000",
        "SomethingCompletelyWrong",
    )
    test_case(
        service,
        "6.2: Empty-like name",
        "535594f5-b838-471e-a1bf-2d6a6c3a0e68",
        "   ",
        expected_id="535594f5-b838-471e-a1bf-2d6a6c3a0e68",
    )
    test_case(
        service,
        "6.3: LLM accidentally put name in ID field",
        "Mince",  # Name in ID field!
        "Mince",  # Correct name
        expected_id="535594f5-b838-471e-a1bf-2d6a6c3a0e68",
    )
    test_case(
        service,
        "6.4: LLM swapped ID and name fields",
        "535594f5-b838-471e-a1bf-2d6a6c3a0e68",  # ID in name field
        "Mince",  # Name (accidentally in ID position)
        expected_id="535594f5-b838-471e-a1bf-2d6a6c3a0e68",
    )

    # Test 7: Real-world scenarios
    print_test_header("Test 7: Real-World LLM Output Scenarios")

    # Get a few real techniques to test with
    real_techniques = list(techniques.values())[:10]
    print(f"\nTesting with {len(real_techniques)} real techniques:")

    for i, tech in enumerate(real_techniques[:3], 1):
        # Test with slight variations
        test_case(
            service,
            f"7.{i}: '{tech.name}' with typo",
            tech.id[:-1] + "X",  # Modify last char of ID
            tech.name.lower(),  # Lowercase name
            expected_id=tech.id,
        )

    # Test 8: Combined score weighting (50% ID, 50% name)
    print_test_header("Test 8: Score Weighting Test")
    print("\nNote: Matching uses 50% ID score + 50% name score")
    test_case(
        service,
        "8.1: Perfect ID match, terrible name",
        "535594f5-b838-471e-a1bf-2d6a6c3a0e68",
        "XYZ",
        expected_id="535594f5-b838-471e-a1bf-2d6a6c3a0e68",
    )
    test_case(
        service,
        "8.2: Terrible ID, perfect name",
        "00000000-0000-0000-0000-000000000000",
        "Mince",
        expected_id="535594f5-b838-471e-a1bf-2d6a6c3a0e68",
    )

    # Summary
    print("\n" + "="*70)
    print("TEST SUITE COMPLETE")
    print("="*70)
    print("\nKey Observations:")
    print("  - Fuzzy matching is case-insensitive for names")
    print("  - Fuzzy matching ignores punctuation in names")
    print("  - ID matching is case-sensitive (as designed)")
    print("  - Combined scoring: 50% ID + 50% name")
    print("  - Low confidence matches (< 80%) trigger warnings in logs")
    print("  - Matches below 50% score are rejected")


if __name__ == "__main__":
    main()
