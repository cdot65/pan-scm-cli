"""Diagnostic helper for BPA config uploads.

This script requests a presigned BPA upload URL from SCM, then attempts a
direct ``curl --upload-file`` PUT of ``config.xml``. It prints verbose
transport details and, when available, extracts ``StringToSign`` from XML
error responses to help debug presigned URL signature mismatches.
"""

import re
import subprocess
import sys
import time

# Allow running this script directly from the repository root.
sys.path.insert(0, "src")

from scm_cli.utils.sdk_client import scm_client


def main():
    """Run a BPA upload diagnostic against a presigned URL.

    Prerequisites:
    - An authenticated SCM context
    - ``config.xml`` present in the current working directory

    Behavior:
    - Retries presigned URL creation on HTTP 429 responses
    - Uploads with curl using the doc-recommended ``--upload-file`` flow
    - Prints response details useful for signature debugging
    """
    # Retry presigned URL creation because the upload-init endpoint can
    # temporarily rate-limit repeated diagnostic attempts.
    for attempt in range(20):
        try:
            print(f"Initiating BPA upload (attempt {attempt + 1})...")
            result = scm_client.initiate_bpa_upload(delete_after_processing=True)
            task_id = result["task_id"]
            upload_url = result["upload_url"]
            print(f"Task ID: {task_id}")
            break
        except Exception as e:
            if "429" in str(e):
                wait = 60
                print(f"  Rate limited. Waiting {wait}s...")
                time.sleep(wait)
            else:
                raise
    else:
        print("FAILED: still rate limited after 20 attempts")
        return

    config_path = "config.xml"

    # Exercise the vendor-documented upload shape first so we can compare any
    # signature failure against a doc-aligned request.
    print("\n=== Test 1: curl --upload-file (no explicit headers, per PA docs) ===")
    curl_result = subprocess.run(
        ["curl", "-v", "-X", "PUT", "--upload-file", config_path, upload_url],
        capture_output=True, text=True, timeout=30,
    )
    print(f"Exit code: {curl_result.returncode}")
    print(f"Stderr (connection info):\n{curl_result.stderr[-1000:]}")
    body = curl_result.stdout
    if "<Error>" in body:
        # Storage backends often include StringToSign in XML auth failures,
        # which helps pinpoint canonical request mismatches.
        sts_match = re.search(r"<StringToSign>(.*?)</StringToSign>", body, re.DOTALL)
        if sts_match:
            print(f"\n=== StringToSign (canonical request) ===")
            print(sts_match.group(1))
        else:
            print(f"\nError body:\n{body[:1000]}")
    else:
        print(f"Response body:\n{body[:500]}")
        print("\nSUCCESS!")


if __name__ == "__main__":
    main()
