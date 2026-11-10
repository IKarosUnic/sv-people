"""Local offline Natural Language Generation (NLG) engine in regional Salvadoran Spanish."""

from __future__ import annotations

import random
from typing import Optional

import numpy as np

from saltbor.social.language.intent import DialogueIntent, Utterance


class LocalDialogueGenerator:
    """Offline NLG system producing contextual, non-repetitive dialogue utterances."""

    def __init__(self, rng: Optional[np.random.Generator] = None) -> None:
        self.rng = rng or np.random.default_rng()

    def generate_surface_text(
        self,
        utterance: Utterance,
        trust: float = 0.5,
        affinity: float = 0.5,
        speaker_mood: float = 0.0,
    ) -> str:
        """Render a semantic Utterance into varied natural Spanish prose."""
        intent = utterance.intent
        topic = utterance.topic
        is_close = (trust > 0.65 and affinity > 0.60)
        is_formal = not is_close

        if intent == DialogueIntent.GREETING:
            if is_close:
                choices = [
                    f"¡Hola! ¿Cómo te va con lo de {topic}?",
                    f"¡Qué onda! Me alegro de verte por acá.",
                    f"Buenas, qué gusto encontrarte. ¿Cómo va tu día?",
                ]
            else:
                choices = [
                    f"Buenos días. Espero que todo marche bien.",
                    f"Buenas tardes, vecino. Qué tranquilo se ve el pueblo hoy.",
                    f"Saludos. Con permiso para saludarle.",
                ]

        elif intent == DialogueIntent.REQUEST:
            item = utterance.content_data.get("item", topic)
            if is_close:
                choices = [
                    f"Mirá, ¿creés que me podrías echar una mano con {item}?",
                    f"Te quería pedir un favor sincero sobre {item}, si tenés un ratito.",
                    f"Hermano, necesito apoyo con {item}. ¿Podrías ayudarme?",
                ]
            else:
                choices = [
                    f"Disculpe la molestia, ¿sería posible que me colaborara con {item}?",
                    f"Buenas, quisiera solicitarle si tiene disponibilidad para {item}.",
                    f"Le pido con mucho respeto si puede orientarme sobre {item}.",
                ]

        elif intent == DialogueIntent.OFFER:
            offer = utterance.content_data.get("offer", topic)
            choices = [
                f"Te tengo una propuesta sobre {offer}, a ver qué te parece.",
                f"Tengo disponible {offer} por si te resulta de utilidad.",
                f"Con gusto puedo compartirte {offer} si lo estás necesitando.",
            ]

        elif intent == DialogueIntent.AGREEMENT:
            choices = [
                f"Totalmente de acuerdo, me parece lo más sensato.",
                f"Cabal, así es como debemos proceder.",
                f"Me parece excelente, cuente con mi apoyo.",
            ]

        elif intent == DialogueIntent.DISAGREEMENT:
            choices = [
                f"Fijate que no lo veo tan claro; tal vez convenga reconsiderar {topic}.",
                f"Con respeto, discrepo en ese punto. Las condiciones no están dadas.",
                f"No me convence del todo esa idea para {topic}.",
            ]

        elif intent == DialogueIntent.WARNING:
            risk = utterance.content_data.get("risk", topic)
            choices = [
                f"¡Ojo con eso! He escuchado que hay problemas con {risk}.",
                f"Tenga cuidado con {risk}, la situación no está para confiarse.",
                f"Le advierto de buena fe: tome precauciones respecto a {risk}.",
            ]

        elif intent == DialogueIntent.GOSSIP:
            rumor = utterance.content_data.get("statement", topic)
            choices = [
                f"¿Ya supiste lo que dicen? Cuentan que {rumor}.",
                f"Mirá, corre el rumor en el pueblo de que {rumor}.",
                f"Por ahí andan diciendo que {rumor}. No sé qué tan cierto sea, pero es lo que suena.",
            ]

        elif intent == DialogueIntent.BEREAVEMENT_CONDOLENCE:
            name = utterance.content_data.get("name", "nuestro ser querido")
            choices = [
                f"Mi más sentido pésame por la partida de {name}. Estamos con ustedes en este dolor.",
                f"Lamento de todo corazón lo sucedido con {name}. Que descanse en paz.",
                f"Qué gran tristeza la pérdida de {name}. Cuente con todo mi apoyo fraternal.",
            ]

        elif intent == DialogueIntent.APOLOGY:
            choices = [
                f"Le ofrezco una disculpa sincera; reconozco que me equivoqué respecto a {topic}.",
                f"Perdón si causé alguna molestia con {topic}, no era mi intención.",
                f"Siento mucho el malentendido, quisiera que estemos en paz.",
            ]

        else:
            choices = [
                f"Hablemos sobre {topic}.",
                f"Quería comentarte algo respecto a {topic}.",
                f"Es importante considerar el tema de {topic}.",
            ]

        idx = int(self.rng.integers(0, len(choices)))
        return choices[idx]
