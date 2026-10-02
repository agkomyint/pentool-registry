# Security

Do not report malicious packages or compromised publisher keys in a public issue before maintainers can contain them. Use GitHub's private vulnerability reporting for this repository.

Published versions are immutable. A compromised version will be yanked from new resolution while its index tombstone and review history remain available. Consumers must verify the archive hash recorded in `index.json` and every asset hash in the package manifest.
