"""
Salvadoran Spanish Lexicon, Pragmatics, and Sociolinguistic Registers.

Captures authentic Salvadoran communicative patterns:
- Voseo pronominal paradigm and verbal morphology ("vos sabés", "mirá", "hacéme el favor")
- Ustedeo for intergenerational respect and formal institutions ("don / doña", "usted")
- Authentic Salvadoreñismos / Caliche vocabulary with semantic definitions and registers
- Agrarian and market measurement units (manzana, tarea, arroba, canasto, cora, cuatro)
- Pragmatic discourse markers ("Dios primero", "por la misericordia de Dios", "con permiso", "fijate que...")
"""

from __future__ import annotations
import dataclasses
from enum import Enum
from typing import Any, Optional


class LinguisticRegister(str, Enum):
    """Sociolinguistic register in Salvadoran Spanish."""
    INTIMATE_FAMILY = "intimate_family"       # Voseo, terms of endearment, domestic talk
    COLLEGIATE_INFORMAL = "collegiate_informal" # Voseo between friends ("cheros"), everyday street caliche
    RESPECTFUL_ELDER = "respectful_elder"     # Ustedeo towards parents, grandparents, venerable neighbors
    FORMAL_INSTITUTIONAL = "formal_institutional" # Ustedeo in legal, municipal, church, or business settings
    RURAL_CAMPESINO = "rural_campesino"       # Agricultural terms, traditional folk expressions, reverential religious markers


@dataclasses.dataclass(frozen=True)
class SalvadoranLexicalEntry:
    """A dictionary entry for a Salvadoran word or idiomatic phrase."""
    term: str
    standard_equivalent: str
    semantic_domain: str                 # "social_relation", "money_commerce", "food", "character", "general"
    registers_allowed: list[LinguisticRegister]
    example_sentence: str
    generational_bias: str               # "all", "older_rural", "youth_urban"
    is_pejorative: bool = False


