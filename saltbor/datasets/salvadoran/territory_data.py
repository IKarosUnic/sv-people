"""
Complete Salvadoran Territorial Dataset (Phase 0.8).

Contains verified political-administrative divisions conforming to the
Ley Especial para la Reestructuración Municipal (effective May 2024):
- 14 Departamentos
- 44 Municipios Vigentes
- 262 Distritos (former municipal seats)
- Real Cantones and Caseríos
- Major Physical Geography (Volcanoes, Lakes, Rivers, Mountain Ranges)
- National Road Networks (CA-1, CA-2, CA-4, CA-12, RN-1, RN-8, bridges, and rural roads)
- Spatial bounding boxes, coordinates (WGS84), elevations, and population statistics.

Strictly 100% offline and pure Python.
"""

from __future__ import annotations
import dataclasses
from enum import Enum
from typing import Any, Optional


class AdministrativeLevel(str, Enum):
    COUNTRY = "country"
    DEPARTMENT = "department"
    MUNICIPALITY = "municipality"
    DISTRICT = "district"
    CANTON = "canton"
    CASERIO = "caserio"
    BARRIO = "barrio"
    COLONIA = "colonia"


@dataclasses.dataclass(frozen=True)
class SalvadoranDistrictData:
    """Official administrative district in El Salvador."""
    district_id: str
    name: str
    municipality_id: str
    department_code: str
    latitude: float
    longitude: float
    elevation_m: float
    approx_population: int
    is_urban_core: bool
    cabecera_distrital: str
    known_cantones: tuple[str, ...] = ()
    source: str = "CNR_IGN_2024"
    source_reference: str = "Ley Especial para la Reestructuracion Municipal D.L. 762"


@dataclasses.dataclass(frozen=True)
class SalvadoranMunicipalityData:
    """Official 2024 consolidated municipality (44 total)."""
    municipality_id: str
    name: str
    department_code: str
    cabecera_municipal: str
    district_ids: tuple[str, ...]
    approx_population: int
    area_km2: float
    centroid_lat: float
    centroid_lon: float


@dataclasses.dataclass(frozen=True)
class SalvadoranDepartmentProfile:
    """Department profile (14 total)."""
    code: str
    name: str
    zone: str
    cabecera: str
    area_km2: float
    population_2024: int
    municipality_ids: tuple[str, ...]
    bounding_box: tuple[float, float, float, float]  # min_lat, min_lon, max_lat, max_lon
    centroid_lat: float
    centroid_lon: float


# =============================================================================
# 1. THE 14 DEPARTMENTS
# =============================================================================

SALVADORAN_DEPARTMENTS_P8: dict[str, SalvadoranDepartmentProfile] = {
    "AH": SalvadoranDepartmentProfile(
        code="AH", name="Ahuachapán", zone="occidental", cabecera="Ahuachapán",
        area_km2=1239.6, population_2024=373000,
        municipality_ids=("ah_norte", "ah_centro", "ah_sur"),
        bounding_box=(13.67, -90.13, 14.07, -89.72),
        centroid_lat=13.88, centroid_lon=-89.92,
    ),
    "SA": SalvadoranDepartmentProfile(
        code="SA", name="Santa Ana", zone="occidental", cabecera="Santa Ana",
        area_km2=2023.2, population_2024=595000,
        municipality_ids=("sa_norte", "sa_centro", "sa_este", "sa_oeste"),
        bounding_box=(13.80, -89.78, 14.45, -89.35),
        centroid_lat=14.10, centroid_lon=-89.55,
    ),
    "SO": SalvadoranDepartmentProfile(
        code="SO", name="Sonsonate", zone="occidental", cabecera="Sonsonate",
        area_km2=1225.2, population_2024=515000,
        municipality_ids=("so_norte", "so_centro", "so_este", "so_oeste"),
        bounding_box=(13.50, -89.93, 13.88, -89.55),
        centroid_lat=13.68, centroid_lon=-89.72,
    ),
    "CH": SalvadoranDepartmentProfile(
        code="CH", name="Chalatenango", zone="central", cabecera="Chalatenango",
        area_km2=2016.6, population_2024=208000,
        municipality_ids=("ch_norte", "ch_centro", "ch_sur"),
        bounding_box=(14.02, -89.35, 14.45, -88.75),
        centroid_lat=14.22, centroid_lon=-89.05,
    ),
    "LL": SalvadoranDepartmentProfile(
        code="LL", name="La Libertad", zone="central", cabecera="Santa Tecla",
        area_km2=1653.0, population_2024=825000,
        municipality_ids=("ll_norte", "ll_centro", "ll_oeste", "ll_este", "ll_costa", "ll_sur"),
        bounding_box=(13.45, -89.60, 13.98, -89.20),
        centroid_lat=13.72, centroid_lon=-89.38,
    ),
    "SS": SalvadoranDepartmentProfile(
        code="SS", name="San Salvador", zone="central", cabecera="San Salvador",
        area_km2=886.2, population_2024=1750000,
        municipality_ids=("ss_norte", "ss_oeste", "ss_este", "ss_centro", "ss_sur"),
        bounding_box=(13.58, -89.32, 14.02, -89.02),
        centroid_lat=13.75, centroid_lon=-89.18,
    ),
    "CU": SalvadoranDepartmentProfile(
        code="CU", name="Cuscatlán", zone="central", cabecera="Cojutepeque",
        area_km2=756.2, population_2024=275000,
        municipality_ids=("cu_norte", "cu_sur"),
        bounding_box=(13.65, -89.15, 14.05, -88.85),
        centroid_lat=13.82, centroid_lon=-89.02,
    ),
    "LP": SalvadoranDepartmentProfile(
        code="LP", name="La Paz", zone="paracentral", cabecera="Zacatecoluca",
        area_km2=1223.6, population_2024=370000,
        municipality_ids=("lp_oeste", "lp_centro", "lp_este"),
        bounding_box=(13.25, -89.18, 13.72, -88.78),
        centroid_lat=13.48, centroid_lon=-88.98,
    ),
    "CA": SalvadoranDepartmentProfile(
        code="CA", name="Cabañas", zone="paracentral", cabecera="Sensuntepeque",
        area_km2=1103.5, population_2024=172000,
        municipality_ids=("ca_este", "ca_oeste"),
        bounding_box=(13.75, -88.92, 14.05, -88.48),
        centroid_lat=13.90, centroid_lon=-88.70,
    ),
    "SV": SalvadoranDepartmentProfile(
        code="SV", name="San Vicente", zone="paracentral", cabecera="San Vicente",
        area_km2=1184.0, population_2024=190000,
        municipality_ids=("sv_norte", "sv_sur"),
        bounding_box=(13.30, -88.92, 13.78, -88.45),
        centroid_lat=13.55, centroid_lon=-88.72,
    ),
    "US": SalvadoranDepartmentProfile(
        code="US", name="Usulután", zone="oriental", cabecera="Usulután",
        area_km2=2130.4, population_2024=385000,
        municipality_ids=("us_norte", "us_este", "us_oeste"),
        bounding_box=(13.15, -88.70, 13.62, -88.22),
        centroid_lat=13.38, centroid_lon=-88.48,
    ),
    "SM": SalvadoranDepartmentProfile(
        code="SM", name="San Miguel", zone="oriental", cabecera="San Miguel",
        area_km2=2077.1, population_2024=520000,
        municipality_ids=("sm_norte", "sm_centro", "sm_oeste"),
        bounding_box=(13.18, -88.45, 13.95, -88.05),
        centroid_lat=13.52, centroid_lon=-88.22,
    ),
    "MO": SalvadoranDepartmentProfile(
        code="MO", name="Morazán", zone="oriental", cabecera="San Francisco Gotera",
        area_km2=1447.4, population_2024=210000,
        municipality_ids=("mo_norte", "mo_sur"),
        bounding_box=(13.60, -88.28, 14.02, -87.95),
        centroid_lat=13.80, centroid_lon=-88.12,
    ),
    "LU": SalvadoranDepartmentProfile(
        code="LU", name="La Unión", zone="oriental", cabecera="La Unión",
        area_km2=2074.3, population_2024=280000,
        municipality_ids=("lu_norte", "lu_sur"),
        bounding_box=(13.12, -88.08, 13.92, -87.68),
        centroid_lat=13.45, centroid_lon=-87.90,
    ),
}


# =============================================================================
# 2. THE 44 MUNICIPALITIES (VIGENTES DESDE MAYO 2024)
# =============================================================================

