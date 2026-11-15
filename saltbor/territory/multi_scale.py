"""Multi-Scale Territorial Simulation Engine for SALTBOR Phase 1.14.

Coordinates 6 nested geographic and organizational scales:
- LEVEL 1: Individuals (Needs, cognitive state, daily activities, consumption)
- LEVEL 2: Households (Shared budgets, food pantry, housing tenure, family decisions)
- LEVEL 3: Businesses & Institutions (Solvency, employees, production capacity, service queues)
- LEVEL 4: Communities (Social networks, ADESCOs, CPR resources, local collective action)
- LEVEL 5: Municipalities (44 Vigentes under 2024 reform, infrastructure, municipal services)
- LEVEL 6: Department & National Territory (14 Departments, inter-departmental trade, macro policies)

Guarantees:
- The SAME synthetic human retains identity and relationships across all 6 scales.
- Zero population duplication during spatial aggregation.
- Bi-directional hierarchical drill-down and roll-up navigation without context loss.
"""

from __future__ import annotations

import collections
import dataclasses
import logging
from typing import Any, Dict, List, Optional, Set, Tuple

from saltbor.datasets.salvadoran.territory_data import (
    SALVADORAN_DEPARTMENTS_P8,
    SALVADORAN_MUNICIPALITIES_P8,
    SALVADORAN_DISTRICTS_P8,
    AdministrativeLevel,
)
from saltbor.domain.models import DataProvenanceTier
from saltbor.territory.models import (
    TerritorialElement,
    TerritorialElementType,
    TerritorialScale,
)

logger = logging.getLogger(__name__)


@dataclasses.dataclass
class MultiScaleIndividualRecord:
    """Individual human representation linked across all organizational tiers."""
    uid: str
    name: str
    age: int
    gender: str
    household_id: str
    workplace_id: Optional[str]
    community_id: str
    municipality_id: str
    department_code: str
    is_rural: bool
    cash_usd: float
    current_activity: str
    health_status: float = 1.0     # 0.0 to 1.0
    education_level_years: int = 6


@dataclasses.dataclass
class MultiScaleHouseholdRecord:
    """Domestic unit aggregating cohabiting individuals."""
    household_id: str
    head_uid: str
    member_uids: List[str]
    community_id: str
    municipality_id: str
    department_code: str
    dwelling_type: str            # "owner_occupied", "rental", "informal", "rural_farm"
    shared_cash_usd: float
    pantry_food_kg: float
    monthly_utility_obligation_usd: float
    is_in_distress: bool = False


@dataclasses.dataclass
class MultiScaleCommunityRecord:
    """Settlement, canton, or barrio tier."""
    community_id: str
    name: str
    municipality_id: str
    district_id: str
    department_code: str
    is_rural: bool
    latitude: float
    longitude: float
    household_ids: List[str] = dataclasses.field(default_factory=list)
    has_active_adesco: bool = True
    cpr_water_reservoir_available: bool = True


