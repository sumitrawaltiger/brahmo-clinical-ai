"""Chunk STW one-pagers and the local protocol into clinically meaningful decision units.

A decision unit = one bullet line under a section heading (a recommendation, a red flag, a contraindication,
a monitoring instruction). Never a token slice. Every unit carries: source document, code, version, effective
date, supersession, specialty, condition, population, section, unit type, page anchor, file sha256.
"""
from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..config import Config, load_config
from ..normalize.text import norm_key, sha256_file, sha256_text

CHUNKER_VERSION = "chunker-1.0.0"

_CODE_RE = re.compile(r"^Code:\s*(\S+)")
_VER_RE = re.compile(r"^Version:\s*(\S+)\s*·\s*Effective:\s*(\d{4}-\d{2}-\d{2})")
_SUP_RE = re.compile(r"^Supersedes:\s*(\S+)\s+v(\S+)")
_ARCHIVE_RE = re.compile(r"ARCHIVE COPY\s*—\s*superseded by v(\S+?)\.?$")
_HEADING_RE = re.compile(r"^[A-Z][A-Z0-9 /&\-—()]+$")
_FOOTER_PREFIX = "SYNTHETIC ASSESSMENT DOCUMENT"
_CTRL_RE = re.compile(r"[\x00-\x1f\x7f•·●]+")


def _clean(s: str) -> str:
    return _CTRL_RE.sub(" ", s).strip()


@dataclass
class Chunk:
    chunk_id: str
    doc_id: str
    source_type: str              # national_stw | local_protocol
    publisher: str
    organization: Optional[str]
    title: str
    code: str
    version: str
    effective_date: str
    supersedes: Optional[str]
    superseded_by: Optional[str]
    is_current: bool
    specialty: str
    condition: str
    population: str
    section: str
    unit_type: str
    unit_index: int
    page: int
    anchor: str
    text: str
    file_name: str
    file_sha256: str
    extra: Dict[str, Any] = field(default_factory=dict)

    def citation(self) -> Dict[str, Any]:
        return {
            "chunk_id": self.chunk_id,
            "source_type": self.source_type,
            "document": self.code,
            "title": self.title,
            "version": self.version,
            "effective_date": self.effective_date,
            "section": self.section,
            "page": self.page,
            "anchor": self.anchor,
            "file": self.file_name,
            "file_sha256": self.file_sha256[:12],
            "organization": self.organization,
            "is_current": self.is_current,
            "superseded_by": self.superseded_by,
        }

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def _unit_type(section: str, mapping: Dict[str, List[str]]) -> str:
    s = section.upper()
    for utype, prefixes in mapping.items():
        for p in prefixes:
            if s.startswith(p) or p in s:
                return utype
    return "other"


def _extract_pdf_text(path: Path) -> List[str]:
    from pypdf import PdfReader

    reader = PdfReader(str(path))
    lines: List[str] = []
    for page in reader.pages:
        lines.extend((page.extract_text() or "").splitlines())
    return lines


def chunk_stw_pdf(path: Path, meta: Dict[str, Any]) -> List[Chunk]:
    lines = _extract_pdf_text(path)
    sha = sha256_file(path)
    title = code = version = effective = ""
    supersedes = superseded_by = None
    chunks: List[Chunk] = []
    section: Optional[str] = None
    unit_idx = 0
    pending_text: List[str] = []
    doc_meta_default = {"condition": "unknown", "specialty": "unknown", "population": "unknown"}

    def flush() -> None:
        nonlocal unit_idx, pending_text
        if not pending_text or section is None:
            pending_text = []
            return
        # pypdf renders the bullet glyph as DEL (0x7f) or a stray symbol; strip control chars and bullet marks
        text = " ".join(_clean(t) for t in pending_text).strip()
        pending_text = []
        if not text:
            return
        unit_idx += 1
        dm = meta["documents"].get(code, doc_meta_default)
        sec_slug = norm_key(section).replace(" ", "_")
        chunks.append(Chunk(
            chunk_id=f"{code}:{version}:{sec_slug}:{unit_idx}", doc_id=f"{code}:{version}", source_type="national_stw",
            publisher=meta.get("publisher_label", "STW"), organization=None, title=title, code=code, version=version,
            effective_date=effective, supersedes=supersedes, superseded_by=superseded_by, is_current=True,
            specialty=dm["specialty"], condition=dm["condition"], population=dm["population"], section=section,
            unit_type=_unit_type(section, meta["section_unit_types"]), unit_index=unit_idx, page=1,
            anchor=f"p1/{sec_slug}/{unit_idx}", text=text, file_name=path.name, file_sha256=sha,
        ))

    header_done = False
    for raw in lines:
        line = raw.rstrip()
        if not line.strip():
            continue
        s = line.strip()
        if s == "STANDARD TREATMENT WORKFLOW":
            continue
        if not title and not header_done:
            title = s
            continue
        m = _CODE_RE.match(s)
        if m:
            code = m.group(1)
            continue
        m = _VER_RE.match(s)
        if m:
            version, effective = m.group(1), m.group(2)
            continue
        m = _SUP_RE.match(s)
        if m:
            supersedes = f"{m.group(1)} v{m.group(2)}"
            continue
        if s.startswith(_FOOTER_PREFIX):
            flush()
            am = _ARCHIVE_RE.search(s)
            if am:
                superseded_by = f"{code} v{am.group(1)}"
            section = None
            continue
        header_done = True
        # heading = whole line uppercase, no leading indent
        if not raw.startswith(" ") and _HEADING_RE.match(s) and len(s) < 60:
            flush()
            section = s
            continue
        # bullet line: the PDF renders bullets as indented lines; a line starting with two spaces starts a new unit,
        # a line starting with one space is also a new unit (pypdf drops the glyph). Treat every indented line as a unit.
        if section is not None:
            flush()
            pending_text = [s]
    flush()
    for c in chunks:
        c.superseded_by = superseded_by
        c.is_current = superseded_by is None
    return chunks