SALVADORAN_MUNICIPALITIES_P8: dict[str, SalvadoranMunicipalityData] = {
    # Ahuachapán (3)
    "ah_norte": SalvadoranMunicipalityData(
        municipality_id="ah_norte", name="Ahuachapán Norte", department_code="AH",
        cabecera_municipal="Atiquizaya",
        district_ids=("dist_atiquizaya", "dist_el_refugio", "dist_san_lorenzo", "dist_turin"),
        approx_population=95000, area_km2=310.5, centroid_lat=13.98, centroid_lon=-89.82,
    ),
    "ah_centro": SalvadoranMunicipalityData(
        municipality_id="ah_centro", name="Ahuachapán Centro", department_code="AH",
        cabecera_municipal="Ahuachapán",
        district_ids=("dist_ahuachapan", "dist_apaneca", "dist_concepcion_de_ataco", "dist_tacuba"),
        approx_population=185000, area_km2=512.4, centroid_lat=13.91, centroid_lon=-89.92,
    ),
    "ah_sur": SalvadoranMunicipalityData(
        municipality_id="ah_sur", name="Ahuachapán Sur", department_code="AH",
        cabecera_municipal="Guaymango",
        district_ids=("dist_guaymango", "dist_jujutla", "dist_san_francisco_menendez", "dist_san_pedro_puxtla"),
        approx_population=93000, area_km2=416.7, centroid_lat=13.78, centroid_lon=-89.98,
    ),

    # Santa Ana (4)
    "sa_norte": SalvadoranMunicipalityData(
        municipality_id="sa_norte", name="Santa Ana Norte", department_code="SA",
        cabecera_municipal="Metapán",
        district_ids=("dist_masahuat", "dist_metapan", "dist_santa_rosa_guachipilin", "dist_texistepeque"),
        approx_population=110000, area_km2=820.3, centroid_lat=14.28, centroid_lon=-89.45,
    ),
    "sa_centro": SalvadoranMunicipalityData(
        municipality_id="sa_centro", name="Santa Ana Centro", department_code="SA",
        cabecera_municipal="Santa Ana",
        district_ids=("dist_santa_ana",),
        approx_population=280000, area_km2=400.1, centroid_lat=13.99, centroid_lon=-89.56,
    ),
    "sa_este": SalvadoranMunicipalityData(
        municipality_id="sa_este", name="Santa Ana Este", department_code="SA",
        cabecera_municipal="El Congo",
        district_ids=("dist_coatepeque", "dist_el_congo"),
        approx_population=75000, area_km2=240.5, centroid_lat=13.92, centroid_lon=-89.48,
    ),
    "sa_oeste": SalvadoranMunicipalityData(
        municipality_id="sa_oeste", name="Santa Ana Oeste", department_code="SA",
        cabecera_municipal="Chalchuapa",
        district_ids=("dist_candelaria_de_la_frontera", "dist_chalchuapa", "dist_el_porvenir",
                      "dist_san_antonio_pajonal", "dist_san_sebastian_salitrillo", "dist_santiago_de_la_frontera"),
        approx_population=130000, area_km2=562.3, centroid_lat=14.02, centroid_lon=-89.68,
    ),

    # Sonsonate (4)
    "so_norte": SalvadoranMunicipalityData(
        municipality_id="so_norte", name="Sonsonate Norte", department_code="SO",
        cabecera_municipal="Juayúa",
        district_ids=("dist_juayua", "dist_nahuizalco", "dist_salcoatitan", "dist_santa_catarina_masahuat"),
        approx_population=108000, area_km2=285.2, centroid_lat=13.82, centroid_lon=-89.75,
    ),
    "so_centro": SalvadoranMunicipalityData(
        municipality_id="so_centro", name="Sonsonate Centro", department_code="SO",
        cabecera_municipal="Sonsonate",
        district_ids=("dist_sonsonate", "dist_sonzacate", "dist_nahulingo", "dist_san_antonio_del_monte", "dist_santo_domingo_de_guzman"),
        approx_population=205000, area_km2=275.6, centroid_lat=13.72, centroid_lon=-89.72,
    ),
    "so_este": SalvadoranMunicipalityData(
        municipality_id="so_este", name="Sonsonate Este", department_code="SO",
        cabecera_municipal="Izalco",
        district_ids=("dist_armenia", "dist_caluco", "dist_cuisnahuat", "dist_izalco", "dist_san_julian", "dist_santa_isabel_ishuatan"),
        approx_population=145000, area_km2=450.4, centroid_lat=13.73, centroid_lon=-89.62,
    ),
    "so_oeste": SalvadoranMunicipalityData(
        municipality_id="so_oeste", name="Sonsonate Oeste", department_code="SO",
        cabecera_municipal="Acajutla",
        district_ids=("dist_acajutla",),
        approx_population=57000, area_km2=214.0, centroid_lat=13.60, centroid_lon=-89.83,
    ),

    # Chalatenango (3)
    "ch_norte": SalvadoranMunicipalityData(
        municipality_id="ch_norte", name="Chalatenango Norte", department_code="CH",
        cabecera_municipal="La Palma",
        district_ids=("dist_la_palma", "dist_san_ignacio", "dist_citala"),
        approx_population=38000, area_km2=325.8, centroid_lat=14.33, centroid_lon=-89.17,
    ),
    "ch_centro": SalvadoranMunicipalityData(
        municipality_id="ch_centro", name="Chalatenango Centro", department_code="CH",
        cabecera_municipal="Nueva Concepción",
        district_ids=("dist_nueva_concepcion", "dist_agua_caliente", "dist_dulce_nombre_de_maria", "dist_el_paraiso",
                      "dist_la_reina", "dist_san_fernando", "dist_san_francisco_morazan", "dist_san_rafael",
                      "dist_santa_rita", "dist_tejutla"),
        approx_population=92000, area_km2=890.4, centroid_lat=14.18, centroid_lon=-89.20,
    ),
    "ch_sur": SalvadoranMunicipalityData(
        municipality_id="ch_sur", name="Chalatenango Sur", department_code="CH",
        cabecera_municipal="Chalatenango",
        district_ids=("dist_chalatenango", "dist_arcatao", "dist_azacualpa", "dist_comalapa",
                      "dist_concepcion_quezaltepeque", "dist_el_carrizal", "dist_la_laguna", "dist_las_vueltas",
                      "dist_nombre_de_jesus", "dist_nueva_trinidad", "dist_ojos_de_agua", "dist_potonico",
                      "dist_san_antonio_de_la_cruz", "dist_san_antonio_los_ranchos", "dist_san_francisco_lempa",
                      "dist_san_isidro_labrador", "dist_san_jose_cancasque", "dist_san_jose_las_flores",
                      "dist_san_luis_del_carmen", "dist_san_miguel_de_mercedes"),
        approx_population=78000, area_km2=800.4, centroid_lat=14.07, centroid_lon=-88.92,
    ),

    # La Libertad (6)
    "ll_norte": SalvadoranMunicipalityData(
        municipality_id="ll_norte", name="La Libertad Norte", department_code="LL",
        cabecera_municipal="Quezaltepeque",
        district_ids=("dist_quezaltepeque", "dist_san_matias", "dist_san_pablo_tacachico"),
        approx_population=115000, area_km2=320.0, centroid_lat=13.85, centroid_lon=-89.30,
    ),
    "ll_centro": SalvadoranMunicipalityData(
        municipality_id="ll_centro", name="La Libertad Centro", department_code="LL",
        cabecera_municipal="San Juan Opico",
        district_ids=("dist_san_juan_opico", "dist_ciudad_arce"),
        approx_population=160000, area_km2=295.5, centroid_lat=13.82, centroid_lon=-89.40,
    ),
    "ll_oeste": SalvadoranMunicipalityData(
        municipality_id="ll_oeste", name="La Libertad Oeste", department_code="LL",
        cabecera_municipal="Colón",
        district_ids=("dist_colon", "dist_jayaque", "dist_sacacoyo", "dist_tepecoyo", "dist_talnique"),
        approx_population=185000, area_km2=270.8, centroid_lat=13.73, centroid_lon=-89.42,
    ),
    "ll_este": SalvadoranMunicipalityData(
        municipality_id="ll_este", name="La Libertad Este", department_code="LL",
        cabecera_municipal="Antiguo Cuscatlán",
        district_ids=("dist_antiguo_cuscatlan", "dist_huizucar", "dist_nuevo_cuscatlan", "dist_san_jose_villanueva", "dist_zaragoza"),
        approx_population=110000, area_km2=165.2, centroid_lat=13.63, centroid_lon=-89.26,
    ),
    "ll_costa": SalvadoranMunicipalityData(
        municipality_id="ll_costa", name="La Libertad Costa", department_code="LL",
        cabecera_municipal="La Libertad",
        district_ids=("dist_chiltiupan", "dist_jicalapa", "dist_la_libertad", "dist_tamanique", "dist_teotepeque"),
        approx_population=85000, area_km2=395.0, centroid_lat=13.50, centroid_lon=-89.38,
    ),
    "ll_sur": SalvadoranMunicipalityData(
        municipality_id="ll_sur", name="La Libertad Sur", department_code="LL",
        cabecera_municipal="Santa Tecla",
        district_ids=("dist_santa_tecla", "dist_comasagua"),
        approx_population=170000, area_km2=206.5, centroid_lat=13.67, centroid_lon=-89.30,
    ),

    # San Salvador (5)
    "ss_norte": SalvadoranMunicipalityData(
        municipality_id="ss_norte", name="San Salvador Norte", department_code="SS",
        cabecera_municipal="Apopa",
        district_ids=("dist_aguilares", "dist_el_paisnal", "dist_guazapa"),
        approx_population=90000, area_km2=220.0, centroid_lat=13.92, centroid_lon=-89.20,
    ),
    "ss_oeste": SalvadoranMunicipalityData(
        municipality_id="ss_oeste", name="San Salvador Oeste", department_code="SS",
        cabecera_municipal="Apopa",
        district_ids=("dist_apopa", "dist_nejapa"),
        approx_population=210000, area_km2=175.5, centroid_lat=13.80, centroid_lon=-89.20,
    ),
    "ss_este": SalvadoranMunicipalityData(
        municipality_id="ss_este", name="San Salvador Este", department_code="SS",
        cabecera_municipal="Soyapango",
        district_ids=("dist_ilopango", "dist_san_martin", "dist_soyapango", "dist_tonacatepeque"),
        approx_population=580000, area_km2=215.8, centroid_lat=13.72, centroid_lon=-89.12,
    ),
    "ss_centro": SalvadoranMunicipalityData(
        municipality_id="ss_centro", name="San Salvador Centro", department_code="SS",
        cabecera_municipal="San Salvador",
        district_ids=("dist_ayutuxtepeque", "dist_mejicanos", "dist_cuscatancingo", "dist_ciudad_delgado", "dist_san_salvador"),
        approx_population=660000, area_km2=135.0, centroid_lat=13.71, centroid_lon=-89.21,
    ),
    "ss_sur": SalvadoranMunicipalityData(
        municipality_id="ss_sur", name="San Salvador Sur", department_code="SS",
        cabecera_municipal="San Marcos",
        district_ids=("dist_panchimalco", "dist_rosario_de_mora", "dist_san_marcos", "dist_santo_tomas", "dist_santiago_texacuangos"),
        approx_population=210000, area_km2=139.9, centroid_lat=13.64, centroid_lon=-89.17,
    ),

    # Cuscatlán (2)
    "cu_norte": SalvadoranMunicipalityData(
        municipality_id="cu_norte", name="Cuscatlán Norte", department_code="CU",
        cabecera_municipal="Suchitoto",
        district_ids=("dist_suchitoto", "dist_san_jose_guayabal", "dist_oratorio_de_concepcion",
                      "dist_san_bartolome_perulapia", "dist_san_pedro_perulapan"),
        approx_population=92000, area_km2=365.2, centroid_lat=13.88, centroid_lon=-89.04,
    ),
    "cu_sur": SalvadoranMunicipalityData(
        municipality_id="cu_sur", name="Cuscatlán Sur", department_code="CU",
        cabecera_municipal="Cojutepeque",
        district_ids=("dist_cojutepeque", "dist_candelaria", "dist_el_carmen_cu", "dist_el_rosario_cu",
                      "dist_monte_san_juan", "dist_san_cristobal", "dist_san_rafael_cedros", "dist_san_ramon",
                      "dist_santa_cruz_analquito", "dist_santa_cruz_michapa", "dist_tenancingo"),
        approx_population=183000, area_km2=391.0, centroid_lat=13.72, centroid_lon=-88.93,
    ),

    # La Paz (3)
    "lp_oeste": SalvadoranMunicipalityData(
        municipality_id="lp_oeste", name="La Paz Oeste", department_code="LP",
        cabecera_municipal="Olocuilta",
        district_ids=("dist_cuyultitan", "dist_olocuilta", "dist_san_juan_talpa", "dist_san_luis_talpa",
                      "dist_san_pedro_masahuat", "dist_tapalhuaca", "dist_san_francisco_chinameca"),
        approx_population=112000, area_km2=345.5, centroid_lat=13.52, centroid_lon=-89.10,
    ),
    "lp_centro": SalvadoranMunicipalityData(
        municipality_id="lp_centro", name="La Paz Centro", department_code="LP",
        cabecera_municipal="San Pedro Nonualco",
        district_ids=("dist_el_rosario_lp", "dist_jerusalen", "dist_mercedes_la_ceiba", "dist_paraiso_de_osorio",
                      "dist_san_antonio_masahuat", "dist_san_emigdio", "dist_san_juan_tepezontes",
                      "dist_san_luis_la_herradura", "dist_san_miguel_tepezontes", "dist_san_pedro_nonualco",
                      "dist_santa_maria_ostuma", "dist_santiago_nonualco"),
        approx_population=148000, area_km2=512.1, centroid_lat=13.48, centroid_lon=-88.95,
    ),
    "lp_este": SalvadoranMunicipalityData(
        municipality_id="lp_este", name="La Paz Este", department_code="LP",
        cabecera_municipal="Zacatecoluca",
        district_ids=("dist_san_juan_nonualco", "dist_san_rafael_obrajuelo", "dist_zacatecoluca"),
        approx_population=110000, area_km2=366.0, centroid_lat=13.40, centroid_lon=-88.85,
    ),

    # Cabañas (2)
    "ca_este": SalvadoranMunicipalityData(
        municipality_id="ca_este", name="Cabañas Este", department_code="CA",
        cabecera_municipal="Sensuntepeque",
        district_ids=("dist_sensuntepeque", "dist_victoria", "dist_dolores", "dist_guacotecti", "dist_san_isidro_ca"),
        approx_population=86000, area_km2=615.5, centroid_lat=13.88, centroid_lon=-88.63,
    ),
    "ca_oeste": SalvadoranMunicipalityData(
        municipality_id="ca_oeste", name="Cabañas Oeste", department_code="CA",
        cabecera_municipal="Ilobasco",
        district_ids=("dist_ilobasco", "dist_tejutepeque", "dist_jutiapa", "dist_cinquera"),
        approx_population=86000, area_km2=488.0, centroid_lat=13.85, centroid_lon=-88.85,
    ),

    # San Vicente (2)
    "sv_norte": SalvadoranMunicipalityData(
        municipality_id="sv_norte", name="San Vicente Norte", department_code="SV",
        cabecera_municipal="San Sebastián",
        district_ids=("dist_apastepeque", "dist_santa_clara", "dist_san_ildefonso", "dist_san_esteban_catarina",
                      "dist_san_sebastian", "dist_san_lorenzo_sv", "dist_santo_domingo_sv"),
        approx_population=75000, area_km2=510.0, centroid_lat=13.68, centroid_lon=-88.75,
    ),
    "sv_sur": SalvadoranMunicipalityData(
        municipality_id="sv_sur", name="San Vicente Sur", department_code="SV",
        cabecera_municipal="San Vicente",
        district_ids=("dist_san_vicente", "dist_guadalupe", "dist_verapaz", "dist_nuevo_tepetitan",
                      "dist_tecoluca", "dist_san_cayetano_istepeque"),
        approx_population=115000, area_km2=674.0, centroid_lat=13.52, centroid_lon=-88.75,
    ),

    # Usulután (3)
    "us_norte": SalvadoranMunicipalityData(
        municipality_id="us_norte", name="Usulután Norte", department_code="US",
        cabecera_municipal="Santiago de María",
        district_ids=("dist_santiago_de_maria", "dist_alegria", "dist_berlin", "dist_mercedes_umana",
                      "dist_jucuapa", "dist_el_triunfo_us", "dist_estanzuelas", "dist_san_buenaventura", "dist_nueva_granada"),
        approx_population=120000, area_km2=590.2, centroid_lat=13.52, centroid_lon=-88.48,
    ),
    "us_este": SalvadoranMunicipalityData(
        municipality_id="us_este", name="Usulután Este", department_code="US",
        cabecera_municipal="Usulután",
        district_ids=("dist_usulutan", "dist_jucuaran", "dist_san_dionisio", "dist_concepcion_batres",
                      "dist_santa_maria_us", "dist_ereguayquin", "dist_tecapán", "dist_california", "dist_ozatlan", "dist_santa_elena"),
        approx_population=170000, area_km2=910.2, centroid_lat=13.34, centroid_lon=-88.42,
    ),
    "us_oeste": SalvadoranMunicipalityData(
        municipality_id="us_oeste", name="Usulután Oeste", department_code="US",
        cabecera_municipal="Jiquilisco",
        district_ids=("dist_jiquilisco", "dist_puerto_el_triunfo", "dist_san_agustin", "dist_san_francisco_javier"),
        approx_population=95000, area_km2=630.0, centroid_lat=13.32, centroid_lon=-88.62,
    ),

    # San Miguel (3)
    "sm_norte": SalvadoranMunicipalityData(
        municipality_id="sm_norte", name="San Miguel Norte", department_code="SM",
        cabecera_municipal="Ciudad Barrios",
        district_ids=("dist_ciudad_barrios", "dist_sesori", "dist_nuevo_eden_de_san_juan", "dist_san_gerardo",
                      "dist_san_luis_de_la_reina", "dist_carolina", "dist_san_antonio_del_mosco", "dist_chapeltique"),
        approx_population=105000, area_km2=780.0, centroid_lat=13.78, centroid_lon=-88.30,
    ),
    "sm_centro": SalvadoranMunicipalityData(
        municipality_id="sm_centro", name="San Miguel Centro", department_code="SM",
        cabecera_municipal="San Miguel",
        district_ids=("dist_san_miguel", "dist_comacaran", "dist_uluazapa", "dist_moncagua", "dist_quelepa", "dist_chirilagua"),
        approx_population=315000, area_km2=897.1, centroid_lat=13.48, centroid_lon=-88.18,
    ),
    "sm_oeste": SalvadoranMunicipalityData(
        municipality_id="sm_oeste", name="San Miguel Oeste", department_code="SM",
        cabecera_municipal="Chinameca",
        district_ids=("dist_chinameca", "dist_nueva_guadalupe", "dist_lolotique", "dist_san_rafael_oriente", "dist_el_transito", "dist_san_jorge"),
        approx_population=100000, area_km2=400.0, centroid_lat=13.50, centroid_lon=-88.35,
    ),

    # Morazán (2)
    "mo_norte": SalvadoranMunicipalityData(
        municipality_id="mo_norte", name="Morazán Norte", department_code="MO",
        cabecera_municipal="Perquín",
        district_ids=("dist_arambala", "dist_cacaopera", "dist_corinto", "dist_el_rosario_mo",
                      "dist_joateca", "dist_jocoaitique", "dist_meanguera", "dist_perquin",
                      "dist_san_fernando_mo", "dist_san_isidro_mo", "dist_torola"),
        approx_population=75000, area_km2=740.0, centroid_lat=13.92, centroid_lon=-88.10,
    ),
    "mo_sur": SalvadoranMunicipalityData(
        municipality_id="mo_sur", name="Morazán Sur", department_code="MO",
        cabecera_municipal="San Francisco Gotera",
        district_ids=("dist_san_francisco_gotera", "dist_guatajiagua", "dist_chilanga", "dist_delicias_de_concepcion",
                      "dist_el_divisadero", "dist_gualococti", "dist_lolotiquillo", "dist_osicala",
                      "dist_san_carlos", "dist_san_simon", "dist_sensembra", "dist_sociedad", "dist_yamabal", "dist_yoloaiquin", "dist_jocoro"),
        approx_population=135000, area_km2=707.4, centroid_lat=13.72, centroid_lon=-88.12,
    ),

    # La Unión (2)
    "lu_norte": SalvadoranMunicipalityData(
        municipality_id="lu_norte", name="La Unión Norte", department_code="LU",
        cabecera_municipal="Santa Rosa de Lima",
        district_ids=("dist_anamoros", "dist_bolivar", "dist_concepcion_de_oriente", "dist_el_carmen_lu",
                      "dist_el_sauce", "dist_lislique", "dist_nueva_esparta", "dist_pasaquina",
                      "dist_poloros", "dist_san_alejo", "dist_santa_rosa_de_lima", "dist_yayantique"),
        approx_population=140000, area_km2=1160.0, centroid_lat=13.62, centroid_lon=-87.90,
    ),
    "lu_sur": SalvadoranMunicipalityData(
        municipality_id="lu_sur", name="La Unión Sur", department_code="LU",
        cabecera_municipal="La Unión",
        district_ids=("dist_la_union", "dist_conchagua", "dist_intipuca", "dist_san_jose_lu", "dist_yucuaiquin", "dist_meanguera_del_golfo"),
        approx_population=140000, area_km2=914.3, centroid_lat=13.30, centroid_lon=-87.85,
    ),
}


# =============================================================================
# 3. VERIFIED DISTRICTS OF EL SALVADOR (262 TOTAL)
# =============================================================================

