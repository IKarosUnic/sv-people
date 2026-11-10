"""
Salvadoran Cultural Elements: Foodways, Patron Saint Festivities, Crafts, and Historical Memory.

Captures authentic cultural knowledge:
- Traditional culinary preparations (pupusas, tamales, atoles, yuca, antojitos)
- Patron saint celebrations across departments
- Traditional handicrafts and regional production centers
- Key historical milestones and agrarian/social transformations
"""

from __future__ import annotations
import dataclasses
from enum import Enum
from typing import Any, Optional


@dataclasses.dataclass(frozen=True)
class SalvadoranFoodItem:
    """A traditional food item, recipe, or street specialty."""
    item_id: str
    name: str
    category: str                       # "staple_main", "tamal", "atol", "antojito", "pastry_sweet", "festive_dish"
    dough_or_base: str                  # "masa_de_maiz", "masa_de_arroz", "yuca", "platano_maduro", "pan_frances"
    typical_fillings_or_toppings: list[str]
    accompanied_by: list[str]           # e.g. ["curtido_con_oregano", "salsa_de_tomate", "chocolate_caliente"]
    regional_association: str           # e.g. "Nacional / Olocuilta para arroz"
    preparation_difficulty: float       # [0.0, 1.0]
    estimated_cost_usd: float           # Typical cost per unit in El Salvador
    cultural_salience: float            # [0.0, 1.0] centrality to national identity


