# Auth Setting

Auth settings configure authentication methods for GlobalProtect mobile agent connections.

## Set Auth Setting

```bash
scm set mobile-agent auth-setting [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--folder TEXT` | Folder location | No |
| `--name TEXT` | Setting name | No |
| `--description TEXT` | Description | No |
| `--auth-type TEXT` | Authentication type (saml, client-certificate, ldap) | No |
| `--os TEXT` | Operating system (Any, Windows, macOS, Linux, iOS, Android, ChromeOS) | No |
| `--max-user INT` | Maximum concurrent users | No |
| `--saml-idp TEXT` | SAML identity provider profile name | No |
| `--certificate-profile TEXT` | Certificate profile name | No |
| `--ldap-profile TEXT` | LDAP server profile name | No |

### Example

```bash
$ scm set mobile-agent auth-setting \
    --folder "Mobile Users" \
    --name "saml-auth" \
    --auth-type saml \
    --saml-idp "okta-idp" \
    --os Any
```

## Show Auth Setting

```bash
scm show mobile-agent auth-setting --folder "Mobile Users"
scm show mobile-agent auth-setting --folder "Mobile Users" --name "saml-auth"
```

## Delete Auth Setting

```bash
scm delete mobile-agent auth-setting --folder "Mobile Users" --name "saml-auth"
```

## Load / Backup

```bash
scm load mobile-agent auth-setting --file auth-settings.yaml
scm backup mobile-agent auth-setting --folder "Mobile Users"
```