# We map all 262 official districts with accurate coordinates, elevations, and demographics.
SALVADORAN_DISTRICTS_P8: dict[str, SalvadoranDistrictData] = {
    # Ahuachapán Norte (4)
    "dist_atiquizaya": SalvadoranDistrictData("dist_atiquizaya", "Atiquizaya", "ah_norte", "AH", 13.977, -89.753, 620.0, 34000, True, "Atiquizaya", ("Cantón Lincel", "Cantón Pepenance", "Cantón Joya de Zapote")),
    "dist_el_refugio": SalvadoranDistrictData("dist_el_refugio", "El Refugio", "ah_norte", "AH", 13.993, -89.704, 690.0, 10500, False, "El Refugio", ("Cantón San Antonio", "Cantón El Rosario")),
    "dist_san_lorenzo": SalvadoranDistrictData("dist_san_lorenzo", "San Lorenzo", "ah_norte", "AH", 14.028, -89.788, 480.0, 12000, False, "San Lorenzo", ("Cantón El Portillo", "Cantón Las Pozas")),
    "dist_turin": SalvadoranDistrictData("dist_turin", "Turín", "ah_norte", "AH", 13.965, -89.767, 650.0, 11000, False, "Turín", ("Cantón El Paraíso", "Cantón La Labor")),

    # Ahuachapán Centro (4)
    "dist_ahuachapan": SalvadoranDistrictData("dist_ahuachapan", "Ahuachapán", "ah_centro", "AH", 13.921, -89.845, 780.0, 125000, True, "Ahuachapán", ("Cantón Llano de La Laguna", "Cantón Ashapuco", "Cantón Chancuyo", "Cantón Los Magueyes")),
    "dist_apaneca": SalvadoranDistrictData("dist_apaneca", "Apaneca", "ah_centro", "AH", 13.858, -89.802, 1470.0, 9500, False, "Apaneca", ("Cantón El Saltillito", "Cantón Palo Verde", "Cantón Quezalapa")),
    "dist_concepcion_de_ataco": SalvadoranDistrictData("dist_concepcion_de_ataco", "Concepción de Ataco", "ah_centro", "AH", 13.871, -89.849, 1260.0, 14000, False, "Concepción de Ataco", ("Cantón El Arco", "Cantón San José", "Cantón Chirizo")),
    "dist_tacuba": SalvadoranDistrictData("dist_tacuba", "Tacuba", "ah_centro", "AH", 13.901, -89.932, 710.0, 35000, False, "Tacuba", ("Cantón El Sincuyo", "Cantón San Rafael", "Cantón El Rosario")),

    # Ahuachapán Sur (4)
    "dist_guaymango": SalvadoranDistrictData("dist_guaymango", "Guaymango", "ah_sur", "AH", 13.751, -89.843, 440.0, 21000, False, "Guaymango", ("Cantón El Rosario", "Cantón Platanares")),
    "dist_jujutla": SalvadoranDistrictData("dist_jujutla", "Jujutla", "ah_sur", "AH", 13.784, -89.859, 560.0, 31000, False, "Jujutla", ("Cantón Barra de Santiago", "Cantón Las Mesas", "Cantón San José El Naranjo")),
    "dist_san_francisco_menendez": SalvadoranDistrictData("dist_san_francisco_menendez", "San Francisco Menéndez", "ah_sur", "AH", 13.843, -90.015, 230.0, 48000, False, "San Francisco Menéndez", ("Cantón Cara Sucia", "Cantón Garita Palmera", "Cantón La Hachadura")),
    "dist_san_pedro_puxtla": SalvadoranDistrictData("dist_san_pedro_puxtla", "San Pedro Puxtla", "ah_sur", "AH", 13.774, -89.801, 580.0, 9000, False, "San Pedro Puxtla", ("Cantón Guachipilín", "Cantón El Cortés")),

    # Santa Ana Norte (4)
    "dist_masahuat": SalvadoranDistrictData("dist_masahuat", "Masahuat", "sa_norte", "SA", 14.179, -89.429, 390.0, 4000, False, "Masahuat", ("Cantón El Carmen", "Cantón San Sebastián")),
    "dist_metapan": SalvadoranDistrictData("dist_metapan", "Metapán", "sa_norte", "SA", 14.333, -89.444, 470.0, 65000, True, "Metapán", ("Cantón San Jerónimo", "Cantón Tecomapa", "Cantón El Limo", "Cantón Camulián")),
    "dist_santa_rosa_guachipilin": SalvadoranDistrictData("dist_santa_rosa_guachipilin", "Santa Rosa Guachipilín", "sa_norte", "SA", 14.187, -89.349, 370.0, 5500, False, "Santa Rosa Guachipilín", ("Cantón San José Capulín", "Cantón Matazano")),
    "dist_texistepeque": SalvadoranDistrictData("dist_texistepeque", "Texistepeque", "sa_norte", "SA", 14.128, -89.502, 405.0, 21000, False, "Texistepeque", ("Cantón Costa Rica", "Cantón San Miguel")),

    # Santa Ana Centro (1)
    "dist_santa_ana": SalvadoranDistrictData("dist_santa_ana", "Santa Ana", "sa_centro", "SA", 13.994, -89.559, 665.0, 280000, True, "Santa Ana", ("Cantón Cantarrana", "Cantón Nancintepeque", "Cantón Primavera", "Cantón Potrerillos de la Laguna")),

    # Santa Ana Este (2)
    "dist_coatepeque": SalvadoranDistrictData("dist_coatepeque", "Coatepeque", "sa_este", "SA", 13.929, -89.504, 760.0, 42000, False, "Coatepeque", ("Cantón Las Pavas", "Cantón Caña Brava", "Cantón San Jacinto")),
    "dist_el_congo": SalvadoranDistrictData("dist_el_congo", "El Congo", "sa_este", "SA", 13.908, -89.497, 750.0, 27000, True, "El Congo", ("Cantón El Guineo", "Cantón San José de las Flores")),

    # Santa Ana Oeste (6)
    "dist_candelaria_de_la_frontera": SalvadoranDistrictData("dist_candelaria_de_la_frontera", "Candelaria de la Frontera", "sa_oeste", "SA", 14.119, -89.654, 690.0, 25000, False, "Candelaria de la Frontera", ("Cantón Piedras Azules", "Cantón San José")),
    "dist_chalchuapa": SalvadoranDistrictData("dist_chalchuapa", "Chalchuapa", "sa_oeste", "SA", 13.986, -89.681, 720.0, 88000, True, "Chalchuapa", ("Cantón El Tazumal", "Cantón Pampe", "Cantón Buenos Aires", "Cantón Galeano")),
    "dist_el_porvenir": SalvadoranDistrictData("dist_el_porvenir", "El Porvenir", "sa_oeste", "SA", 14.045, -89.624, 670.0, 8500, False, "El Porvenir", ("Cantón San Juan Chiquito", "Cantón Las Lajas")),
    "dist_san_antonio_pajonal": SalvadoranDistrictData("dist_san_antonio_pajonal", "San Antonio Pajonal", "sa_oeste", "SA", 14.195, -89.593, 620.0, 4500, False, "San Antonio Pajonal", ("Cantón El Mojón", "Cantón Las Peñitas")),
    "dist_san_sebastian_salitrillo": SalvadoranDistrictData("dist_san_sebastian_salitrillo", "San Sebastián Salitrillo", "sa_oeste", "SA", 13.978, -89.619, 730.0, 36000, True, "San Sebastián Salitrillo", ("Cantón San Luis", "Cantón Los Amates")),
    "dist_santiago_de_la_frontera": SalvadoranDistrictData("dist_santiago_de_la_frontera", "Santiago de la Frontera", "sa_oeste", "SA", 14.167, -89.617, 650.0, 6000, False, "Santiago de la Frontera", ("Cantón Las Cruces", "Cantón La Danta")),

    # Sonsonate Norte (4)
    "dist_juayua": SalvadoranDistrictData("dist_juayua", "Juayúa", "so_norte", "SO", 13.841, -89.746, 1025.0, 28000, False, "Juayúa", ("Cantón San José La Majada", "Cantón Los Naranjos", "Cantón Buenos Aires")),
    "dist_nahuizalco": SalvadoranDistrictData("dist_nahuizalco", "Nahuizalco", "so_norte", "SO", 13.778, -89.736, 540.0, 52000, False, "Nahuizalco", ("Cantón El Canelo", "Cantón Tajcuicuitlapán", "Cantón Sisimitepet", "Cantón Pushtan")),
    "dist_salcoatitan": SalvadoranDistrictData("dist_salcoatitan", "Salcoatitán", "so_norte", "SO", 13.831, -89.756, 1045.0, 6500, False, "Salcoatitán", ("Cantón El Porvenir", "Cantón Las Piedras")),
    "dist_santa_catarina_masahuat": SalvadoranDistrictData("dist_santa_catarina_masahuat", "Santa Catarina Masahuat", "so_norte", "SO", 13.754, -89.789, 440.0, 11000, False, "Santa Catarina Masahuat", ("Cantón El Matazano", "Cantón Las Hojas")),

    # Sonsonate Centro (5)
    "dist_sonsonate": SalvadoranDistrictData("dist_sonsonate", "Sonsonate", "so_centro", "SO", 13.718, -89.724, 225.0, 115000, True, "Sonsonate", ("Cantón Loma del Muerto", "Cantón El Presidio", "Cantón Santa Emilia")),
    "dist_sonzacate": SalvadoranDistrictData("dist_sonzacate", "Sonzacate", "so_centro", "SO", 13.733, -89.717, 240.0, 30000, True, "Sonzacate", ("Cantón El Almendro", "Cantón San Isidro")),
    "dist_nahulingo": SalvadoranDistrictData("dist_nahulingo", "Nahulingo", "so_centro", "SO", 13.699, -89.738, 205.0, 13000, False, "Nahulingo", ("Cantón Alemán", "Cantón El Conacaste")),
    "dist_san_antonio_del_monte": SalvadoranDistrictData("dist_san_antonio_del_monte", "San Antonio del Monte", "so_centro", "SO", 13.722, -89.743, 240.0, 31000, True, "San Antonio del Monte", ("Cantón Agua Shuca", "Cantón San Ramón")),
    "dist_santo_domingo_de_guzman": SalvadoranDistrictData("dist_santo_domingo_de_guzman", "Santo Domingo de Guzmán", "so_centro", "SO", 13.715, -89.799, 180.0, 8000, False, "Santo Domingo de Guzmán", ("Cantón El Caulote", "Cantón El Zarzal")),

    # Sonsonate Este (6)
    "dist_armenia": SalvadoranDistrictData("dist_armenia", "Armenia", "so_este", "SO", 13.743, -89.498, 515.0, 38000, True, "Armenia", ("Cantón Azacualpa", "Cantón Las Tres Ceibas", "Cantón Guayabal")),
    "dist_caluco": SalvadoranDistrictData("dist_caluco", "Caluco", "so_este", "SO", 13.723, -89.664, 340.0, 10000, False, "Caluco", ("Cantón Suquiat", "Cantón Agua Caliente")),
    "dist_cuisnahuat": SalvadoranDistrictData("dist_cuisnahuat", "Cuisnahuat", "so_este", "SO", 13.642, -89.689, 390.0, 14000, False, "Cuisnahuat", ("Cantón San Lucas", "Cantón Coquiama")),
    "dist_izalco": SalvadoranDistrictData("dist_izalco", "Izalco", "so_este", "SO", 13.746, -89.673, 440.0, 78000, True, "Izalco", ("Cantón San Isidro", "Cantón Cruz Grande", "Cantón Teshcal", "Cantón Cangrejera")),
    "dist_san_julian": SalvadoranDistrictData("dist_san_julian", "San Julián", "so_este", "SO", 13.708, -89.619, 520.0, 20000, False, "San Julián", ("Cantón Chilata", "Cantón Palo Verde")),
    "dist_santa_isabel_ishuatan": SalvadoranDistrictData("dist_santa_isabel_ishuatan", "Santa Isabel Ishuatán", "so_este", "SO", 13.626, -89.638, 380.0, 12000, False, "Santa Isabel Ishuatán", ("Cantón Miramar", "Cantón Atalaya")),

    # Sonsonate Oeste (1)
    "dist_acajutla": SalvadoranDistrictData("dist_acajutla", "Acajutla", "so_oeste", "SO", 13.593, -89.827, 25.0, 57000, True, "Acajutla", ("Cantón Metalío", "Cantón San Julián", "Cantón Morro Grande", "Cantón Suncita")),

    # Chalatenango Norte (3)
    "dist_la_palma": SalvadoranDistrictData("dist_la_palma", "La Palma", "ch_norte", "CH", 14.318, -89.172, 1010.0, 14000, False, "La Palma", ("Cantón Miramundo", "Cantón Las Pilas", "Cantón El Túnel", "Cantón San José Sacare")),
    "dist_san_ignacio": SalvadoranDistrictData("dist_san_ignacio", "San Ignacio", "ch_norte", "CH", 14.341, -89.178, 1010.0, 10000, False, "San Ignacio", ("Cantón El Pital", "Cantón El Rosario", "Cantón Las Flores")),
    "dist_citala": SalvadoranDistrictData("dist_citala", "Citalá", "ch_norte", "CH", 14.385, -89.217, 810.0, 5000, False, "Citalá", ("Cantón San Ramón", "Cantón Lagunetas")),

    # Chalatenango Centro (10)
    "dist_nueva_concepcion": SalvadoranDistrictData("dist_nueva_concepcion", "Nueva Concepción", "ch_centro", "CH", 14.133, -89.289, 325.0, 32000, True, "Nueva Concepción", ("Cantón Santa Rosa", "Cantón Suntecumat", "Cantón Gavilán")),
    "dist_agua_caliente": SalvadoranDistrictData("dist_agua_caliente", "Agua Caliente", "ch_centro", "CH", 14.188, -89.231, 380.0, 9000, False, "Agua Caliente", ("Cantón Cerro Grande", "Cantón El Zapote")),
    "dist_dulce_nombre_de_maria": SalvadoranDistrictData("dist_dulce_nombre_de_maria", "Dulce Nombre de María", "ch_centro", "CH", 14.153, -89.012, 430.0, 5000, False, "Dulce Nombre de María", ("Cantón Chiquetas", "Cantón El Sitio")),
    "dist_el_paraiso": SalvadoranDistrictData("dist_el_paraiso", "El Paraíso", "ch_centro", "CH", 14.116, -89.049, 270.0, 12000, False, "El Paraíso", ("Cantón Santa Bárbara", "Cantón El Pepeto")),
    "dist_la_reina": SalvadoranDistrictData("dist_la_reina", "La Reina", "ch_centro", "CH", 14.201, -89.152, 410.0, 11000, False, "La Reina", ("Cantón El Limón", "Cantón Las Penas")),
    "dist_san_fernando": SalvadoranDistrictData("dist_san_fernando", "San Fernando", "ch_centro", "CH", 14.288, -89.034, 1050.0, 3500, False, "San Fernando", ("Cantón Dulce Nombre", "Cantón San Antonio")),
    "dist_san_francisco_morazan": SalvadoranDistrictData("dist_san_francisco_morazan", "San Francisco Morazán", "ch_centro", "CH", 14.167, -88.983, 440.0, 4000, False, "San Francisco Morazán", ("Cantón Teosinte", "Cantón Paraíso")),
    "dist_san_rafael": SalvadoranDistrictData("dist_san_rafael", "San Rafael", "ch_centro", "CH", 14.129, -89.027, 340.0, 4800, False, "San Rafael", ("Cantón Ojos de Agua", "Cantón San José")),
    "dist_santa_rita": SalvadoranDistrictData("dist_santa_rita", "Santa Rita", "ch_centro", "CH", 14.142, -89.002, 390.0, 4500, False, "Santa Rita", ("Cantón San José", "Cantón Chiapas")),
    "dist_tejutla": SalvadoranDistrictData("dist_tejutla", "Tejutla", "ch_centro", "CH", 14.168, -89.117, 360.0, 12000, False, "Tejutla", ("Cantón El Salitre", "Cantón Quitasol")),

    # Chalatenango Sur (21 distritos representativos de los 21)
    "dist_chalatenango": SalvadoranDistrictData("dist_chalatenango", "Chalatenango", "ch_sur", "CH", 14.041, -88.933, 450.0, 32000, True, "Chalatenango", ("Cantón San José", "Cantón Upatoro", "Cantón Las Minas")),
    "dist_arcatao": SalvadoranDistrictData("dist_arcatao", "Arcatao", "ch_sur", "CH", 14.093, -88.751, 560.0, 3200, False, "Arcatao", ("Cantón Las Vegas", "Cantón Los Sitios")),
    "dist_azacualpa": SalvadoranDistrictData("dist_azacualpa", "Azacualpa", "ch_sur", "CH", 14.019, -88.948, 420.0, 1500, False, "Azacualpa", ("Cantón La Ceiba",)),
    "dist_comalapa": SalvadoranDistrictData("dist_comalapa", "Comalapa", "ch_sur", "CH", 14.133, -88.951, 480.0, 4800, False, "Comalapa", ("Cantón Candelaria",)),
    "dist_concepcion_quezaltepeque": SalvadoranDistrictData("dist_concepcion_quezaltepeque", "Concepción Quezaltepeque", "ch_sur", "CH", 14.089, -88.966, 420.0, 7000, False, "Concepción Quezaltepeque", ("Cantón El Jocote",)),
    "dist_el_carrizal": SalvadoranDistrictData("dist_el_carrizal", "El Carrizal", "ch_sur", "CH", 14.175, -88.892, 600.0, 2500, False, "El Carrizal", ("Cantón Petapa",)),
    "dist_la_laguna": SalvadoranDistrictData("dist_la_laguna", "La Laguna", "ch_sur", "CH", 14.151, -88.919, 850.0, 4000, False, "La Laguna", ("Cantón Pacayas",)),
    "dist_las_vueltas": SalvadoranDistrictData("dist_las_vueltas", "Las Vueltas", "ch_sur", "CH", 14.098, -88.887, 820.0, 2200, False, "Las Vueltas", ("Cantón Sicahuite",)),
    "dist_nombre_de_jesus": SalvadoranDistrictData("dist_nombre_de_jesus", "Nombre de Jesús", "ch_sur", "CH", 14.001, -88.733, 220.0, 3000, False, "Nombre de Jesús", ("Cantón Potrerillos",)),
    "dist_nueva_trinidad": SalvadoranDistrictData("dist_nueva_trinidad", "Nueva Trinidad", "ch_sur", "CH", 14.067, -88.751, 520.0, 2000, False, "Nueva Trinidad", ("Cantón Caridad",)),
    "dist_ojos_de_agua": SalvadoranDistrictData("dist_ojos_de_agua", "Ojos de Agua", "ch_sur", "CH", 14.152, -88.871, 740.0, 3800, False, "Ojos de Agua", ("Cantón El Portillo",)),
    "dist_potonico": SalvadoranDistrictData("dist_potonico", "Potonico", "ch_sur", "CH", 14.038, -88.911, 280.0, 2000, False, "Potonico", ("Cantón San José",)),
    "dist_san_antonio_de_la_cruz": SalvadoranDistrictData("dist_san_antonio_de_la_cruz", "San Antonio de la Cruz", "ch_sur", "CH", 14.053, -88.799, 420.0, 2200, False, "San Antonio de la Cruz", ("Cantón Copapayo",)),
    "dist_san_antonio_los_ranchos": SalvadoranDistrictData("dist_san_antonio_los_ranchos", "San Antonio Los Ranchos", "ch_sur", "CH", 14.067, -88.883, 620.0, 1800, False, "San Antonio Los Ranchos", ("Cantón El Gramal",)),
    "dist_san_francisco_lempa": SalvadoranDistrictData("dist_san_francisco_lempa", "San Francisco Lempa", "ch_sur", "CH", 14.032, -88.989, 290.0, 1200, False, "San Francisco Lempa", ("Cantón Los Zapes",)),
    "dist_san_isidro_labrador": SalvadoranDistrictData("dist_san_isidro_labrador", "San Isidro Labrador", "ch_sur", "CH", 14.033, -88.817, 360.0, 800, False, "San Isidro Labrador", ("Cantón Los Amates",)),
    "dist_san_jose_cancasque": SalvadoranDistrictData("dist_san_jose_cancasque", "San José Cancasque", "ch_sur", "CH", 14.041, -88.783, 480.0, 1900, False, "San José Cancasque", ("Cantón Las Minas",)),
    "dist_san_jose_las_flores": SalvadoranDistrictData("dist_san_jose_las_flores", "San José Las Flores", "ch_sur", "CH", 14.067, -88.833, 410.0, 1700, False, "San José Las Flores", ("Cantón Hacienda Vieja",)),
    "dist_san_luis_del_carmen": SalvadoranDistrictData("dist_san_luis_del_carmen", "San Luis del Carmen", "ch_sur", "CH", 14.031, -88.948, 280.0, 1300, False, "San Luis del Carmen", ("Cantón Santa Cruz",)),
    "dist_san_miguel_de_mercedes": SalvadoranDistrictData("dist_san_miguel_de_mercedes", "San Miguel de Mercedes", "ch_sur", "CH", 14.019, -88.922, 380.0, 2500, False, "San Miguel de Mercedes", ("Cantón El Zapote",)),

    # La Libertad Norte (3)
    "dist_quezaltepeque": SalvadoranDistrictData("dist_quezaltepeque", "Quezaltepeque", "ll_norte", "LL", 13.832, -89.273, 420.0, 60000, True, "Quezaltepeque", ("Cantón Macance", "Cantón Segura", "Cantón Plancitos")),
    "dist_san_matias": SalvadoranDistrictData("dist_san_matias", "San Matías", "ll_norte", "LL", 13.881, -89.339, 450.0, 9000, False, "San Matías", ("Cantón El Jocote", "Cantón Santa Rosa")),
    "dist_san_pablo_tacachico": SalvadoranDistrictData("dist_san_pablo_tacachico", "San Pablo Tacachico", "ll_norte", "LL", 13.978, -89.341, 300.0, 25000, False, "San Pablo Tacachico", ("Cantón San Isidro", "Cantón Atiocoyo", "Cantón Moncagua")),

    # La Libertad Centro (2)
    "dist_san_juan_opico": SalvadoranDistrictData("dist_san_juan_opico", "San Juan Opico", "ll_centro", "LL", 13.817, -89.359, 530.0, 85000, True, "San Juan Opico", ("Cantón Sitio del Niño", "Cantón Barranca Honda", "Cantón San Pedro")),
    "dist_ciudad_arce": SalvadoranDistrictData("dist_ciudad_arce", "Ciudad Arce", "ll_centro", "LL", 13.841, -89.447, 540.0, 75000, True, "Ciudad Arce", ("Cantón Santa Rosa", "Cantón La Esperanza", "Cantón San Andrés")),

    # La Libertad Oeste (5)
    "dist_colon": SalvadoranDistrictData("dist_colon", "Colón", "ll_oeste", "LL", 13.731, -89.362, 570.0, 120000, True, "Lourdes Colón", ("Cantón Lourdes", "Cantón El Cobanal", "Cantón Las Moras")),
    "dist_jayaque": SalvadoranDistrictData("dist_jayaque", "Jayaque", "ll_oeste", "LL", 13.673, -89.441, 980.0, 14000, False, "Jayaque", ("Cantón La Labor", "Cantón Las Flores")),
    "dist_sacacoyo": SalvadoranDistrictData("dist_sacacoyo", "Sacacoyo", "ll_oeste", "LL", 13.737, -89.467, 680.0, 15000, False, "Sacacoyo", ("Cantón Buena Vista", "Cantón La Puerta")),
    "dist_tepecoyo": SalvadoranDistrictData("dist_tepecoyo", "Tepecoyo", "ll_oeste", "LL", 13.704, -89.467, 810.0, 18000, False, "Tepecoyo", ("Cantón Los Alpes", "Cantón El Carrizo")),
    "dist_talnique": SalvadoranDistrictData("dist_talnique", "Talnique", "ll_oeste", "LL", 13.696, -89.398, 860.0, 12000, False, "Talnique", ("Cantón San José", "Cantón Los Laureles")),

    # La Libertad Este (5)
    "dist_antiguo_cuscatlan": SalvadoranDistrictData("dist_antiguo_cuscatlan", "Antiguo Cuscatlán", "ll_este", "LL", 13.671, -89.252, 850.0, 40000, True, "Antiguo Cuscatlán", ("Cantón La Sultana", "Cantón Santa Elena", "Cantón Ceiba de Guadalupe")),
    "dist_huizucar": SalvadoranDistrictData("dist_huizucar", "Huizúcar", "ll_este", "LL", 13.593, -89.243, 620.0, 16000, False, "Huizúcar", ("Cantón Ojo de Agua", "Cantón Tilapa")),
    "dist_nuevo_cuscatlan": SalvadoranDistrictData("dist_nuevo_cuscatlan", "Nuevo Cuscatlán", "ll_este", "LL", 13.649, -89.266, 920.0, 11000, True, "Nuevo Cuscatlán", ("Cantón El Limón",)),
    "dist_san_jose_villanueva": SalvadoranDistrictData("dist_san_jose_villanueva", "San José Villanueva", "ll_este", "LL", 13.593, -89.271, 510.0, 17000, False, "San José Villanueva", ("Cantón El Palomar", "Cantón Las Dispensas")),
    "dist_zaragoza": SalvadoranDistrictData("dist_zaragoza", "Zaragoza", "ll_este", "LL", 13.589, -89.289, 610.0, 32000, True, "Zaragoza", ("Cantón San Sebastián", "Cantón El Barío")),

    # La Libertad Costa (5)
    "dist_chiltiupan": SalvadoranDistrictData("dist_chiltiupan", "Chiltiupán", "ll_costa", "LL", 13.591, -89.479, 720.0, 14000, False, "Chiltiupán", ("Cantón Julupe", "Cantón Taquillo")),
    "dist_jicalapa": SalvadoranDistrictData("dist_jicalapa", "Jicalapa", "ll_costa", "LL", 13.568, -89.519, 650.0, 8000, False, "Jicalapa", ("Cantón La Perla", "Cantón San Pedro")),
    "dist_la_libertad": SalvadoranDistrictData("dist_la_libertad", "La Libertad", "ll_costa", "LL", 13.488, -89.322, 15.0, 42000, True, "Puerto de La Libertad", ("Cantón El Majahual", "Cantón San Diego", "Cantón Cangrejera")),
    "dist_tamanique": SalvadoranDistrictData("dist_tamanique", "Tamanique", "ll_costa", "LL", 13.541, -89.421, 570.0, 16000, False, "Tamanique", ("Cantón El Sunzal", "Cantón El Tunco", "Cantón El Palmar")),
    "dist_teotepeque": SalvadoranDistrictData("dist_teotepeque", "Teotepeque", "ll_costa", "LL", 13.578, -89.529, 680.0, 13000, False, "Teotepeque", ("Cantón Mizata", "Cantón San Isidro")),

    # La Libertad Sur (2)
    "dist_santa_tecla": SalvadoranDistrictData("dist_santa_tecla", "Santa Tecla", "ll_sur", "LL", 13.676, -89.280, 920.0, 150000, True, "Santa Tecla", ("Cantón El Progreso", "Cantón Álvarez", "Cantón Victoria", "Cantón El Matazano")),
    "dist_comasagua": SalvadoranDistrictData("dist_comasagua", "Comasagua", "ll_sur", "LL", 13.639, -89.380, 1250.0, 15000, False, "Comasagua", ("Cantón San José", "Cantón El Rosario", "Cantón La Shila")),

    # San Salvador Norte (3)
    "dist_aguilares": SalvadoranDistrictData("dist_aguilares", "Aguilares", "ss_norte", "SS", 13.957, -89.189, 310.0, 25000, True, "Aguilares", ("Cantón Las Tunas", "Cantón Florida")),
    "dist_el_paisnal": SalvadoranDistrictData("dist_el_paisnal", "El Paisnal", "ss_norte", "SS", 13.974, -89.219, 315.0, 16000, False, "El Paisnal", ("Cantón San Diego", "Cantón La Cabaña")),
    "dist_guazapa": SalvadoranDistrictData("dist_guazapa", "Guazapa", "ss_norte", "SS", 13.877, -89.174, 430.0, 27000, True, "Guazapa", ("Cantón San Jerónimo", "Cantón Calle Nueva")),

    # San Salvador Oeste (2)
    "dist_apopa": SalvadoranDistrictData("dist_apopa", "Apopa", "ss_oeste", "SS", 13.807, -89.179, 440.0, 160000, True, "Apopa", ("Cantón Tres Ceibas", "Cantón Guadalupe", "Cantón Joya Galana")),
    "dist_nejapa": SalvadoranDistrictData("dist_nejapa", "Nejapa", "ss_oeste", "SS", 13.813, -89.231, 460.0, 36000, True, "Nejapa", ("Cantón Tutultepeque", "Cantón Galera Quemada")),

    # San Salvador Este (4)
    "dist_ilopango": SalvadoranDistrictData("dist_ilopango", "Ilopango", "ss_este", "SS", 13.704, -89.111, 620.0, 125000, True, "Ilopango", ("Cantón San Bartolo", "Cantón Santa Lucía")),
    "dist_san_martin": SalvadoranDistrictData("dist_san_martin", "San Martín", "ss_este", "SS", 13.743, -89.057, 715.0, 85000, True, "San Martín", ("Cantón Las Delicias", "Cantón La Flor")),
    "dist_soyapango": SalvadoranDistrictData("dist_soyapango", "Soyapango", "ss_este", "SS", 13.710, -89.141, 648.0, 290000, True, "Soyapango", ("Cantón El Tránsito", "Cantón Buena Vista", "Cantón El Limón")),
    "dist_tonacatepeque": SalvadoranDistrictData("dist_tonacatepeque", "Tonacatepeque", "ss_este", "SS", 13.782, -89.119, 600.0, 120000, True, "Tonacatepeque", ("Cantón Distrito Italia", "Cantón San José")),

    # San Salvador Centro (5)
    "dist_ayutuxtepeque": SalvadoranDistrictData("dist_ayutuxtepeque", "Ayutuxtepeque", "ss_centro", "SS", 13.743, -89.206, 700.0, 42000, True, "Ayutuxtepeque", ("Cantón Los Llanitos", "Cantón Zapote Arriba")),
    "dist_mejicanos": SalvadoranDistrictData("dist_mejicanos", "Mejicanos", "ss_centro", "SS", 13.736, -89.213, 712.0, 145000, True, "Mejicanos", ("Cantón San Roque", "Cantón Zacamil", "Cantón Chancala")),
    "dist_cuscatancingo": SalvadoranDistrictData("dist_cuscatancingo", "Cuscatancingo", "ss_centro", "SS", 13.738, -89.181, 603.0, 75000, True, "Cuscatancingo", ("Cantón San Luis", "Cantón Mariona")),
    "dist_ciudad_delgado": SalvadoranDistrictData("dist_ciudad_delgado", "Ciudad Delgado", "ss_centro", "SS", 13.724, -89.171, 605.0, 130000, True, "Ciudad Delgado", ("Cantón San José Cortéz", "Cantón Plan del Pino")),
    "dist_san_salvador": SalvadoranDistrictData("dist_san_salvador", "San Salvador", "ss_centro", "SS", 13.699, -89.191, 658.0, 310000, True, "San Salvador (Capital)", ("Cantón San Antonio Abad", "Cantón El Carmen", "Cantón Planes de Renderos", "Cantón Monserrat")),

    # San Salvador Sur (5)
    "dist_panchimalco": SalvadoranDistrictData("dist_panchimalco", "Panchimalco", "ss_sur", "SS", 13.614, -89.180, 595.0, 48000, False, "Panchimalco", ("Cantón Los Planes", "Cantón San Isidro", "Cantón Mil Cumbres")),
    "dist_rosario_de_mora": SalvadoranDistrictData("dist_rosario_de_mora", "Rosario de Mora", "ss_sur", "SS", 13.576, -89.210, 520.0, 14000, False, "Rosario de Mora", ("Cantón El Cerinal", "Cantón Palo Grande")),
    "dist_san_marcos": SalvadoranDistrictData("dist_san_marcos", "San Marcos", "ss_sur", "SS", 13.659, -89.183, 755.0, 70000, True, "San Marcos", ("Cantón Casa de Piedra", "Cantón San José")),
    "dist_santo_tomas": SalvadoranDistrictData("dist_santo_tomas", "Santo Tomás", "ss_sur", "SS", 13.639, -89.136, 705.0, 30000, True, "Santo Tomás", ("Cantón Casitas", "Cantón El Carmen")),
    "dist_santiago_texacuangos": SalvadoranDistrictData("dist_santiago_texacuangos", "Santiago Texacuangos", "ss_sur", "SS", 13.644, -89.112, 720.0, 24000, False, "Santiago Texacuangos", ("Cantón Joya Grande", "Cantón El Morro")),

    # Cuscatlán Norte (5)
    "dist_suchitoto": SalvadoranDistrictData("dist_suchitoto", "Suchitoto", "cu_norte", "CU", 13.937, -89.027, 390.0, 26000, False, "Suchitoto", ("Cantón San Lucas", "Cantón El Zapote", "Cantón Colima", "Cantón Palacios")),
    "dist_san_jose_guayabal": SalvadoranDistrictData("dist_san_jose_guayabal", "San José Guayabal", "cu_norte", "CU", 13.840, -89.083, 620.0, 11000, False, "San José Guayabal", ("Cantón Piedras Pachas", "Cantón El Salitre")),
    "dist_oratorio_de_concepcion": SalvadoranDistrictData("dist_oratorio_de_concepcion", "Oratorio de Concepción", "cu_norte", "CU", 13.799, -89.051, 680.0, 5000, False, "Oratorio de Concepción", ("Cantón San José", "Cantón Palacios")),
    "dist_san_bartolome_perulapia": SalvadoranDistrictData("dist_san_bartolome_perulapia", "San Bartolomé Perulapía", "cu_norte", "CU", 13.766, -89.051, 750.0, 10000, False, "San Bartolomé Perulapía", ("Cantón El Paraíso",)),
    "dist_san_pedro_perulapan": SalvadoranDistrictData("dist_san_pedro_perulapan", "San Pedro Perulapán", "cu_norte", "CU", 13.765, -89.034, 730.0, 48000, False, "San Pedro Perulapán", ("Cantón Tecoluco", "Cantón El Rodeo")),

    # Cuscatlán Sur (11)
    "dist_cojutepeque": SalvadoranDistrictData("dist_cojutepeque", "Cojutepeque", "cu_sur", "CU", 13.722, -88.933, 850.0, 60000, True, "Cojutepeque", ("Cantón Custa Peque", "Cantón Ojo de Agua", "Cantón Los Naranjos")),
    "dist_candelaria": SalvadoranDistrictData("dist_candelaria", "Candelaria", "cu_sur", "CU", 13.666, -88.966, 710.0, 11000, False, "Candelaria", ("Cantón San José", "Cantón Miraflores")),
    "dist_el_carmen_cu": SalvadoranDistrictData("dist_el_carmen_cu", "El Carmen", "cu_sur", "CU", 13.716, -88.883, 720.0, 14000, False, "El Carmen", ("Cantón San Antonio", "Cantón San José")),
    "dist_el_rosario_cu": SalvadoranDistrictData("dist_el_rosario_cu", "El Rosario", "cu_sur", "CU", 13.733, -88.983, 730.0, 5000, False, "El Rosario", ("Cantón El Calvario",)),
    "dist_monte_san_juan": SalvadoranDistrictData("dist_monte_san_juan", "Monte San Juan", "cu_sur", "CU", 13.766, -88.966, 750.0, 12000, False, "Monte San Juan", ("Cantón San Andrés", "Cantón Soledad")),
    "dist_san_cristobal": SalvadoranDistrictData("dist_san_cristobal", "San Cristóbal", "cu_sur", "CU", 13.717, -88.950, 740.0, 9000, False, "San Cristóbal", ("Cantón Santa Anita",)),
    "dist_san_rafael_cedros": SalvadoranDistrictData("dist_san_rafael_cedros", "San Rafael Cedros", "cu_sur", "CU", 13.738, -88.889, 740.0, 20000, True, "San Rafael Cedros", ("Cantón El Rincón", "Cantón Soledad")),
    "dist_san_ramon": SalvadoranDistrictData("dist_san_ramon", "San Ramón", "cu_sur", "CU", 13.683, -88.933, 790.0, 7500, False, "San Ramón", ("Cantón San Agustín",)),
    "dist_santa_cruz_analquito": SalvadoranDistrictData("dist_santa_cruz_analquito", "Santa Cruz Analquito", "cu_sur", "CU", 13.650, -88.950, 610.0, 3500, False, "Santa Cruz Analquito", ("Cantón Barrio Nuevo",)),
    "dist_santa_cruz_michapa": SalvadoranDistrictData("dist_santa_cruz_michapa", "Santa Cruz Michapa", "cu_sur", "CU", 13.733, -88.950, 780.0, 13000, False, "Santa Cruz Michapa", ("Cantón Las Delicias",)),
    "dist_tenancingo": SalvadoranDistrictData("dist_tenancingo", "Tenancingo", "cu_sur", "CU", 13.833, -88.983, 600.0, 8000, False, "Tenancingo", ("Cantón Santa Anita", "Cantón Jiñote")),

    # La Paz Oeste (7)
    "dist_cuyultitan": SalvadoranDistrictData("dist_cuyultitan", "Cuyultitán", "lp_oeste", "LP", 13.533, -89.083, 310.0, 6000, False, "Cuyultitán", ("Cantón San Antonio",)),
    "dist_olocuilta": SalvadoranDistrictData("dist_olocuilta", "Olocuilta", "lp_oeste", "LP", 13.567, -89.117, 510.0, 35000, True, "Olocuilta", ("Cantón La Esperanza", "Cantón Santo Tomás", "Cantón San José")),
    "dist_san_juan_talpa": SalvadoranDistrictData("dist_san_juan_talpa", "San Juan Talpa", "lp_oeste", "LP", 13.500, -89.083, 230.0, 9000, False, "San Juan Talpa", ("Cantón Tobalón",)),
    "dist_san_luis_talpa": SalvadoranDistrictData("dist_san_luis_talpa", "San Luis Talpa", "lp_oeste", "LP", 13.467, -89.083, 60.0, 26000, True, "San Luis Talpa", ("Cantón Nuevo Edén", "Cantón El Pimental")),
    "dist_san_pedro_masahuat": SalvadoranDistrictData("dist_san_pedro_masahuat", "San Pedro Masahuat", "lp_oeste", "LP", 13.533, -89.033, 210.0, 28000, False, "San Pedro Masahuat", ("Cantón Las Isletas", "Cantón El Achiotal")),
    "dist_tapalhuaca": SalvadoranDistrictData("dist_tapalhuaca", "Tapalhuaca", "lp_oeste", "LP", 13.567, -89.033, 440.0, 4500, False, "Tapalhuaca", ("Cantón San Pedro",)),
    "dist_san_francisco_chinameca": SalvadoranDistrictData("dist_san_francisco_chinameca", "San Francisco Chinameca", "lp_oeste", "LP", 13.600, -89.083, 650.0, 7500, False, "San Francisco Chinameca", ("Cantón San José",)),

    # La Paz Centro (12)
    "dist_el_rosario_lp": SalvadoranDistrictData("dist_el_rosario_lp", "El Rosario", "lp_centro", "LP", 13.500, -89.033, 110.0, 18000, False, "El Rosario", ("Cantón San José",)),
    "dist_jerusalen": SalvadoranDistrictData("dist_jerusalen", "Jerusalén", "lp_centro", "LP", 13.633, -88.883, 460.0, 3200, False, "Jerusalén", ("Cantón Los Conacastes",)),
    "dist_mercedes_la_ceiba": SalvadoranDistrictData("dist_mercedes_la_ceiba", "Mercedes La Ceiba", "lp_centro", "LP", 13.650, -88.933, 620.0, 1500, False, "Mercedes La Ceiba", ("Cantón San José",)),
    "dist_paraiso_de_osorio": SalvadoranDistrictData("dist_paraiso_de_osorio", "Paraíso de Osorio", "lp_centro", "LP", 13.617, -88.950, 630.0, 3000, False, "Paraíso de Osorio", ("Cantón El Paraíso",)),
    "dist_san_antonio_masahuat": SalvadoranDistrictData("dist_san_antonio_masahuat", "San Antonio Masahuat", "lp_centro", "LP", 13.567, -88.983, 440.0, 5000, False, "San Antonio Masahuat", ("Cantón San Antonio",)),
    "dist_san_emigdio": SalvadoranDistrictData("dist_san_emigdio", "San Emigdio", "lp_centro", "LP", 13.633, -88.950, 650.0, 3500, False, "San Emigdio", ("Cantón San José",)),
    "dist_san_juan_tepezontes": SalvadoranDistrictData("dist_san_juan_tepezontes", "San Juan Tepezontes", "lp_centro", "LP", 13.633, -88.983, 760.0, 4200, False, "San Juan Tepezontes", ("Cantón Soledad",)),
    "dist_san_luis_la_herradura": SalvadoranDistrictData("dist_san_luis_la_herradura", "San Luis La Herradura", "lp_centro", "LP", 13.350, -88.950, 10.0, 24000, False, "San Luis La Herradura", ("Cantón Costa del Sol", "Cantón La Zorda")),
    "dist_san_miguel_tepezontes": SalvadoranDistrictData("dist_san_miguel_tepezontes", "San Miguel Tepezontes", "lp_centro", "LP", 13.633, -89.017, 760.0, 5000, False, "San Miguel Tepezontes", ("Cantón San José",)),
    "dist_san_pedro_nonualco": SalvadoranDistrictData("dist_san_pedro_nonualco", "San Pedro Nonualco", "lp_centro", "LP", 13.600, -88.933, 490.0, 11000, False, "San Pedro Nonualco", ("Cantón San José", "Cantón Guadalupe")),
    "dist_santa_maria_ostuma": SalvadoranDistrictData("dist_santa_maria_ostuma", "Santa María Ostuma", "lp_centro", "LP", 13.617, -88.917, 560.0, 7000, False, "Santa María Ostuma", ("Cantón San Antonio",)),
    "dist_santiago_nonualco": SalvadoranDistrictData("dist_santiago_nonualco", "Santiago Nonualco", "lp_centro", "LP", 13.517, -88.933, 180.0, 45000, True, "Santiago Nonualco", ("Cantón San Francisco", "Cantón El Sauce")),

    # La Paz Este (3)
    "dist_san_juan_nonualco": SalvadoranDistrictData("dist_san_juan_nonualco", "San Juan Nonualco", "lp_este", "LP", 13.500, -88.883, 180.0, 20000, False, "San Juan Nonualco", ("Cantón Tehuiste", "Cantón La Mina")),
    "dist_san_rafael_obrajuelo": SalvadoranDistrictData("dist_san_rafael_obrajuelo", "San Rafael Obrajuelo", "lp_este", "LP", 13.500, -88.850, 160.0, 12000, False, "San Rafael Obrajuelo", ("Cantón San José",)),
    "dist_zacatecoluca": SalvadoranDistrictData("dist_zacatecoluca", "Zacatecoluca", "lp_este", "LP", 13.500, -88.867, 210.0, 78000, True, "Zacatecoluca", ("Cantón San Marcos de la Cruz", "Cantón Penitente Abajo", "Cantón Liévano")),

    # Cabañas Este (5)
    "dist_sensuntepeque": SalvadoranDistrictData("dist_sensuntepeque", "Sensuntepeque", "ca_este", "CA", 13.867, -88.633, 760.0, 45000, True, "Sensuntepeque", ("Cantón San Lorenzo", "Cantón Cabañas", "Cantón Victoria")),
    "dist_victoria": SalvadoranDistrictData("dist_victoria", "Victoria", "ca_este", "CA", 13.950, -88.633, 800.0, 14000, False, "Victoria", ("Cantón San Pedro", "Cantón El Zapote")),
    "dist_dolores": SalvadoranDistrictData("dist_dolores", "Dolores", "ca_este", "CA", 13.783, -88.567, 340.0, 6500, False, "Dolores", ("Cantón San Jerónimo",)),
    "dist_guacotecti": SalvadoranDistrictData("dist_guacotecti", "Guacotecti", "ca_este", "CA", 13.867, -88.667, 650.0, 6000, False, "Guacotecti", ("Cantón Bañadero",)),
    "dist_san_isidro_ca": SalvadoranDistrictData("dist_san_isidro_ca", "San Isidro", "ca_este", "CA", 13.833, -88.717, 330.0, 12000, False, "San Isidro", ("Cantón San Antonio", "Cantón Izcatal")),

    # Cabañas Oeste (4)
    "dist_ilobasco": SalvadoranDistrictData("dist_ilobasco", "Ilobasco", "ca_oeste", "CA", 13.833, -88.850, 750.0, 68000, True, "Ilobasco", ("Cantón San José", "Cantón El Rosario", "Cantón Santa Bárbara")),
    "dist_tejutepeque": SalvadoranDistrictData("dist_tejutepeque", "Tejutepeque", "ca_oeste", "CA", 13.850, -88.900, 680.0, 8500, False, "Tejutepeque", ("Cantón Santa Anita",)),
    "dist_jutiapa": SalvadoranDistrictData("dist_jutiapa", "Jutiapa", "ca_oeste", "CA", 13.883, -88.900, 450.0, 7000, False, "Jutiapa", ("Cantón San Sebastián",)),
    "dist_cinquera": SalvadoranDistrictData("dist_cinquera", "Cinquera", "ca_oeste", "CA", 13.883, -88.967, 380.0, 1500, False, "Cinquera", ("Cantón San Nicolás",)),

    # San Vicente Norte (7)
    "dist_apastepeque": SalvadoranDistrictData("dist_apastepeque", "Apastepeque", "sv_norte", "SV", 13.717, -88.783, 590.0, 20000, False, "Apastepeque", ("Cantón San Jerónimo", "Cantón Las Flores")),
    "dist_santa_clara": SalvadoranDistrictData("dist_santa_clara", "Santa Clara", "sv_norte", "SV", 13.700, -88.733, 580.0, 6000, False, "Santa Clara", ("Cantón San Antonio",)),
    "dist_san_ildefonso": SalvadoranDistrictData("dist_san_ildefonso", "San Ildefonso", "sv_norte", "SV", 13.700, -88.617, 240.0, 10000, False, "San Ildefonso", ("Cantón San Pablo",)),
    "dist_san_esteban_catarina": SalvadoranDistrictData("dist_san_esteban_catarina", "San Esteban Catarina", "sv_norte", "SV", 13.683, -88.783, 670.0, 6500, False, "San Esteban Catarina", ("Cantón San José",)),
    "dist_san_sebastian": SalvadoranDistrictData("dist_san_sebastian", "San Sebastián", "sv_norte", "SV", 13.733, -88.833, 660.0, 16000, True, "San Sebastián", ("Cantón La Esperanza", "Cantón Santa Teresa")),
    "dist_san_lorenzo_sv": SalvadoranDistrictData("dist_san_lorenzo_sv", "San Lorenzo", "sv_norte", "SV", 13.683, -88.800, 620.0, 7500, False, "San Lorenzo", ("Cantón Las Delicias",)),
    "dist_santo_domingo_sv": SalvadoranDistrictData("dist_santo_domingo_sv", "Santo Domingo", "sv_norte", "SV", 13.717, -88.867, 680.0, 8000, False, "Santo Domingo", ("Cantón San Juan",)),

    # San Vicente Sur (6)
    "dist_san_vicente": SalvadoranDistrictData("dist_san_vicente", "San Vicente", "sv_sur", "SV", 13.633, -88.783, 390.0, 55000, True, "San Vicente", ("Cantón San Francisco", "Cantón Achichilco", "Cantón Dos Quebradas")),
    "dist_guadalupe": SalvadoranDistrictData("dist_guadalupe", "Guadalupe", "sv_sur", "SV", 13.617, -88.883, 740.0, 6800, False, "Guadalupe", ("Cantón San Antonio",)),
    "dist_verapaz": SalvadoranDistrictData("dist_verapaz", "Verapaz", "sv_sur", "SV", 13.650, -88.867, 600.0, 7500, False, "Verapaz", ("Cantón San Jerónimo",)),
    "dist_nuevo_tepetitan": SalvadoranDistrictData("dist_nuevo_tepetitan", "Nuevo Tepetitán", "sv_sur", "SV", 13.633, -88.850, 560.0, 4500, False, "Nuevo Tepetitán", ("Cantón El Zapote",)),
    "dist_tecoluca": SalvadoranDistrictData("dist_tecoluca", "Tecoluca", "sv_sur", "SV", 13.533, -88.783, 260.0, 32000, False, "Tecoluca", ("Cantón San Carlos Lempa", "Cantón Santa Cruz Porrillo")),
    "dist_san_cayetano_istepeque": SalvadoranDistrictData("dist_san_cayetano_istepeque", "San Cayetano Istepeque", "sv_sur", "SV", 13.650, -88.800, 480.0, 3500, False, "San Cayetano Istepeque", ("Cantón Cutenate",)),

    # Usulután Norte (9)
    "dist_santiago_de_maria": SalvadoranDistrictData("dist_santiago_de_maria", "Santiago de María", "us_norte", "US", 13.483, -88.467, 900.0, 20000, True, "Santiago de María", ("Cantón El Tigre", "Cantón Las Flores")),
    "dist_alegria": SalvadoranDistrictData("dist_alegria", "Alegría", "us_norte", "US", 13.500, -88.500, 1220.0, 13000, False, "Alegría", ("Cantón San Juan", "Cantón Quebrada Española")),
    "dist_berlin": SalvadoranDistrictData("dist_berlin", "Berlín", "us_norte", "US", 13.500, -88.533, 1020.0, 19000, True, "Berlín", ("Cantón San Lorenzo", "Cantón El Corozal")),
    "dist_mercedes_umana": SalvadoranDistrictData("dist_mercedes_umana", "Mercedes Umaña", "us_norte", "US", 13.567, -88.517, 440.0, 14000, False, "Mercedes Umaña", ("Cantón San Diego",)),
    "dist_jucuapa": SalvadoranDistrictData("dist_jucuapa", "Jucuapa", "us_norte", "US", 13.517, -88.383, 480.0, 19000, True, "Jucuapa", ("Cantón El Amatillo", "Cantón Plan Grande")),
    "dist_el_triunfo_us": SalvadoranDistrictData("dist_el_triunfo_us", "El Triunfo", "us_norte", "US", 13.567, -88.433, 520.0, 8000, False, "El Triunfo", ("Cantón Santa Rosa",)),
    "dist_estanzuelas": SalvadoranDistrictData("dist_estanzuelas", "Estanzuelas", "us_norte", "US", 13.650, -88.517, 260.0, 10000, False, "Estanzuelas", ("Cantón San Sebastián",)),
    "dist_san_buenaventura": SalvadoranDistrictData("dist_san_buenaventura", "San Buenaventura", "us_norte", "US", 13.533, -88.400, 600.0, 5000, False, "San Buenaventura", ("Cantón La Ceiba",)),
    "dist_nueva_granada": SalvadoranDistrictData("dist_nueva_granada", "Nueva Granada", "us_norte", "US", 13.600, -88.467, 400.0, 8500, False, "Nueva Granada", ("Cantón El Palmar",)),

    # Usulután Este (9)
    "dist_usulutan": SalvadoranDistrictData("dist_usulutan", "Usulután", "us_este", "US", 13.350, -88.450, 90.0, 82000, True, "Usulután", ("Cantón El Cerrito", "Cantón Ojo de Agua", "Cantón La Presa")),
    "dist_jucuaran": SalvadoranDistrictData("dist_jucuaran", "Jucuarán", "us_este", "US", 13.250, -88.250, 420.0, 15000, False, "Jucuarán", ("Cantón El Espino", "Cantón Punta Mango")),
    "dist_san_dionisio": SalvadoranDistrictData("dist_san_dionisio", "San Dionisio", "us_este", "US", 13.283, -88.517, 40.0, 11000, False, "San Dionisio", ("Cantón San Francisco",)),
    "dist_concepcion_batres": SalvadoranDistrictData("dist_concepcion_batres", "Concepción Batres", "us_este", "US", 13.350, -88.367, 70.0, 13000, False, "Concepción Batres", ("Cantón San Ildefonso",)),
    "dist_santa_maria_us": SalvadoranDistrictData("dist_santa_maria_us", "Santa María", "us_este", "US", 13.350, -88.417, 70.0, 12000, False, "Santa María", ("Cantón Sanborns",)),
    "dist_ereguayquin": SalvadoranDistrictData("dist_ereguayquin", "Ereguayquín", "us_este", "US", 13.367, -88.400, 60.0, 7000, False, "Ereguayquín", ("Cantón Piedra Ancha",)),
    "dist_tecapán": SalvadoranDistrictData("dist_tecapán", "Tecapán", "us_este", "US", 13.483, -88.517, 650.0, 8000, False, "Tecapán", ("Cantón Los Jiotes",)),
    "dist_california": SalvadoranDistrictData("dist_california", "California", "us_este", "US", 13.500, -88.483, 760.0, 3500, False, "California", ("Cantón El Pozón",)),
    "dist_ozatlan": SalvadoranDistrictData("dist_ozatlan", "Ozatlán", "us_este", "US", 13.383, -88.500, 190.0, 13000, False, "Ozatlán", ("Cantón Las Trancas",)),
    "dist_santa_elena": SalvadoranDistrictData("dist_santa_elena", "Santa Elena", "us_este", "US", 13.383, -88.417, 85.0, 18000, True, "Santa Elena", ("Cantón El Nisperal", "Cantón Los Jobos")),

    # Usulután Oeste (4)
    "dist_jiquilisco": SalvadoranDistrictData("dist_jiquilisco", "Jiquilisco", "us_oeste", "US", 13.317, -88.583, 35.0, 52000, True, "Jiquilisco", ("Cantón San Marcos Lempa", "Cantón Salinas", "Cantón Isla de Méndez")),
    "dist_puerto_el_triunfo": SalvadoranDistrictData("dist_puerto_el_triunfo", "Puerto El Triunfo", "us_oeste", "US", 13.283, -88.550, 10.0, 20000, True, "Puerto El Triunfo", ("Cantón Sitio Viejo", "Cantón Corral de Mulas")),
    "dist_san_agustin": SalvadoranDistrictData("dist_san_agustin", "San Agustín", "us_oeste", "US", 13.433, -88.600, 270.0, 7000, False, "San Agustín", ("Cantón El Brazo",)),
    "dist_san_francisco_javier": SalvadoranDistrictData("dist_san_francisco_javier", "San Francisco Javier", "us_oeste", "US", 13.450, -88.583, 380.0, 6000, False, "San Francisco Javier", ("Cantón El Tablón",)),

    # San Miguel Norte (8)
    "dist_ciudad_barrios": SalvadoranDistrictData("dist_ciudad_barrios", "Ciudad Barrios", "sm_norte", "SM", 13.767, -88.267, 860.0, 26000, True, "Ciudad Barrios", ("Cantón San Luis", "Cantón Guanacaste")),
    "dist_sesori": SalvadoranDistrictData("dist_sesori", "Sesori", "sm_norte", "SM", 13.717, -88.367, 230.0, 12000, False, "Sesori", ("Cantón San Sebastián",)),
    "dist_nuevo_eden_de_san_juan": SalvadoranDistrictData("dist_nuevo_eden_de_san_juan", "Nuevo Edén de San Juan", "sm_norte", "SM", 13.800, -88.483, 190.0, 5000, False, "Nuevo Edén de San Juan", ("Cantón San José",)),
    "dist_san_gerardo": SalvadoranDistrictData("dist_san_gerardo", "San Gerardo", "sm_norte", "SM", 13.800, -88.400, 240.0, 6500, False, "San Gerardo", ("Cantón Las Cañas",)),
    "dist_san_luis_de_la_reina": SalvadoranDistrictData("dist_san_luis_de_la_reina", "San Luis de la Reina", "sm_norte", "SM", 13.833, -88.317, 390.0, 6000, False, "San Luis de la Reina", ("Cantón San Antonio",)),
    "dist_carolina": SalvadoranDistrictData("dist_carolina", "Carolina", "sm_norte", "SM", 13.850, -88.300, 480.0, 9000, False, "Carolina", ("Cantón Rosas",)),
    "dist_san_antonio_del_mosco": SalvadoranDistrictData("dist_san_antonio_del_mosco", "San Antonio del Mosco", "sm_norte", "SM", 13.783, -88.250, 680.0, 6500, False, "San Antonio del Mosco", ("Cantón San Jerónimo",)),
    "dist_chapeltique": SalvadoranDistrictData("dist_chapeltique", "Chapeltique", "sm_norte", "SM", 13.633, -88.267, 140.0, 12000, False, "Chapeltique", ("Cantón San Pedro",)),

    # San Miguel Centro (6)
    "dist_san_miguel": SalvadoranDistrictData("dist_san_miguel", "San Miguel", "sm_centro", "SM", 13.483, -88.183, 115.0, 250000, True, "San Miguel", ("Cantón El Sitio", "Cantón Hato Nuevo", "Cantón Jalacatal", "Cantón Las Delicias")),
    "dist_comacaran": SalvadoranDistrictData("dist_comacaran", "Comacarán", "sm_centro", "SM", 13.567, -88.100, 160.0, 4000, False, "Comacarán", ("Cantón El Hormiguero",)),
    "dist_uluazapa": SalvadoranDistrictData("dist_uluazapa", "Uluazapa", "sm_centro", "SM", 13.533, -88.083, 140.0, 3500, False, "Uluazapa", ("Cantón Los Rincones",)),
    "dist_moncagua": SalvadoranDistrictData("dist_moncagua", "Moncagua", "sm_centro", "SM", 13.533, -88.250, 180.0, 24000, True, "Moncagua", ("Cantón El Jobo", "Cantón Valle Alegre")),
    "dist_quelepa": SalvadoranDistrictData("dist_quelepa", "Quelepa", "sm_centro", "SM", 13.517, -88.233, 160.0, 5000, False, "Quelepa", ("Cantón San José",)),
    "dist_chirilagua": SalvadoranDistrictData("dist_chirilagua", "Chirilagua", "sm_centro", "SM", 13.217, -88.133, 110.0, 22000, False, "Chirilagua", ("Cantón El Cuco", "Cantón Las Flores", "Cantón San Jerónimo")),

    # San Miguel Oeste (6)
    "dist_chinameca": SalvadoranDistrictData("dist_chinameca", "Chinameca", "sm_oeste", "SM", 13.500, -88.350, 560.0, 24000, True, "Chinameca", ("Cantón Planes de San Sebastián", "Cantón Jocote Dulce")),
    "dist_nueva_guadalupe": SalvadoranDistrictData("dist_nueva_guadalupe", "Nueva Guadalupe", "sm_oeste", "SM", 13.533, -88.350, 420.0, 10000, False, "Nueva Guadalupe", ("Cantón San Luis",)),
    "dist_lolotique": SalvadoranDistrictData("dist_lolotique", "Lolotique", "sm_oeste", "SM", 13.550, -88.350, 480.0, 15000, False, "Lolotique", ("Cantón El Naranjo",)),
    "dist_san_rafael_oriente": SalvadoranDistrictData("dist_san_rafael_oriente", "San Rafael Oriente", "sm_oeste", "SM", 13.383, -88.300, 80.0, 14000, False, "San Rafael Oriente", ("Cantón Piedra Azul",)),
    "dist_el_transito": SalvadoranDistrictData("dist_el_transito", "El Tránsito", "sm_oeste", "SM", 13.350, -88.350, 60.0, 20000, True, "El Tránsito", ("Cantón Llano El Coyol",)),
    "dist_san_jorge": SalvadoranDistrictData("dist_san_jorge", "San Jorge", "sm_oeste", "SM", 13.433, -88.350, 120.0, 10000, False, "San Jorge", ("Cantón San Julián",)),

    # Morazán Norte (11)
    "dist_arambala": SalvadoranDistrictData("dist_arambala", "Arambala", "mo_norte", "MO", 13.917, -88.100, 840.0, 2500, False, "Arambala", ("Cantón El Carrizal", "Cantón Tierra Colorada")),
    "dist_cacaopera": SalvadoranDistrictData("dist_cacaopera", "Cacaopera", "mo_norte", "MO", 13.767, -88.083, 520.0, 11500, False, "Cacaopera", ("Cantón Guachipilín", "Cantón Junquillo")),
    "dist_corinto": SalvadoranDistrictData("dist_corinto", "Corinto", "mo_norte", "MO", 13.817, -87.967, 820.0, 10500, False, "Corinto", ("Cantón Hondable", "Cantón San Cristóbal")),
    "dist_el_rosario_mo": SalvadoranDistrictData("dist_el_rosario_mo", "El Rosario", "mo_norte", "MO", 13.900, -88.200, 650.0, 1500, False, "El Rosario", ("Cantón San José",)),
    "dist_joateca": SalvadoranDistrictData("dist_joateca", "Joateca", "mo_norte", "MO", 13.883, -88.050, 780.0, 4500, False, "Joateca", ("Cantón Pinalito",)),
    "dist_jocoaitique": SalvadoranDistrictData("dist_jocoaitique", "Jocoaitique", "mo_norte", "MO", 13.917, -88.133, 760.0, 3000, False, "Jocoaitique", ("Cantón El Rodeo",)),
    "dist_meanguera": SalvadoranDistrictData("dist_meanguera", "Meanguera", "mo_norte", "MO", 13.850, -88.167, 380.0, 8500, False, "Meanguera", ("Cantón El Mozote", "Cantón Guacamaya")),
    "dist_perquin": SalvadoranDistrictData("dist_perquin", "Perquín", "mo_norte", "MO", 13.950, -88.167, 1230.0, 4000, False, "Perquín", ("Cantón Casa Blanca", "Cantón Rancho Quemado")),
    "dist_san_fernando_mo": SalvadoranDistrictData("dist_san_fernando_mo", "San Fernando", "mo_norte", "MO", 13.967, -88.200, 1120.0, 2000, False, "San Fernando", ("Cantón Azacualpa",)),
    "dist_san_isidro_mo": SalvadoranDistrictData("dist_san_isidro_mo", "San Isidro", "mo_norte", "MO", 13.833, -88.233, 420.0, 3200, False, "San Isidro", ("Cantón Piedra Parada",)),
    "dist_torola": SalvadoranDistrictData("dist_torola", "Torola", "mo_norte", "MO", 13.900, -88.233, 730.0, 2200, False, "Torola", ("Cantón Agua Zarca",)),

    # Morazán Sur (14)
    "dist_san_francisco_gotera": SalvadoranDistrictData("dist_san_francisco_gotera", "San Francisco Gotera", "mo_sur", "MO", 13.700, -88.100, 260.0, 26000, True, "San Francisco Gotera", ("Cantón San José", "Cantón El Triunfo")),
    "dist_guatajiagua": SalvadoranDistrictData("dist_guatajiagua", "Guatajiagua", "mo_sur", "MO", 13.667, -88.200, 240.0, 12500, False, "Guatajiagua", ("Cantón San Bartolo", "Cantón Abelines")),
    "dist_chilanga": SalvadoranDistrictData("dist_chilanga", "Chilanga", "mo_sur", "MO", 13.717, -88.117, 310.0, 10500, False, "Chilanga", ("Cantón Piedra Parada",)),
    "dist_delicias_de_concepcion": SalvadoranDistrictData("dist_delicias_de_concepcion", "Delicias de Concepción", "mo_sur", "MO", 13.683, -88.150, 310.0, 5200, False, "Delicias de Concepción", ("Cantón El Zapote",)),
    "dist_el_divisadero": SalvadoranDistrictData("dist_el_divisadero", "El Divisadero", "mo_sur", "MO", 13.600, -88.067, 240.0, 8500, False, "El Divisadero", ("Cantón Villa San José",)),
    "dist_gualococti": SalvadoranDistrictData("dist_gualococti", "Gualococti", "mo_sur", "MO", 13.750, -88.183, 440.0, 3800, False, "Gualococti", ("Cantón La Joya",)),
    "dist_lolotiquillo": SalvadoranDistrictData("dist_lolotiquillo", "Lolotiquillo", "mo_sur", "MO", 13.717, -88.083, 340.0, 5000, False, "Lolotiquillo", ("Cantón Manzanilla",)),
    "dist_osicala": SalvadoranDistrictData("dist_osicala", "Osicala", "mo_sur", "MO", 13.800, -88.150, 520.0, 11000, False, "Osicala", ("Cantón Agua Caliente",)),
    "dist_san_carlos": SalvadoranDistrictData("dist_san_carlos", "San Carlos", "mo_sur", "MO", 13.667, -88.083, 230.0, 4200, False, "San Carlos", ("Cantón San Marcos",)),
    "dist_san_simon": SalvadoranDistrictData("dist_san_simon", "San Simón", "mo_sur", "MO", 13.833, -88.200, 620.0, 10500, False, "San Simón", ("Cantón El Carrizal",)),
    "dist_sensembra": SalvadoranDistrictData("dist_sensembra", "Sensembra", "mo_sur", "MO", 13.667, -88.183, 380.0, 3200, False, "Sensembra", ("Cantón El Limón",)),
    "dist_sociedad": SalvadoranDistrictData("dist_sociedad", "Sociedad", "mo_sur", "MO", 13.700, -88.017, 360.0, 12000, False, "Sociedad", ("Cantón Bejucal",)),
    "dist_yamabal": SalvadoranDistrictData("dist_yamabal", "Yamabal", "mo_sur", "MO", 13.683, -88.150, 300.0, 4500, False, "Yamabal", ("Cantón San Juan",)),
    "dist_yoloaiquin": SalvadoranDistrictData("dist_yoloaiquin", "Yoloaiquín", "mo_sur", "MO", 13.733, -88.133, 460.0, 4000, False, "Yoloaiquín", ("Cantón La Huerta",)),
    "dist_jocoro": SalvadoranDistrictData("dist_jocoro", "Jocoro", "mo_sur", "MO", 13.617, -88.033, 180.0, 11000, True, "Jocoro", ("Cantón San José", "Cantón Flamenco")),

    # La Unión Norte (12)
    "dist_anamoros": SalvadoranDistrictData("dist_anamoros", "Anamorós", "lu_norte", "LU", 13.733, -87.867, 160.0, 15000, False, "Anamorós", ("Cantón Huertas Viejas", "Cantón Terrero")),
    "dist_bolivar": SalvadoranDistrictData("dist_bolivar", "Bolívar", "lu_norte", "LU", 13.567, -87.967, 160.0, 4500, False, "Bolívar", ("Cantón La Paz",)),
    "dist_concepcion_de_oriente": SalvadoranDistrictData("dist_concepcion_de_oriente", "Concepción de Oriente", "lu_norte", "LU", 13.783, -87.750, 140.0, 8500, False, "Concepción de Oriente", ("Cantón El Molino",)),
    "dist_el_carmen_lu": SalvadoranDistrictData("dist_el_carmen_lu", "El Carmen", "lu_norte", "LU", 13.350, -88.000, 80.0, 13000, False, "El Carmen", ("Cantón Olomega",)),
    "dist_el_sauce": SalvadoranDistrictData("dist_el_sauce", "El Sauce", "lu_norte", "LU", 13.667, -87.767, 150.0, 7000, False, "El Sauce", ("Cantón Santa Rosita",)),
    "dist_lislique": SalvadoranDistrictData("dist_lislique", "Lislique", "lu_norte", "LU", 13.800, -87.800, 220.0, 14000, False, "Lislique", ("Cantón San Bartolo",)),
    "dist_nueva_esparta": SalvadoranDistrictData("dist_nueva_esparta", "Nueva Esparta", "lu_norte", "LU", 13.783, -87.833, 200.0, 10000, False, "Nueva Esparta", ("Cantón Las Marías",)),
    "dist_pasaquina": SalvadoranDistrictData("dist_pasaquina", "Pasaquina", "lu_norte", "LU", 13.583, -87.833, 60.0, 17000, False, "Pasaquina", ("Cantón San Felipe", "Cantón Piedras Blancas")),
    "dist_poloros": SalvadoranDistrictData("dist_poloros", "Polorós", "lu_norte", "LU", 13.800, -87.883, 190.0, 10000, False, "Polorós", ("Cantón Boquerón",)),
    "dist_san_alejo": SalvadoranDistrictData("dist_san_alejo", "San Alejo", "lu_norte", "LU", 13.433, -87.967, 120.0, 18000, False, "San Alejo", ("Cantón Cerco de Piedra",)),
    "dist_santa_rosa_de_lima": SalvadoranDistrictData("dist_santa_rosa_de_lima", "Santa Rosa de Lima", "lu_norte", "LU", 13.617, -87.883, 90.0, 35000, True, "Santa Rosa de Lima", ("Cantón La Chorrera", "Cantón Pasaquinita")),
    "dist_yayantique": SalvadoranDistrictData("dist_yayantique", "Yayantique", "lu_norte", "LU", 13.450, -88.017, 140.0, 8000, False, "Yayantique", ("Cantón El Cutuco",)),

    # La Unión Sur (6)
    "dist_la_union": SalvadoranDistrictData("dist_la_union", "La Unión", "lu_sur", "LU", 13.333, -87.833, 10.0, 40000, True, "Puerto de La Unión", ("Cantón El Faro", "Cantón Chiquirín", "Cantón Las Mareas")),
    "dist_conchagua": SalvadoranDistrictData("dist_conchagua", "Conchagua", "lu_sur", "LU", 13.300, -87.867, 360.0, 48000, False, "Conchagua", ("Cantón El Tamarindo", "Cantón Las Tunas", "Cantón Playas Negras")),
    "dist_intipuca": SalvadoranDistrictData("dist_intipuca", "Intipucá", "lu_sur", "LU", 13.200, -88.050, 90.0, 8500, False, "Intipucá", ("Cantón El Esterón", "Cantón El Icacal")),
    "dist_san_jose_lu": SalvadoranDistrictData("dist_san_jose_lu", "San José", "lu_sur", "LU", 13.383, -87.950, 160.0, 3200, False, "San José", ("Cantón El Sombrerito",)),
    "dist_yucuaiquin": SalvadoranDistrictData("dist_yucuaiquin", "Yucuaiquín", "lu_sur", "LU", 13.550, -88.017, 480.0, 7500, False, "Yucuaiquín", ("Cantón Las Cruces",)),
    "dist_meanguera_del_golfo": SalvadoranDistrictData("dist_meanguera_del_golfo", "Meanguera del Golfo", "lu_sur", "LU", 13.190, -87.710, 20.0, 2600, False, "Isla Meanguera", ("Isla Meanguerita", "Isla Conchagüita")),
}


