---
name: Publish a Pentool package
about: Add an immutable .penpkg release to the public registry
---

## Package

- Name:
- Version:
- Namespace owner:
- Source repository:
- License:

## Checklist

- [ ] I built this archive with `pentool package pack`.
- [ ] `pentool package verify` succeeds locally.
- [ ] The package path matches its manifest name and version.
- [ ] This version has never been published before.
- [ ] All included work may be redistributed under the declared license.
- [ ] The archive contains no scripts, executables, secrets, or private information.
- [ ] I ran `python scripts/build_registry.py` and committed the generated indexes.
