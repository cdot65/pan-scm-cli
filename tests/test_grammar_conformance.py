"""2.0 CLI grammar conformance tests.

One grammar, enforced by introspection:

- set/delete/show take the object name as a positional argument (no --name).
- Containerized types accept --folder/--snippet/--device (exactly-one enforced
  at runtime by validate_location_params; presence checked here).
- Every load command has --dry-run; every backup command has --file.
- Tag lists are `--tags` (repeatable); no CSV `--tag` variants.
- Show commands have --output and --max-results (list mode) and no dead --list.
- Job ids are `--id` everywhere.
"""

import click
import pytest
import typer

from src.scm_cli.commands import deployment, identity, mobile_agent, network, objects, security, setup

CONFIG_MODULES = {
    "objects": objects,
    "network": network,
    "security": security,
    "identity": identity,
    "mobile_agent": mobile_agent,
    "deployment": deployment,
    "setup": setup,
}

# Types keyed by something other than a positional NAME, or singletons with no
# name at all. (module, command-name) pairs, per action app.
NO_POSITIONAL_NAME = {
    ("objects", "quarantined-device"),  # keyed by --host-id
    ("deployment", "bgp-routing"),  # singleton
    ("deployment", "network-location"),  # read-only list
    ("mobile_agent", "agent-version"),  # read-only list
    ("mobile_agent", "global-setting"),  # singleton
    ("mobile_agent", "infrastructure-setting"),  # singleton
    ("mobile_agent", "location"),  # read-only list (if present)
    ("setup", "device"),  # keyed by device id records
    ("deployment", "bandwidth-allocation"),  # deletes require --spn-name-list pairing; name positional still applies -> see NAME_STILL_POSITIONAL
}

# Global resources: no container flags expected.
NO_CONTAINER = {
    ("deployment", "bandwidth-allocation"),
    ("deployment", "bgp-routing"),
    ("deployment", "internal-dns-server"),
    ("deployment", "remote-network"),
    ("deployment", "service-connection"),
    ("deployment", "network-location"),
    ("setup", "folder"),
    ("setup", "label"),
    ("setup", "snippet"),
    ("setup", "device"),
    ("objects", "quarantined-device"),
    ("mobile_agent", "agent-version"),
}


def _click_group(typer_app) -> click.Group:
    return typer.main.get_command(typer_app)


def _commands(module, app_name: str) -> dict[str, click.Command]:
    app = getattr(module, app_name, None)
    if app is None:
        return {}
    group = _click_group(app)
    ctx = click.Context(group)
    return {name: group.get_command(ctx, name) for name in group.list_commands(ctx)}


def _param_names(cmd: click.Command) -> set[str]:
    names = set()
    for param in cmd.params:
        names.update(param.opts)
        names.update(param.secondary_opts)
    return names


def _positional_params(cmd: click.Command) -> list[click.Argument]:
    return [p for p in cmd.params if isinstance(p, click.Argument)]


def _iter_commands(app_attr: str):
    for module_name, module in CONFIG_MODULES.items():
        for cmd_name, cmd in _commands(module, app_attr).items():
            yield module_name, cmd_name, cmd


class TestPositionalName:
    @pytest.mark.parametrize("app_attr", ["set_app", "delete_app", "show_app"])
    def test_no_name_option_anywhere(self, app_attr):
        offenders = [f"{m}:{n}" for m, n, cmd in _iter_commands(app_attr) if "--name" in _param_names(cmd)]
        assert offenders == [], f"{app_attr} commands still using --name: {offenders}"

    @pytest.mark.parametrize("app_attr", ["set_app", "delete_app", "show_app"])
    def test_positional_name_present(self, app_attr):
        offenders = []
        for module_name, cmd_name, cmd in _iter_commands(app_attr):
            if (module_name, cmd_name) in NO_POSITIONAL_NAME:
                continue
            positionals = _positional_params(cmd)
            if not positionals or positionals[0].name != "name":
                offenders.append(f"{module_name}:{cmd_name}")
        assert offenders == [], f"{app_attr} commands without positional NAME: {offenders}"


class TestContainerFlags:
    @pytest.mark.parametrize("app_attr", ["set_app", "delete_app", "show_app"])
    def test_containerized_types_accept_all_three(self, app_attr):
        offenders = []
        for module_name, cmd_name, cmd in _iter_commands(app_attr):
            if (module_name, cmd_name) in NO_CONTAINER:
                continue
            if module_name == "mobile_agent":
                # SDK mobile-agent services are folder-scoped ("Mobile Users");
                # snippet/device are not supported upstream.
                continue
            names = _param_names(cmd)
            missing = {"--folder", "--snippet", "--device"} - names
            if missing:
                offenders.append(f"{module_name}:{cmd_name} missing {sorted(missing)}")
        assert offenders == [], f"{app_attr} container-flag gaps: {offenders}"


class TestLoadAndBackup:
    def test_every_load_has_dry_run(self):
        offenders = [f"{m}:{n}" for m, n, cmd in _iter_commands("load_app") if "--dry-run" not in _param_names(cmd)]
        assert offenders == [], f"load commands without --dry-run: {offenders}"

    def test_every_backup_has_file(self):
        offenders = [f"{m}:{n}" for m, n, cmd in _iter_commands("backup_app") if "--file" not in _param_names(cmd)]
        assert offenders == [], f"backup commands without --file: {offenders}"


class TestFlagHygiene:
    @pytest.mark.parametrize("app_attr", ["set_app", "delete_app", "show_app", "load_app", "backup_app"])
    def test_no_csv_tag_flag(self, app_attr):
        offenders = [f"{m}:{n}" for m, n, cmd in _iter_commands(app_attr) if "--tag" in _param_names(cmd)]
        assert offenders == [], f"--tag (CSV or collision) remains: {offenders}"

    def test_tags_is_repeatable_list(self):
        offenders = []
        for module_name, cmd_name, cmd in _iter_commands("set_app"):
            for param in cmd.params:
                if "--tags" in getattr(param, "opts", []) and not param.multiple:
                    offenders.append(f"{module_name}:{cmd_name}")
        assert offenders == [], f"--tags not repeatable(list) on: {offenders}"

    def test_no_dead_list_flag_on_show(self):
        offenders = [f"{m}:{n}" for m, n, cmd in _iter_commands("show_app") if "--list" in _param_names(cmd)]
        assert offenders == [], f"dead --list on show commands: {offenders}"

    def test_show_commands_have_output_and_max_results(self):
        offenders = []
        for module_name, cmd_name, cmd in _iter_commands("show_app"):
            names = _param_names(cmd)
            if "--output" not in names:
                offenders.append(f"{module_name}:{cmd_name} (--output)")
            if "--max-results" not in names:
                offenders.append(f"{module_name}:{cmd_name} (--max-results)")
        assert offenders == [], f"show flag gaps: {offenders}"


class TestJobIdFlag:
    def test_operations_uses_id(self):
        from src.scm_cli.commands import operations

        group = _click_group(operations.app)
        ctx = click.Context(group)
        status = group.get_command(ctx, "status")
        names = _param_names(status)
        assert "--id" in names
        assert "--job-id" not in names
        assert "-j" not in names  # -j is reserved for --json in incidents
