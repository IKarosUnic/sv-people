"""Console-based visualization and monitoring dashboard for Saltbor.

Provides formatted terminal displays of settlement overview, population rosters,
activity allocations, and recent event feeds without requiring heavy GUI dependencies.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from saltbor.simulation.runner import SimulationRunner


class ConsoleVisualizer:
    """Renders formatted ASCII/Unicode terminal dashboards of simulation state."""

    @staticmethod
    def render_overview(runner: SimulationRunner) -> str:
        """Produce a formatted overview of the world, population, and recent activities."""
        clock = runner.clock
        pop = runner.population
        events = runner.event_bus.event_log[-5:]

        lines: list[str] = []
        lines.append("=" * 80)
        lines.append(f"  SALTBOR SIMULATION — {clock.time_string()} (Tick #{clock.current_tick})")
        lines.append(f"  Phase: {runner.phase.value.upper()} | Daylight: {'Day (Sun)' if clock.is_daytime else 'Night (Moon)'} | Population: {pop.count}")
        lines.append("=" * 80)

        # -------------------------------------------------------------------
        # Population Status Table
        # -------------------------------------------------------------------
        lines.append(f"{'#':<3} {'Name':<22} {'Age':<4} {'Occupation':<20} {'Location':<18} {'Activity':<10} {'Energy':<6} {'Mood':<6}")
        lines.append("-" * 80)

        for h in pop.get_all():
            summary = h.get_status_summary()
            name_trunc = summary["name"][:21]
            occ_trunc = summary["occupation"][:19]
            loc_trunc = (summary["location"] or "transit")[:17]
            act_trunc = summary["activity"][:9]
            energy_bar = f"{int(summary['energy'] * 100)}%"
            mood_str = f"{summary['mood']:+.2f}"

            lines.append(
                f"{summary['serial']:<3} {name_trunc:<22} {summary['age']:<4} {occ_trunc:<20} "
                f"{loc_trunc:<18} {act_trunc:<10} {energy_bar:<6} {mood_str:<6}"
            )

        lines.append("-" * 80)

        # -------------------------------------------------------------------
        # Recent Event Ticker
        # -------------------------------------------------------------------
        lines.append("  RECENT EVENTS:")
        if not events:
            lines.append("    (No events recorded yet)")
        else:
            for evt in events:
                src = f"Human #{evt.source_human_id}" if evt.source_human_id else "System"
                loc = f"@{evt.location_id}" if evt.location_id else ""
                lines.append(f"    [T{evt.tick:>4}] {evt.event_type.value:<22} {loc:<18} (imp: {evt.importance:.2f})")

        lines.append("=" * 80)
        return "\n".join(lines)

    @staticmethod
    def render_location_distribution(runner: SimulationRunner) -> str:
        """Show human occupant counts per location."""
        lines = ["\n  LOCATION OCCUPANCY:"]
        for loc in runner.locations.get_all():
            occupants = runner.population.get_at_location(loc.location_id)
            if occupants:
                names = ", ".join(h.identity.display_name for h in occupants[:4])
                if len(occupants) > 4:
                    names += f", +{len(occupants) - 4} more"
                lines.append(f"    • {loc.name:<32} ({len(occupants):>2}/{loc.capacity:<2}): {names}")
        return "\n".join(lines)
