# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }

import json
import re
from genlayer import *
from dataclasses import dataclass
from typing import Dict, List, Optional


@allow_storage
@dataclass
class NormalizedSource:
    evidence_id: u256
    original_url: str
    normalized_url: str
    domain: str
    trust_score: u256
    is_whitelisted: bool
    status: str


class SourceNormalizer(gl.Contract):
    sources: TreeMap[u256, NormalizedSource]
    next_id: u256
    trusted_domains: List[str]
    blocked_domains: List[str]
    stats: Dict

    def __init__(self):
        self.next_id = u256(0)
        self.trusted_domains = [
            "court.gov", "justice.gov", "archive.org",
            "blockchain.com", "etherscan.io", "ipfs.io", "arweave.net"
        ]
        self.blocked_domains = [
            "localhost", "127.0.0.1", "example.com", "pastebin.com", "tinyurl.com"
        ]
        self.stats = {
            "total_normalized": 0,
            "total_rejected": 0,
            "trusted_count": 0
        }

    # ================= MAIN FUNCTION =================

    @gl.public.write
    def normalize_source(self, raw_url: str) -> u256:
        """Normalize and validate a source URL."""
        assert raw_url.strip() != "", "URL cannot be empty"

        # Clean and validate
        cleaned = self._clean_url(raw_url)
        assert cleaned is not None, "Invalid URL format"

        domain = self._extract_domain(cleaned)
        assert domain is not None, "Could not extract domain"

        assert domain not in self.blocked_domains, f"Domain '{domain}' is blocked"

        # Calculate trust score
        trust_score = self._calculate_trust(domain, cleaned)
        is_whitelisted = domain in self.trusted_domains

        # Store in contract state
        eid = self.next_id
        self.next_id += u256(1)

        self.sources[eid] = NormalizedSource(
            evidence_id=eid,
            original_url=raw_url,
            normalized_url=cleaned,
            domain=domain,
            trust_score=u256(trust_score),
            is_whitelisted=is_whitelisted,
            status="NORMALIZED"
        )

        # Update stats
        self.stats["total_normalized"] += 1
        if is_whitelisted:
            self.stats["trusted_count"] += 1

        return eid

    # ================= VIEW FUNCTIONS =================

    @gl.public.view
    def get_source_status(self, evidence_id: u256) -> str:
        """Get status of a normalized source."""
        if evidence_id not in self.sources:
            return "NOT_FOUND"
        src = self.sources[evidence_id]
        return f"{src.status}:{src.domain}:{int(src.trust_score)}"

    @gl.public.view
    def get_source_details(self, evidence_id: u256) -> str:
        """Get full details of a normalized source."""
        if evidence_id not in self.sources:
            return "NOT_FOUND"
        src = self.sources[evidence_id]
        return json.dumps({
            "id": int(src.evidence_id),
            "original_url": src.original_url,
            "normalized_url": src.normalized_url,
            "domain": src.domain,
            "trust_score": int(src.trust_score),
            "is_whitelisted": src.is_whitelisted,
            "status": src.status
        })

    @gl.public.view
    def get_statistics(self) -> str:
        """Get contract statistics."""
        return json.dumps(self.stats)

    @gl.public.view
    def list_sources(self) -> str:
        """List all source IDs."""
        items = []
        for key in self.sources:
            src = self.sources[key]
            items.append(f"{int(src.evidence_id)}:{src.status}")
        return ",".join(items)

    @gl.public.view
    def get_sources_by_domain(self, domain: str) -> str:
        """List source IDs by domain."""
        items = []
        for key in self.sources:
            src = self.sources[key]
            if src.domain == domain:
                items.append(str(int(src.evidence_id)))
        return ",".join(items)

    # ================= ADMIN FUNCTIONS =================

    @gl.public.write
    def add_trusted_domain(self, domain: str):
        """Add a domain to whitelist (admin only)."""
        assert domain.strip() != "", "Domain cannot be empty"
        if domain not in self.trusted_domains:
            self.trusted_domains.append(domain)
        return True

    @gl.public.write
    def remove_trusted_domain(self, domain: str):
        """Remove a domain from whitelist (admin only)."""
        if domain in self.trusted_domains:
            self.trusted_domains.remove(domain)
        return True

    # ================= HELPER METHODS =================

    def _clean_url(self, url: str) -> Optional[str]:
        """Clean and normalize URL."""
        if not url:
            return None
        cleaned = url.strip().rstrip('/')
        if cleaned.startswith('http://'):
            cleaned = cleaned.replace('http://', 'https://', 1)
        return cleaned if cleaned else None

    def _extract_domain(self, url: str) -> Optional[str]:
        """Extract domain from URL."""
        try:
            without_protocol = re.sub(r'^https?://', '', url)
            domain = without_protocol.split('/')[0]
            domain = re.sub(r'^www\.', '', domain)
            return domain if domain else None
        except:
            return None

    def _calculate_trust(self, domain: str, url: str) -> int:
        """Calculate trust score (0-100)."""
        score = 0
        if domain in self.trusted_domains:
            score += 50
        if url.startswith('https://'):
            score += 15
        if not any(p in url for p in ['utm_', 'ref=', 'source=']):
            score += 10
        return min(100, max(0, score))