SALVADORAN_FOOD_CATALOG: dict[str, SalvadoranFoodItem] = {
    "pupusa_revuelta": SalvadoranFoodItem(
        item_id="pupusa_revuelta",
        name="Pupusa Revuelta (Chicharrón, Frijol y Quesillo)",
        category="staple_main",
        dough_or_base="masa_de_maiz",
        typical_fillings_or_toppings=["chicharron_molido", "frijoles_refritos", "quesillo_salvadoreno"],
        accompanied_by=["curtido_en_vinagre", "salsa_de_tomate_cocida"],
        regional_association="Nacional (plato insignia de El Salvador)",
        preparation_difficulty=0.65,
        estimated_cost_usd=0.85,
        cultural_salience=1.0,
    ),
    "pupusa_queso_loroco": SalvadoranFoodItem(
        item_id="pupusa_queso_loroco",
        name="Pupusa de Queso con Loroco",
        category="staple_main",
        dough_or_base="masa_de_maiz",
        typical_fillings_or_toppings=["quesillo_salvadoreno", "loroco_tierno_picado"],
        accompanied_by=["curtido_en_vinagre", "salsa_de_tomate_cocida"],
        regional_association="Nacional / Valles centrales y cafetaleros donde abunda el loroco",
        preparation_difficulty=0.60,
        estimated_cost_usd=0.90,
        cultural_salience=0.98,
    ),
    "pupusa_arroz_olocuilta": SalvadoranFoodItem(
        item_id="pupusa_arroz_olocuilta",
        name="Pupusa de Arroz de Olocuilta",
        category="staple_main",
        dough_or_base="masa_de_arroz",
        typical_fillings_or_toppings=["chicharron", "quesillo", "ayote_rallado", "frijoles"],
        accompanied_by=["curtido_en_vinagre", "salsa_de_tomate_cocida"],
        regional_association="Olocuilta, Departamento de La Paz (pupusódromos tradicionales)",
        preparation_difficulty=0.75,
        estimated_cost_usd=0.90,
        cultural_salience=0.95,
    ),
    "tamal_gallina_india": SalvadoranFoodItem(
        item_id="tamal_gallina_india",
        name="Tamal de Gallina India",
        category="tamal",
        dough_or_base="masa_de_maiz_sancochada",
        typical_fillings_or_toppings=["carne_de_gallina_criolla", "recaudo_salvadoreno", "papa", "garbanzo", "aceituna"],
        accompanied_by=["pan_frances", "cafe_de_palo"],
        regional_association="Celebraciones familiares, nochebuena, domingos en todo el país",
        preparation_difficulty=0.80,
        estimated_cost_usd=1.25,
        cultural_salience=0.96,
    ),
    "tamal_pisque": SalvadoranFoodItem(
        item_id="tamal_pisque",
        name="Tamal Pisque con Ceniza",
        category="tamal",
        dough_or_base="masa_de_maiz_con_ceniza_o_cal",
        typical_fillings_or_toppings=["frijoles_negros_o_rojos_refritos"],
        accompanied_by=["curtido", "chile_en_vinagre"],
        regional_association="Semana Santa y ferias rurales",
        preparation_difficulty=0.70,
        estimated_cost_usd=0.75,
        cultural_salience=0.88,
    ),
    "atol_de_elote": SalvadoranFoodItem(
        item_id="atol_de_elote",
        name="Atol de Elote Tierno",
        category="atol",
        dough_or_base="grano_de_elote_tierno_molido",
        typical_fillings_or_toppings=["leche", "canela", "granos_de_elote_sancochados"],
        accompanied_by=["elote_loco_con_salsa_negra_mostaza_queso"],
        regional_association="Temporada de cosecha de primera (julio-agosto)",
        preparation_difficulty=0.55,
        estimated_cost_usd=1.00,
        cultural_salience=0.92,
    ),
    "atol_shuco": SalvadoranFoodItem(
        item_id="atol_shuco",
        name="Atol Shuco en Guacal de Morro",
        category="atol",
        dough_or_base="maiz_fermentado_molido",
        typical_fillings_or_toppings=["alhuashte_semilla_de_ayote", "frijoles_monos_enteros", "chile_picante"],
        accompanied_by=["pan_frances"],
        regional_association="Tradición ancestral Pipil / San Salvador, Sonsonate, Cojutepeque al atardecer",
        preparation_difficulty=0.70,
        estimated_cost_usd=0.75,
        cultural_salience=0.94,
    ),
    "yuca_con_chicharron": SalvadoranFoodItem(
        item_id="yuca_con_chicharron",
        name="Yuca Sancochada o Frita con Chicharrón",
        category="antojito",
        dough_or_base="yuca",
        typical_fillings_or_toppings=["trozos_de_chicharron_de_cerdo", "pescaditas_secas_fritas", "curtido_rosado"],
        accompanied_by=["salsa_de_tomate", "pepino", "rabano"],
        regional_association="Salcoatitán y Juayúa en Sonsonate, parques centrales de pueblos",
        preparation_difficulty=0.50,
        estimated_cost_usd=2.50,
        cultural_salience=0.90,
    ),
    "quesadilla_artesanal": SalvadoranFoodItem(
        item_id="quesadilla_artesanal",
        name="Quesadilla Salvadoreña Tradicional",
        category="pastry_sweet",
        dough_or_base="harina_de_arroz_con_crema_y_queso",
        typical_fillings_or_toppings=["queso_duro_blando", "cuajada_fresca", "ajonjoli_en_cubierta"],
        accompanied_by=["taza_de_cafe_de_altura"],
        regional_association="Domingos por la mañana, municipios lecheros (Metapán, San Vicente, Santa Rosa de Lima)",
        preparation_difficulty=0.65,
        estimated_cost_usd=1.50,
        cultural_salience=0.93,
    ),
}


@dataclasses.dataclass(frozen=True)
class SalvadoranFestivity:
    """A patron saint festivity or national cultural celebration."""
    festivity_id: str
    name: str
    department_code: str
    month: int                          # 1 to 12
    patron_saint_or_theme: str
    typical_activities: list[str]
    required_materials: list[str]       # pólvora, flores, música, mantas
    economic_impact_description: str


