# Pentool Community Registry

The public, backend-free package registry for [Pentool](https://github.com/agkomyint/pentoolgg). There are no registry accounts or proprietary publishing APIs: packages are proposed through GitHub pull requests, checked automatically, reviewed in public, and served as immutable static files.

Registry URL after GitHub Pages is enabled:

```text
https://agkomyint.github.io/pentool-registry/registry
```

Use it from Pentool:

```sh
pentool registry search https://agkomyint.github.io/pentool-registry/registry icons
pentool package install namespace/package@1.0.0 \
  --registry https://agkomyint.github.io/pentool-registry/registry
```

## Publish through a pull request

1. Fork this repository.
2. Build and verify your deterministic package:

   ```sh
   pentool package pack ./my-library --output my-library-1.0.0.penpkg
   pentool package verify my-library-1.0.0.penpkg
   ```

3. If this is a new namespace, add `registry/namespaces/<namespace>.json` containing its GitHub owners and license policy.
4. Place the archive at `registry/packages/<namespace>/<package>/<version>.penpkg`.
5. Run `python scripts/build_registry.py` and commit the regenerated `registry/index.json` and `registry/catalog.json`.
6. Open a pull request using the package submission template.

The package name and version inside `pentool.package.json` must match the path. Published versions are immutable. To correct a release, publish a new version.

## What GitHub provides

- GitHub identities and pull-request authorship
- Public review and moderation history
- Branch protection and required checks
- GitHub Actions validation
- Static distribution through GitHub Pages
- Forkable and mirrorable registry data

The registry follows Pentool protocol schema 1. The CLI only requires `index.json` plus immutable package paths; `catalog.json` is optional metadata for pentool.space and other browser catalogs.

## Safety limits

- Maximum package archive: 25 MiB
- Maximum expanded content: 100 MiB
- Maximum archive entries: 1,000
- No absolute, escaping, backslash, or symlink paths
- No scripts, executables, or active hooks
- SHA-256 verification for the archive and every declared asset

Packages must be redistributable under the license declared in their manifest. Maintainers may reject misleading, infringing, malicious, or low-quality submissions.
