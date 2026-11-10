"""Production recipes governing real resource transformation and conservation."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from saltbor.economy.inventory.item import ItemType, UnitType


@dataclass(frozen=True)
class ProductionRecipe:
    """Defines inputs, tools, labor, and outputs for manufacturing or farming goods."""

    recipe_id: str
    name: str
    inputs: dict[ItemType, float]             # Raw materials consumed
    outputs: dict[ItemType, tuple[float, UnitType]] # Goods produced (qty, unit)
    tools_required: list[ItemType] = field(default_factory=list) # Durable tools required
    labor_ticks: int = 4                      # Work duration required (ticks)
    required_skill_id: Optional[str] = None  # Skill needed
    min_skill_level: float = 0.0              # Minimum proficiency threshold
    tool_wear_per_batch: float = 0.02         # Durability loss on tools


# Standard recipe catalog for Saltbor industries
STANDARD_RECIPES: dict[str, ProductionRecipe] = {
    "carpentry_furniture": ProductionRecipe(
        recipe_id="carpentry_furniture",
        name="Craft Wooden Furniture",
        inputs={ItemType.WOOD: 4.0},
        outputs={ItemType.FURNITURE: (1.0, UnitType.PIECE)},
        tools_required=[ItemType.TOOL],
        labor_ticks=4,
        required_skill_id="skill_technical",
        min_skill_level=0.2,
        tool_wear_per_batch=0.03,
    ),
    "craft_tool": ProductionRecipe(
        recipe_id="craft_tool",
        name="Forge / Assemble Hand Tool",
        inputs={ItemType.WOOD: 2.0, ItemType.CONSTRUCTION_MATERIAL: 1.0},
        outputs={ItemType.TOOL: (1.0, UnitType.PIECE)},
        tools_required=[ItemType.TOOL],
        labor_ticks=5,
        required_skill_id="skill_technical",
        min_skill_level=0.3,
        tool_wear_per_batch=0.05,
    ),
    "farm_grain_harvest": ProductionRecipe(
        recipe_id="farm_grain_harvest",
        name="Cultivate and Harvest Grain",
        inputs={ItemType.SEEDS: 1.0},
        outputs={ItemType.GRAIN: (8.0, UnitType.KG)},
        tools_required=[ItemType.TOOL],
        labor_ticks=6,
        required_skill_id="skill_physical",
        min_skill_level=0.1,
        tool_wear_per_batch=0.02,
    ),
    "cook_meals": ProductionRecipe(
        recipe_id="cook_meals",
        name="Prepare Hot Comedor Meals",
        inputs={ItemType.GRAIN: 2.0},
        outputs={ItemType.FOOD: (4.0, UnitType.MEAL)},
        tools_required=[],
        labor_ticks=3,
        required_skill_id="skill_creative",
        min_skill_level=0.1,
        tool_wear_per_batch=0.0,
    ),
}