_MD_FIELD_RE = re.compile(r"\*\*(.+?):\*\*\s*([^·]+)")
_MD_STEP_RE = re.compile(r"^(\d+)\.\s+(.*)$")


def chunk_local_protocol_md(path: Path, meta: Dict[str, Any]) -> List[Chunk]:
    text = path.read_text(encoding="utf-8")
    sha = sha256_file(path)
    lines = [l.rstrip() for l in text.splitlines()]
    title = lines[0].lstrip("# ").strip() if lines else path.stem
    fields: Dict[str, str] = {}
    scope = ""
    steps: List[str] = []
    for l in lines[1:]:
        if l.startswith("**Document:**") or "**Version:**" in l:
            for k, v in _MD_FIELD_RE.findall(l):
                fields[k.strip().lower()] = v.strip().strip("*").strip()
        elif l.startswith("**Scope:**"):
            scope = l.replace("**Scope:**", "").strip()
        else:
            m = _MD_STEP_RE.match(l.strip())
            if m:
                steps.append(m.group(2).replace("**", "").strip())
    code = fields.get("document", path.stem)
    version = fields.get("version", "unknown")
    effective = fields.get("approved", "unknown")
    lp = meta.get("local_protocols", {}).get(code, {"condition": "unknown", "specialty": "unknown", "population": "unknown", "organization": "unknown"})
    chunks: List[Chunk] = []
    for i, step in enumerate(steps, start=1):
        chunks.append(Chunk(
            chunk_id=f"{code}:{version}:step:{i}", doc_id=f"{code}:{version}", source_type="local_protocol", publisher="clinic internal SOP",
            organization=lp.get("organization"), title=title, code=code, version=version, effective_date=effective, supersedes=None,
            superseded_by=None, is_current=True, specialty=lp["specialty"], condition=lp["condition"], population=lp["population"],
            section=f"Protocol step {i}", unit_type="recommendation", unit_index=i, page=1, anchor=f"p1/step/{i}", text=step,
            file_name=path.name, file_sha256=sha,
            extra={"approver": fields.get("approver"), "review_due": fields.get("review due"), "scope": scope},
        ))
    return chunks


def chunk_corpus(cfg: Optional[Config] = None) -> List[Chunk]:
    cfg = cfg or load_config()
    meta = cfg.load_json("corpus.metadata_path")
    corpus_dir = cfg.path("corpus.dir")
    chunks: List[Chunk] = []
    for pdf in sorted(corpus_dir.glob(cfg["corpus.stw_glob"])):
        chunks.extend(chunk_stw_pdf(pdf, meta))
    for lp in cfg["corpus.local_protocols"]:
        p = cfg.resolve_path(lp)
        if p.exists():
            chunks.extend(chunk_local_protocol_md(p, meta))
    # supersession across files: if any doc declares "Supersedes: CODE vX", mark that edition superseded
    declared = {c.supersedes for c in chunks if c.supersedes}
    for c in chunks:
        if f"{c.code} v{c.version}" in declared and c.is_current:
            newer = next((x for x in chunks if x.supersedes == f"{c.code} v{c.version}"), None)
            c.is_current = False
            c.superseded_by = f"{newer.code} v{newer.version}" if newer else c.superseded_by
    return chunks


def corpus_fingerprint(chunks: List[Chunk]) -> str:
    return sha256_text(CHUNKER_VERSION + "\n" + "\n".join(f"{c.chunk_id}\t{c.text}" for c in chunks))[:16]
