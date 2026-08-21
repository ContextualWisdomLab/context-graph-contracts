"""Reject regular-file replacement of release-attestation verification output."""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path
from typing import Any

_SCRIPT_PATH = Path("scripts/verify_release_attestations.sh")
_SOURCE_SHA = "a" * 40
_EXPECTED_SBOM: dict[str, Any] = {
    "@context": "https://spdx.org/rdf/3.0.1/spdx-context.jsonld",
    "@graph": [
        {
            "type": "software_Package",
            "name": "cwl-context-contracts",
        }
    ],
}
_MISMATCHED_SBOM: dict[str, Any] = {
    **_EXPECTED_SBOM,
    "@graph": [
        {
            "type": "software_Package",
            "name": "different-signed-package",
        }
    ],
}


def test_verifier_rejects_regular_output_replacement_after_gh_writes(
    tmp_path: Path,
) -> None:
    """Compare the signed predicate bytes received from gh, not a reopened pathname."""
    evidence_dir = tmp_path / "evidence"
    evidence_dir.mkdir()
    wheel = evidence_dir / "cwl_context_contracts-0.1-py3-none-any.whl"
    sdist = evidence_dir / "cwl_context_contracts-0.1.tar.gz"
    wheel.write_bytes(b"wheel")
    sdist.write_bytes(b"sdist")
    (evidence_dir / "cwl-context-contracts.spdx.json").write_text(
        json.dumps(_EXPECTED_SBOM),
        encoding="utf-8",
    )

    verification_dir = tmp_path / "verification"
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    gh_path = bin_dir / "gh"
    gh_path.write_text(
        "#!/usr/bin/env bash\n"
        "set -euo pipefail\n"
        'if [[ " $* " == *" --predicate-type "* ]]; then\n'
        '  printf \'%s\\n\' "$GH_FAKE_MISMATCHED_RESULT"\n'
        '  output_path="$GH_FAKE_VERIFICATION_DIR/$(basename "$3").sbom.json"\n'
        '  rm -f "$output_path"\n'
        '  printf \'%s\\n\' "$GH_FAKE_ATTACKER_RESULT" > "$output_path"\n'
        "else\n"
        "  printf '[{\"verificationResult\":{\"statement\":{\"predicate\":{}}}}]\\n'\n"
        "fi\n",
        encoding="utf-8",
    )
    gh_path.chmod(0o755)

    mismatched_result = json.dumps(
        [
            {
                "verificationResult": {
                    "statement": {"predicate": _MISMATCHED_SBOM},
                }
            }
        ]
    )
    attacker_result = json.dumps(
        [
            {
                "verificationResult": {
                    "statement": {"predicate": _EXPECTED_SBOM},
                }
            }
        ]
    )
    env = os.environ.copy()
    env.update(
        {
            "PATH": f"{bin_dir}{os.pathsep}{env['PATH']}",
            "GH_FAKE_MISMATCHED_RESULT": mismatched_result,
            "GH_FAKE_ATTACKER_RESULT": attacker_result,
            "GH_FAKE_VERIFICATION_DIR": str(verification_dir),
            "SOURCE_SHA": _SOURCE_SHA,
            "SOURCE_REF": "refs/heads/main",
            "EXPECTED_SOURCE_REF": "refs/heads/main",
            "REPOSITORY": "ContextualWisdomLab/context-graph-contracts",
            "SIGNER_WORKFLOW": (
                "ContextualWisdomLab/context-graph-contracts/"
                ".github/workflows/supply-chain.yml"
            ),
            "SPDX_PREDICATE": "https://spdx.dev/Document/v3",
            "EVIDENCE_DIR": str(evidence_dir),
            "VERIFICATION_DIR": str(verification_dir),
        }
    )

    result = subprocess.run(
        ["bash", str(_SCRIPT_PATH)],
        check=False,
        capture_output=True,
        text=True,
        env=env,
    )

    assert result.returncode != 0
    assert "attested SPDX predicate does not match downloaded package SBOM" in result.stderr
