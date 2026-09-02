"""Deterministic consolidation of already-grouped domain fragments."""

import json
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Literal

from .bank_grouper import BankGroupingResult
from .fragment_contract import GroupedFragment, JSONValue, SourceReference
from .location_grouper import LocationGroupingResult
from .net_grouper import NetGroupingResult
from .personal_grouper import PersonalGroupingResult
from .professional_grouper import ProfessionalGroupingResult

DomainName = Literal["personal", "location", "professional", "bank", "net"]
ConsolidationStatus = Literal["complete", "incomplete", "ambiguous"]


@dataclass(frozen=True)
class DomainContribution:
    """Grouped evidence contributed by one domain."""

    fragments: tuple[GroupedFragment, ...]


@dataclass(frozen=True)
class UnresolvedContribution:
    """Input evidence that could not join an approved operational component."""

    payload: JSONValue
    context: str | None
    source_reference: SourceReference | None
    reason: str


@dataclass(frozen=True)
class ConsolidatedPersonRecord:
    """One deterministic operational connected component."""

    domains: Mapping[DomainName, DomainContribution | None]
    status: ConsolidationStatus
    correlation_rules: tuple[str, ...]
    provenance: tuple[SourceReference, ...]


@dataclass(frozen=True)
class ConsolidationResult:
    """Consolidated records and explicit unresolved input material."""

    records: tuple[ConsolidatedPersonRecord, ...]
    unresolved: tuple[UnresolvedContribution, ...]


@dataclass(frozen=True)
class _Node:
    domain: DomainName
    key: str
    fragments: tuple[GroupedFragment, ...]
    ambiguous: bool


def consolidate_person_records(
    personal: PersonalGroupingResult,
    location: LocationGroupingResult,
    professional: ProfessionalGroupingResult,
    bank: BankGroupingResult,
    net: NetGroupingResult,
) -> ConsolidationResult:
    """Assemble grouped domain results using only ADR-0006 exact edges."""

    nodes = _nodes(personal, location, professional, bank, net)
    parents = list(range(len(nodes)))
    rules_by_pair: dict[tuple[int, int], set[str]] = {}

    def union(left: int, right: int, rule: str) -> None:
        root_left = _find(parents, left)
        root_right = _find(parents, right)
        if root_left != root_right:
            parents[root_right] = root_left
        pair: tuple[int, int] = (min(left, right), max(left, right))
        rules_by_pair.setdefault(pair, set()).add(rule)

    for personal_index, personal_node in _by_domain(nodes, "personal"):
        for bank_index, bank_node in _by_domain(nodes, "bank"):
            if personal_node.key == bank_node.key:
                union(personal_index, bank_index, "personal_bank_passport")
        for location_index, location_node in _by_domain(nodes, "location"):
            if _personal_fullnames(personal_node) & {location_node.key}:
                union(personal_index, location_index, "personal_location_fullname")

    for location_index, location_node in _by_domain(nodes, "location"):
        for professional_index, professional_node in _by_domain(nodes, "professional"):
            if location_node.key == professional_node.key:
                union(location_index, professional_index, "location_professional_fullname")
        for net_index, net_node in _by_domain(nodes, "net"):
            if _location_addresses(location_node) & {net_node.key}:
                union(location_index, net_index, "location_net_address")

    components: dict[int, list[int]] = {}
    for index in range(len(nodes)):
        components.setdefault(_find(parents, index), []).append(index)

    records = tuple(
        _record(
            tuple(
                nodes[index]
                for index in sorted(indexes, key=lambda i: (nodes[i].domain, nodes[i].key))
            ),
            nodes,
            rules_by_pair,
        )
        for indexes in sorted(components.values(), key=lambda group: _component_key(group, nodes))
    )
    return ConsolidationResult(
        records=records,
        unresolved=_unresolved(personal, location, professional, bank, net),
    )


def _nodes(
    personal: PersonalGroupingResult,
    location: LocationGroupingResult,
    professional: ProfessionalGroupingResult,
    bank: BankGroupingResult,
    net: NetGroupingResult,
) -> tuple[_Node, ...]:
    return tuple(
        [_node("personal", group) for group in personal.groups]
        + [_node("location", group) for group in location.groups]
        + [_node("professional", group) for group in professional.groups]
        + [_node("bank", group) for group in bank.groups]
        + [_node("net", group) for group in net.groups]
    )


