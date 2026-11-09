"""Mock dataset generator for Saltbor's initial population of 20 individuals.

Produces 20 meaningfully differentiated personas rooted in Salvadoran culture,
with realistic occupations, personality traits, physical baselines, home assignments,
and initial social networks. All generated data is explicitly tagged as MOCK_GENERATED.
"""

from __future__ import annotations

from typing import Any, Optional

import numpy as np

from saltbor.core.types import DataSource, Gender


# The 20 distinct persona archetypes
PERSONA_TEMPLATES: list[dict[str, Any]] = [
    {
        "serial": 1,
        "given_name": "Carlos",
        "family_name": "Rivera Flores",
        "nickname": "Don Carlos",
        "age": 48,
        "gender": Gender.MALE,
        "occupation": "Carpintero Maestro",
        "education_level": "Secundaria Técnica",
        "income_level": 0.55,
        "home_id": "casa_norte_1",
        "work_id": "taller_artesanal",
        "money": 120.0,
        "personality": {
            "openness": 0.50, "conscientiousness": 0.85, "extraversion": 0.55,
            "agreeableness": 0.75, "neuroticism": 0.30, "risk_tolerance": 0.40,
            "patience": 0.80, "persistence": 0.85
        },
        "strengths": ["Ebanistería", "Paciencia", "Resolución de problemas prácticos"],
        "weaknesses": ["Resistencia al cambio tecnológico"],
        "aspirations": "Construir un taller modelo y entrenar aprendices jóvenes.",
    },
    {
        "serial": 2,
        "given_name": "María Elena",
        "family_name": "Gómez de Rivera",
        "nickname": "Doña Elena",
        "age": 45,
        "gender": Gender.FEMALE,
        "occupation": "Cocinera y Dueña de Comedor",
        "education_level": "Secundaria Completa",
        "income_level": 0.60,
        "home_id": "casa_norte_1",
        "work_id": "comedor_dona_maria",
        "money": 150.0,
        "personality": {
            "openness": 0.65, "conscientiousness": 0.80, "extraversion": 0.85,
            "agreeableness": 0.90, "neuroticism": 0.35, "risk_tolerance": 0.50,
            "patience": 0.70, "persistence": 0.80
        },
        "strengths": ["Gastronomía tradicional", "Empatía", "Liderazgo comunitario"],
        "weaknesses": ["Sobrecarga de trabajo por cuidar a todos"],
        "aspirations": "Hacer de su comedor el corazón cultural y solidario de Saltbor.",
    },
    {
        "serial": 3,
        "given_name": "Mateo",
        "family_name": "Rivera Gómez",
        "nickname": "Teo",
        "age": 20,
        "gender": Gender.MALE,
        "occupation": "Estudiante y Aprendiz de Taller",
        "education_level": "Bachillerato Técnico en Curso",
        "income_level": 0.25,
        "home_id": "casa_norte_1",
        "work_id": "escuela_comunal",
        "money": 35.0,
        "personality": {
            "openness": 0.80, "conscientiousness": 0.50, "extraversion": 0.70,
            "agreeableness": 0.65, "neuroticism": 0.45, "risk_tolerance": 0.70,
            "patience": 0.40, "persistence": 0.60
        },
        "strengths": ["Curiosidad tecnológica", "Creatividad", "Energía juvenil"],
        "weaknesses": ["Impulsividad", "Falta de constancia"],
        "aspirations": "Diseñar maquinaria agrícola solar para la comunidad.",
    },
    {
        "serial": 4,
        "given_name": "Sofía",
        "family_name": "Hernández Ramos",
        "nickname": "Profe Sofi",
        "age": 34,
        "gender": Gender.FEMALE,
        "occupation": "Profesora de Escuela Primaria",
        "education_level": "Licenciatura en Ciencias de la Educación",
        "income_level": 0.50,
        "home_id": "casa_norte_2",
        "work_id": "escuela_comunal",
        "money": 95.0,
        "personality": {
            "openness": 0.85, "conscientiousness": 0.75, "extraversion": 0.75,
            "agreeableness": 0.85, "neuroticism": 0.35, "risk_tolerance": 0.45,
            "patience": 0.85, "persistence": 0.75
        },
        "strengths": ["Pedagogía activa", "Fomento a la lectura", "Paciencia"],
        "weaknesses": ["Dificultad para desconectarse de las necesidades escolares"],
        "aspirations": "Crear la biblioteca comunal más completa de la región.",
    },
    {
        "serial": 5,
        "given_name": "David",
        "family_name": "Alvarado Cruz",
        "nickname": "Dave",
        "age": 36,
        "gender": Gender.MALE,
        "occupation": "Enfermero Comunitario",
        "education_level": "Técnico en Enfermería y Salud Pública",
        "income_level": 0.55,
        "home_id": "casa_norte_2",
        "work_id": "clinica_salud",
        "money": 110.0,
        "personality": {
            "openness": 0.60, "conscientiousness": 0.85, "extraversion": 0.60,
            "agreeableness": 0.80, "neuroticism": 0.40, "risk_tolerance": 0.35,
            "patience": 0.75, "persistence": 0.80
        },
        "strengths": ["Atención primaria", "Calma bajo presión", "Higiene y protocolos"],
        "weaknesses": ["Desgaste emocional por casos difíciles"],
        "aspirations": "Erradicar las infecciones respiratorias estacionales infantiles.",
    },
    {
        "serial": 6,
        "given_name": "Rosa Isabel",
        "family_name": "Mendoza Santos",
        "nickname": "Rosita",
        "age": 52,
        "gender": Gender.FEMALE,
        "occupation": "Comerciante de Frutas y Verduras",
        "education_level": "Primaria Completa",
        "income_level": 0.45,
        "home_id": "casa_sur_1",
        "work_id": "mercado_central",
        "money": 80.0,
        "personality": {
            "openness": 0.40, "conscientiousness": 0.75, "extraversion": 0.80,
            "agreeableness": 0.70, "neuroticism": 0.45, "risk_tolerance": 0.50,
            "patience": 0.65, "persistence": 0.85
        },
        "strengths": ["Negociación justa", "Vigor madrugador", "Redes de proveedores"],
        "weaknesses": ["Preocupación crónica por fluctuaciones de precios"],
        "aspirations": "Modernizar la cadena de frío del mercado municipal.",
    },
    {
        "serial": 7,
        "given_name": "Joaquín",
        "family_name": "Vásquez Portillo",
        "nickname": "Don Quino",
        "age": 62,
        "gender": Gender.MALE,
        "occupation": "Director de Cooperativa Agrícola",
        "education_level": "Secundaria e Instructor Agrícola",
        "income_level": 0.65,
        "home_id": "casa_sur_1",
        "work_id": "cooperativa_agricola",
        "money": 180.0,
        "personality": {
            "openness": 0.55, "conscientiousness": 0.85, "extraversion": 0.65,
            "agreeableness": 0.70, "neuroticism": 0.25, "risk_tolerance": 0.45,
            "patience": 0.85, "persistence": 0.90
        },
        "strengths": ["Conocimiento de suelos y semillas", "Liderazgo cooperativo", "Prudencia"],
        "weaknesses": ["Terquedad en métodos agrícolas tradicionales"],
        "aspirations": "Garantizar la soberanía alimentaria y reservas de maíz en Saltbor.",
    },
    {
        "serial": 8,
        "given_name": "Lucía",
        "family_name": "Vásquez Santos",
        "nickname": "Lucy",
        "age": 27,
        "gender": Gender.FEMALE,
        "occupation": "Agrónoma y Técnica de Cultivos",
        "education_level": "Ingeniería Agronómica",
        "income_level": 0.55,
        "home_id": "casa_sur_1",
        "work_id": "cooperativa_agricola",
        "money": 90.0,
        "personality": {
            "openness": 0.85, "conscientiousness": 0.75, "extraversion": 0.60,
            "agreeableness": 0.75, "neuroticism": 0.35, "risk_tolerance": 0.60,
            "patience": 0.70, "persistence": 0.80
        },
        "strengths": ["Biotecnología agroecológica", "Riego por goteo", "Análisis de datos"],
        "weaknesses": ["Frustración ante la lentitud burocrática"],
        "aspirations": "Implementar huertos orgánicos y compostaje en todo Saltbor.",
    },
    {
        "serial": 9,
        "given_name": "Héctor",
        "family_name": "Castillo Ortiz",
        "nickname": "Teto",
        "age": 41,
        "gender": Gender.MALE,
        "occupation": "Mecánico y Soldador",
        "education_level": "Secundaria Técnica",
        "income_level": 0.50,
        "home_id": "casa_sur_2",
        "work_id": "taller_artesanal",
        "money": 100.0,
        "personality": {
            "openness": 0.50, "conscientiousness": 0.70, "extraversion": 0.50,
            "agreeableness": 0.60, "neuroticism": 0.40, "risk_tolerance": 0.55,
            "patience": 0.65, "persistence": 0.75
        },
        "strengths": ["Reparación de motores y bombas de agua", "Inventiva con chatarra"],
        "weaknesses": ["Carácter reservado y a veces brusco"],
        "aspirations": "Restaurar el tractor colectivo de la cooperativa.",
    },
    {
        "serial": 10,
        "given_name": "Gabriela",
        "family_name": "Pérez Miranda",
        "nickname": "Gaby",
        "age": 29,
        "gender": Gender.FEMALE,
        "occupation": "Costurera y Diseñadora Textil",
        "education_level": "Bachillerato General",
        "income_level": 0.40,
        "home_id": "casa_sur_2",
        "work_id": "mercado_central",
        "money": 70.0,
        "personality": {
            "openness": 0.80, "conscientiousness": 0.65, "extraversion": 0.55,
            "agreeableness": 0.75, "neuroticism": 0.45, "risk_tolerance": 0.50,
            "patience": 0.70, "persistence": 0.70
        },
        "strengths": ["Confección y bordado a mano", "Ojo para los colores", "Detallismo"],
        "weaknesses": ["Inseguridad al cobrar por su trabajo artesanal"],
        "aspirations": "Crear un colectivo de tejedoras y comercializar bordados.",
    },
    {
        "serial": 11,
        "given_name": "Antonio",
        "family_name": "Montoya Benítez",
        "nickname": "Toño",
        "age": 55,
        "gender": Gender.MALE,
        "occupation": "Panadero Artesanal",
        "education_level": "Secundaria Incompleta",
        "income_level": 0.50,
        "home_id": "casa_este_1",
        "work_id": "mercado_central",
        "money": 85.0,
        "personality": {
            "openness": 0.45, "conscientiousness": 0.85, "extraversion": 0.65,
            "agreeableness": 0.80, "neuroticism": 0.30, "risk_tolerance": 0.35,
            "patience": 0.90, "persistence": 0.85
        },
        "strengths": ["Fermentación tradicional", "Disciplina de madrugada", "Puntualidad"],
        "weaknesses": ["Fatiga acumulada por horarios de horno"],
        "aspirations": "Hornear el pan dulce más reconocido del departamento.",
    },
    {
        "serial": 12,
        "given_name": "Carmen",
        "family_name": "Zelaya de Montoya",
        "nickname": "Carmencita",
        "age": 53,
        "gender": Gender.FEMALE,
        "occupation": "Secretaria Comunal y Gestora",
        "education_level": "Secretariado Comercial",
        "income_level": 0.50,
        "home_id": "casa_este_1",
        "work_id": "casa_comunal",
        "money": 115.0,
        "personality": {
            "openness": 0.60, "conscientiousness": 0.90, "extraversion": 0.70,
            "agreeableness": 0.80, "neuroticism": 0.35, "risk_tolerance": 0.30,
            "patience": 0.85, "persistence": 0.80
        },
        "strengths": ["Organización de actas", "Memoria institucional", "Mediación"],
        "weaknesses": ["Aversión extrema al desorden"],
        "aspirations": "Digitalizar el archivo histórico y catastral de Saltbor.",
    },
    {
        "serial": 13,
        "given_name": "Emilio",
        "family_name": "Montoya Zelaya",
        "nickname": "Milo",
        "age": 22,
        "gender": Gender.MALE,
        "occupation": "Electricista y Soporte Técnico",
        "education_level": "Técnico Electricista",
        "income_level": 0.45,
        "home_id": "casa_este_1",
        "work_id": "taller_artesanal",
        "money": 60.0,
        "personality": {
            "openness": 0.75, "conscientiousness": 0.70, "extraversion": 0.65,
            "agreeableness": 0.70, "neuroticism": 0.35, "risk_tolerance": 0.55,
            "patience": 0.60, "persistence": 0.70
        },
        "strengths": ["Instalaciones eléctricas seguras", "Reparación de celulares y radios"],
        "weaknesses": ["Distracción con proyectos personales"],
        "aspirations": "Instalar una red de radio comunitaria y energía solar vecinal.",
    },
    {
        "serial": 14,
        "given_name": "Teresa",
        "family_name": "Figueroa Rivas",
        "nickname": "Doña Tere",
        "age": 70,
        "gender": Gender.FEMALE,
        "occupation": "Curandera Tradicional y Cronista",
        "education_level": "Saber Ancestral y Primaria",
        "income_level": 0.30,
        "home_id": "casa_oeste_1",
        "work_id": "clinica_salud",
        "money": 50.0,
        "personality": {
            "openness": 0.75, "conscientiousness": 0.70, "extraversion": 0.60,
            "agreeableness": 0.85, "neuroticism": 0.25, "risk_tolerance": 0.35,
            "patience": 0.95, "persistence": 0.80
        },
        "strengths": ["Herbolaria medicinal", "Memoria oral", "Consejo sabio"],
        "weaknesses": ["Limitaciones físicas propias de la edad"],
        "aspirations": "Transmitir los saberes medicinales antes de que se olviden.",
    },
    {
        "serial": 15,
        "given_name": "Manuel",
        "family_name": "Cáceres Lemus",
        "nickname": "Meme",
        "age": 38,
        "gender": Gender.MALE,
        "occupation": "Agricultor y Apicultor",
        "education_level": "Secundaria Completa",
        "income_level": 0.45,
        "home_id": "casa_oeste_1",
        "work_id": "cooperativa_agricola",
        "money": 75.0,
        "personality": {
            "openness": 0.65, "conscientiousness": 0.80, "extraversion": 0.45,
            "agreeableness": 0.75, "neuroticism": 0.30, "risk_tolerance": 0.50,
            "patience": 0.85, "persistence": 0.85
        },
        "strengths": ["Manejo de abejas", "Observación de clima", "Paciencia"],
        "weaknesses": ["Poco comunicativo en asambleas grandes"],
        "aspirations": "Aumentar a 50 las colmenas y exportar miel pura.",
    },
    {
        "serial": 16,
        "given_name": "Adriana",
        "family_name": "Mejía Solórzano",
        "nickname": "Adri",
        "age": 31,
        "gender": Gender.FEMALE,
        "occupation": "Música y Animadora Cultural",
        "education_level": "Profesorado en Artes Musicales",
        "income_level": 0.35,
        "home_id": "casa_oeste_1",
        "work_id": "casa_comunal",
        "money": 45.0,
        "personality": {
            "openness": 0.90, "conscientiousness": 0.55, "extraversion": 0.85,
            "agreeableness": 0.80, "neuroticism": 0.50, "risk_tolerance": 0.65,
            "patience": 0.55, "persistence": 0.65
        },
        "strengths": ["Guitarra, canto y percusión", "Carisma festivo", "Improvisación"],
        "weaknesses": ["Inestabilidad de ingresos", "Desorganización financiera"],
        "aspirations": "Formar la orquesta infantil de guitarras y marimba de Saltbor.",
    },
    {
        "serial": 17,
        "given_name": "Fernando",
        "family_name": "Quinteros Paz",
        "nickname": "Fercho",
        "age": 44,
        "gender": Gender.MALE,
        "occupation": "Transportista y Conductor de Camioneta",
        "education_level": "Secundaria Completa",
        "income_level": 0.55,
        "home_id": "casa_norte_2",
        "work_id": "mercado_central",
        "money": 130.0,
        "personality": {
            "openness": 0.55, "conscientiousness": 0.70, "extraversion": 0.80,
            "agreeableness": 0.65, "neuroticism": 0.35, "risk_tolerance": 0.60,
            "patience": 0.60, "persistence": 0.75
        },
        "strengths": ["Manejo en caminos difíciles", "Conocimiento de rutas rurales", "Buen humor"],
        "weaknesses": ["Gasto impulsivo en repuestos y accesorios"],
        "aspirations": "Comprar un microbús para conectar Saltbor con el hospital cabecera.",
    },
    {
        "serial": 18,
        "given_name": "Claudia",
        "family_name": "Baires Choto",
        "nickname": "Clau",
        "age": 25,
        "gender": Gender.FEMALE,
        "occupation": "Asistente de Farmacia y Botiquín",
        "education_level": "Técnico en Farmacia",
        "income_level": 0.45,
        "home_id": "casa_sur_2",
        "work_id": "clinica_salud",
        "money": 65.0,
        "personality": {
            "openness": 0.70, "conscientiousness": 0.85, "extraversion": 0.60,
            "agreeableness": 0.80, "neuroticism": 0.30, "risk_tolerance": 0.35,
            "patience": 0.80, "persistence": 0.75
        },
        "strengths": ["Conocimiento de fármacos básicos", "Atención empática", "Precisión"],
        "weaknesses": ["Timidez en debates acalorados"],
        "aspirations": "Tener farmacia comunitaria autosostenible con medicamentos asequibles.",
    },
    {
        "serial": 19,
        "given_name": "Óscar",
        "family_name": "Navarro Orellana",
        "nickname": "Don Óscar",
        "age": 66,
        "gender": Gender.MALE,
        "occupation": "Vigilante Comunal y Cuidador de Parque",
        "education_level": "Primaria",
        "income_level": 0.35,
        "home_id": "casa_este_1",
        "work_id": "parque_la_ceiba",
        "money": 55.0,
        "personality": {
            "openness": 0.40, "conscientiousness": 0.80, "extraversion": 0.50,
            "agreeableness": 0.70, "neuroticism": 0.30, "risk_tolerance": 0.25,
            "patience": 0.90, "persistence": 0.85
        },
        "strengths": ["Sentido del deber", "Vigilancia nocturna", "Conocimiento del terreno"],
        "weaknesses": ["Desconfianza inicial ante personas forasteras"],
        "aspirations": "Mantener el parque y la ceiba protegidos contra vandalismo y tala.",
    },
    {
        "serial": 20,
        "given_name": "Valeria",
        "family_name": "Castillo Ramos",
        "nickname": "Vale",
        "age": 19,
        "gender": Gender.FEMALE,
        "occupation": "Estudiante y Diseñadora Digital Autodidacta",
        "education_level": "Bachillerato General Reciente",
        "income_level": 0.20,
        "home_id": "casa_sur_2",
        "work_id": "casa_comunal",
        "money": 25.0,
        "personality": {
            "openness": 0.90, "conscientiousness": 0.60, "extraversion": 0.65,
            "agreeableness": 0.75, "neuroticism": 0.45, "risk_tolerance": 0.65,
            "patience": 0.50, "persistence": 0.65
        },
        "strengths": ["Diseño gráfico digital", "Redes sociales", "Facilidad con software"],
        "weaknesses": ["Ansiedad por el futuro laboral"],
        "aspirations": "Ganar una beca universitaria en ciencias de la computación.",
    },
]


