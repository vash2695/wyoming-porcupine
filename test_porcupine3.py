#!/usr/bin/env python3
"""Test script for Porcupine v3 wake word detection."""
import argparse
import sys
import pvporcupine

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Test Porcupine v3 wake word detection"
    )
    parser.add_argument(
        "--access-key", required=True, help="Access key from Picovoice console"
    )
    parser.add_argument(
        "--keyword", default="porcupine", help="Keyword to detect"
    )
    parser.add_argument(
        "--sensitivity", type=float, default=0.5, help="Detection sensitivity (0-1)"
    )
    
    args = parser.parse_args()
    
    print("Available keywords:", ", ".join(pvporcupine.KEYWORDS))
    
    try:
        porcupine = pvporcupine.create(
            access_key=args.access_key,
            keywords=[args.keyword],
            sensitivities=[args.sensitivity]
        )
        
        print(f"Successfully initialized Porcupine v3")
        print(f"Keyword: {args.keyword}")
        print(f"Sensitivity: {args.sensitivity}")
        print(f"Sample rate: {porcupine.sample_rate}")
        print(f"Frame length: {porcupine.frame_length}")
        
        # Clean up
        porcupine.delete()
        
        return 0
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main()) 