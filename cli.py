
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime
import time
import json
import logging
from enum import Enum

import typer
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.panel import Panel
from rich.prompt import Confirm

# Initialize Rich console for stderr (keeps stdout clean for piping)
console = Console(stderr=True)
app = typer.Typer(
    help="✨ Modern CLI Tool - Process and manage data with style",
    no_args_is_help=True,
    rich_markup_mode="rich",
    add_completion=False,
)

# Logging setup
logger = logging.getLogger(__name__)

def setup_logging(verbose: bool):
    """Configure logging based on verbosity."""
    level = logging.DEBUG if verbose else logging.WARNING
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%H:%M:%S'
    )

# ============= CORE LOGIC (Testable, Separated from CLI) =============

def process_file_core(filepath: Path, transform: str = "upper") -> Dict[str, Any]:
    """Core processing logic - pure function for testing."""
    if not filepath.exists():
        raise FileNotFoundError(f"File not found: {filepath}")
    
    content = filepath.read_text()
    if transform == "upper":
        result = content.upper()
    elif transform == "lower":
        result = content.lower()
    else:
        result = content
    
    return {
        "original_size": len(content),
        "processed_size": len(result),
        "transform": transform,
        "result": result
    }

def list_items_core(directory: Path, pattern: str = "*") -> List[Dict[str, Any]]:
    """Core listing logic - returns structured data."""
    if not directory.exists():
        raise FileNotFoundError(f"Directory not found: {directory}")
    
    items = []
    for path in directory.glob(pattern):
        items.append({
            "name": path.name,
            "type": "dir" if path.is_dir() else "file",
            "size": path.stat().st_size if path.is_file() else 0,
            "modified": datetime.fromtimestamp(path.stat().st_mtime),
        })
    return sorted(items, key=lambda x: (x["type"], x["name"]))

# ============= CLI COMMANDS =============

@app.command()
def process(
    files: List[Path] = typer.Argument(
        ...,
        help="Files to process",
        exists=True,
        file_okay=True,
        dir_okay=False,
    ),
    transform: str = typer.Option(
        "upper",
        "--transform", "-t",
        help="Transformation to apply",
        rich_help_panel="Processing Options",
    ),
    output_dir: Optional[Path] = typer.Option(
        None,
        "--output", "-o",
        help="Output directory (default: current)",
        rich_help_panel="Processing Options",
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="Preview changes without writing",
        rich_help_panel="Safety Options",
    ),
    yes: bool = typer.Option(
        False,
        "--yes", "-y",
        help="Skip confirmation prompts",
        rich_help_panel="Safety Options",
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose", "-v",
        help="Enable debug output",
        rich_help_panel="Advanced Options",
    ),
):
    """Process files with transformations and Rich feedback."""
    setup_logging(verbose)
    logger.debug(f"Processing {len(files)} files with transform={transform}")
    
    # Confirmation for multiple files
    if len(files) > 1 and not yes and not dry_run:
        console.print(f"[yellow]⚠️  About to process {len(files)} files[/yellow]")
        if not Confirm.ask("Continue?", console=console):
            console.print("[red]Aborted by user[/red]")
            raise typer.Exit(code=130)  # Standard SIGINT code
    
    # Dry run preview
    if dry_run:
        console.print("\n[cyan]🔍 DRY RUN - No files will be modified[/cyan]")
        for file in files:
            console.print(f"  Would process: {file.name} → {transform}")
        raise typer.Exit(code=0)
    
    output_dir = output_dir or Path.cwd()
    
    # Process with progress bar
    errors = []
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=console,
    ) as progress:
        task = progress.add_task("Processing files...", total=len(files))
        
        for file in files:
            try:
                logger.debug(f"Processing {file}")
                result = process_file_core(file, transform)
                
                # Write output
                output_path = output_dir / f"{file.stem}_{transform}{file.suffix}"
                output_path.write_text(result["result"])
                
                progress.update(
                    task,
                    advance=1,
                    description=f"✓ {file.name}"
                )
                logger.info(f"Wrote {result['processed_size']} bytes to {output_path}")
                
            except Exception as e:
                errors.append((file, str(e)))
                progress.update(task, advance=1, description=f"✗ {file.name}")
                logger.error(f"Failed to process {file}: {e}")
    
    # Summary panel
    if errors:
        console.print("\n[red]⚠️  Some files failed:[/red]")
        for file, error in errors:
            console.print(f"  • {file.name}: {error}", style="red")
        raise typer.Exit(code=1)
    else:
        console.print(Panel(
            f"[green]✨ Successfully processed {len(files)} file(s)[/green]",
            title="Complete",
            border_style="green"
        ))

@app.command()
def list(
    directory: Path = typer.Argument(
        Path.cwd(),
        help="Directory to list",
        exists=True,
        file_okay=False,
        dir_okay=True,
    ),
    pattern: str = typer.Option(
        "*",
        "--pattern", "-p",
        help="Glob pattern to filter",
        rich_help_panel="Filter Options",
    ),
    json_output: bool = typer.Option(
        False,
        "--json",
        help="Output as JSON",
        rich_help_panel="Output Options",
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose", "-v",
        help="Show additional details",
        rich_help_panel="Advanced Options",
    ),
):
    """List directory contents in a beautiful table."""
    setup_logging(verbose)
    logger.debug(f"Listing {directory} with pattern={pattern}")
    
    try:
        items = list_items_core(directory, pattern)
        
        if json_output:
            # Machine-readable output for scripting
            output = json.dumps(
                [{"name": i["name"], "type": i["type"], "size": i["size"]} for i in items],
                indent=2
            )
            typer.echo(output)  # Use echo for stdout
        else:
            # Human-readable Rich table
            table = Table(
                title=f"📁 {directory.resolve()}",
                caption=f"Found {len(items)} items matching '{pattern}'",
                show_lines=True,
            )
            table.add_column("Name", style="cyan", no_wrap=True)
            table.add_column("Type", style="magenta")
            table.add_column("Size", justify="right", style="green")
            table.add_column("Modified", style="yellow")
            
            for item in items:
                size_str = f"{item['size']:,}" if item['type'] == 'file' else "-"
                table.add_row(
                    item["name"],
                    item["type"],
                    size_str,
                    item["modified"].strftime("%Y-%m-%d %H:%M"),
                )
            
            console.print(table)
            
            if verbose:
                console.print(f"\n[dim]Total size: {sum(i['size'] for i in items):,} bytes[/dim]")
                
    except FileNotFoundError as e:
        console.print(f"[red]Error: {e}[/red]")
        console.print("[yellow]Tip: Check the path exists and you have read permissions[/yellow]")
        raise typer.Exit(code=1)
    except Exception as e:
        console.print(f"[red]Unexpected error: {e}[/red]")
        logger.exception("Failed to list directory")
        raise typer.Exit(code=1)

@app.callback()
def main_callback(
    version: bool = typer.Option(
        False,
        "--version",
        help="Show version and exit",
        is_eager=True,
    ),
):
    """Modern CLI with beautiful, user-friendly output."""
    if version:
        console.print("[bold cyan]modern-cli[/bold cyan] version 1.0.0")
        raise typer.Exit()

if __name__ == "__main__":
    app()