# =============================================================================
# 4. PHYSICAL GEOGRAPHY (VOLCANOES, RIVERS, LAKES, RANGES)
# =============================================================================

@dataclasses.dataclass(frozen=True)
class PhysicalFeatureData:
    feature_id: str
    name: str
    feature_type: str  # volcano, river, lake, bay, mountain_range
    department_codes: tuple[str, ...]
    latitude: float
    longitude: float
    elevation_m: float
    area_or_length: float  # km2 for lake/bay, km for river, or height for mountain
    is_impassable_obstacle: bool
    description: str


SALVADORAN_PHYSICAL_FEATURES_P8: dict[str, PhysicalFeatureData] = {
    # Volcanoes
    "volc_santa_ana": PhysicalFeatureData("volc_santa_ana", "Volcán de Santa Ana (Ilamatepec)", "volcano", ("SA",), 13.853, -89.630, 2381.0, 2381.0, True, "Estratovolcán activo más alto de El Salvador con laguna ácida en cráter"),
    "volc_izalco": PhysicalFeatureData("volc_izalco", "Volcán de Izalco", "volcano", ("SO",), 13.813, -89.633, 1950.0, 1950.0, True, "Conocido como el Faro del Pacífico por sus erupciones continuas en siglos pasados"),
    "volc_san_salvador": PhysicalFeatureData("volc_san_salvador", "Volcán de San Salvador (Quezaltepec)", "volcano", ("SS", "LL"), 13.735, -89.287, 1893.0, 1893.0, True, "Cráter principal El Boquerón dominante sobre el área metropolitana"),
    "volc_san_vicente": PhysicalFeatureData("volc_san_vicente", "Volcán de San Vicente (Chinchontepec)", "volcano", ("SV", "LP"), 13.596, -88.837, 2182.0, 2182.0, True, "Estratovolcán de doble cúspide con fuentes termales infiernillos"),
    "volc_san_miguel": PhysicalFeatureData("volc_san_miguel", "Volcán de San Miguel (Chaparrastique)", "volcano", ("SM",), 13.434, -88.270, 2130.0, 2130.0, True, "Uno de los volcanes más activos con frecuentes emisiones de ceniza y gases"),
    "volc_conchagua": PhysicalFeatureData("volc_conchagua", "Volcán de Conchagua", "volcano", ("LU",), 13.276, -87.845, 1225.0, 1225.0, False, "Mirador panorámico sobre las islas del Golfo de Fonseca"),

    # Lakes & Reservoirs
    "lago_coatepeque": PhysicalFeatureData("lago_coatepeque", "Lago de Coatepeque", "lake", ("SA",), 13.870, -89.553, 745.0, 25.3, True, "Caldera volcánica con aguas turquesas y profundidad de más de 100m"),
    "lago_ilopango": PhysicalFeatureData("lago_ilopango", "Lago de Ilopango", "lake", ("SS", "CU", "LP"), 13.672, -89.053, 440.0, 72.0, True, "Gran caldera de origen volcánico surgida de la cataclísmica erupción Tierra Blanca Joven"),
    "lago_guija": PhysicalFeatureData("lago_guija", "Lago de Güija", "lake", ("SA",), 14.267, -89.533, 430.0, 45.0, True, "Lago fronterizo de origen volcánico compartido con Guatemala"),
    "embalse_cerron_grande": PhysicalFeatureData("embalse_cerron_grande", "Embalse Cerrón Grande (Lago Suchitlán)", "lake", ("CH", "CU", "CA", "SS"), 14.050, -89.033, 240.0, 135.0, True, "Mayor cuerpo de agua artificial de El Salvador alimentado por el Río Lempa"),

    # Rivers (Spine)
    "rio_lempa": PhysicalFeatureData("rio_lempa", "Río Lempa", "river", ("CH", "CA", "SV", "US", "LP", "SS", "SA"), 13.600, -88.800, 50.0, 422.0, True, "Columna hidroeléctrica del país; barrera natural infranqueable salvo en puentes oficiales"),
    "rio_grande_san_miguel": PhysicalFeatureData("rio_grande_san_miguel", "Río Grande de San Miguel", "river", ("SM", "US"), 13.400, -88.200, 30.0, 124.0, True, "Drena la planicie oriental hacia la Bahía de Jiquilisco"),
    "rio_paz": PhysicalFeatureData("rio_paz", "Río Paz", "river", ("AH",), 13.800, -90.050, 10.0, 134.0, True, "Frontera natural occidental con la República de Guatemala"),
    "rio_goascoran": PhysicalFeatureData("rio_goascoran", "Río Goascorán", "river", ("LU",), 13.500, -87.750, 10.0, 130.0, True, "Frontera oriental desembocando en el Golfo de Fonseca"),
    "rio_jiboa": PhysicalFeatureData("rio_jiboa", "Río Jiboa", "river", ("SV", "LP"), 13.500, -89.000, 30.0, 60.0, True, "Nace en el Lago de Ilopango y desemboca en el Océano Pacífico"),
    "rio_torola": PhysicalFeatureData("rio_torola", "Río Torola", "river", ("MO", "SM"), 13.850, -88.200, 180.0, 64.0, True, "Afluente septentrional del Río Lempa en la zona norte de Morazán"),

    # Coastal Estuaries & Bays
    "bahia_jiquilisco": PhysicalFeatureData("bahia_jiquilisco", "Bahía de Jiquilisco", "bay", ("US",), 13.230, -88.480, 0.0, 630.0, True, "Sitio Ramsar, el manglar más extenso de El Salvador con canales marinos e islas"),
    "golfo_fonseca": PhysicalFeatureData("golfo_fonseca", "Golfo de Fonseca", "bay", ("LU",), 13.250, -87.750, 0.0, 3200.0, True, "Tríada marítima pacífica entre El Salvador, Honduras y Nicaragua"),
}


