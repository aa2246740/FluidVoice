"""Run dependency-free Swift regressions with timing and a real coverage gate."""

import json
import os
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CASES = {
    "OnboardingAISetupControllerTests": ["Services/OnboardingAISetupController.swift"],
    "OnboardingPolishPracticeTests": ["Services/OnboardingPolishPractice.swift"],
    "OnboardingDictationOutputPolicyTests": ["Services/OnboardingDictationOutputPolicy.swift"],
    "PrivateAIHardwareRecommendationTests": ["Services/PrivateAIHardwareRecommendation.swift"],
    "ReleaseHighlightsPolicyTests": ["UI/ReleaseHighlightsPolicy.swift", "UI/ReleaseHighlightsContent.swift"],
    "CloudASRClientTests": ["String+Localization.swift", "Services/CloudASR/CloudASRClient.swift"],
    "LogSanitizerTests": ["Services/LogSanitizer.swift"],
}
MINIMUM_LINES = 75.0


def coverage_report(export, sources):
    files = [
        item for data in export["data"] for item in data["files"]
        if Path(item["filename"]).resolve() in sources
    ]
    if {Path(item["filename"]).resolve() for item in files} != sources:
        raise ValueError("Coverage export is missing critical production sources")
    count = sum(item["summary"]["lines"]["count"] for item in files)
    covered = sum(item["summary"]["lines"]["covered"] for item in files)
    if count == 0:
        raise ValueError("No instrumented production lines")
    return {
        "scope": "dependency-free regression production sources, not the entire app",
        "line_percent": 100 * covered / count,
        "minimum_line_percent": MINIMUM_LINES,
        "covered_lines": covered, "executable_lines": count,
        "files": [
            {"path": str(Path(item["filename"]).resolve().relative_to(ROOT)),
             "lines": item["summary"]["lines"]}
            for item in files
        ],
    }


def main():
    from measure import run
    os.chdir(ROOT)
    output = ROOT / "quality-artifacts"
    output.mkdir(exist_ok=True)
    sources = set()
    with tempfile.TemporaryDirectory(prefix="fluidvoice-coverage-") as directory:
        temporary = Path(directory)
        binaries = []
        for name, paths in CASES.items():
            production = [ROOT / "Sources/Fluid" / path for path in paths]
            sources.update(production)
            binary = temporary / name
            command = [
                "xcrun", "swiftc", "-parse-as-library",
                "-profile-generate", "-profile-coverage-mapping",
                *map(str, production), str(ROOT / "Tests" / f"{name}.swift"), "-o", str(binary),
            ]
            subprocess.run(command, check=True)
            environment = os.environ.copy()
            environment["LLVM_PROFILE_FILE"] = str(temporary / f"{name}-%p.profraw")
            # Each test process writes its own profile; timers preserve failures.
            previous = os.environ.get("LLVM_PROFILE_FILE")
            os.environ["LLVM_PROFILE_FILE"] = environment["LLVM_PROFILE_FILE"]
            try:
                status = run(name, [str(binary)], output / "standalone-timings.json")
            finally:
                if previous is None:
                    os.environ.pop("LLVM_PROFILE_FILE", None)
                else:
                    os.environ["LLVM_PROFILE_FILE"] = previous
            if status:
                raise SystemExit(status)
            binaries.append(binary)
        profile = temporary / "coverage.profdata"
        subprocess.run(
            ["xcrun", "llvm-profdata", "merge", "-sparse",
             *map(str, temporary.glob("*.profraw")), "-o", str(profile)], check=True,
        )
        command = ["xcrun", "llvm-cov", "export", str(binaries[0]), f"-instr-profile={profile}"]
        for binary in binaries[1:]:
            command += ["-object", str(binary)]
        export = json.loads(subprocess.check_output(command))
        report = coverage_report(export, sources)
        (output / "core-coverage.json").write_text(json.dumps(report, indent=2) + "\n")
        print(f"Critical production line coverage: {report['line_percent']:.2f}% (minimum {MINIMUM_LINES}%)")
        if report["line_percent"] < MINIMUM_LINES:
            raise SystemExit("Critical-source coverage threshold failed")


if __name__ == "__main__":
    main()
