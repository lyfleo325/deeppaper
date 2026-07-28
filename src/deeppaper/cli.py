"""DeepPaper CLI ? ?? obsidian-wiki ??"""

import click
import sys
import os


@click.group()
@click.version_option(version="0.1.0", prog_name="deeppaper")
def cli():
    """DeepPaper ? ??????????????

    Five research directions. Three sources. Your Obsidian, always up to date.
    """
    pass


@cli.command()
@click.option("--push", is_flag=True, help="??? Obsidian ???")
@click.option("--directions", "-d", multiple=True, help="????????????")
def run(push, directions):
    """????????"""
    from deeppaper.main import run_pipeline, load_config, setup_logging

    config = load_config()
    setup_logging(config)
    config["_push_to_obsidian"] = push

    if directions:
        from deeppaper.main import logger
        avail = [d["name"] for d in config.get("directions", [])]
        filtered = [d for d in config["directions"] if d["name"] in directions]
        unknown = set(directions) - set(avail)
        if unknown:
            click.secho(f"Unknown direction(s): {', '.join(unknown)}", fg="red")
            click.secho(f"Available: {', '.join(avail)}", fg="yellow")
            sys.exit(1)
        config["directions"] = filtered
        click.secho(f"Running directions: {', '.join(directions)}", fg="cyan")

    success = run_pipeline(config)

    if not push:
        click.secho("\nReview notes in note/ directory, then run:", fg="yellow")
        click.secho("  deeppaper run --push", fg="green")
    sys.exit(0 if success else 1)


@cli.command()
@click.option("--output", "-o", default=None, help="??????????? cwd/config.yaml?")
@click.option("--force", is_flag=True, help="?????? config.yaml")
def setup(output, force):
    """??????????????"""
    import shutil

    target = output or os.path.join(os.getcwd(), "config.yaml")

    if os.path.exists(target) and not force:
        click.secho(f"Config already exists: {target}", fg="yellow")
        click.secho("Use --force to overwrite, or edit it directly.", fg="yellow")
        sys.exit(1)

    builtin = os.path.join(os.path.dirname(__file__), "config.yaml")
    shutil.copy(builtin, target)
    click.secho(f"Config written to: {target}", fg="green")
    click.secho("Edit this file to set your Obsidian vault path and research directions.", fg="cyan")


@cli.command()
@click.option("--edit", is_flag=True, help="????????? config.yaml")
def config(edit):
    """?????????"""
    from deeppaper.main import load_config

    try:
        cfg = load_config()
    except FileNotFoundError as e:
        click.secho(str(e), fg="red")
        click.secho("Run `deeppaper setup` first.", fg="yellow")
        sys.exit(1)

    if edit:
        import subprocess
        search_paths = [
            os.path.join(os.getcwd(), "config.yaml"),
            os.path.join(os.path.dirname(__file__), "config.yaml"),
        ]
        config_path = next((p for p in search_paths if os.path.exists(p)), None)
        if config_path:
            subprocess.run(["notepad", config_path])
        return

    # Display config summary
    click.secho("=== DeepPaper Configuration ===", fg="cyan", bold=True)
    sched = cfg.get("schedule", {})
    click.echo(f"Schedule:       {', '.join(sched.get('days', []))} at {sched.get('hour',12):02d}:{sched.get('minute',0):02d}")

    obs = cfg.get("obsidian", {})
    click.echo(f"Obsidian KB:    {obs.get('kb_root', 'NOT SET')}")
    click.echo(f"Papers/dir:     {cfg.get('papers_per_direction', 2)}")

    click.secho("\nResearch Directions:", fg="cyan", bold=True)
    for d in cfg.get("directions", []):
        pk = d.get("keywords", {}).get("primary", [])
        pk_preview = ", ".join(pk[:3])
        if len(pk) > 3:
            pk_preview += f" ... (+{len(pk)-3})"
        click.echo(f"  [{d.get('tag', '?')}] {d.get('name', '?')}")
        click.echo(f"    ? {pk_preview}")

    sources = cfg.get("sources", {})
    click.secho("\nSources:", fg="cyan", bold=True)
    for name, src in sources.items():
        status = "?" if src.get("enabled") else "?"
        color = "green" if src.get("enabled") else "red"
        click.secho(f"  [{status}] {name}", fg=color)


