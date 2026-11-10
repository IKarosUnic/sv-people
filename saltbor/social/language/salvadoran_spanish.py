"""
Salvadoran Spanish Linguistic and Pragmatic Communication Engine (Section 19.5).

Models authentic, culturally grounded Salvadoran communication:
- Voseo pronominal paradigm ('vos sabés', 'mirá', 'hacéme la balona') for familiar relations
- Ustedeo of respect for elders, community authorities, and institutional contexts
- Sociolinguistic registers:
  * INTIMATE_FAMILY (domestic voseo, terms of endearment)
  * COLLEGIATE_INFORMAL (chero-talk, street caliche)
  * RESPECTFUL_ELDER (reverential ustedeo, 'don/doña', traditional greetings)
  * FORMAL_INSTITUTIONAL (municipal, church, legal, trade hearings)
  * RURAL_CAMPESINO (agricultural measures, pious formulas: 'Dios primero')
- Generational divergence (older rural speakers vs. younger urban speakers)
- Natural dialogue generation without caricature or exaggerated stereotypes
"""

from __future__ import annotations
import dataclasses
from typing import Any, Optional

from saltbor.datasets.salvadoran import (
    SALVADORAN_LEXICON,
    LinguisticRegister,
    SalvadoranLexicalEntry,
)


@dataclasses.dataclass
class SalvadoranUtterance:
    """A natural utterance spoken by a Salvadoran synthetic human."""
    speaker_uid: str
    recipient_uid: str
    register: LinguisticRegister
    uses_voseo: bool
    text: str
    underlying_intent: str
    salvadorenismos_included: list[str]


class SalvadoranSpanishEngine:
    """Generates authentic Salvadoran dialogue matching sociolinguistic context."""

    def __init__(self) -> None:
        self._lexicon: dict[str, SalvadoranLexicalEntry] = dict(SALVADORAN_LEXICON)

    def determine_appropriate_register(
        self,
        speaker_age: float,
        recipient_age: float,
        relationship_trust: float = 0.5,
        is_family: bool = False,
        is_rural: bool = False,
        is_institutional_setting: bool = False,
    ) -> LinguisticRegister:
        """Select sociolinguistically accurate register based on interpersonal context."""
        if is_institutional_setting:
            return LinguisticRegister.FORMAL_INSTITUTIONAL

        # Deference to elders: if recipient is significantly older (>20 years difference and age >= 55)
        if recipient_age >= 55.0 and (recipient_age - speaker_age) >= 15.0:
            return LinguisticRegister.RESPECTFUL_ELDER

        if is_rural and speaker_age >= 50.0:
            return LinguisticRegister.RURAL_CAMPESINO

        if is_family:
            return LinguisticRegister.INTIMATE_FAMILY

        if relationship_trust >= 0.40:
            return LinguisticRegister.COLLEGIATE_INFORMAL

        # Default to respectful formal between strangers
        return LinguisticRegister.FORMAL_INSTITUTIONAL

    def render_greeting(
        self,
        speaker_uid: str,
        recipient_uid: str,
        register: LinguisticRegister,
        time_of_day: str = "manana", # "manana", "tarde", "noche"
    ) -> SalvadoranUtterance:
        """Generate contextual greeting."""
        salvadorenismos = []

        if register == LinguisticRegister.COLLEGIATE_INFORMAL:
            uses_voseo = True
            salvadorenismos.append("chero")
            text = "¿Qué pasó, chero? ¿Cómo estás? ¿Qué me contás de nuevo?"
        elif register == LinguisticRegister.INTIMATE_FAMILY:
            uses_voseo = True
            text = "¡Hola! Pasá adelante, ¿ya comiste o querés que te sirva algo?"
        elif register == LinguisticRegister.RESPECTFUL_ELDER:
            uses_voseo = False # Strict ustedeo
            salvadorenismos.append("dios_primero")
            greeting_time = "Buenas mañanas tenga usted" if time_of_day == "manana" else "Buenas tardes nos dé Dios"
            text = f"{greeting_time}. ¿Cómo le ha ido con sus quehaceres? Dios primero se encuentre bien de salud."
        elif register == LinguisticRegister.RURAL_CAMPESINO:
            uses_voseo = False
            salvadorenismos.append("dios_primero")
            text = "Buenos días nos dé el Creador. ¿Qué tal amaneció la milpa por su cantón?"
        else: # FORMAL_INSTITUTIONAL
            uses_voseo = False
            text = "Muy buenos días. Mucho gusto en saludarle, pase adelante."

        return SalvadoranUtterance(
            speaker_uid=speaker_uid,
            recipient_uid=recipient_uid,
            register=register,
            uses_voseo=uses_voseo,
            text=text,
            underlying_intent="greeting",
            salvadorenismos_included=salvadorenismos,
        )

    def render_market_inquiry(
        self,
        customer_uid: str,
        vendor_uid: str,
        item_name: str = "frijoles",
        register: LinguisticRegister = LinguisticRegister.COLLEGIATE_INFORMAL,
    ) -> SalvadoranUtterance:
        """Customer inquiring at a market stall or corner store."""
        salvadorenismos = []

        if register in (LinguisticRegister.COLLEGIATE_INFORMAL, LinguisticRegister.INTIMATE_FAMILY):
            uses_voseo = True
            salvadorenismos.append("cora")
            text = f"Buenas doñita, ¿a cuánto me da la libra de {item_name}? Dáme dos coras de eso, por favor."
        else:
            uses_voseo = False
            text = f"Buenos días. Disculpe, ¿a cómo tiene el precio de {item_name} el día de hoy?"

        return SalvadoranUtterance(
            speaker_uid=customer_uid,
            recipient_uid=vendor_uid,
            register=register,
            uses_voseo=uses_voseo,
            text=text,
            underlying_intent="price_inquiry",
            salvadorenismos_included=salvadorenismos,
        )

    def render_community_cooperation_call(
        self,
        organizer_uid: str,
        recipient_uid: str,
        project_description: str = "limpiar la quebrada para evitar inundaciones",
        register: LinguisticRegister = LinguisticRegister.RURAL_CAMPESINO,
    ) -> SalvadoranUtterance:
        """Community leader or neighbor summoning to collective work (faena comunal)."""
        salvadorenismos = ["faena"]
        if register == LinguisticRegister.RURAL_CAMPESINO:
            uses_voseo = False
            salvadorenismos.append("dios_primero")
            text = (
                f"Vecino, le venía a invitar porque este domingo tenemos faena comunal con la ADESCO para {project_description}. "
                f"Dios primero entre todos dejamos terminado el trabajo en la mañana."
            )
        else:
            uses_voseo = True
            salvadorenismos.append("volado")
            text = (
                f"Mirá, el domingo nos vamos a juntar con la mara de la directiva para {project_description}. "
                f"Hacéte la fuerza de llegar para sacar ese volado rápido."
            )

        return SalvadoranUtterance(
            speaker_uid=organizer_uid,
            recipient_uid=recipient_uid,
            register=register,
            uses_voseo=uses_voseo,
            text=text,
            underlying_intent="community_cooperation_request",
            salvadorenismos_included=salvadorenismos,
        )
