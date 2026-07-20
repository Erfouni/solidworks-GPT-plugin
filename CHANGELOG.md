# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and versions use
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.0.2] - 2026-07-20

### Fixed

- Made the bundled validator work in Codex's versioned plugin-cache layout as
  well as in a source checkout.
- Added a Python 3.9/3.13 CI gate that installs the bundle into a temporary
  versioned layout and runs its complete structural and runtime checks there.

## [1.0.1] - 2026-07-20

### Added

- Root install manifest for direct plugin discovery.
- Project and bundled plugin icons.
- Security disclosure policies, bundled license, and package-level README.
- HOL Plugin Scanner CI with an 80-point minimum score and high-severity gate.
- Repository checks for manifest consistency, icon integrity, package documents,
  and immutable GitHub Action references.

### Changed

- Pinned all external GitHub Actions to full commit SHAs.
- Expanded the public README with the validated workflow, trust boundaries, and
  a concrete first-task example.
- Added contribution guidance, structured issue forms, and repository social
  preview artwork.

## [1.0.0] - 2026-07-20

### Added

- Initial public release with five coordinated SolidWorks design, knowledge,
  learning, and reporting skills.
- Deterministic session, feedback validation, and submission utilities.
- Plugin marketplace metadata, MIT license, and upstream attribution.

[Unreleased]: https://github.com/Erfouni/solidworks-GPT-plugin/compare/v1.0.2...HEAD
[1.0.2]: https://github.com/Erfouni/solidworks-GPT-plugin/compare/v1.0.1...v1.0.2
[1.0.1]: https://github.com/Erfouni/solidworks-GPT-plugin/compare/v1.0.0...v1.0.1
[1.0.0]: https://github.com/Erfouni/solidworks-GPT-plugin/releases/tag/v1.0.0
