---
"pan-scm-cli": patch
---

`scm delete network zone`, `scm delete network ipsec-crypto-profile`, and `scm delete network nat-rule` now ask for confirmation before deleting, matching every other delete command. Pass `--force` to skip the prompt (the flag was already documented but previously unimplemented).
