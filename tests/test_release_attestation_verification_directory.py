"""Reject pre-existing release-attestation output paths before GitHub verification."""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

_SCRIPT_PATH = Path("scripts/verify_release_attestations.sh")
_SOURCE_SHA = "a" * 40
_EXPECTED_SBOM = {
    "@context": "https://spdx.org/rdf/3.0.1/spdx-context.jsonld",
    "@graph": [
        {
            "type": "software_Package",
            "name": "cwl-context-contracts",
        }
    ],
}


def test_verifier_refuses_preexisting_verification_directory(tmp_path: Path) -> None:
    """Do not let checkout-controlled symlinks capture retained verification output."""
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
    verification_dir.mkdir()
    victim = tmp_path / "victim.txt"
    victim.write_text("sentinel\n", encoding="utf-8")
    (verification_dir / f"{wheel.name}.provenance.json").symlink_to(victim)

    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    gh_log = tmp_path / "gh.log"
    gh_path = bin_dir / "gh"
    sbom_result = json.dumps(
        [
            {
                "verificationResult": {
                    "statement": {"predicate": _EXPECTED_SBOM},
                }
            }
        ]
    )
    gh_path.write_text(
        "#!/usr/bin/env bash\n"
        "set -euo pipefail\n"
        'printf \'%s\\n\' "$*" >> "$GH_FAKE_LOG"\n'
        'if [[ " $* " == *" --predicate-type "* ]]; then\n'
        '  printf \'%s\\n\' "$GH_FAKE_SBOM_RESULT"\n'
        "else\n"
        "  printf '[{\"verificationResult\":{\"statement\":{\"predicate\":{}}}}]\\n'\n"
        "fi\n",
        encoding="utf-8",
    )
    gh_path.chmod(0o755)

    env = os.environ.copy()
    env.update(
        {
            "PATH": f"{bin_dir}{os.pathsep}{env['PATH']}",
            "GH_FAKE_LOG": str(gh_log),
            "GH_FAKE_SBOM_RESULT": sbom_result,
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
    assert "verification directory must not pre-exist" in result.stderr
    assert victim.read_text(encoding="utf-8") == "sentinel\n"
    assert not gh_log.exists()