SALVADORAN_LEXICON: dict[str, SalvadoranLexicalEntry] = {
    "chero": SalvadoranLexicalEntry(
        term="chero / chera",
        standard_equivalent="amigo / compañero de confianza",
        semantic_domain="social_relation",
        registers_allowed=[LinguisticRegister.COLLEGIATE_INFORMAL, LinguisticRegister.INTIMATE_FAMILY],
        example_sentence="El Juan es mi chero de toda la vida, crecimos juntos en el cantón.",
        generational_bias="all",
    ),
    "cipote": SalvadoranLexicalEntry(
        term="cipote / cipota",
        standard_equivalent="niño / muchacho / joven",
        semantic_domain="social_relation",
        registers_allowed=[LinguisticRegister.COLLEGIATE_INFORMAL, LinguisticRegister.INTIMATE_FAMILY, LinguisticRegister.RURAL_CAMPESINO],
        example_sentence="Mandá al cipote a la tienda a traer una cora de pan francés.",
        generational_bias="all",
    ),
    "bicho": SalvadoranLexicalEntry(
        term="bicho / bicha",
        standard_equivalent="niño / joven / menor de edad",
        semantic_domain="social_relation",
        registers_allowed=[LinguisticRegister.COLLEGIATE_INFORMAL, LinguisticRegister.INTIMATE_FAMILY],
        example_sentence="Esos bichos andan jugando fútbol descalzos en la calle de tierra.",
        generational_bias="all",
    ),
    "pisto": SalvadoranLexicalEntry(
        term="pisto",
        standard_equivalent="dinero / efectivo",
        semantic_domain="money_commerce",
        registers_allowed=[LinguisticRegister.COLLEGIATE_INFORMAL, LinguisticRegister.INTIMATE_FAMILY, LinguisticRegister.RURAL_CAMPESINO],
        example_sentence="Ahorita no ando pisto para comprar el abono, hasta que me caiga la remesa.",
        generational_bias="all",
    ),
    "volado": SalvadoranLexicalEntry(
        term="volado",
        standard_equivalent="asunto / encargo / objeto no especificado",
        semantic_domain="general",
        registers_allowed=[LinguisticRegister.COLLEGIATE_INFORMAL, LinguisticRegister.INTIMATE_FAMILY],
        example_sentence="Hacéme el volado de cuidar el puesto mientras voy a almorzar.",
        generational_bias="all",
    ),
    "chivo": SalvadoranLexicalEntry(
        term="chivo / bien chivo",
        standard_equivalent="bueno / excelente / agradable / conveniente",
        semantic_domain="general",
        registers_allowed=[LinguisticRegister.COLLEGIATE_INFORMAL, LinguisticRegister.INTIMATE_FAMILY],
        example_sentence="¡Qué chivo que llovió anoche! Ya le hacía falta agua a la milpa.",
        generational_bias="all",
    ),
    "cora": SalvadoranLexicalEntry(
        term="cora",
        standard_equivalent="moneda de 25 centavos de dólar (quarter)",
        semantic_domain="money_commerce",
        registers_allowed=[LinguisticRegister.COLLEGIATE_INFORMAL, LinguisticRegister.INTIMATE_FAMILY, LinguisticRegister.RURAL_CAMPESINO, LinguisticRegister.FORMAL_INSTITUTIONAL],
        example_sentence="Dáme dos pupusas revueltas y una soda de cora.",
        generational_bias="all",
    ),
    "fiado": SalvadoranLexicalEntry(
        term="el fiado / fiar",
        standard_equivalent="crédito informal minorista basado en confianza",
        semantic_domain="money_commerce",
        registers_allowed=[LinguisticRegister.COLLEGIATE_INFORMAL, LinguisticRegister.INTIMATE_FAMILY, LinguisticRegister.RURAL_CAMPESINO],
        example_sentence="Doña María, ¿me lo puede apuntar en el cuaderno de fiado para pagárselo el sábado?",
        generational_bias="all",
    ),
    "chambre": SalvadoranLexicalEntry(
        term="chambre",
        standard_equivalent="chisme / rumor vecinal no verificado",
        semantic_domain="social_relation",
        registers_allowed=[LinguisticRegister.COLLEGIATE_INFORMAL, LinguisticRegister.INTIMATE_FAMILY],
        example_sentence="No le hagás caso a esos chambres, la gente inventa porque no tiene qué hacer.",
        generational_bias="all",
    ),
    "cachada": SalvadoranLexicalEntry(
        term="cachada",
        standard_equivalent="ganga / oportunidad comercial económica",
        semantic_domain="money_commerce",
        registers_allowed=[LinguisticRegister.COLLEGIATE_INFORMAL, LinguisticRegister.INTIMATE_FAMILY],
        example_sentence="Conseguí una cachada de herramientas usadas en el mercado central.",
        generational_bias="all",
    ),
    "faena": SalvadoranLexicalEntry(
        term="faena comunal",
        standard_equivalent="jornada voluntaria de trabajo colectivo comunitario",
        semantic_domain="social_relation",
        registers_allowed=[LinguisticRegister.RURAL_CAMPESINO, LinguisticRegister.FORMAL_INSTITUTIONAL, LinguisticRegister.COLLEGIATE_INFORMAL],
        example_sentence="El domingo tenemos faena con la ADESCO para bachear la cuesta del cantón.",
        generational_bias="older_rural",
    ),
    "dios_primero": SalvadoranLexicalEntry(
        term="Dios primero",
        standard_equivalent="si Dios lo permite / esperanza confiada en el porvenir",
        semantic_domain="general",
        registers_allowed=[LinguisticRegister.RURAL_CAMPESINO, LinguisticRegister.RESPECTFUL_ELDER, LinguisticRegister.INTIMATE_FAMILY],
        example_sentence="Dios primero tengamos buena cosecha de maíz este invierno.",
        generational_bias="older_rural",
    ),
    "canasto": SalvadoranLexicalEntry(
        term="canasto / canastada",
        standard_equivalent="medida tradicional de corte de café o canasta de mimbre",
        semantic_domain="money_commerce",
        registers_allowed=[LinguisticRegister.RURAL_CAMPESINO, LinguisticRegister.COLLEGIATE_INFORMAL],
        example_sentence="Ayer corté cuatro canastos de café maduro en la finca.",
        generational_bias="older_rural",
    ),
    "tarea": SalvadoranLexicalEntry(
        term="tarea de tierra",
        standard_equivalent="medida agraria tradicional de superficie o jornal de siembra",
        semantic_domain="general",
        registers_allowed=[LinguisticRegister.RURAL_CAMPESINO],
        example_sentence="Ya limpié dos tareas de rastrojo para empezar a sembrar.",
        generational_bias="older_rural",
    ),
}
