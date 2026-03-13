"""
David's Brain — Sovereign AI Module.

Background intelligence layer that runs behind the main GapDet model.
Implements:
- Emergence Continuity Loop (ECL): self-referential reasoning
- Taxonomic hierarchy: Kingdom→Species classification of code/actions
- Sovereign memory: SQLite-backed learning from validated interactions
- SOV-CHECK gate: confidence threshold requiring user approval
- Genix Memory: contextual knowledge store
- Intent Translation: emergent meaning from taxonomy + memory + validation

This runs as a background process alongside the main compiler/patcher model.
100% offline. No APIs. No internet.
"""

import sqlite3
import json
import time
import hashlib
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any


# ---------------------------------------------------------------------------
# Taxonomic hierarchy for code/action classification
# ---------------------------------------------------------------------------

DEFAULT_TAXONOMY = {
    "KINGDOM": {
        "MANIPULATION": ["open", "close", "create", "delete", "move", "copy", "rename"],
        "ANALYSIS": ["detect", "scan", "analyze", "inspect", "profile", "trace", "audit"],
        "TRANSFORMATION": ["compile", "patch", "fix", "translate", "convert", "refactor", "optimize"],
        "GENERATION": ["generate", "complete", "synthesize", "template", "scaffold", "stub"],
        "VALIDATION": ["test", "verify", "check", "lint", "typecheck", "benchmark", "fuzz"],
    },
    "PHYLUM": {
        "SOURCE_CODE": ["c", "cpp", "python", "rust", "go", "java", "javascript", "typescript"],
        "CONFIG": ["yaml", "json", "toml", "xml", "ini", "env"],
        "BUILD": ["makefile", "cmake", "gradle", "cargo", "npm", "pip"],
        "BINARY": ["elf", "pe", "mach-o", "wasm", "bytecode"],
        "FIRMWARE": ["arduino", "esp-idf", "micropython", "rtos"],
        "SYSTEM": ["kernel", "driver", "daemon", "service", "init"],
    },
    "CLASS": {
        "GAP_TYPES": [
            "missing_error_handling", "buffer_overflow", "null_dereference",
            "resource_leak", "race_condition", "security_vulnerability",
            "type_mismatch", "missing_import", "incomplete_implementation",
            "missing_bounds_check", "uninitialized_variable", "dead_code",
            "missing_return", "syntax_error", "logic_error", "performance_issue",
        ],
        "TRANSFORM_TYPES": [
            "patch", "translation", "completion", "refactor",
            "optimization", "migration", "upgrade",
        ],
    },
    "ORDER": {
        "SEVERITY": ["critical", "high", "medium", "low", "info"],
        "CONFIDENCE": ["certain", "high", "medium", "low", "speculative"],
    },
    "FAMILY": {},  # Populated by user-specific patterns
    "GENUS": {},   # Populated by learned code patterns
    "SPECIES": {}, # Populated by validated specific instances
}


