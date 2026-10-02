# Namespace claims

A namespace claim is a JSON file named after the first segment of a package name.

```json
{
  "schema": 1,
  "namespace": "open-design",
  "owners": ["github-handle"],
  "description": "Shared open design libraries",
  "required_license": "MIT OR Apache-2.0"
}
```

The first claim is reviewed by registry maintainers. Later package pull requests should be opened by a listed owner. Ownership changes require approval from an existing owner or documented recovery review.