def _node(domain: DomainName, group: object) -> _Node:
    fragments = tuple(sorted(group.fragments, key=_canonical_fragment))  # type: ignore[attr-defined]
    return _Node(
        domain=domain,
        key=group.key,  # type: ignore[attr-defined]
        fragments=fragments,
        ambiguous=group.status == "ambiguous",  # type: ignore[attr-defined]
    )


def _by_domain(nodes: tuple[_Node, ...], domain: DomainName) -> tuple[tuple[int, _Node], ...]:
    return tuple((index, node) for index, node in enumerate(nodes) if node.domain == domain)


def _personal_fullnames(node: _Node) -> set[str]:
    values: set[str] = set()
    for fragment in node.fragments:
        name = fragment.payload.get("name")
        last_name = fragment.payload.get("last_name")
        if isinstance(name, str) and isinstance(last_name, str):
            values.add(f"{name} {last_name}")
    return values


def _location_addresses(node: _Node) -> set[str]:
    return {
        address
        for fragment in node.fragments
        if isinstance(address := fragment.payload.get("address"), str)
    }


def _record(
    component: tuple[_Node, ...],
    all_nodes: tuple[_Node, ...],
    rules_by_pair: dict[tuple[int, int], set[str]],
) -> ConsolidatedPersonRecord:
    domains: dict[DomainName, DomainContribution | None] = {
        "personal": None,
        "location": None,
        "professional": None,
        "bank": None,
        "net": None,
    }
    rules: set[str] = set()
    component_indexes = {all_nodes.index(node) for node in component}
    for node in component:
        contribution = DomainContribution(node.fragments)
        existing = domains[node.domain]
        if existing is None:
            domains[node.domain] = contribution
        else:
            domains[node.domain] = DomainContribution(
                tuple(sorted(existing.fragments + contribution.fragments, key=_canonical_fragment))
            )
        for pair, pair_rules in rules_by_pair.items():
            if pair[0] in component_indexes and pair[1] in component_indexes:
                rules.update(pair_rules)

    ambiguous = any(node.ambiguous for node in component) or any(
        sum(node.domain == domain for node in component) > 1
        for domain in ("personal", "location", "professional", "bank", "net")
    )
    status: ConsolidationStatus = (
        "ambiguous"
        if ambiguous
        else ("complete" if all(value is not None for value in domains.values()) else "incomplete")
    )
    provenance = tuple(
        sorted(
            {
                reference
                for node in component
                for fragment in node.fragments
                for reference in (fragment.source_reference,)
            }
        )
    )
    return ConsolidatedPersonRecord(
        domains=domains,
        status=status,
        correlation_rules=tuple(sorted(rules)),
        provenance=provenance,
    )


def _unresolved(*results: object) -> tuple[UnresolvedContribution, ...]:
    entries: list[UnresolvedContribution] = []
    for result in results:
        for item in result.unresolved:  # type: ignore[attr-defined]
            entries.append(
                UnresolvedContribution(
                    payload=item.payload,
                    context=getattr(item, "classification", None),
                    source_reference=getattr(item, "source_reference", None),
                    reason=item.reason,
                )
            )
    return tuple(
        sorted(
            entries,
            key=lambda item: (
                item.reason,
                item.source_reference or "",
                _canonical_value(item.payload),
            ),
        )
    )


def _find(parents: list[int], index: int) -> int:
    while parents[index] != index:
        parents[index] = parents[parents[index]]
        index = parents[index]
    return index


def _component_key(indexes: list[int], nodes: tuple[_Node, ...]) -> tuple[tuple[str, str], ...]:
    return tuple(sorted((nodes[index].domain, nodes[index].key) for index in indexes))


def _canonical_fragment(fragment: GroupedFragment) -> str:
    return json.dumps(
        (fragment.payload, fragment.source_reference),
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
    )


def _canonical_value(value: object) -> str:
    return json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":"))
