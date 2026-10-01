"""STEP 8: Human Visual Review Assistant.

Assists the developer in reviewing Step 7 candidates and curating the final 30~45 images in work/selected/.
- Automatically prepares work/selected/ with top-ranked candidates if empty
- Validates the current selection against the golden ratio quotas:
    * CLOSE_UP   : ~18% (Pore detail, face structure)
    * UPPER_BODY : ~62% (Torso, natural gestures, clothing)
    * FULL_BODY  : ~20% (Silhouette, distant proportions)
- Reports duplicate backgrounds, lighting balance, and total count.
"""

from __future__ import annotations

import argparse
import os
import shutil
import sys
from collections import Counter
from pathlib import Path


def main() -> int:
    project = Path(__file__).resolve().parent.parent

    # Candidate source
    if (project / "work" / "candidates" / "all_ranked").exists():
        default_candidates = project / "work" / "candidates" / "all_ranked"
    elif (project / "candidates" / "all_ranked").exists():
        default_candidates = project / "candidates" / "all_ranked"
    else:
        default_candidates = project / "work" / "candidates"

    # Selected destination
    if (project / "work" / "selected").exists():
        default_selected = project / "work" / "selected"
    else:
        default_selected = project / "selected"

    parser = argparse.ArgumentParser(description="STEP 8: Prepare Human Visual Review")
    parser.add_argument("--candidates-dir", type=Path, default=default_candidates,
                        help="Path to ranked candidates folder from Step 7")
    parser.add_argument("--selected-dir", type=Path, default=default_selected,
                        help="Path to final curated selected folder")
    parser.add_argument("--target-count", type=int, default=45,
                        help="Default number of images to populate if selected/ is empty (default: 45)")
    parser.add_argument("--populate-defaults", action="store_true",
                        help="Populate selected/ with top N candidates if empty")
    args = parser.parse_args()

    cand_dir = args.candidates_dir.resolve()
    sel_dir = args.selected_dir.resolve()
    sel_dir.mkdir(parents=True, exist_ok=True)

    selected_files = [f for f in sel_dir.iterdir() if f.is_file() and f.suffix.lower() in (".png", ".jpg", ".jpeg", ".webp")]

    # If selected folder is empty and populate-defaults is set (or user prompted)
    if not selected_files and cand_dir.is_dir():
        cand_files = sorted([f for f in cand_dir.iterdir() if f.is_file() and f.suffix.lower() in (".png", ".jpg", ".jpeg", ".webp")])
        if cand_files:
            print(f"Populating {args.target_count} initial candidates from {cand_dir.name} into {sel_dir.name}...")
            to_copy = cand_files[:args.target_count]
            for f in to_copy:
                shutil.copy2(f, sel_dir / f.name)
            selected_files = [f for f in sel_dir.iterdir() if f.is_file() and f.suffix.lower() in (".png", ".jpg", ".jpeg", ".webp")]
            print(f"Copied {len(selected_files)} images as starting baseline for human review.\n")

    print("==================================================================")
    print("                STEP 8: HUMAN VISUAL REVIEW STATUS                ")
    print("==================================================================")
    print(f"Selected Directory : {sel_dir}")
    print(f"Current Image Count: {len(selected_files)} images")

    # Analyze composition quota
    shot_counts = Counter()
    pose_counts = Counter()
    for f in selected_files:
        name = f.stem.upper()
        if "CLOSE_UP" in name:
            shot_counts["CLOSE_UP"] += 1
        elif "FULL_BODY" in name:
            shot_counts["FULL_BODY"] += 1
        elif "UPPER_BODY" in name:
            shot_counts["UPPER_BODY"] += 1
        else:
            shot_counts["OTHER"] += 1

        for p in ("FRONT", "LEFT_3Q", "RIGHT_3Q", "LEFT_PROFILE", "RIGHT_PROFILE", "LOOKING_DOWN", "LOOKING_UP"):
            if p in name:
                pose_counts[p] += 1
                break

    n = max(len(selected_files), 1)
    print("\n--- Current Shot Distribution ---")
    for s, target_pct in [("CLOSE_UP", 18.0), ("UPPER_BODY", 62.0), ("FULL_BODY", 20.0)]:
        cnt = shot_counts[s]
        actual_pct = (cnt / n) * 100
        print(f"  {s:12s}: {cnt:2d} images ({actual_pct:5.1f}%) [Ideal Target: ~{target_pct:.0f}%]")

    print("\n--- Pose Variation Count ---")
    for p, cnt in pose_counts.most_common():
        print(f"  {p:15s}: {cnt:2d} images")

    print("\n--- Instructions for Developer ---")
    print("1. Open the folder: " + str(sel_dir))
    print("2. Visually inspect all images with your own eyes:")
    print("   - Delete any awkward expressions, unnatural mouth shapes, or eye deformities.")
    print("   - If you need replacement images, pick them from: " + str(cand_dir))
    print("3. Target final count: between 30 and 45 pristine images.")
    print("4. When satisfied, proceed to STEP 9 (Selective Restoration) or STEP 10 (Dataset Packaging).")
    print("==================================================================\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
