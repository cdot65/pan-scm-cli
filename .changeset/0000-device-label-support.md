---
"pan-scm-cli": minor
---

Add device commands to manage writable fields landed in pan-scm-sdk 0.14.0: `scm set setup device`, `scm load setup device`, and `scm backup setup device`. Display writable fields (display_name, description, labels, snippets) in `scm show setup device`. Devices remain uncreatable and undeletable — they register through the firewall itself.