SALVADORAN_FESTIVITIES: dict[str, SalvadoranFestivity] = {
    "fiestas_agostinas": SalvadoranFestivity(
        festivity_id="fiestas_agostinas",
        name="Fiestas Agostinas de San Salvador",
        department_code="SS",
        month=8, # August 1 to 6
        patron_saint_or_theme="Divino Salvador del Mundo (Patrono Nacional)",
        typical_activities=[
            "Desfile del Correo",
            "Desfile del Comercio",
            "La Bajada (Transfiguración frente a Catedral)",
            "Juegos mecánicos en feria Consuma",
            "Venta masiva de dulces típicos (camote, nance, guayaba)",
        ],
        required_materials=["polvora_artesanal", "flores_de_ensarte", "toldos_de_mercado", "carrozas"],
        economic_impact_description="Pico comercial del año para microempresas de comida callejera, turismo interno y comercio formal",
    ),
    "carnaval_san_miguel": SalvadoranFestivity(
        festivity_id="carnaval_san_miguel",
        name="Carnaval de San Miguel",
        department_code="SM",
        month=11, # Late November
        patron_saint_or_theme="Virgen de la Paz",
        typical_activities=[
            "Desfile de carrozas monumentales",
            "Orquestas y cumbias en toda la Avenida Roosevelt",
            "Carnavales barriales previos",
            "Llegada masiva de la diáspora salvadoreña desde EE.UU.",
        ],
        required_materials=["sonido_e_iluminacion", "vestuarios_artesanales", "hielo_y_bebidas", "tarimas"],
        economic_impact_description="Mayor inyección de liquidez y remesas de turistas del oriente; hoteles y pupuserías colapsan de demanda",
    ),
    "fiestas_julianas": SalvadoranFestivity(
        festivity_id="fiestas_julianas",
        name="Fiestas Julianas de Santa Ana",
        department_code="SA",
        month=7, # July 17 to 26
        patron_saint_or_theme="Señora Santa Ana",
        typical_activities=[
            "Feria ganadera y jaripeos",
            "Procesión solemne con imagen de Señora Santa Ana",
            "Encuentros de bandas de paz",
            "Degustación de dulces y atoles",
        ],
        required_materials=["ganado_en_exhibicion", "polvora", "altares_florales"],
        economic_impact_description="Impulsa transacciones agropecuarias, tiangues de ganado y comercio minorista en la zona occidental",
    ),
    "dia_de_la_cruz": SalvadoranFestivity(
        festivity_id="dia_de_la_cruz",
        name="Celebración del Día de la Cruz",
        department_code="SS", # Celebrated nationwide in all homes
        month=5, # May 3
        patron_saint_or_theme="Cruz de Jiote y anuncio de la temporada de lluvias (agradecimiento a la tierra)",
        typical_activities=[
            "Instalación de la cruz de palo de jiote en patios y solares",
            "Adorno con cadenas de papel de china encerado y frutas de estación (mangos, coyoles, jocotes, mamey)",
            "Persignarse ante la cruz y comer una fruta de ofrenda",
        ],
        required_materials=["madera_de_jiote", "papel_de_china_picado", "fruta_de_temporada"],
        economic_impact_description="Auge de venta para pequeños agricultores y marchantas de mercado vendiendo frutas de estación",
    ),
    "semana_santa_alfombras": SalvadoranFestivity(
        festivity_id="semana_santa_alfombras",
        name="Semana Santa y Alfombras Tradicionales",
        department_code="SO", # Sonsonate is national capital of alfombras
        month=4, # April (or March)
        patron_saint_or_theme="Pasión y Santo Entierro de Cristo",
        typical_activities=[
            "Elaboración comunitaria nocturna de alfombras de sal y aserrín teñido",
            "Procesiones solemnes con tambores y matracas",
            "Consumo familiar de sopa de tortas de pescado seco y nuégados con miel de panela",
        ],
        required_materials=["sal_refinada_o_grano", "anilinas_y_tintes", "aserrin_fino", "pescado_seco"],
        economic_impact_description="Cooperación vecinal intensiva en barrios tradicionales; alta demanda de sal y pescado seco",
    ),
}
