"""
CKC Security System
====================

Sikkerhedslag for CKC med:
- Input sanitering (forstørrelse/obduktion ved mistanke)
- Korruptionsdetektion
- Integritetskontrol
- Krypteret brugerdata

Alt input forstørres og obduceres ved mistanke FØR det når et læringsrum.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple, Set, Callable
from enum import Enum
import re
import hashlib
import base64
import json
import asyncio

from cirkelline.config import logger


class ThreatLevel(Enum):
    """Trusselsniveau for input."""
    SAFE = "safe"
    SUSPICIOUS = "suspicious"
    DANGEROUS = "dangerous"
    BLOCKED = "blocked"


class InputType(Enum):
    """Type af input."""
    TEXT = "text"
    FILE = "file"
    EMOJI = "emoji"
    URL = "url"
    CODE = "code"
    COMMAND = "command"
    MIXED = "mixed"


@dataclass
class SanitizationResult:
    """
    Resultat af input sanitering.

    Attributes:
        original: Originalt input
        sanitized: Saneret output
        threat_level: Trusselsniveau
        issues_found: Liste af fundne problemer
        blocked_elements: Elementer der blev blokeret
        magnified: Om input blev forstørret for analyse
        autopsy_performed: Om obduktion blev udført
    """
    original: Any
    sanitized: Any
    input_type: InputType
    threat_level: ThreatLevel
    issues_found: List[str] = field(default_factory=list)
    blocked_elements: List[str] = field(default_factory=list)
    magnified: bool = False
    autopsy_performed: bool = False
    analysis_notes: str = ""
    timestamp: datetime = field(default_factory=datetime.utcnow)
    integrity_hash: Optional[str] = None

    @property
    def is_safe(self) -> bool:
        """Er input sikkert at bruge?"""
        return self.threat_level in [ThreatLevel.SAFE, ThreatLevel.SUSPICIOUS]

    @property
    def requires_review(self) -> bool:
        """Kræver input menneskelig gennemgang?"""
        return self.threat_level == ThreatLevel.SUSPICIOUS

    def to_dict(self) -> Dict[str, Any]:
        """Konverter til dictionary."""
        return {
            "input_type": self.input_type.value,
            "threat_level": self.threat_level.value,
            "is_safe": self.is_safe,
            "requires_review": self.requires_review,
            "issues_found": self.issues_found,
            "blocked_elements": self.blocked_elements,
            "magnified": self.magnified,
            "autopsy_performed": self.autopsy_performed,
            "analysis_notes": self.analysis_notes,
            "timestamp": self.timestamp.isoformat(),
            "integrity_hash": self.integrity_hash
        }


class InputSanitizer:
    """
    Input Sanitizer for CKC.

    Forstørrer og obducerer input ved mistanke før det når læringsrum.

    Features:
    - Tekst sanitering (XSS, injection, etc.)
    - Fil validering
    - Emoji/ikon screening
    - URL validering
    - Kode analyse
    - Kommando detektion
    """

    # Farlige mønstre
    DANGEROUS_PATTERNS = [
        # Script injection (XSS)
        r'<script[^>]*>.*?</script>',
        r'javascript:',
        r'on\w+\s*=',
        # SQL injection
        r"('\s*(or|and)\s*'?\d*\s*=\s*\d*)",
        r'(union\s+select|drop\s+table|delete\s+from)',
        # Command injection
        r'[;&|`$]',
        r'\$\([^)]+\)',
        r'`[^`]+`',
        # Path traversal
        r'\.\./|\.\.\\',
        # Null bytes
        r'\x00',
        # XXE (XML External Entity) - F-002
        r'<!DOCTYPE[^>]*\[',
        r'<!ENTITY\s+',
        r'SYSTEM\s+["\']file://',
        r'SYSTEM\s+["\']http://',
        r'<!ELEMENT\s+',
        # Entity references (kræver XML context - kun farlige med DOCTYPE)
        r'&(xxe|file|system|data)[a-zA-Z0-9_]*;',
        # SSTI (Server-Side Template Injection) - F-002 FIXED
        # Mere præcise mønstre der IKKE matcher legitim JSON
        # Jinja2/Twig: {{ variable }} eller {{ obj.method() }}
        r'\{\{\s*[a-zA-Z_][a-zA-Z0-9_]*(\.[a-zA-Z_][a-zA-Z0-9_]*)*(\([^)]*\))?\s*\}\}',
        # Jinja2 block tags: {% if %}, {% for %}, etc.
        r'\{%\s*(if|for|block|extends|include|import|macro|set|raw|autoescape)',
        # Java EL / Freemarker: ${expression} - men IKKE ${} alene
        r'\$\{\s*[a-zA-Z_][a-zA-Z0-9_]*',
        # Thymeleaf: #{message.key} eller *{field}
        r'[#\*]\{[a-zA-Z_][a-zA-Z0-9_.]*\}',
        # Thymeleaf inline: [[${...}]] eller [(...)]
        r'\[\[\s*\$\{',
        r'\[\(\s*[a-zA-Z_]',
        # ERB/JSP: <%=, <%, <%@
        r'<%[=@]?\s*[a-zA-Z_]',
        # Razor (.NET): @{ }, @Model, @Html
        r'@\{\s*[a-zA-Z_]',
        r'@(Model|Html|Url|ViewBag)\.',
        # Pebble/Velocity: $variable eller ${variable}
        r'\$[a-zA-Z_][a-zA-Z0-9_]*\.',
        # LDAP Injection
        r'\)\s*\(\|',
        r'\)\s*\(\&',
        r'\*\)\s*\(',
        # NoSQL Injection - mere præcise for at undgå false positives
        r'["\']?\$where["\']?\s*:\s*["\']',
        r'["\']?\$gt["\']?\s*:\s*[{\d]',
        r'["\']?\$ne["\']?\s*:\s*[{\d"\']',
        r'["\']?\$regex["\']?\s*:',
        r'["\']?\$or["\']?\s*:\s*\[',
        r'["\']?\$and["\']?\s*:\s*\[',
        # Header Injection (CRLF)
        r'\r\n',
        r'%0d%0a',
        r'%0D%0A',
    ]

    SUSPICIOUS_PATTERNS = [
        # Encoded content
        r'%[0-9a-fA-F]{2}',
        r'&#\d+;',
        r'\\u[0-9a-fA-F]{4}',
        # Excessive special chars
        r'[<>{}[\]]{3,}',
        # Hidden content
        r'\s{10,}',
        r'[\u200b-\u200f\u2028-\u202f\u2060-\u206f]',
    ]

    BLOCKED_DOMAINS = [
        'malware.com',
        'phishing.net',
        'exploit.org',
    ]

    ALLOWED_FILE_TYPES = {
        'text/plain', 'application/pdf', 'application/json',
        'image/png', 'image/jpeg', 'image/gif', 'image/webp',
        'audio/mpeg', 'audio/wav', 'video/mp4',
    }

    def __init__(self):
        self._dangerous_regex = [re.compile(p, re.IGNORECASE) for p in self.DANGEROUS_PATTERNS]
        self._suspicious_regex = [re.compile(p, re.IGNORECASE) for p in self.SUSPICIOUS_PATTERNS]
        self._analysis_log: List[SanitizationResult] = []
        self._blocked_count = 0
        self._suspicious_count = 0

    async def sanitize(
        self,
        content: Any,
        input_type: Optional[InputType] = None,
        force_magnify: bool = False
    ) -> SanitizationResult:
        """
        Sanitér input før det når et læringsrum.

        Args:
            content: Input at sanitere
            input_type: Type af input (auto-detekteres hvis None)
            force_magnify: Tving forstørrelse uanset mistanke

        Returns:
            SanitizationResult med saneret output
        """
        # Auto-detekter input type
        if input_type is None:
            input_type = self._detect_type(content)

        # Initial screening
        issues = []
        blocked = []
        threat_level = ThreatLevel.SAFE
        magnified = False
        autopsy = False

        # Check for dangerous patterns
        dangerous_found = self._check_dangerous(content)
        if dangerous_found:
            threat_level = ThreatLevel.DANGEROUS
            issues.extend(dangerous_found)
            magnified = True
            autopsy = True

        # Check for suspicious patterns
        if threat_level == ThreatLevel.SAFE:
            suspicious_found = self._check_suspicious(content)
            if suspicious_found:
                threat_level = ThreatLevel.SUSPICIOUS
                issues.extend(suspicious_found)
                magnified = True

        # Force magnification if requested
        if force_magnify and not magnified:
            magnified = True

        # Perform detailed analysis if magnified
        analysis_notes = ""
        if magnified:
            analysis_notes = await self._magnify_and_analyze(content, input_type)

        # Perform autopsy if needed
        if autopsy or (magnified and threat_level == ThreatLevel.DANGEROUS):
            autopsy_result = await self._perform_autopsy(content, input_type)
            analysis_notes += f"\n\nAUTOPSY RESULT:\n{autopsy_result}"
            autopsy = True

        # Sanitize content
        sanitized = self._sanitize_content(content, input_type, blocked)

        # Block if dangerous
        if threat_level == ThreatLevel.DANGEROUS:
            threat_level = ThreatLevel.BLOCKED
            self._blocked_count += 1
        elif threat_level == ThreatLevel.SUSPICIOUS:
            self._suspicious_count += 1

        # Create result
        result = SanitizationResult(
            original=content,
            sanitized=sanitized,
            input_type=input_type,
            threat_level=threat_level,
            issues_found=issues,
            blocked_elements=blocked,
            magnified=magnified,
            autopsy_performed=autopsy,
            analysis_notes=analysis_notes,
            integrity_hash=self._compute_hash(content)
        )

        self._analysis_log.append(result)

        if not result.is_safe:
            logger.warning(f"Input blocked/suspicious: {result.threat_level.value} - {issues}")

        return result

    def _detect_type(self, content: Any) -> InputType:
        """Auto-detekter input type."""
        if isinstance(content, bytes):
            return InputType.FILE
        if not isinstance(content, str):
            content = str(content)

        # Check for URLs
        if re.search(r'https?://', content):
            return InputType.URL

        # Check for code patterns
        code_patterns = [
            r'def\s+\w+\(', r'class\s+\w+:', r'import\s+',
            r'function\s+\w+\(', r'const\s+\w+\s*=', r'let\s+\w+\s*=',
            r'#include', r'int\s+main\(',
        ]
        for pattern in code_patterns:
            if re.search(pattern, content):
                return InputType.CODE

        # Check for commands
        if content.startswith('/') or content.startswith('!'):
            return InputType.COMMAND

        # Check for emojis
        emoji_pattern = re.compile(
            "["
            "\U0001F600-\U0001F64F"
            "\U0001F300-\U0001F5FF"
            "\U0001F680-\U0001F6FF"
            "\U0001F1E0-\U0001F1FF"
            "]+", flags=re.UNICODE
        )
        if emoji_pattern.search(content):
            if len(emoji_pattern.findall(content)) > 5:
                return InputType.EMOJI

        return InputType.TEXT

    def _check_dangerous(self, content: Any) -> List[str]:
        """Check for dangerous patterns."""
        issues = []
        content_str = str(content)

        for i, pattern in enumerate(self._dangerous_regex):
            if pattern.search(content_str):
                issues.append(f"Dangerous pattern #{i+1} detected")

        return issues

    def _check_suspicious(self, content: Any) -> List[str]:
        """Check for suspicious patterns."""
        issues = []
        content_str = str(content)

        for i, pattern in enumerate(self._suspicious_regex):
            if pattern.search(content_str):
                issues.append(f"Suspicious pattern #{i+1} detected")

        return issues

    async def _magnify_and_analyze(
        self,
        content: Any,
        input_type: InputType
    ) -> str:
        """
        Forstør input for detaljeret analyse.

        "Forstørrelse" betyder dyb inspektion af indholdet.
        """
        analysis = []
        content_str = str(content)

        analysis.append(f"=== MAGNIFIED ANALYSIS ===")
        analysis.append(f"Input Type: {input_type.value}")
        analysis.append(f"Content Length: {len(content_str)}")
        analysis.append(f"Unique Characters: {len(set(content_str))}")

        # Character distribution
        char_types = {
            "alpha": sum(1 for c in content_str if c.isalpha()),
            "digit": sum(1 for c in content_str if c.isdigit()),
            "space": sum(1 for c in content_str if c.isspace()),
            "special": sum(1 for c in content_str if not c.isalnum() and not c.isspace()),
        }
        analysis.append(f"Character Distribution: {char_types}")

        # Entropy analysis (higher entropy = more random = potentially obfuscated)
        if content_str:
            entropy = self._calculate_entropy(content_str)
            analysis.append(f"Entropy: {entropy:.2f}")
            if entropy > 5.0:
                analysis.append("WARNING: High entropy detected - possible obfuscation")

        # URL analysis
        urls = re.findall(r'https?://[^\s<>"{}|\\^`\[\]]+', content_str)
        if urls:
            analysis.append(f"URLs Found: {len(urls)}")
            for url in urls[:5]:  # Max 5
                domain = re.search(r'://([^/]+)', url)
                if domain:
                    d = domain.group(1)
                    if d in self.BLOCKED_DOMAINS:
                        analysis.append(f"BLOCKED DOMAIN: {d}")

        return "\n".join(analysis)

    async def _perform_autopsy(
        self,
        content: Any,
        input_type: InputType
    ) -> str:
        """
        Udfør obduktion på potentielt farligt input.

        "Obduktion" er en dyb dekonstruktion af indholdet.
        """
        autopsy = []
        content_str = str(content)

        autopsy.append("=== AUTOPSY REPORT ===")
        autopsy.append(f"Timestamp: {datetime.utcnow().isoformat()}")

        # Hex dump (first 100 bytes)
        hex_dump = content_str[:100].encode('utf-8', errors='replace').hex()
        autopsy.append(f"Hex (first 100): {hex_dump}")

        # Base64 detection
        base64_pattern = r'^[A-Za-z0-9+/=]{20,}$'
        if re.match(base64_pattern, content_str.strip()):
            autopsy.append("DETECTED: Content appears to be base64 encoded")
            try:
                decoded = base64.b64decode(content_str.strip())
                autopsy.append(f"Decoded length: {len(decoded)} bytes")
            except:
                pass

        # Hidden characters
        hidden = []
        for i, c in enumerate(content_str[:500]):
            if ord(c) < 32 and c not in '\n\r\t':
                hidden.append(f"pos {i}: \\x{ord(c):02x}")
            elif 0x200b <= ord(c) <= 0x206f:
                hidden.append(f"pos {i}: zero-width/invisible char")

        if hidden:
            autopsy.append(f"Hidden Characters Found: {len(hidden)}")
            autopsy.append(f"Locations: {hidden[:10]}")

        # Verdict
        if len(hidden) > 0 or 'Decoded' in str(autopsy):
            autopsy.append("\nVERDICT: Content contains obfuscation - BLOCK RECOMMENDED")
        else:
            autopsy.append("\nVERDICT: Content structure appears normal")

        return "\n".join(autopsy)

    def _sanitize_content(
        self,
        content: Any,
        input_type: InputType,
        blocked_list: List[str]
    ) -> Any:
        """Sanitér indholdet baseret på type."""
        if not isinstance(content, str):
            return content

        sanitized = content

        # Remove dangerous elements
        for pattern in self._dangerous_regex:
            match = pattern.search(sanitized)
            if match:
                blocked_list.append(match.group())
                sanitized = pattern.sub('[REMOVED]', sanitized)

        # HTML entities
        sanitized = sanitized.replace('<', '&lt;').replace('>', '&gt;')

        # Null bytes
        sanitized = sanitized.replace('\x00', '')

        # Excessive whitespace
        sanitized = re.sub(r'\s{10,}', ' ', sanitized)

        return sanitized

    def _calculate_entropy(self, text: str) -> float:
        """Beregn Shannon entropy."""
        import math
        if not text:
            return 0.0

        freq = {}
        for c in text:
            freq[c] = freq.get(c, 0) + 1

        entropy = 0.0
        for count in freq.values():
            p = count / len(text)
            entropy -= p * math.log2(p)

        return entropy

    def _compute_hash(self, content: Any) -> str:
        """Beregn integritetshash."""
        content_bytes = str(content).encode('utf-8')
        return hashlib.sha256(content_bytes).hexdigest()[:16]

    def get_statistics(self) -> Dict[str, Any]:
        """Hent statistik over sanitering."""
        return {
            "total_processed": len(self._analysis_log),
            "blocked_count": self._blocked_count,
            "suspicious_count": self._suspicious_count,
            "safe_count": len(self._analysis_log) - self._blocked_count - self._suspicious_count,
            "block_rate": self._blocked_count / max(1, len(self._analysis_log)),
        }


class CorruptionDetector:
    """
    Detektor for korruption i systemet.

    Overvåger for:
    - Dataintegritetsbrud
    - Uautoriserede ændringer
    - Anomal adfærd
    - Manipulation forsøg
    """

    def __init__(self):
        self._baseline_hashes: Dict[str, str] = {}
        self._anomaly_log: List[Dict[str, Any]] = []
        self._corruption_detected = False

    async def establish_baseline(self, component_id: str, data: Any) -> str:
        """Etabler baseline hash for en komponent."""
        hash_value = hashlib.sha256(str(data).encode()).hexdigest()
        self._baseline_hashes[component_id] = hash_value
        return hash_value

    async def verify_integrity(self, component_id: str, data: Any) -> bool:
        """Verificer integritet mod baseline."""
        if component_id not in self._baseline_hashes:
            return True  # No baseline = can't verify

        current_hash = hashlib.sha256(str(data).encode()).hexdigest()
        baseline = self._baseline_hashes[component_id]

        if current_hash != baseline:
            self._corruption_detected = True
            self._anomaly_log.append({
                "type": "integrity_violation",
                "component_id": component_id,
                "expected": baseline,
                "actual": current_hash,
                "timestamp": datetime.utcnow().isoformat()
            })
            logger.error(f"Corruption detected in {component_id}")
            return False

        return True

    async def detect_anomaly(
        self,
        component_id: str,
        metrics: Dict[str, float],
        thresholds: Dict[str, Tuple[float, float]]
    ) -> List[str]:
        """Detekter anomalier i metrics."""
        anomalies = []

        for metric, value in metrics.items():
            if metric in thresholds:
                min_val, max_val = thresholds[metric]
                if value < min_val or value > max_val:
                    anomaly = f"{metric}: {value} (expected {min_val}-{max_val})"
                    anomalies.append(anomaly)
                    self._anomaly_log.append({
                        "type": "metric_anomaly",
                        "component_id": component_id,
                        "metric": metric,
                        "value": value,
                        "threshold": thresholds[metric],
                        "timestamp": datetime.utcnow().isoformat()
                    })

        return anomalies

    def is_corrupted(self) -> bool:
        """Er korruption blevet detekteret?"""
        return self._corruption_detected

    def get_anomaly_log(self) -> List[Dict[str, Any]]:
        """Hent log over anomalier."""
        return self._anomaly_log


class IntegrityValidator:
    """
    Validator for dataintegritet.

    Sikrer at data ikke er blevet manipuleret.
    """

    def __init__(self):
        self._validators: Dict[str, Callable] = {}

    def register_validator(
        self,
        name: str,
        validator: Callable[[Any], bool]
    ) -> None:
        """Registrer en custom validator."""
        self._validators[name] = validator

    async def validate(
        self,
        data: Any,
        validators: Optional[List[str]] = None
    ) -> Tuple[bool, List[str]]:
        """
        Valider data med registrerede validators.

        Returns:
            Tuple af (is_valid, list of failed validators)
        """
        failed = []
        validators_to_use = validators or list(self._validators.keys())

        for name in validators_to_use:
            if name in self._validators:
                try:
                    if not self._validators[name](data):
                        failed.append(name)
                except Exception as e:
                    failed.append(f"{name} (error: {e})")

        return len(failed) == 0, failed

    async def validate_chain(
        self,
        data_chain: List[Any]
    ) -> bool:
        """Valider en kæde af data for konsistens."""
        if len(data_chain) < 2:
            return True

        # Check each link in chain
        for i in range(1, len(data_chain)):
            prev_hash = hashlib.sha256(str(data_chain[i-1]).encode()).hexdigest()
            # Chain should reference previous
            if hasattr(data_chain[i], 'prev_hash'):
                if data_chain[i].prev_hash != prev_hash:
                    return False

        return True


# ═══════════════════════════════════════════════════════════════
# SINGLETON INSTANCES
# ═══════════════════════════════════════════════════════════════

_sanitizer: Optional[InputSanitizer] = None
_corruption_detector: Optional[CorruptionDetector] = None
_integrity_validator: Optional[IntegrityValidator] = None


def get_sanitizer() -> InputSanitizer:
    """Hent singleton InputSanitizer."""
    global _sanitizer
    if _sanitizer is None:
        _sanitizer = InputSanitizer()
    return _sanitizer


def get_corruption_detector() -> CorruptionDetector:
    """Hent singleton CorruptionDetector."""
    global _corruption_detector
    if _corruption_detector is None:
        _corruption_detector = CorruptionDetector()
    return _corruption_detector


def get_integrity_validator() -> IntegrityValidator:
    """Hent singleton IntegrityValidator."""
    global _integrity_validator
    if _integrity_validator is None:
        _integrity_validator = IntegrityValidator()
    return _integrity_validator


logger.info("CKC Security module loaded")
