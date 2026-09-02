# ADR 0001: Represent enterprise org hierarchy and concurrent membership as Context Assertions, not a new schema family

- Status: Accepted
- Date: 2026-09-02

## Context

ContextualWisdomLab products need a general way to represent an enterprise customer's
organizational hierarchy — 지주(holding) → 계열사(affiliate) → 사업부문(division) →
사업부(unit) → 파트(part) → 팀(team) — where **team/part ordering can invert per
company**, and a person can hold **concurrent membership in more than one unit**
(TFT / dual-hat assignments), not just one primary reporting line. This needs to
work for ABAC/RBAC permission scoping (Keyverse backlog items 20/22: "Keyverse
becomes a service ABAC/RBAC engine") and for any product that needs to answer
"which org unit does this user/resource belong to."

### Where this does *not* already live

`docs/product-goal-directive.md` §9 (`ContextualWisdomLab/.github`) enumerates the
ecosystem's reference repositories by name; it does not mention
`enterprise-architecture-core` or `context-graph-contracts`. Both repositories exist
(created 2026-08-16) and are active, but as of this ADR neither has open work on
org-hierarchy, org-unit, tenant, or ABAC/RBAC topics — confirmed by re-reading every
open PR and issue title in both repos on 2026-09-02:

- `enterprise-architecture-core` (26 open issues/PRs): target-state transformation
  workflow, EA fitness-function baseline, CSAP/SOC2 evidence boundary, data-management
  assessment. None touch org hierarchy.
- `context-graph-contracts` (14 open issues/PRs): CloudEvent envelope binding,
  conformance-evidence/release-package admission, a bounded-context fitness baseline,
  and one already-merged-shaped foundation PR (#4, non-draft) defining the
  `ContextAssertion` / `ContextMembership` / CloudEvent contract family. None touch
  org hierarchy either.

So this is a genuine gap, not a duplicated effort — but the *building blocks* for it
already exist in three places, none of which is a green field:

1. **Orgmetra** (`packages/hris-kernel`) already owns a correctly-shaped org tree:
   `OrganizationUnitVersion` is tenant-scoped, bitemporal, and has one nullable
   `parent_organization_unit_id` — a generic, variable-depth, cycle-checked tree
   (`organization.py` rejects visible parent cycles) with **no hardcoded level names
   or fixed depth**. `docs/DATA_MODEL.md:12` documents that the persisted
   `organization_unit_version` table also carries a `type` column per node (the
   kernel's validation dataclass omits it — it only carries what cycle-detection
   needs). Concurrent multi-membership is modeled at two layers: `EmploymentVersion
   .employment_concurrency_code` is `exclusive` or `concurrent`
   (`employment.py:37,45-47`), and `validate_assignment_portfolio`
   (`assignment.py`) explicitly allows multiple concurrent `AssignmentFact` rows per
   person through one employment, each carrying a `Decimal` `allocation_ratio`,
   rejecting only when the visible total exceeds `1.0000` FTE.
   `docs/DATA_MODEL.md:55` states outright: *"Assignments remain a legitimately
   multiple-membership fact."* Org-unit linkage is two hops
   (`assignment_record → position_record → organization_unit`, per
   `DATA_MODEL.md:11,15`), not a direct person→unit edge.
   **Gap in Orgmetra**: no explicit primary-vs-secondary/TFT tag on an assignment —
   only a continuous `allocation_ratio`. Inferring "primary = highest ratio" would be
   exactly the kind of heuristic this ecosystem's engineering conventions forbid
   (`docs/product-goal-directive.md` §6: no heuristics/rules of thumb without a basis).
   This is flagged as a follow-up (see below), not solved here.

2. **Keyverse** (open draft PR #103, `feat(authorization): hierarchical PDP, start-login
   helper, and PATs`, base `main`, `mergeable_state: dirty`) already builds an
   issuer/PDP: `services/account_unification/app/org_authorization.py` +
   `docs/adr/0010-hierarchical-authorization-plane.md`. It explicitly reaffirms
   Orgmetra as org-tree source of truth and never persists it (module docstring:
   *"Employment and org-tree truth stay in Orgmetra; this module consumes a
   caller-supplied assignment snapshot and never treats the snapshot as a source of
   record."*). But its org-path model is a **closed, hardcoded 5-level taxonomy**:

   ```python
   ORG_PATH_LEVELS: tuple[str, ...] = (
       "group_company", "legal_entity", "business_unit", "team", "person",
   )
   ```

   `parse_org_path` enforces this exact order for *every* tenant — a level whose name
   doesn't match `expected_levels[expected_index]` at its position raises
   `"org_path levels must be contiguous from group_company"`. There is no 파트
   concept and no per-tenant level reordering. `AssignmentSnapshot.org_path` is a
   single `str` — one path per snapshot; nothing rejects a caller building N snapshots
   for one person's N concurrent assignments, but the PDP itself has no primitive for
   "this subject holds these N org paths concurrently, decide over all of them."
   Grepping the module and ADR-0010 for multi-membership/concurrent/TFT/겸직 returns
   zero hits.

3. **Keyverse's own README** (`README.md:8-11`) is explicit that Keyverse is not the
   place to fix (1) or (2)'s tree-shape problem: *"It is not the employment or
   org-tree system of record. Orgmetra owns employment and organizational-tree truth.
   Keyverse does not copy Orgmetra tables."* Keycloak natively supports multi-group
   membership per user — verified against real code, not just Keycloak docs:
   `services/account_unification/app/models.py:45-54` defines `GroupMembership`
   mapping 1:1 to Keycloak's `GroupRepresentation`, and
   `services/account_unification/app/service.py:277-285` calls
   `list_group_memberships` for both the merge survivor and the duplicate and moves
   each set independently — real production code already depends on one Keycloak user
   holding multiple concurrent groups. But `deploy/keycloak/realm-cwl.json` (397
   lines) has **zero** `"groups"` occurrences — Keycloak Groups are not configured in
   this realm at all today. The only org-shaped claims that exist
   (`naruon-web` client's `org`/`workspace`/`role`) are `oidc-hardcoded-claim-mapper`
   entries returning the *same static string* (`"org-cwl"`, `"workspace-org-cwl"`,
   `"member"`) for every user — not a real per-membership resolution.

### Why Keycloak Groups are the wrong host for this specific requirement

Keycloak Groups are a single-parent tree per realm, and per-user multi-group
membership is real and already load-bearing in Keyverse's own merge service. That
would seem to make Groups a plausible host: the *tree* Keycloak groups model is
single-parent (matches the requirement — the org hierarchy itself is a single-parent
tree, it is the *membership* that must be multi-valued, and Keycloak already allows
that). The reason not to use Groups as the host anyway is that Keyverse's own README
already assigns organizational-tree *authorship* to Orgmetra, not Keycloak — building
the tree as native realm Groups would mean Keyverse (or a sync job) becomes a second
place that writes and owns the tree, directly contradicting "Keyverse does not copy
Orgmetra tables." Groups would also couple every relying party's org-scoping decision
to a live Keycloak Admin API call or an out-of-band group-sync job, instead of a
versioned, product-agnostic wire fact naruon (or any future consumer) can validate
without depending on Keyverse's runtime at all. Keycloak Groups therefore stay exactly
where they already are — a real, useful multi-membership *primitive* Keyverse's own
merge service depends on for identity plumbing — but they are not adopted as the
system of record for the org-hierarchy or membership *data model* itself.

## Decision — ownership split

**(c) Hybrid**, not (a) pure Keyverse and not (b) `enterprise-architecture-core`:

| Concern | Owner | Why |
|---|---|---|
| Org-unit tree source of truth (nodes, parent edges, per-node type/name, bitemporal history) | **Orgmetra** (unchanged) | Already the right shape (generic, variable-depth, cycle-checked, typed). Keyverse's own README already assigns this authority to Orgmetra. Building a second tree anywhere else duplicates a component that is already correct. |
| Person↔org-unit membership *fact*, including concurrent primary/secondary and an effective-date range | **Orgmetra**, exposed as a **cross-product wire contract owned by `context-graph-contracts`** | The membership *fact* (who, which unit, primary or TFT, when) is HR truth and stays in Orgmetra's assignment model. But every relying party (Keyverse's PDP, naruon, any future consumer) needs a stable, versioned way to *read* that fact without opening Orgmetra's database or depending on its runtime — that is precisely what `context-graph-contracts` ADR-0001 (`contract-only-boundary`) already exists to provide, and precisely what its `ContextAssertion` / `ContextMembership` schemas (ADR-0006, `context-assertion-membership`) already model. |
| ABAC/RBAC decision evaluation (the PDP) | **Keyverse**, extending PR #103 | Already Keyverse's stated domain (identity ledger, backlog items 20/22, existing draft PDP). The PDP consumes the contract above as caller-supplied evidence — exactly the pattern PR #103 already uses for `AssignmentSnapshot` — it does not own or persist the tree. |

`enterprise-architecture-core` was considered and rejected for this specific piece:
its existing and in-flight work (target-state transformation workflow, EA
fitness-function baseline, CSAP/SOC2 evidence, "Context Fabric" *projections*) is
architecture-*governance* tooling — process and decision-rights over the
architecture itself — not a data-interchange schema. `context-graph-contracts`'s
stated purpose ("shared, versioned interoperability contracts") and its existing
artifact shapes (a subject/predicate/object assertion with bitemporal interval and
provenance) are a precise structural match for "who is a member of which org unit,
primary or secondary, for how long" — an interchange *fact*, not a governance
*process*. Per this org's own convention (`product-goal-directive.md` §1: choose a
repository by product responsibility / reuse boundary, not by name, and don't create
a new repo when an existing boundary fits), `context-graph-contracts` already exists
and its boundary already fits; no new repository is proposed.

Pure-Keyverse (option a) was rejected for one concrete, load-bearing reason:
Keyverse's own README explicitly disclaims org-tree ownership and states Keyverse
does not copy Orgmetra tables. Designing the *hierarchy and membership data model*
inside Keyverse would either contradict that boundary or duplicate Orgmetra's
already-correct tree. Keyverse remains the right and sufficient owner for the *PDP
evaluation logic* — that part of the requirement genuinely is Keyverse's domain, and
is not being moved.

## Decision — wire contract shape (this repository)

No new schema family is introduced. The existing `ContextAssertion` /
`ContextMembership` pair (ADR-0006) already models exactly this shape once a
predicate vocabulary is registered:

- `ContextMembership.membership_level` (integer, 0-15) **is** the "ordered depth-level
  integer" the requirement asks for. A tenant where 파트 sits above 팀 and a tenant
  where 팀 sits above 파트 differ only in which *type label* a given depth maps to for
  that tenant — a display/config concern resolved by the owning product (Orgmetra's
  `organization_unit_version.type`, surfaced through whatever admin UI configures
  policy), never a structural difference the wire contract encodes. This is the
  "ordered depth-level integer plus a display type-label" design the requirement
  asked for, achieved by *not* encoding the label in the contract at all.
- `ContextMembership.context_ref` / `parent_context_ref` (canonical asset URIs)
  already carry a node and its immediate parent. Populating the `memberships` array
  with the full ancestor chain (one entry per level, from the immediate unit up to
  the tenant root) turns each assertion into a **self-contained, denormalized
  closure list** for that person's placement — see the query sketch below.
- `ContextAssertion.interval` (bitemporal: `valid_from`/`valid_to`/`recorded_at`/
  `superseded_at`) already gives **every assertion its own effective-date range** —
  exactly the "optional effective-date range, since TFT is often time-bounded"
  requirement, for free, per membership.
- **Concurrency and primary/secondary are modeled as separate assertions, not a
  multi-valued field.** One `ContextAssertion` per concurrent membership:

  ```json
  {
    "assertion_id": "0195...",
    "subject": "urn:cwl:tenant_001:orgmetra:person:0195...",
    "predicate": "org_member_primary",
    "object": "urn:cwl:tenant_001:orgmetra:organization_unit:0195...team-a",
    "truth_status": "authoritative",
    "interval": {"valid_from": "2026-01-01T00:00:00Z", "recorded_at": "2026-01-01T00:05:00Z", "valid_to": null, "superseded_at": null},
    "provenance": {"evidence_ref": "urn:cwl:tenant_001:orgmetra:assignment_record:0195...", "sha256": "...", "source_locator": "$.assignments[0]"},
    "memberships": [
      {"context_ref": "urn:cwl:tenant_001:orgmetra:organization_unit:...team-a",   "membership_level": 5, "parent_context_ref": "urn:cwl:tenant_001:orgmetra:organization_unit:...part-a"},
      {"context_ref": "urn:cwl:tenant_001:orgmetra:organization_unit:...part-a",   "membership_level": 4, "parent_context_ref": "urn:cwl:tenant_001:orgmetra:organization_unit:...unit-a"},
      {"context_ref": "urn:cwl:tenant_001:orgmetra:organization_unit:...unit-a",   "membership_level": 3, "parent_context_ref": "urn:cwl:tenant_001:orgmetra:organization_unit:...division-a"},
      {"context_ref": "urn:cwl:tenant_001:orgmetra:organization_unit:...division-a","membership_level": 2, "parent_context_ref": "urn:cwl:tenant_001:orgmetra:organization_unit:...affiliate-a"},
      {"context_ref": "urn:cwl:tenant_001:orgmetra:organization_unit:...affiliate-a","membership_level": 1, "parent_context_ref": "urn:cwl:tenant_001:orgmetra:organization_unit:...holding-a"},
      {"context_ref": "urn:cwl:tenant_001:orgmetra:organization_unit:...holding-a", "membership_level": 0, "parent_context_ref": null}
    ]
  }
  ```

  A second, concurrent TFT assignment for the same person is a **second**
  `ContextAssertion` with `predicate: "org_member_secondary"`, `object` pointing at
  the TFT unit, and its own bounded `interval`. Nothing about `ContextAssertion`
  needs to change for a person to hold both at once — that is exactly what "multiple
  assertions about the same subject" already means in this contract family; no
  `additionalProperties` schema edit is required in this ADR.
- **Registered predicate vocabulary** (new — this ADR is the registration record, the
  same way ADR-0006 registered `derived_from` / `realized_by` as examples without a
  closed enum in the schema, since `predicate` is validated only by pattern, not by a
  fixed list):
  - `org_member_primary` — the subject's primary reporting-line membership in `object`.
  - `org_member_secondary` — a concurrent, non-primary membership (TFT / dual-hat) in
    `object`. Multiple `org_member_secondary` assertions may coexist for one subject.

No `.schema.json` file changes in this ADR. `context-assertion.schema.json` and
`context-membership.schema.json` already accept this shape unmodified — confirmed by
hand-tracing both schemas and the existing `fixtures/valid-assertion.json`, which
already contains a worked `urn:cwl:tenant_001:orgmetra:employment_group:...` membership
example.

## Verification — multi-root and direction-agnostic typing (owner follow-up, 2026-09-02)

The owner's follow-up refinement to the requirement above: there can be **two holding
companies** (no common parent); a **Regional HQ** level sits between holding company and
affiliate/subsidiary; **Regional HQ and affiliate/subsidiary can swap positions**; and a
**business division can sometimes own a Regional HQ** — i.e. the parent-child *direction*
between a `regional_hq`-typed node and a `business_division`-typed node can invert between
tenants. This was checked directly against the schemas and Orgmetra's actual validation
code (`ContextualWisdomLab/Orgmetra`, `packages/hris-kernel`), not re-derived from the
design above. Both properties already hold, with no schema or code change required:

**(1) Multiple independent roots per tenant.** Nothing in the stack requires exactly one
root:

- `ContextMembership.parent_context_ref` (`context-membership.schema.json`) is
  `oneOf [canonical-asset-uri, null]` — a node with no parent is just `null`; nothing caps
  how many memberships in a tenant may have a null `parent_context_ref`.
- Orgmetra's `OrganizationUnitVersion.parent_organization_unit_id` (`facts.py:47`) is
  `UUID | None` with the same shape, and `validate_organization_hierarchy`
  (`organization.py:38-69`) only walks each unit's parent chain looking for a **cycle**
  (`current in seen`, `organization.py:61-67`); a chain that ends at `None` simply
  terminates the walk (`organization.py:59-60`) — there is no assertion anywhere in the
  function that exactly one, or even any particular, unit resolves to `None`. Two units
  both having `parent_organization_unit_id = None` in the same tenant pass through
  unchanged.
- The persisted table (`database/migrations/0001_foundation_schema.sql:106-134`) has no
  constraint of the shape "at most one `parent_organization_unit_id IS NULL` per
  `tenant_record_id`" — `parent_organization_unit_id` is a bare nullable `uuid` with only a
  not-self check (line 123-124) and tenant-scoped FK (line 120-122), never a root-count rule.
- Verified by executing the real kernel, not just reading it: `HOLDING_A` and `HOLDING_B`
  both given `parent_id=None` in tenant `TENANT_ALPHA`,
  `validate_organization_hierarchy(...)` raises nothing — see
  `Orgmetra` scratch check `multiroot_check.py` (run: `python3 multiroot_check.py`,
  case 1, PASS).

**(2) Direction-agnostic typing — no ordering constraint between type labels.** The
wire contract and Orgmetra's kernel both structurally cannot enforce a type-ordering rule,
because neither carries a type at the validated layer:

- `ContextMembership` (`context-membership.schema.json`) has exactly three properties —
  `context_ref`, `membership_level`, `parent_context_ref` — no `type`/`kind` field at all.
  `membership_level` is a bare `integer` (0-15) with no enum or mapping tying a level number
  to a type name.
- `canonical-asset-uri.schema.json`'s pattern treats the asset-type segment of the URI
  (e.g. `regional_hq`, `business_division`, `holding_company`) as an unconstrained
  `[a-z][a-z0-9]+(?:_[a-z0-9]+)*` slug — structurally identical to every other segment;
  the schema cannot distinguish "regional_hq" from "business_division" to order them even
  if it wanted to.
- Orgmetra's own `OrganizationUnitVersion` dataclass (`facts.py:41-49`) — the thing
  `validate_organization_hierarchy` actually receives and checks — has no `type` field
  either; the kernel's validation cannot see `organization_type_code` at all, so it cannot
  condition cycle-detection or any other rule on it. `organization_type_code` exists only
  one layer up, in the persisted table (`0001_foundation_schema.sql:111`), as a bare
  `text NOT NULL` with no `CHECK`/enum/FK tying its value to `parent_organization_unit_id`
  or to any other row's type.
- Verified by executing the real kernel with the owner's exact swap scenario: tenant A has
  `regional_hq` parenting `business_division` (holding → regional_hq → division); tenant B
  has the same two type-labeled units with the parent edge reversed (division as the root,
  regional_hq as its child). Both validate cleanly in the same process, using the same
  `validate_organization_hierarchy` function — see `multiroot_check.py`, case 2, PASS. The
  ecosystem's existing test suite (`tests/test_organization_hierarchy.py`) only exercises
  cycle rejection and tenant/knowledge-time isolation; it has no test asserting a fixed
  type order because the kernel has no mechanism that could enforce one.

**Concrete mapping onto the owner's scenario**, entirely inside the existing contract —
`membership_level` is per-tenant depth, not a fixed level-name table, exactly as the
original ADR text above already argued for 파트/팀 reordering; the same mechanism covers
Regional HQ:

```
Tenant 001 (two holding companies, Regional HQ below holding):
  holding_company "Holding A"      membership_level 0   parent: null
  holding_company "Holding B"      membership_level 0   parent: null   # second, independent root
  regional_hq      "APAC HQ"       membership_level 1   parent: Holding A
  affiliate        "KR Affiliate"  membership_level 2   parent: APAC HQ

Tenant 002 (Regional HQ and affiliate swapped; a business division owns the Regional HQ):
  holding_company  "Holding C"     membership_level 0   parent: null
  business_division "Platform Div" membership_level 1   parent: Holding C
  regional_hq       "EMEA HQ"      membership_level 2   parent: Platform Div   # division owns the HQ
  affiliate         "DE Affiliate" membership_level 3   parent: EMEA HQ
```

No `org_member_primary`/`org_member_secondary` predicate, schema field, or Orgmetra
validation rule changes between these two tenants — only the per-tenant
`organization_unit_version.organization_type_code` values and which `context_ref` a given
`parent_context_ref` points at change. This is the same "depth-integer, not a level-name
table" design already decided above, extended with the owner's own examples as evidence it
holds for Regional HQ and multi-root, not just 파트/팀.

**Not covered here — deferred, not silently dropped.** The owner's follow-up also requires
this hierarchy to be "exchangeable via SCIM, OIDC, and SAML." That is a separate,
substantial design question (SCIM resource/schema mapping, an OIDC claims shape, a SAML
attribute-statement shape, and how each represents a multi-root, dynamically-ordered tree
plus concurrent primary/secondary membership) that this verification pass does not
attempt — it needs its own ADR. Flagged so it is not mistaken for out-of-scope-because-solved.

## Decision — ABAC/RBAC evaluation sketch (Keyverse-side, follow-up work)

A policy scoped to org unit `X` must answer "any subject with a membership (primary
or secondary) in `X` or any descendant of `X`." Because every assertion already
carries the *ancestor* closure in `memberships[].context_ref`, the query never walks
the tree at decision time:

```python
def has_membership_in_or_under(subject_assertions: list[ContextAssertion], unit_ref: str, *, at: datetime) -> bool:
    """O(assertions * memberships-per-assertion); no tree traversal at decision time."""
    for a in subject_assertions:
        if a.predicate not in ("org_member_primary", "org_member_secondary"):
            continue
        if not a.interval.covers(at):          # bitemporal validity check, not a heuristic
            continue
        if a.object == unit_ref:                # direct membership
            return True
        if any(m.context_ref == unit_ref for m in a.memberships):  # unit_ref is an ancestor
            return True
    return False
```

The *storage* side of this (materializing the ancestor closure per assignment when
Orgmetra emits an assertion) is a standard closure-table / materialized-path
technique over Orgmetra's already-cycle-checked `organization_unit_version` tree —
walk `parent_organization_unit_id` from the assigned unit to the tenant root once,
cache it, and re-walk only when a `organization_unit_version` in that chain gets a
new bitemporal version. This sketch is not implemented in this PR — see Deferred,
below.

## Reconciliation with Keyverse PR #103

**Compatible, unchanged:** the issuer/PDP-vs-PEP split (ADR-0008), the
most-specific-wins grant precedence, the ABAC attribute-constraint concept
(`purpose`/`sensitivity`/`clearance`/`residency`), and the general shape of
"Keyverse consumes a caller-supplied snapshot, never treats it as a source of
record" all remain correct and are the pattern this ADR's contract slots into.

**Specifically incompatible, and why:**

1. `ORG_PATH_LEVELS` is one global, hardcoded, position-checked 5-level name tuple.
   `parse_org_path` rejects any `org_path` whose level name at index *N* is not
   exactly `expected_levels[N]`. This cannot represent a tenant where 파트 sits above
   팀 and a different tenant where 팀 sits above 파트 — the *name* is pinned to a
   *position*. It must become depth-only structural validation (bounded depth, valid
   slugs) with level *names* resolved per tenant out of band (Orgmetra's
   `organization_unit_version.type`), not enforced as a fixed global sequence.
2. `AssignmentSnapshot.org_path: str` is exactly one path per snapshot. There is no
   PDP primitive for "this subject holds N org paths concurrently, decide over all of
   them" — a caller could construct N snapshots and combine results externally, but
   that pushes the concurrency semantics (primary vs. secondary, which one wins a
   conflicting grant) out of the PDP and into every caller, inconsistently. This is a
   structural gap, not an additive one: `AssignmentSnapshot` needs a
   `memberships: list[OrgMembership]` (each carrying `org_path`, an `is_primary` or
   `membership_kind` tag, and its own effective window) in place of the single
   `org_path` field.
3. `ORG_PATH_LEVELS` includes `"person"` as the fifth, leaf level — the path itself
   terminates in the person. That conflates the org-unit tree with identity: this
   contract (and Orgmetra's model) treats a person and an org unit as different
   entity types connected by a *membership edge* (`subject`/`object` in
   `ContextAssertion`), not nodes in the same tree. `AssignmentSnapshot
   .keyverse_subject` already carries the person identity separately, which makes the
   trailing `/person/<id>` segment redundant with it. Reconciling this means dropping
   `"person"` from `ORG_PATH_LEVELS` entirely, not extending it.

None of this is implemented against PR #103 in this ADR — PR #103 is itself draft and
`mergeable_state: dirty` (conflicting with current `main`), and is not the artifact
this ADR modifies. The above is the reconciliation record so whoever next touches
`org_authorization.py` does not have to rediscover it.

## Risks

- **Numbering collision.** `context-graph-contracts`'s `develop` branch currently
  contains only a placeholder `README.md`; several open, unmerged draft PRs (e.g.
  #4, #14, #20, #21) each independently define `docs/adr/0001` through `0015` for
  unrelated topics (CloudEvent envelopes, conformance evidence, DDD fitness
  baseline). This ADR is filed as `0001` against the current, bare `develop` and will
  need renumbering by whichever PR merges second — a normal, expected consequence of
  concurrent agent work in this ecosystem, not a defect in this decision.
- **Predicate vocabulary is not schema-enforced.** `predicate` is validated only by a
  generic lowercase-snake pattern, not a closed enum, so nothing currently stops a
  producer from emitting `org_member_primary` with a typo or an unregistered synonym.
  Acceptable at this repository's stated maturity (ADR-0001's own compatibility
  policy treats new predicates as additive), but conformance tests for the two
  registered predicates are real follow-up work, not implemented here.
- **Orgmetra's `assignment_record` has no explicit primary/secondary field yet.**
  Without one, whatever service first emits `org_member_primary` vs.
  `org_member_secondary` assertions would have to guess — and guessing (e.g.
  "highest `allocation_ratio` wins") is exactly the heuristic this ecosystem's own
  engineering conventions forbid. This is Orgmetra's gap to close, not something this
  ADR can resolve by itself.
- **`context-membership.schema.json`'s 16-item cap on `memberships`.** A tenant whose
  hierarchy is deeper than 16 levels (unlikely for 지주→...→팀, which is 6) cannot use
  the full-ancestor-closure encoding above without truncation. Not a practical
  concern for the stated requirement; flagged so a future, much deeper hierarchy
  does not silently truncate.

## Deferred to later cycles (explicitly out of scope for this ADR)

1. Adding an explicit `assignment_category_code` (or equivalent, non-heuristic)
   primary/secondary field to Orgmetra's `assignment_record` — Orgmetra's own ADR
   process, not this repository's.
2. Implementing the closure/materialized-path emitter described in the evaluation
   sketch above (an Orgmetra-side or Keyverse-side service that turns
   `organization_unit_version` chains into the `memberships[]` array shown here).
3. Extending Keyverse PR #103's `org_authorization.py` per the Reconciliation section
   — depth-only `parse_org_path`, `AssignmentSnapshot.memberships: list[...]`,
   dropping the `"person"` leaf level. PR #103 is itself unmerged and conflicting;
   this ADR does not touch it.
4. Wiring naruon's `Organization`/`OrganizationGroup` tenant model (currently a fixed
   two-level tree with no self-referential nesting) to this contract.
5. Conformance fixtures and tests in this repository for the two registered
   predicates (`org_member_primary`, `org_member_secondary`), following the existing
   `tests/test_schemas.py` / `tests/test_packaged_fixtures.py` pattern once this ADR
   has had a chance to be reviewed on its own.
6. Designing how this hierarchy and membership model is exchanged over SCIM, OIDC, and
   SAML (owner follow-up, 2026-09-02) — a resource/claims/attribute-statement mapping
   for a multi-root, dynamically-ordered tree plus concurrent primary/secondary
   membership. Needs its own ADR; not attempted by the verification section above.

None of the above is implemented in this pull request. This ADR is the design record;
each deferred item is a separately reviewable follow-up PR in its owning repository.

## References

National Institute of Standards and Technology. (2014). *Guide to attribute based
access control (ABAC) definition and considerations* (NIST Special Publication
800-162). U.S. Department of Commerce. https://doi.org/10.6028/NIST.SP.800-162
