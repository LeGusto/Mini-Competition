#!/usr/bin/env python3
"""
Test script to manually trigger contest submission creation
"""

import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.submission import SubmissionService
from services.contest import ContestService


def test_contest_submission():
    print("🔍 Testing contest submission creation...")

    # Initialize services
    submission_service = SubmissionService()
    contest_service = ContestService()

    # Test with submission ID 45
    submission_id = 45
    problem_id = "1"

    print(f"Testing with submission_id: {submission_id}, problem_id: {problem_id}")

    # Step 1: Get active contest
    print("Step 1: Getting active contest...")
    contest = submission_service.get_active_contest_for_problem(problem_id)
    print(f"Contest result: {contest}")

    if contest:
        # Step 2: Get submission details
        print("Step 2: Getting submission details...")
        submission_details = submission_service.get_submission_details(submission_id)
        print(f"Submission details: {submission_details}")

        if submission_details:
            user_id = submission_details["user_id"]
            print(f"User ID: {user_id}")

            # Step 3: Check registration status
            print("Step 3: Checking registration status...")
            registration_status = contest_service.get_user_registration_status(
                contest["id"], user_id
            )
            print(f"Registration status: {registration_status}")

            if registration_status["is_registered"]:
                print("✅ All checks passed - should create contest submission")

                # Step 4: Create contest submission
                is_accepted = submission_details["status"] == "accepted"
                score = 100 if is_accepted else 0
                penalty_time = 0

                print(
                    f"Creating contest submission with accepted={is_accepted}, score={score}"
                )

                result = submission_service.create_contest_submission(
                    contest["id"],
                    user_id,
                    problem_id,
                    submission_id,
                    submission_details["submission_time"],
                    is_accepted,
                    score,
                    penalty_time,
                )
                print(f"Contest submission result: {result}")
            else:
                print("❌ User not registered for contest")
        else:
            print("❌ Could not get submission details")
    else:
        print("❌ No active contest found")


if __name__ == "__main__":
    test_contest_submission()