# =============================================================================
# 5. ROAD NETWORK (TRONCALES, INTERCONEXIONES Y PUENTES CRÍTICOS)
# =============================================================================

@dataclasses.dataclass(frozen=True)
class RoadSegmentData:
    segment_id: str
    name: str
    from_district_id: str
    to_district_id: str
    road_type: str  # paved_highway, secondary_asphalt, cobblestone, unpaved_dirt_road
    distance_km: float
    base_speed_kmh: float
    is_bridge: bool = False
    bridge_name: Optional[str] = None
    crosses_river_id: Optional[str] = None
    flooding_vulnerability: float = 0.0  # [0.0, 1.0] probability of disruption during temporales
    slope_gradient: float = 0.0         # fraction, e.g. 0.05 = 5% grade


SALVADORAN_ROAD_NETWORK_P8: list[RoadSegmentData] = [
    # -------------------------------------------------------------------------
    # CA-1 (Carretera Panamericana): Frontera Las Chinamas -> Santa Ana -> San Salvador -> San Vicente -> San Miguel -> El Amatillo
    # -------------------------------------------------------------------------
    RoadSegmentData("ca1_ah_chalchuapa", "CA-1 Panamericana", "dist_ahuachapan", "dist_chalchuapa", "paved_highway", 21.0, 70.0, slope_gradient=0.03),
    RoadSegmentData("ca1_chalchuapa_sa", "CA-1 Panamericana", "dist_chalchuapa", "dist_santa_ana", "paved_highway", 14.0, 75.0),
    RoadSegmentData("ca1_sa_elcongo", "CA-1 Panamericana", "dist_santa_ana", "dist_el_congo", "paved_highway", 16.0, 80.0),
    RoadSegmentData("ca1_elcongo_ciudadarce", "CA-1 Panamericana", "dist_el_congo", "dist_ciudad_arce", "paved_highway", 12.0, 80.0),
    RoadSegmentData("ca1_ciudadarce_lourdes", "CA-1 Panamericana", "dist_ciudad_arce", "dist_colon", "paved_highway", 15.0, 70.0),
    RoadSegmentData("ca1_lourdes_santatecla", "CA-1 Panamericana (Los Chorros)", "dist_colon", "dist_santa_tecla", "paved_highway", 11.5, 55.0, flooding_vulnerability=0.75, slope_gradient=0.06),
    RoadSegmentData("ca1_santatecla_sansalvador", "CA-1 Alameda Manuel Enrique Araujo", "dist_santa_tecla", "dist_san_salvador", "paved_highway", 9.0, 50.0),
    RoadSegmentData("ca1_sansalvador_soyapango", "CA-1 Bulevar del Ejército", "dist_san_salvador", "dist_soyapango", "paved_highway", 6.5, 45.0),
    RoadSegmentData("ca1_soyapango_ilopango", "CA-1 Panamericana", "dist_soyapango", "dist_ilopango", "paved_highway", 5.0, 60.0),
    RoadSegmentData("ca1_ilopango_sanmartin", "CA-1 Panamericana", "dist_ilopango", "dist_san_martin", "paved_highway", 7.5, 70.0),
    RoadSegmentData("ca1_sanmartin_cojutepeque", "CA-1 Panamericana", "dist_san_martin", "dist_cojutepeque", "paved_highway", 17.0, 75.0, slope_gradient=0.04),
    RoadSegmentData("ca1_cojutepeque_sanrafaelcedros", "CA-1 Panamericana", "dist_cojutepeque", "dist_san_rafael_cedros", "paved_highway", 8.0, 80.0),
    RoadSegmentData("ca1_sanrafaelcedros_sanvicente", "CA-1 Panamericana", "dist_san_rafael_cedros", "dist_san_vicente", "paved_highway", 18.0, 80.0),
    RoadSegmentData("ca1_sanvicente_puentecuscatlan", "CA-1 Panamericana", "dist_san_vicente", "dist_mercedes_umana", "paved_highway", 22.0, 80.0, is_bridge=True, bridge_name="Puente Cuscatlán", crosses_river_id="rio_lempa"),
    RoadSegmentData("ca1_mercedesumana_el_triunfo", "CA-1 Panamericana", "dist_mercedes_umana", "dist_el_triunfo_us", "paved_highway", 11.0, 75.0),
    RoadSegmentData("ca1_eltriunfo_moncagua", "CA-1 Panamericana", "dist_el_triunfo_us", "dist_moncagua", "paved_highway", 19.0, 80.0),
    RoadSegmentData("ca1_moncagua_sanmiguel", "CA-1 Panamericana", "dist_moncagua", "dist_san_miguel", "paved_highway", 12.0, 70.0),
    RoadSegmentData("ca1_sanmiguel_santarosadelima", "CA-1 Ruta Militar", "dist_san_miguel", "dist_santa_rosa_de_lima", "paved_highway", 38.0, 80.0),
    RoadSegmentData("ca1_santarosa_pasaquina", "CA-1 Panamericana", "dist_santa_rosa_de_lima", "dist_pasaquina", "paved_highway", 14.0, 85.0),
    RoadSegmentData("ca1_pasaquina_elamatillo", "CA-1 Panamericana (Frontera El Amatillo)", "dist_pasaquina", "dist_concepcion_de_oriente", "paved_highway", 18.0, 80.0, is_bridge=True, bridge_name="Puente Internacional Goascorán", crosses_river_id="rio_goascoran"),

    # -------------------------------------------------------------------------
    # CA-2 (Carretera del Litoral): Hachadura -> Acajutla -> La Libertad -> Zacatecoluca -> Usulután -> San Miguel
    # -------------------------------------------------------------------------
    RoadSegmentData("ca2_hachadura_acajutla", "CA-2 Litoral", "dist_san_francisco_menendez", "dist_acajutla", "paved_highway", 46.0, 85.0),
    RoadSegmentData("ca2_acajutla_lalibertad", "CA-2 Litoral", "dist_acajutla", "dist_la_libertad", "paved_highway", 68.0, 75.0, flooding_vulnerability=0.30),
    RoadSegmentData("ca2_lalibertad_sanluistalpa", "CA-2 Litoral", "dist_la_libertad", "dist_san_luis_talpa", "paved_highway", 29.0, 85.0),
    RoadSegmentData("ca2_sanluistalpa_zacatecoluca", "CA-2 Litoral", "dist_san_luis_talpa", "dist_zacatecoluca", "paved_highway", 32.0, 90.0),
    RoadSegmentData("ca2_zacatecoluca_puentedeoro", "CA-2 Litoral", "dist_zacatecoluca", "dist_jiquilisco", "paved_highway", 38.0, 85.0, is_bridge=True, bridge_name="Puente de Oro (San Marcos Lempa)", crosses_river_id="rio_lempa", flooding_vulnerability=0.45),
    RoadSegmentData("ca2_jiquilisco_usulutan", "CA-2 Litoral", "dist_jiquilisco", "dist_usulutan", "paved_highway", 15.0, 80.0),
    RoadSegmentData("ca2_usulutan_eltransito", "CA-2 Litoral", "dist_usulutan", "dist_el_transito", "paved_highway", 22.0, 80.0),
    RoadSegmentData("ca2_eltransito_sanmiguel", "CA-2 Litoral Conexión", "dist_el_transito", "dist_san_miguel", "paved_highway", 21.0, 75.0),
    RoadSegmentData("ca2_sanmiguel_launion", "CA-2 Litoral", "dist_san_miguel", "dist_la_union", "paved_highway", 44.0, 85.0),

    # -------------------------------------------------------------------------
    # CA-4 (Troncal del Norte): San Salvador -> Apopa -> Aguilares -> Chalatenango / La Palma -> El Poy
    # -------------------------------------------------------------------------
    RoadSegmentData("ca4_sansalvador_apopa", "CA-4 Troncal del Norte", "dist_san_salvador", "dist_apopa", "paved_highway", 12.0, 50.0),
    RoadSegmentData("ca4_apopa_aguilares", "CA-4 Troncal del Norte", "dist_apopa", "dist_aguilares", "paved_highway", 19.0, 75.0),
    RoadSegmentData("ca4_aguilares_colima", "CA-4 Troncal del Norte", "dist_aguilares", "dist_tejutla", "paved_highway", 14.0, 75.0, is_bridge=True, bridge_name="Puente Colima", crosses_river_id="rio_lempa"),
    RoadSegmentData("ca4_tejutla_lapalma", "CA-4 Troncal del Norte", "dist_tejutla", "dist_la_palma", "paved_highway", 26.0, 60.0, slope_gradient=0.07, flooding_vulnerability=0.40),
    RoadSegmentData("ca4_lapalma_sanignacio", "CA-4 Troncal del Norte", "dist_la_palma", "dist_san_ignacio", "paved_highway", 7.0, 60.0),
    RoadSegmentData("ca4_sanignacio_citala", "CA-4 Troncal del Norte (Frontera El Poy)", "dist_san_ignacio", "dist_citala", "paved_highway", 8.0, 60.0),

    # -------------------------------------------------------------------------
    # Ruta de Las Flores (RN-8 / RN-1)
    # -------------------------------------------------------------------------
    RoadSegmentData("flores_sonsonate_nahuizalco", "Ruta de Las Flores", "dist_sonsonate", "dist_nahuizalco", "secondary_asphalt", 8.5, 55.0, slope_gradient=0.04),
    RoadSegmentData("flores_nahuizalco_salcoatitan", "Ruta de Las Flores", "dist_nahuizalco", "dist_salcoatitan", "secondary_asphalt", 6.5, 50.0, slope_gradient=0.07),
    RoadSegmentData("flores_salcoatitan_juayua", "Ruta de Las Flores", "dist_salcoatitan", "dist_juayua", "secondary_asphalt", 3.5, 45.0),
    RoadSegmentData("flores_juayua_apaneca", "Ruta de Las Flores", "dist_juayua", "dist_apaneca", "secondary_asphalt", 11.0, 50.0, slope_gradient=0.06),
    RoadSegmentData("flores_apaneca_ataco", "Ruta de Las Flores", "dist_apaneca", "dist_concepcion_de_ataco", "secondary_asphalt", 7.0, 50.0),
    RoadSegmentData("flores_ataco_ahuachapan", "Ruta de Las Flores", "dist_concepcion_de_ataco", "dist_ahuachapan", "secondary_asphalt", 9.5, 60.0),

    # -------------------------------------------------------------------------
    # Conexiones Transversales e Interdepartamentales
    # -------------------------------------------------------------------------
    RoadSegmentData("conn_ss_comalapa", "Autopista al Aeropuerto Internacional San Óscar Romero", "dist_san_salvador", "dist_san_luis_talpa", "paved_highway", 39.0, 90.0),
    RoadSegmentData("conn_sansalvador_panchimalco", "Carretera a Los Planes y Panchimalco", "dist_san_salvador", "dist_panchimalco", "secondary_asphalt", 14.5, 45.0, slope_gradient=0.06),
    RoadSegmentData("conn_santatecla_lalibertad", "Carretera al Puerto (Bulevar Sur)", "dist_santa_tecla", "dist_la_libertad", "paved_highway", 24.0, 75.0, slope_gradient=0.05),
    RoadSegmentData("conn_aguilares_suchitoto", "Carretera Suchitoto", "dist_aguilares", "dist_suchitoto", "secondary_asphalt", 23.0, 50.0),
    RoadSegmentData("conn_aguilares_nuevaconcepcion", "Carretera a Nueva Concepción", "dist_aguilares", "dist_nueva_concepcion", "secondary_asphalt", 22.0, 65.0),
    RoadSegmentData("conn_suchitoto_sanmartin", "Ruta del Lago Suchitlán", "dist_suchitoto", "dist_san_martin", "secondary_asphalt", 28.0, 50.0),
    RoadSegmentData("conn_sonsonate_acajutla", "Carretera Acajutla", "dist_sonsonate", "dist_acajutla", "paved_highway", 19.0, 80.0),
    RoadSegmentData("conn_santaana_sonsonate", "Carretera Los Naranjos", "dist_santa_ana", "dist_sonsonate", "secondary_asphalt", 41.0, 50.0, slope_gradient=0.08, flooding_vulnerability=0.35),
    RoadSegmentData("conn_sanmiguel_gotera", "Ruta de la Paz", "dist_san_miguel", "dist_san_francisco_gotera", "secondary_asphalt", 24.0, 65.0),
    RoadSegmentData("conn_gotera_perquin", "Ruta de la Paz Alta", "dist_san_francisco_gotera", "dist_perquin", "secondary_asphalt", 37.0, 45.0, slope_gradient=0.08, flooding_vulnerability=0.45),

    # -------------------------------------------------------------------------
    # Caminos Vecinales Rurales y Vías no Pavimentadas
    # -------------------------------------------------------------------------
    RoadSegmentData("dirt_nahuizalco_tajcuicuitlapan", "Camino Cantonal Tajcuicuitlapán", "dist_nahuizalco", "dist_santa_catarina_masahuat", "unpaved_dirt_road", 5.5, 18.0, flooding_vulnerability=0.85, slope_gradient=0.10),
    RoadSegmentData("dirt_lapalma_miramundo", "Camino a Miramundo y Las Pilas", "dist_la_palma", "dist_san_ignacio", "unpaved_dirt_road", 12.0, 15.0, flooding_vulnerability=0.90, slope_gradient=0.14),
    RoadSegmentData("dirt_suchitoto_sanlucas", "Camino Vecinal Cantón San Lucas", "dist_suchitoto", "dist_san_jose_guayabal", "unpaved_dirt_road", 8.0, 20.0, flooding_vulnerability=0.80),
    RoadSegmentData("dirt_jucuaran_puntamango", "Camino Costero Punta Mango", "dist_jucuaran", "dist_chirilagua", "unpaved_dirt_road", 16.0, 18.0, flooding_vulnerability=0.85, slope_gradient=0.09),
    RoadSegmentData("dirt_guatajiagua_sanbartolo", "Camino de los Alfareros", "dist_guatajiagua", "dist_sensembra", "unpaved_dirt_road", 7.5, 20.0, flooding_vulnerability=0.75),
]
