# Runtime 5 CI validation

This branch combines Runtime 5 Execution Gateway with the CI resilience reformulation.

## Validation intent

The required correctness path must use broadly available standard hosted runners. Large runners remain optional performance infrastructure and must not be prerequisites for Runtime 5 validation.

## Expected runner topology

- Python test generation: `ubuntu-latest`
- Python test slices: `ubuntu-latest`, up to 8 in parallel
- E2E: `ubuntu-latest`
- macOS tests: `macos-latest`
- Windows tests: `windows-latest`
- Nix: `ubuntu-latest`

## Acceptance evidence

A successful PR run must show that Python and Windows jobs enter execution rather than remaining queued before their first step. Docker and Nix must also complete on the combined branch.

This document records validation intent only; it does not claim workflow success before GitHub Actions produces the result.