class MockDataGenerator:
    """Generates initial demographic profiles and starting network connections."""

    @staticmethod
    def get_personas() -> list[dict[str, Any]]:
        return list(PERSONA_TEMPLATES)

    @staticmethod
    def get_initial_relationships() -> list[dict[str, Any]]:
        """Pre-existing social ties representing family, work partners, and close neighbors."""
        return [
            # Family: Carlos & María Elena (Husband & Wife)
            {"serial_a": 1, "serial_b": 2, "type": "partner", "trust": 0.90, "affinity": 0.92, "familiarity": 0.95},
            # Family: Carlos & Mateo (Father & Son)
            {"serial_a": 1, "serial_b": 3, "type": "family", "trust": 0.85, "affinity": 0.80, "familiarity": 0.90},
            # Family: María Elena & Mateo (Mother & Son)
            {"serial_a": 2, "serial_b": 3, "type": "family", "trust": 0.90, "affinity": 0.88, "familiarity": 0.92},
            # Family: Joaquín & Lucía (Father & Daughter)
            {"serial_a": 7, "serial_b": 8, "type": "family", "trust": 0.88, "affinity": 0.85, "familiarity": 0.90},
            # Family: Antonio & Carmen (Husband & Wife)
            {"serial_a": 11, "serial_b": 12, "type": "partner", "trust": 0.88, "affinity": 0.86, "familiarity": 0.93},
            # Family: Antonio/Carmen & Emilio (Parents & Son)
            {"serial_a": 11, "serial_b": 13, "type": "family", "trust": 0.82, "affinity": 0.80, "familiarity": 0.88},
            {"serial_a": 12, "serial_b": 13, "type": "family", "trust": 0.85, "affinity": 0.82, "familiarity": 0.90},
            # Family: Héctor & Gabriela (Siblings in casa_sur_2)
            {"serial_a": 9, "serial_b": 10, "type": "family", "trust": 0.80, "affinity": 0.78, "familiarity": 0.85},
            {"serial_a": 9, "serial_b": 20, "type": "family", "trust": 0.75, "affinity": 0.75, "familiarity": 0.80},
            # Colleagues / Friends:
            # Carlos (Carpenter) & Héctor (Mechanic/Welder) -> Colleagues at Workshop
            {"serial_a": 1, "serial_b": 9, "type": "colleague", "trust": 0.75, "affinity": 0.70, "familiarity": 0.75},
            # Sofía (Teacher) & David (Nurse) -> Good friends in casa_norte_2
            {"serial_a": 4, "serial_b": 5, "type": "close_friend", "trust": 0.82, "affinity": 0.85, "familiarity": 0.80},
            # Rosa (Merchant) & María Elena (Cook) -> Trade partners / friends
            {"serial_a": 6, "serial_b": 2, "type": "friend", "trust": 0.78, "affinity": 0.80, "familiarity": 0.75},
            # Joaquín (Coop Dir) & Manuel (Beekeeper) -> Close farming allies
            {"serial_a": 7, "serial_b": 15, "type": "colleague", "trust": 0.80, "affinity": 0.72, "familiarity": 0.78},
            # Teresa (Healer) & David (Nurse) -> Mutual respect medical partners
            {"serial_a": 14, "serial_b": 5, "type": "colleague", "trust": 0.75, "affinity": 0.72, "familiarity": 0.70},
            # Adriana (Musician) & Mateo (Youth) -> Friendly neighbors
            {"serial_a": 16, "serial_b": 3, "type": "friend", "trust": 0.65, "affinity": 0.70, "familiarity": 0.60},
        ]
