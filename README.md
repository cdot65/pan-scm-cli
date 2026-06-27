<p align="center">
  <img src="docs-site/static/img/logo-banner.svg" alt="pan-scm-cli" width="400">
</p>

<p align="center">
  <strong>Command-line interface for Palo Alto Networks Strata Cloud Manager</strong>
</p>

<p align="center">
  <a href="https://pypi.org/project/pan-scm-cli/"><img src="https://img.shields.io/pypi/v/pan-scm-cli.svg" alt="PyPI"></a>
  <a href="https://pypi.org/project/pan-scm-cli/"><img src="https://img.shields.io/pypi/pyversions/pan-scm-cli.svg" alt="Python"></a>
  <a href="https://github.com/cdot65/pan-scm-cli/blob/main/LICENSE"><img src="https://img.shields.io/badge/License-Apache_2.0-blue.svg" alt="License"></a>
</p>

---

## Install

```bash
pip install pan-scm-cli
```

## Quick Start

```bash
# configure authentication
scm context create myenv \
  --client-id "app@123456.iam.panserviceaccount.com" \
  --client-secret "your-secret" \
  --tsg-id "123456"

# list addresses
scm show object address --folder Texas

# create an address
scm set object address --folder Texas --name webserver --ip-netmask 10.1.1.100/32

# backup to YAML
scm backup object address --folder Texas
```

## Documentation

Full documentation, CLI reference, and user guides are available at:

**[https://cdot65.github.io/pan-scm-cli/](https://cdot65.github.io/pan-scm-cli/)**

## License

Apache 2.0
