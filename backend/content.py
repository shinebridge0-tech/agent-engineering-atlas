from pathlib import Path
from typing import Literal
import re
import yaml
from pydantic import BaseModel, ConfigDict, Field, model_validator

ROOT = Path(__file__).resolve().parents[1]
CONTENT = ROOT / "content" / "cases"

class Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")

class Requirement(Strict):
    key: Literal["framework", "framework_version", "data_external", "approval", "idempotency"]
    value: str
    critical: bool = True

class Claim(Strict):
    claim_id: str
    text: str
    kind: Literal["source_fact", "inference", "recommendation"]
    evidence_ids: list[str]

class Source(Strict):
    source_id: str
    source_type: Literal["code", "official_doc", "local_experiment"]
    url: str | None
    repo: str | None
    revision: str | None
    path: str | None
    symbol: str | None
    lines: str | None
    observed_at: str
    title: str
    license_status: str
    content_hash: str | None
    mutable: bool

    @model_validator(mode="after")
    def check_source(self):
        if self.source_type != "local_experiment" and (not self.url or not self.url.startswith("https://")):
            raise ValueError("external evidence requires HTTPS URL")
        if self.source_type == "code" and (not self.repo or not self.path or not self.symbol or not self.revision or not re.fullmatch(r"[0-9a-f]{40}", self.revision)):
            raise ValueError("code evidence requires confirmed commit, path and symbol")
        if self.source_type == "official_doc" and not self.mutable:
            raise ValueError("unversioned official docs must be marked mutable")
        return self

class Review(Strict):
    status: Literal["draft", "source_checked", "reviewed"]
    reviewer: str | None
    at: str | None
    scope: str | None

class Validation(Strict):
    status: Literal["not_run", "local_passed", "independently_reproduced"]
    environment: str | None
    command: str | None
    result: str | None

class Freshness(Strict):
    status: Literal["current", "needs_recheck", "deprecated"]
    reason: str
    updated_at: str

class Card(Strict):
    id: str = Field(pattern=r"^[a-z][a-z0-9-]{2,60}$")
    schema_version: Literal["1.0"]
    revision: int = Field(ge=1)
    locale: Literal["zh-CN", "en"]
    title: str
    problem_cluster: Literal["retrieval", "recovery", "safety"]
    tags: list[str]
    aliases: list[str]
    problem: str
    context: str
    preconditions: list[str]
    hard_requirements: list[Requirement]
    required_components: list[str]
    approach: str
    alternatives: list[str]
    tradeoffs: list[str]
    failure_modes: list[str]
    not_applicable: list[str]
    implementation_steps: list[str]
    validation_plan: list[str]
    frameworks: list[str]
    tested_versions: list[str]
    applicable_version_range: str
    claims: list[Claim]
    sources: list[Source]
    review: Review
    validation: Validation
    freshness: Freshness
    contributors: list[str]
    ai_assistance: bool
    body: str = ""

    @model_validator(mode="after")
    def references(self):
        ids = [s.source_id for s in self.sources]
        claims = [c.claim_id for c in self.claims]
        if len(ids) != len(set(ids)) or len(claims) != len(set(claims)):
            raise ValueError("duplicate evidence or claim ID")
        for claim in self.claims:
            if not claim.evidence_ids or not set(claim.evidence_ids).issubset(ids):
                raise ValueError("claim evidence reference missing")
        if self.review.status != "draft" and (not self.sources or not self.review.at or not self.review.scope):
            raise ValueError("checked content needs evidence and review scope")
        if self.review.status == "reviewed" and not self.review.reviewer:
            raise ValueError("independent review requires reviewer")
        if self.validation.status != "not_run" and not all([self.validation.environment, self.validation.command, self.validation.result]):
            raise ValueError("validation requires actual evidence")
        return self

def load_card(path: Path, root: Path = CONTENT) -> Card:
    if not path.resolve().is_relative_to(root.resolve()):
        raise ValueError("content path outside allowed root")
    if path.stat().st_size > 128_000:
        raise ValueError("content file too large")
    text = path.read_text(encoding="utf-8")
    pieces = text.split("---", 2)
    if len(pieces) != 3 or pieces[0].strip():
        raise ValueError("YAML front matter required")
    data = yaml.safe_load(pieces[1])
    if not isinstance(data, dict):
        raise ValueError("mapping required")
    data["body"] = pieces[2].strip()
    return Card.model_validate(data)

def load_all(root: Path = CONTENT) -> list[Card]:
    if root.resolve() != root.absolute():
        raise ValueError("content root symlink/junction escape rejected")
    cards = [load_card(p, root) for p in sorted(root.glob("*.md"))]
    ids = [(c.id, c.locale) for c in cards]
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate case ID and locale")
    return cards