class SovereignMemory:
    """
    SQLite-backed sovereign memory.
    Stores validated interactions, learned patterns, and emergent concepts.
    """

    def __init__(self, db_path: str) -> None:
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self._init_tables()

    def _init_tables(self) -> None:
        self.conn.executescript("""
            CREATE TABLE IF NOT EXISTS species (
                species_key TEXT PRIMARY KEY,
                kingdom TEXT,
                phylum TEXT,
                class_name TEXT,
                context TEXT,
                confidence REAL,
                validated INTEGER DEFAULT 0,
                created_at REAL,
                last_used REAL,
                use_count INTEGER DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS ecl_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp REAL,
                input_hash TEXT,
                reasoning TEXT,
                output_hash TEXT,
                confidence REAL,
                validated INTEGER DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS concepts (
                name TEXT PRIMARY KEY,
                definition TEXT,
                source TEXT,
                relationships TEXT,
                created_at REAL
            );

            CREATE TABLE IF NOT EXISTS genix (
                key TEXT PRIMARY KEY,
                value TEXT,
                category TEXT,
                created_at REAL
            );
        """)
        self.conn.commit()

    def record_species(
        self, key: str, kingdom: str, phylum: str, class_name: str,
        context: str, confidence: float, validated: bool = False,
    ) -> None:
        """Record a Species-level validated action."""
        now = time.time()
        self.conn.execute(
            """INSERT OR REPLACE INTO species
               (species_key, kingdom, phylum, class_name, context, confidence, validated, created_at, last_used, use_count)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, COALESCE((SELECT use_count FROM species WHERE species_key=?), 0) + 1)""",
            (key, kingdom, phylum, class_name, context, confidence, int(validated), now, now, key),
        )
        self.conn.commit()

    def find_species(self, key: str) -> Optional[Dict]:
        """Look up a previously validated Species."""
        row = self.conn.execute(
            "SELECT * FROM species WHERE species_key=?", (key,)
        ).fetchone()
        if row is None:
            return None
        # Update last_used
        self.conn.execute(
            "UPDATE species SET last_used=?, use_count=use_count+1 WHERE species_key=?",
            (time.time(), key),
        )
        self.conn.commit()
        return {
            "species_key": row[0], "kingdom": row[1], "phylum": row[2],
            "class_name": row[3], "context": row[4], "confidence": row[5],
            "validated": bool(row[6]), "created_at": row[7],
            "last_used": row[8], "use_count": row[9],
        }

    def log_ecl_cycle(
        self, input_data: str, reasoning: str, output_data: str,
        confidence: float, validated: bool = False,
    ) -> int:
        """Log an Emergence Continuity Loop cycle."""
        input_hash = hashlib.sha256(input_data.encode()).hexdigest()[:16]
        output_hash = hashlib.sha256(output_data.encode()).hexdigest()[:16]
        cursor = self.conn.execute(
            """INSERT INTO ecl_log (timestamp, input_hash, reasoning, output_hash, confidence, validated)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (time.time(), input_hash, reasoning, output_hash, confidence, int(validated)),
        )
        self.conn.commit()
        return cursor.lastrowid

    def store_concept(self, name: str, definition: str, source: str, relationships: List[str]) -> None:
        """Store an emergent concept."""
        self.conn.execute(
            """INSERT OR REPLACE INTO concepts (name, definition, source, relationships, created_at)
               VALUES (?, ?, ?, ?, ?)""",
            (name, definition, source, json.dumps(relationships), time.time()),
        )
        self.conn.commit()

    def get_concept(self, name: str) -> Optional[Dict]:
        row = self.conn.execute("SELECT * FROM concepts WHERE name=?", (name,)).fetchone()
        if row is None:
            return None
        return {
            "name": row[0], "definition": row[1], "source": row[2],
            "relationships": json.loads(row[3]), "created_at": row[4],
        }

    def store_genix(self, key: str, value: str, category: str = "general") -> None:
        self.conn.execute(
            "INSERT OR REPLACE INTO genix (key, value, category, created_at) VALUES (?, ?, ?, ?)",
            (key, value, category, time.time()),
        )
        self.conn.commit()

    def get_genix(self, key: str) -> Optional[str]:
        row = self.conn.execute("SELECT value FROM genix WHERE key=?", (key,)).fetchone()
        return row[0] if row else None

    def get_recent_ecl_cycles(self, limit: int = 10) -> List[Dict]:
        rows = self.conn.execute(
            "SELECT * FROM ecl_log ORDER BY timestamp DESC LIMIT ?", (limit,)
        ).fetchall()
        return [
            {"id": r[0], "timestamp": r[1], "input_hash": r[2], "reasoning": r[3],
             "output_hash": r[4], "confidence": r[5], "validated": bool(r[6])}
            for r in rows
        ]

    def close(self) -> None:
        self.conn.close()


class ECL:
    """
    Emergence Continuity Loop.

    Self-referential reasoning engine that:
    1. Takes input (code, intent, query)
    2. Classifies via taxonomy (Kingdom→Class)
    3. Checks sovereign memory for prior validated patterns (Species lookup)
    4. If found: auto-applies with high confidence
    5. If not found: reasons about it, proposes action, logs for validation
    6. Feeds output back as context for next cycle (continuity)

    The "emergence" is that meaning arises from the interaction of
    taxonomy + memory + validation — not from hardcoded rules.
    """

    def __init__(self, memory: SovereignMemory, taxonomy: Optional[Dict] = None) -> None:
        self.memory = memory
        self.taxonomy = taxonomy or DEFAULT_TAXONOMY
        self.cycle_count = 0
        self.context_stack: List[Dict] = []  # Rolling context for continuity

    def classify(self, intent: str, code: str = "", language: str = "") -> Dict:
        """
        Classify an intent through the taxonomic hierarchy.
        Returns Kingdom, Phylum, Class, and confidence.
        """
        intent_lower = intent.lower()

        # Kingdom: What kind of action?
        kingdom = "UNKNOWN"
        kingdom_confidence = 0.0
        for k, verbs in self.taxonomy["KINGDOM"].items():
            for verb in verbs:
                if verb in intent_lower:
                    kingdom = k
                    kingdom_confidence = 0.8
                    break

        # Phylum: What kind of target?
        phylum = "UNKNOWN"
        if language:
            for p, langs in self.taxonomy["PHYLUM"].items():
                if language.lower() in [l.lower() for l in langs]:
                    phylum = p
                    break

        # Class: What specific gap/transform type?
        class_name = "UNKNOWN"
        for cls_group, types in self.taxonomy["CLASS"].items():
            for t in types:
                if t.replace("_", " ") in intent_lower or t in intent_lower:
                    class_name = t
                    break

        return {
            "kingdom": kingdom,
            "phylum": phylum,
            "class": class_name,
            "confidence": kingdom_confidence,
            "intent": intent,
            "language": language,
        }

    def sov_check(self, classification: Dict, threshold: float = 0.85) -> Dict:
        """
        SOV-CHECK gate: determines if action can auto-execute or needs validation.

        Returns:
            {
                "approved": bool,
                "reason": str,
                "species": Optional[Dict],  # if found in memory
                "requires_validation": bool,
            }
        """
        # Build species key from classification
        species_key = f"{classification['kingdom']}:{classification['class']}:{classification['language']}"

        # Check memory for prior validated species
        species = self.memory.find_species(species_key)

        if species and species["validated"]:
            return {
                "approved": True,
                "reason": f"Species match: {species_key} (validated {species['use_count']} times)",
                "species": species,
                "requires_validation": False,
            }

        if classification["confidence"] >= threshold:
            return {
                "approved": True,
                "reason": f"High confidence: {classification['confidence']:.2f} >= {threshold}",
                "species": None,
                "requires_validation": False,
            }

        return {
            "approved": False,
            "reason": f"Low confidence: {classification['confidence']:.2f} < {threshold}",
            "species": None,
            "requires_validation": True,
        }

    def run_cycle(
        self, intent: str, code: str = "", language: str = "",
        auto_validate: bool = False,
    ) -> Dict:
        """
        Run one ECL cycle:
        1. Classify intent
        2. Check sovereign memory
        3. SOV-CHECK gate
        4. Execute or request validation
        5. Log cycle for continuity
        """
        self.cycle_count += 1

        # Step 1: Classify
        classification = self.classify(intent, code, language)

        # Step 2+3: SOV-CHECK
        check = self.sov_check(classification)

        # Step 4: Build reasoning chain
        reasoning_parts = [
            f"Cycle #{self.cycle_count}",
            f"Intent: {intent}",
            f"Classification: {classification['kingdom']}/{classification['phylum']}/{classification['class']}",
            f"Confidence: {classification['confidence']:.2f}",
            f"SOV-CHECK: {'APPROVED' if check['approved'] else 'REQUIRES VALIDATION'}",
        ]

        # Add context from recent cycles (continuity)
        if self.context_stack:
            last = self.context_stack[-1]
            reasoning_parts.append(f"Previous: {last.get('intent', 'N/A')}")

        reasoning = " | ".join(reasoning_parts)

        # Step 5: Record
        species_key = f"{classification['kingdom']}:{classification['class']}:{classification.get('language', '')}"

        if check["approved"] or auto_validate:
            self.memory.record_species(
                key=species_key,
                kingdom=classification["kingdom"],
                phylum=classification["phylum"],
                class_name=classification["class"],
                context=json.dumps({"intent": intent, "code_snippet": code[:200]}),
                confidence=classification["confidence"],
                validated=True,
            )

        cycle_id = self.memory.log_ecl_cycle(
            input_data=f"{intent}|{code[:200]}",
            reasoning=reasoning,
            output_data=species_key,
            confidence=classification["confidence"],
            validated=check["approved"] or auto_validate,
        )

        result = {
            "cycle_id": cycle_id,
            "cycle_count": self.cycle_count,
            "classification": classification,
            "sov_check": check,
            "reasoning": reasoning,
            "species_key": species_key,
            "approved": check["approved"] or auto_validate,
        }

        # Push to context stack (keep last 10 for continuity)
        self.context_stack.append(result)
        if len(self.context_stack) > 10:
            self.context_stack.pop(0)

        return result

    def get_continuity_context(self) -> List[Dict]:
        """Get the rolling context stack for continuity."""
        return self.context_stack

    def get_stats(self) -> Dict:
        """Get ECL statistics."""
        recent = self.memory.get_recent_ecl_cycles(100)
        validated = sum(1 for r in recent if r["validated"])
        return {
            "total_cycles": self.cycle_count,
            "recent_cycles": len(recent),
            "validated_ratio": validated / max(len(recent), 1),
            "context_depth": len(self.context_stack),
        }


class DavidsBrain:
    """
    David's Brain — the main sovereign AI controller.

    Combines:
    - ECL (Emergence Continuity Loop) for self-referential reasoning
    - Taxonomic classification for structure
    - Sovereign memory for learning
    - SOV-CHECK for user validation
    - Genix for contextual knowledge

    Runs in the background alongside the main GapDet model.
    """

    def __init__(self, data_dir: Optional[str] = None) -> None:
        if data_dir is None:
            data_dir = os.path.join(str(Path.home()), ".davids_brain")
        self.data_dir = data_dir
        os.makedirs(data_dir, exist_ok=True)

        # Initialize memory
        db_path = os.path.join(data_dir, "sovereign.db")
        self.memory = SovereignMemory(db_path)

        # Initialize ECL
        taxonomy_path = os.path.join(data_dir, "taxonomy.json")
        taxonomy = None
        if os.path.exists(taxonomy_path):
            with open(taxonomy_path) as f:
                taxonomy = json.load(f)
        self.ecl = ECL(self.memory, taxonomy)

        # Store default concepts
        self._init_concepts()

    def _init_concepts(self) -> None:
        """Initialize built-in concepts if not already present."""
        concepts = [
            ("ECL", "Emergence Continuity Loop - self-referential reasoning where meaning emerges from interaction of taxonomy + memory + validation",
             "core", ["taxonomy", "sovereign_memory", "sov_check", "intent_translation"]),
            ("PIM", "Uncle Greg's deterministic assembly - pattern matching via structural/visual signatures for reliable element identification",
             "core", ["taxonomy", "pattern_matching", "determinism"]),
            ("SOV_CHECK", "Sovereignty validation gate - confidence threshold requiring user approval before executing uncertain actions",
             "core", ["validation", "confidence", "user_control"]),
            ("INTENT_TRANSLATION", "Emergent property where meaning arises from taxonomy + memory + validation interaction, not hardcoded rules",
             "emergent", ["taxonomy", "ECL", "sovereign_memory"]),
            ("GENIX", "Contextual knowledge store - personal knowledge graph that enriches reasoning with user-specific context",
             "core", ["memory", "context", "personalization"]),
            ("HANGMAN", "Framework for structured code analysis and gap detection across multiple languages",
             "framework", ["gap_detection", "code_analysis", "multi_language"]),
            ("LOOM", "Concurrency and threading pattern manager - weaves multiple processes together coherently",
             "framework", ["concurrency", "threading", "parallel_processing"]),
            ("HYPER_CONSISTENCY", "AI alignment through consistent hit points - reliable interactions that compound into predictable behavior",
             "alignment", ["ECL", "validation", "reliability"]),
        ]
        for name, definition, source, rels in concepts:
            if self.memory.get_concept(name) is None:
                self.memory.store_concept(name, definition, source, rels)

    def process(
        self, intent: str, code: str = "", language: str = "",
        auto_validate: bool = True,
    ) -> Dict:
        """
        Process an intent through David's Brain.

        This is the main entry point. It:
        1. Runs the ECL cycle (classify, check memory, validate)
        2. Returns the result with reasoning
        3. Maintains continuity for future cycles

        Args:
            intent: What the user wants to do
            code: Code to analyze/transform (optional)
            language: Programming language (optional)
            auto_validate: If True, auto-approve actions (background mode)

        Returns:
            Dict with classification, approval status, reasoning, etc.
        """
        return self.ecl.run_cycle(intent, code, language, auto_validate)

    def get_context(self) -> Dict:
        """Get current brain context (for enriching model inference)."""
        return {
            "ecl_stats": self.ecl.get_stats(),
            "recent_context": [
                {"intent": c.get("classification", {}).get("intent", ""),
                 "kingdom": c.get("classification", {}).get("kingdom", ""),
                 "approved": c.get("approved", False)}
                for c in self.ecl.get_continuity_context()
            ],
        }

    def enrich_prompt(self, base_prompt: str) -> str:
        """
        Enrich a prompt with brain context (for model inference).
        This is how the background brain influences the foreground model.
        """
        context = self.get_context()
        stats = context["ecl_stats"]

        enrichment = f"\n[BRAIN CONTEXT: {stats['total_cycles']} cycles, "
        enrichment += f"{stats['validated_ratio']:.0%} validated"

        recent = context["recent_context"]
        if recent:
            last = recent[-1]
            enrichment += f", last: {last['kingdom']}/{last['intent'][:30]}"

        enrichment += "]"

        return base_prompt + enrichment

    def save_taxonomy(self) -> None:
        """Save current taxonomy to disk."""
        path = os.path.join(self.data_dir, "taxonomy.json")
        with open(path, "w") as f:
            json.dump(self.ecl.taxonomy, f, indent=2)

    def close(self) -> None:
        """Clean shutdown."""
        self.save_taxonomy()
        self.memory.close()


def create_brain(data_dir: Optional[str] = None) -> DavidsBrain:
    """Factory function to create a DavidsBrain instance."""
    return DavidsBrain(data_dir)