@cli.command()
def doctor():
    """??????"""
    import sys

    results = []
    issues = 0

    def check(label, condition, hint=""):
        nonlocal issues
        if condition:
            results.append((label, True, ""))
        else:
            results.append((label, False, hint))
            issues += 1

    # Python version
    py_ver = f"{sys.version_info.major}.{sys.version_info.minor}"
    check(f"Python >= 3.10  ({py_ver})", sys.version_info >= (3, 10))

    # PyYAML
    try:
        import yaml
        check("PyYAML installed", True)
    except ImportError:
        check("PyYAML installed", False, "pip install PyYAML")

    # Click
    try:
        import click
        check("Click installed", True)
    except ImportError:
        check("Click installed", False, "pip install click")

    # Config
    try:
        from deeppaper.main import load_config
        cfg = load_config()
        check("config.yaml found", True)

        # Obsidian vault
        kb_root = cfg.get("obsidian", {}).get("kb_root", "")
        check(f"Obsidian vault   ({kb_root})", os.path.exists(kb_root), "Vault path not found")

        # Directions
        dirs = cfg.get("directions", [])
        check(f"Research directions ({len(dirs)} defined)", len(dirs) > 0)

        # Sources
        sources = cfg.get("sources", {})
        enabled_src = [n for n, s in sources.items() if s.get("enabled")]
        check(f"Data sources ({len(enabled_src)} enabled: {', '.join(enabled_src)})", len(enabled_src) > 0)

    except FileNotFoundError:
        check("config.yaml found", False, "Run `deeppaper setup`")

    # Print results
    click.secho("=== DeepPaper Health Check ===\n", fg="cyan", bold=True)
    for label, ok, hint in results:
        icon = "[OK]" if ok else "[FAIL]"
        color = "green" if ok else "red"
        click.secho(f"  {icon}", fg=color, nl=False)
        click.echo(f"  {label}")
        if hint:
            click.secho(f"         ? {hint}", fg="yellow")

    click.echo()
    if issues == 0:
        click.secho("All checks passed!", fg="green", bold=True)
    else:
        click.secho(f"{issues} issue(s) found.", fg="red", bold=True)
    sys.exit(min(issues, 1))


@cli.command()
def directions():
    """????????????"""
    from deeppaper.main import load_config

    try:
        cfg = load_config()
    except FileNotFoundError as e:
        click.secho(str(e), fg="red")
        sys.exit(1)

    for d in cfg.get("directions", []):
        click.secho(f"\n{d.get('name', '?')}", fg="cyan", bold=True)
        click.echo(f"  Tag:      {d.get('tag', '?')}")
        click.echo(f"  Project:  {d.get('ob_project', '?')}")
        pk = d.get("keywords", {}).get("primary", [])
        sk = d.get("keywords", {}).get("secondary", [])
        ex = d.get("keywords", {}).get("exclude", [])
        venues = d.get("venue_filter", [])
        click.echo(f"  Primary:  {', '.join(pk[:5])}{'...' if len(pk)>5 else ''}")
        click.echo(f"  Secondary:{', '.join(sk[:3])}{'...' if len(sk)>3 else ''}")
        click.echo(f"  Exclude:  {', '.join(ex[:3])}{'...' if len(ex)>3 else ''}")
        click.echo(f"  Venues:   {', '.join(venues)}")


@cli.command()
@click.argument("action", type=click.Choice(["install", "status", "remove"]), default="status")
def schedule(action):
    """?? Windows ????"""
    import subprocess
    import sys

    ps1 = os.path.join(os.path.dirname(__file__), "..", "..", "setup_scheduler.ps1")
    if not os.path.exists(ps1):
        # Try repo root
        ps1 = os.path.join(os.getcwd(), "setup_scheduler.ps1")

    if not os.path.exists(ps1):
        click.secho("setup_scheduler.ps1 not found. Run from repo root.", fg="red")
        sys.exit(1)

    if action == "status":
        subprocess.run(["powershell", "-File", ps1, "-Status"])
    elif action == "install":
        click.echo("Installing scheduled task (Mon/Wed 12:10)...")
        subprocess.run(["powershell", "-File", ps1])
        click.secho("Task installed.", fg="green")
    elif action == "remove":
        subprocess.run(["powershell", "-File", ps1, "-Remove"])
        click.secho("Task removed.", fg="green")


if __name__ == "__main__":
    cli()
