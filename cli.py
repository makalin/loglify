#!/usr/bin/env python3
import click
import httpx
import sys
from datetime import datetime
from typing import Optional
from config import settings
import re


def parse_duration(duration_str: str) -> Optional[float]:
    """Parse duration string (e.g., '30m', '2h', '45min') to minutes"""
    if not duration_str:
        return None
    
    # Remove whitespace
    duration_str = duration_str.strip().lower()
    
    # Patterns
    patterns = [
        (r'(\d+(?:\.\d+)?)\s*h(?:ours?|rs?)?', lambda m: float(m.group(1)) * 60),
        (r'(\d+(?:\.\d+)?)\s*m(?:in(?:utes?|s?))?', lambda m: float(m.group(1))),
    ]
    
    for pattern, converter in patterns:
        match = re.search(pattern, duration_str)
        if match:
            return converter(match)
    
    # Try to parse as number (assume minutes)
    try:
        return float(duration_str)
    except ValueError:
        return None


@click.group()
@click.version_option(version="0.1.0")
def cli():
    """Loglify CLI - Track your life activities"""
    pass


@cli.command()
@click.argument("message")
@click.option("--tag", "-t", multiple=True, help="Tags for the log entry")
@click.option("--duration", "-d", help="Duration (e.g., '30m', '2h', '45min')")
@click.option("--project", "-p", help="Project name")
def log(message: str, tag: tuple, duration: Optional[str], project: Optional[str]):
    """Log an activity"""
    duration_minutes = parse_duration(duration) if duration else None
    
    log_entry = {
        "source": "cli",
        "raw_text": message,
        "action": message,
        "project": project,
        "duration": duration_minutes,
        "tags": list(tag) if tag else None
    }
    
    try:
        with httpx.Client() as client:
            response = client.post(
                f"http://localhost:{settings.port}/api/logs",
                json=log_entry,
                timeout=10.0
            )
            
            if response.status_code == 200:
                entry = response.json()
                click.echo(f"✅ Logged: {entry['action']}")
                if entry.get('duration'):
                    click.echo(f"   Duration: {entry['duration']} minutes")
                if entry.get('project'):
                    click.echo(f"   Project: {entry['project']}")
                if entry.get('tags'):
                    click.echo(f"   Tags: {', '.join(entry['tags'])}")
            else:
                click.echo(f"❌ Error: {response.status_code} - {response.text}", err=True)
                sys.exit(1)
                
    except httpx.ConnectError:
        click.echo("❌ Error: Could not connect to Loglify API. Is the server running?", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"❌ Error: {str(e)}", err=True)
        sys.exit(1)


@cli.command()
@click.option("--days", "-d", default=7, help="Number of days to show")
def stats(days: int):
    """Show statistics"""
    try:
        with httpx.Client() as client:
            response = client.get(
                f"http://localhost:{settings.port}/api/logs/stats?days={days}",
                timeout=10.0
            )
            
            if response.status_code == 200:
                stats_data = response.json()
                
                click.echo(f"\n📊 Statistics (Last {days} days)\n")
                click.echo(f"Total Logs: {stats_data['total_logs']}")
                click.echo(f"Total Time: {stats_data['total_duration_hours']} hours\n")
                
                click.echo("By Source:")
                for source, count in stats_data['logs_by_source'].items():
                    click.echo(f"  • {source}: {count}")
                
                click.echo("\nTop Actions:")
                for action, count in list(stats_data['top_actions'].items())[:10]:
                    click.echo(f"  • {action}: {count}")
            else:
                click.echo(f"❌ Error: {response.status_code}", err=True)
                sys.exit(1)
                
    except httpx.ConnectError:
        click.echo("❌ Error: Could not connect to Loglify API. Is the server running?", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"❌ Error: {str(e)}", err=True)
        sys.exit(1)


@cli.command()
@click.option("--limit", "-l", default=10, help="Number of entries to show")
@click.option("--source", "-s", help="Filter by source")
def list(limit: int, source: Optional[str]):
    """List recent log entries"""
    try:
        url = f"http://localhost:{settings.port}/api/logs?limit={limit}"
        if source:
            url += f"&source={source}"
        
        with httpx.Client() as client:
            response = client.get(url, timeout=10.0)
            
            if response.status_code == 200:
                entries = response.json()
                
                if not entries:
                    click.echo("No log entries found.")
                    return
                
                click.echo(f"\n📝 Recent Log Entries ({len(entries)})\n")
                
                for entry in entries:
                    timestamp = datetime.fromisoformat(entry['timestamp'].replace('Z', '+00:00'))
                    click.echo(f"[{timestamp.strftime('%Y-%m-%d %H:%M')}] {entry['action']}")
                    if entry.get('project'):
                        click.echo(f"  Project: {entry['project']}")
                    if entry.get('duration'):
                        click.echo(f"  Duration: {entry['duration']} min")
                    if entry.get('tags'):
                        click.echo(f"  Tags: {', '.join(entry['tags'])}")
                    click.echo()
            else:
                click.echo(f"❌ Error: {response.status_code}", err=True)
                sys.exit(1)
                
    except httpx.ConnectError:
        click.echo("❌ Error: Could not connect to Loglify API. Is the server running?", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"❌ Error: {str(e)}", err=True)
        sys.exit(1)


@cli.command()
@click.option("--github", is_flag=True, help="Sync GitHub data")
def sync(github: bool):
    """Sync passive data sources"""
    if github:
        click.echo("🔄 Syncing GitHub data...")
        # This would trigger the GitHub aggregator
        # For now, just a placeholder
        click.echo("✅ GitHub sync completed")
    else:
        click.echo("Please specify a source to sync (e.g., --github)")


if __name__ == "__main__":
    cli()