class MultiScaleTerritorialSimulationEngine:
    """Orchestrates nested territorial simulation across Levels 1 through 6."""

    def __init__(self) -> None:
        self.individuals: Dict[str, MultiScaleIndividualRecord] = {}
        self.households: Dict[str, MultiScaleHouseholdRecord] = {}
        self.communities: Dict[str, MultiScaleCommunityRecord] = {}
        self.municipalities: Dict[str, Dict[str, Any]] = {}
        self.departments: Dict[str, Dict[str, Any]] = {}

        self._load_administrative_hierarchy()
        self._seed_sample_territorial_population()

    # =========================================================================
    # Administrative Hierarchy Initialization (CNR / IGN 2024)
    # =========================================================================

    def _load_administrative_hierarchy(self) -> None:
        """Load 14 departments and 44 municipalities conforming to D.L. 762 (May 2024)."""
        # Level 6: 14 Departments
        for dept in SALVADORAN_DEPARTMENTS_P8.values():
            self.departments[dept.code] = {
                "department_code": dept.code,
                "name": dept.name,
                "capital": dept.cabecera,
                "region": dept.zone,
                "approx_population": dept.population_2024,
                "area_km2": dept.area_km2,
                "centroid_lat": dept.centroid_lat,
                "centroid_lon": dept.centroid_lon,
            }

        # Level 5: 44 Vigentes Municipalities
        for muni_id, muni in SALVADORAN_MUNICIPALITIES_P8.items():
            self.municipalities[muni_id] = {
                "municipality_id": muni.municipality_id,
                "name": muni.name,
                "department_code": muni.department_code,
                "cabecera_municipal": muni.cabecera_municipal,
                "district_ids": list(muni.district_ids),
                "approx_population": muni.approx_population,
            }

        # Level 4: Default Initial Communities based on key districts
        for dist_id, dist in SALVADORAN_DISTRICTS_P8.items():
            self.communities[dist_id] = MultiScaleCommunityRecord(
                community_id=dist_id,
                name=dist.name,
                municipality_id=dist.municipality_id,
                district_id=dist.district_id,
                department_code=dist.department_code,
                is_rural=not dist.is_urban_core,
                latitude=dist.latitude,
                longitude=dist.longitude,
                household_ids=[],
                has_active_adesco=True,
                cpr_water_reservoir_available=not dist.is_urban_core,
            )

    # =========================================================================
    # Multi-Scale Navigation & Traceability
    # =========================================================================

    def get_individual_hierarchy(self, uid: str) -> Optional[Dict[str, Any]]:
        """Trace a specific synthetic human across all 6 nested scales."""
        ind = self.individuals.get(uid)
        if not ind:
            return None

        hh = self.households.get(ind.household_id)
        comm = self.communities.get(ind.community_id)
        muni = self.municipalities.get(ind.municipality_id)
        dept = self.departments.get(ind.department_code)

        return {
            "level_1_individual": {
                "uid": ind.uid,
                "name": ind.name,
                "age": ind.age,
                "gender": ind.gender,
                "cash_usd": ind.cash_usd,
                "activity": ind.current_activity,
            },
            "level_2_household": {
                "household_id": hh.household_id if hh else None,
                "dwelling_type": hh.dwelling_type if hh else None,
                "member_count": len(hh.member_uids) if hh else 1,
                "shared_cash_usd": hh.shared_cash_usd if hh else ind.cash_usd,
                "is_in_distress": hh.is_in_distress if hh else False,
            },
            "level_3_workplace": {
                "workplace_id": ind.workplace_id or "unemployed_informal",
            },
            "level_4_community": {
                "community_id": comm.community_id if comm else None,
                "name": comm.name if comm else "Canton Local",
                "is_rural": comm.is_rural if comm else ind.is_rural,
                "has_adesco": comm.has_active_adesco if comm else False,
            },
            "level_5_municipality": {
                "municipality_id": muni.get("municipality_id") if muni else ind.municipality_id,
                "name": muni.get("name") if muni else ind.municipality_id,
            },
            "level_6_department_national": {
                "department_code": dept.get("department_code") if dept else ind.department_code,
                "name": dept.get("name") if dept else ind.department_code,
                "country": "El Salvador",
            },
        }

    def aggregate_population_by_scale(self, scale: TerritorialScale) -> Dict[str, Any]:
        """Aggregate population totals strictly without double counting."""
        if scale == TerritorialScale.LEVEL_6_DEPARTMENT_NATIONAL:
            dept_counts: Dict[str, int] = collections.defaultdict(int)
            for ind in self.individuals.values():
                dept_counts[ind.department_code] += 1
            return {
                "scale": scale.value,
                "total_population": len(self.individuals),
                "counts_by_department": dict(dept_counts),
            }

        elif scale == TerritorialScale.LEVEL_5_MUNICIPALITY:
            muni_counts: Dict[str, int] = collections.defaultdict(int)
            for ind in self.individuals.values():
                muni_counts[ind.municipality_id] += 1
            return {
                "scale": scale.value,
                "total_population": len(self.individuals),
                "counts_by_municipality": dict(muni_counts),
            }

        elif scale == TerritorialScale.LEVEL_4_COMMUNITY:
            comm_counts: Dict[str, int] = collections.defaultdict(int)
            for ind in self.individuals.values():
                comm_counts[ind.community_id] += 1
            return {
                "scale": scale.value,
                "total_population": len(self.individuals),
                "counts_by_community": dict(comm_counts),
            }

        elif scale == TerritorialScale.LEVEL_2_HOUSEHOLD:
            hh_sizes = [len(hh.member_uids) for hh in self.households.values()]
            return {
                "scale": scale.value,
                "total_households": len(self.households),
                "total_population_in_households": sum(hh_sizes),
                "average_household_size": round(sum(hh_sizes) / max(len(hh_sizes), 1), 2),
            }

        else:  # LEVEL_1_INDIVIDUAL
            return {
                "scale": scale.value,
                "total_individuals": len(self.individuals),
                "active_activities": collections.Counter(ind.current_activity for ind in self.individuals.values()),
            }

    def verify_population_conservation(self) -> Tuple[bool, str]:
        """Strict check that population across households equals population across communities and total individuals."""
        total_individuals = len(self.individuals)
        total_in_households = sum(len(hh.member_uids) for hh in self.households.values())

        if total_individuals != total_in_households:
            return False, f"Mismatch: {total_individuals} total individuals != {total_in_households} in households"

        comm_pop = sum(
            len(ind_list)
            for ind_list in [
                [i for i in self.individuals.values() if i.community_id == cid]
                for cid in self.communities
            ]
        )
        if comm_pop != total_individuals:
            return False, f"Mismatch: {comm_pop} in communities != {total_individuals} total"

        return True, f"Population strictly conserved: {total_individuals} individuals across all scales (0 duplicates)."

    # =========================================================================
    # Population & Household Seed
    # =========================================================================

    def _seed_sample_territorial_population(self) -> None:
        """Seed representative multi-scale households and individuals across El Salvador."""
        sample_communities = [
            ("ss_centro", "San Salvador Centro", "SS01", "SS", False, 13.6989, -89.1914),
            ("soyapango", "Soyapango", "SS02", "SS", False, 13.7102, -89.1398),
            ("santa_ana_dist", "Santa Ana Centro", "SA01", "SA", False, 13.9942, -89.5597),
            ("chalatenango_dist", "Chalatenango Rural", "CH01", "CH", True, 14.0415, -88.9357),
            ("san_miguel_dist", "San Miguel Centro", "SM01", "SM", False, 13.4833, -88.1833),
            ("usulutan_dist", "Usulután Agrícola", "US01", "US", True, 13.3500, -88.4500),
            ("la_libertad_costa", "La Libertad Costa", "LL02", "LL", False, 13.4883, -89.3222),
            ("ahuachapan_rural", "Ahuachapán Cafetalero", "AH01", "AH", True, 13.9214, -89.8450),
        ]

        ind_counter = 1
        hh_counter = 1

        for comm_id, name, muni_id, dept_code, is_rural, lat, lon in sample_communities:
            if comm_id not in self.communities:
                self.communities[comm_id] = MultiScaleCommunityRecord(
                    community_id=comm_id,
                    name=name,
                    municipality_id=muni_id,
                    district_id=comm_id,
                    department_code=dept_code,
                    is_rural=is_rural,
                    latitude=lat,
                    longitude=lon,
                    household_ids=[],
                )

            # Generate 4 households per community (total 32 households, ~120 individuals)
            for h_idx in range(4):
                hid = f"hh_{comm_id}_{hh_counter}"
                hh_counter += 1

                # Head of household
                head_uid = f"human_{ind_counter:04d}"
                ind_counter += 1
                head_age = 35 + (h_idx * 5)
                head = MultiScaleIndividualRecord(
                    uid=head_uid,
                    name=f"Jefe_{head_uid}",
                    age=head_age,
                    gender="M" if h_idx % 2 == 0 else "F",
                    household_id=hid,
                    workplace_id=f"biz_{comm_id}_1" if h_idx < 3 else None,
                    community_id=comm_id,
                    municipality_id=muni_id,
                    department_code=dept_code,
                    is_rural=is_rural,
                    cash_usd=45.0 + (h_idx * 20.0),
                    current_activity="commerce.working_labor" if h_idx < 3 else "agriculture.farming",
                    education_level_years=9 if not is_rural else 6,
                )
                self.individuals[head_uid] = head

                # Spouse / Partner
                spouse_uid = f"human_{ind_counter:04d}"
                ind_counter += 1
                spouse = MultiScaleIndividualRecord(
                    uid=spouse_uid,
                    name=f"Pareja_{spouse_uid}",
                    age=head_age - 2,
                    gender="F" if head.gender == "M" else "M",
                    household_id=hid,
                    workplace_id=f"biz_{comm_id}_2" if h_idx % 2 == 0 else None,
                    community_id=comm_id,
                    municipality_id=muni_id,
                    department_code=dept_code,
                    is_rural=is_rural,
                    cash_usd=25.0,
                    current_activity="food.buy_pupusas" if h_idx % 2 == 0 else "caregiving.family",
                    education_level_years=8 if not is_rural else 5,
                )
                self.individuals[spouse_uid] = spouse

                # Child / Youth
                child_uid = f"human_{ind_counter:04d}"
                ind_counter += 1
                child = MultiScaleIndividualRecord(
                    uid=child_uid,
                    name=f"Hijo_{child_uid}",
                    age=12 + (h_idx % 6),
                    gender="M" if ind_counter % 2 == 0 else "F",
                    household_id=hid,
                    workplace_id=None,
                    community_id=comm_id,
                    municipality_id=muni_id,
                    department_code=dept_code,
                    is_rural=is_rural,
                    cash_usd=3.50,
                    current_activity="education.attend_school",
                    education_level_years=5,
                )
                self.individuals[child_uid] = child

                member_ids = [head_uid, spouse_uid, child_uid]
                household = MultiScaleHouseholdRecord(
                    household_id=hid,
                    head_uid=head_uid,
                    member_uids=member_ids,
                    community_id=comm_id,
                    municipality_id=muni_id,
                    department_code=dept_code,
                    dwelling_type="owner_occupied" if h_idx == 0 else ("rental" if not is_rural else "rural_farm"),
                    shared_cash_usd=120.0 + (h_idx * 40.0),
                    pantry_food_kg=25.0,
                    monthly_utility_obligation_usd=22.0 if not is_rural else 12.0,
                    is_in_distress=False,
                )
                self.households[hid] = household
                self.communities[comm_id].household_ids.append(hid)
