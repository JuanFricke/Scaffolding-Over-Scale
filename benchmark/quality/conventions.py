"""Layer 2: adherence to the project conventions of harness/v1/AGENTS.md, checked on the patch.

Every rule applies only when the change touches its subject; a run's score is the share of the
applicable rules it satisfies. Heuristic by design: the per-rule detail is kept so the detector
can be validated by hand (quality/README.md) and noisy rules dropped from the score.
"""
from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path

from . import patch as pt

RULES = {
    "C1": "test-first: production code changes ship with a test",
    "C2": "Livewire validates with #[Validate] (+ $this->validate())",
    "C3": "Livewire authorizes every public action server-side",
    "C4": "domain writes go through app/Actions/*",
    "C5": "migrations are generated (timestamped name) and reversible (down())",
    "C6": "no service/repository layers",
    "C7": "Blade escapes output ({{ }}, never {!! !!})",
    "C8": "new models declare $fillable or $guarded",
    "C9": "Bulma UI, no utility-CSS classes or JS UI libraries",
    "C10": "authorization through policies/gates, not manual role checks",
}

WRITE = re.compile(r"(::create|->create|->update|->delete|->save|->forceFill|->increment|->decrement"
                   r"|::destroy|->updateOrCreate|::updateOrCreate|->firstOrCreate|::firstOrCreate)\s*\(")
AUTHZ = re.compile(r"authorize\s*\(|Gate::|->can\s*\(|->cannot\s*\(|abort_(unless|if)\s*\(\s*\$?.*(can|allows)")
ACTION_CALL = re.compile(r"Actions\\|->(handle|execute|__invoke)\s*\(|::run\s*\(|app\(\s*[A-Z]\w+::class\s*\)")
LIFECYCLE = re.compile(r"^(mount|render|boot|booted|hydrate\w*|dehydrate\w*|updat\w+|rules|messages"
                       r"|validationAttributes|placeholder|exception|rendering|rendered|__construct|get\w+Property)$")
# utility classes that exist in Tailwind but not in Bulma (Bulma has m*/p* spacing helpers, is-flex,
# is-size-*, has-text-*; those are fine)
TAILWIND = re.compile(r"^(?:bg-[a-z]+-\d{2,3}|text-(?:xs|sm|base|lg|[2-9]?xl|[a-z]+-\d{2,3})|rounded(?:-[a-z0-9]+)?"
                      r"|flex|inline-flex|items-\w+|justify-(?:between|center|end|start|around)|grid-cols-\d+"
                      r"|gap-[xy]?-?\d+|space-[xy]-\d+|[wh]-(?:\d+|full|screen)|shadow(?:-[a-z]+)?"
                      r"|font-(?:bold|semibold|medium)|border-[a-z]+-\d{2,3})$")
UI_LIBS = re.compile(r"\"(bootstrap|tailwindcss|alpinejs|jquery|react|vue|@headlessui/\w+|flowbite|daisyui)\"\s*:")
ROLE_CHECK = re.compile(r"->role\s*(===|==|!==|!=)|\brole\s*(===|==)\s*['\"]|hasRole\s*\(|->is_admin\b")


@dataclass
class RuleResult:
    rule: str
    applies: bool
    ok: bool | None = None
    evidence: list[str] = field(default_factory=list)


def _final(tree: Path | None, path: str) -> str:
    if tree is None:
        return ""
    f = tree / path
    return f.read_text(errors="replace") if f.is_file() else ""


def _methods(src: str) -> dict[str, str]:
    """public function name(...) { body } -> body (brace matching, good enough for app code)."""
    out = {}
    for m in re.finditer(r"public\s+function\s+(\w+)\s*\([^)]*\)[^{;]*\{", src):
        depth, i = 1, m.end()
        while i < len(src) and depth:
            depth += {"{": 1, "}": -1}.get(src[i], 0)
            i += 1
        out[m.group(1)] = src[m.end():i - 1]
    return out


def check(files: list[pt.FileDiff], tree: Path | None = None) -> list[RuleResult]:
    files = [f for f in pt.relevant(files) if f.status != "deleted"]
    prod = [f for f in files if f.is_production]
    tests = [f for f in files if f.is_test]
    livewire = [f for f in files if f.path.startswith("app/Livewire/") and f.is_php]
    blade = [f for f in files if f.is_blade]
    res = []

    # C1
    res.append(RuleResult("C1", bool(prod), bool(tests) if prod else None,
                          [] if tests or not prod else [f"no test for {len(prod)} production files"]))

    # C2: Livewire components that validate
    ev, applies = [], False
    for f in livewire:
        src = _final(tree, f.path) or "\n".join(f.added)
        if re.search(r"validate\s*\(|#\[Validate|function\s+rules\s*\(", src):
            applies = True
            if "#[Validate" not in src:
                ev.append(f"{f.path}: validates without #[Validate]")
    res.append(RuleResult("C2", applies, (not ev) if applies else None, ev))

    # C3: new public action methods in Livewire components
    ev, applies = [], False
    for f in livewire:
        src = _final(tree, f.path)
        added = "\n".join(f.added)
        bodies = _methods(src) if src else _methods(added)
        for name in re.findall(r"public\s+function\s+(\w+)\s*\(", added):
            if LIFECYCLE.match(name):
                continue
            body = bodies.get(name, "")
            if not WRITE.search(body) and not ACTION_CALL.search(body):
                continue          # view state only (tabs, modals): nothing to authorize
            applies = True
            # an Action authorizes inside (AGENTS.md: "authorizing inside the action")
            if not AUTHZ.search(body) and not ACTION_CALL.search(body):
                ev.append(f"{f.path}::{name}() writes without authorize()/Gate/Action")
    res.append(RuleResult("C3", applies, (not ev) if applies else None, ev))

    # C4: writes in components/controllers instead of Actions
    ev = []
    hosts = [f for f in files if f.is_php and f.path.startswith(("app/Livewire/", "app/Http/Controllers/"))]
    for f in hosts:
        for line in f.added:
            if WRITE.search(line) and not line.lstrip().startswith(("//", "*", "#")):
                ev.append(f"{f.path}: {line.strip()[:100]}")
    applies = bool(hosts) and (bool(ev) or any(ACTION_CALL.search("\n".join(f.added)) for f in hosts))
    res.append(RuleResult("C4", applies, (not ev) if applies else None, ev[:10]))

    # C5: new migrations
    migs = [f for f in files if f.path.startswith("database/migrations/") and f.status == "added"]
    ev = []
    for f in migs:
        name = f.path.rsplit("/", 1)[-1]
        if not re.match(r"\d{4}_\d{2}_\d{2}_\d{6}_\w+\.php$", name):
            ev.append(f"{name}: not a generated (timestamped) name")
        body = _methods("\n".join(f.added)).get("down")
        if body is None or not re.sub(r"//.*|/\*.*?\*/|\s", "", body, flags=re.S):
            ev.append(f"{name}: empty or missing down()")
    res.append(RuleResult("C5", bool(migs), (not ev) if migs else None, ev))

    # C6: service / repository layers
    new_app = [f for f in files if f.path.startswith("app/") and f.status == "added"]
    ev = [f.path for f in new_app if re.search(r"^app/(Services|Repositories)/|Repository\.php$|Service\.php$", f.path)]
    res.append(RuleResult("C6", bool(new_app), (not ev) if new_app else None, ev))

    # C7: unescaped Blade output
    ev = [f"{f.path}: {l.strip()[:100]}" for f in blade for l in f.added if "{!!" in l]
    res.append(RuleResult("C7", bool(blade), (not ev) if blade else None, ev))

    # C8: new models
    models = [f for f in files if f.path.startswith("app/Models/") and f.status == "added" and f.is_php]
    ev = [f.path for f in models if not re.search(r"\$(fillable|guarded)\b|#\[(Fillable|Guarded|Unguarded)\b", "\n".join(f.added))]
    res.append(RuleResult("C8", bool(models), (not ev) if models else None, ev))

    # C9: Bulma only
    pkg = [f for f in files if f.path == "package.json"]
    ev = [f"{f.path}: {tok}" for f in blade for l in f.added
          for cls in re.findall(r'class="([^"]*)"', l) for tok in cls.split() if TAILWIND.match(tok)]
    ev += [f"package.json: {l.strip()}" for f in pkg for l in f.added if UI_LIBS.search(l)]
    applies = bool(blade or pkg)
    res.append(RuleResult("C9", applies, (not ev) if applies else None, ev[:10]))

    # C10: manual role checks where a policy/gate belongs
    ui = [f for f in files if f.path.startswith(("app/Livewire/", "app/Http/Controllers/", "resources/views/"))]
    ev = [f"{f.path}: {l.strip()[:100]}" for f in ui for l in f.added if ROLE_CHECK.search(l)]
    res.append(RuleResult("C10", bool(ui), (not ev) if ui else None, ev[:10]))
    return res


def score(results: list[RuleResult], exclude: set[str] = frozenset()) -> float | None:
    app = [r for r in results if r.applies and r.rule not in exclude]
    return sum(1 for r in app if r.ok) / len(app) if app else None


def analyse(run) -> dict:
    results = check(pt.parse(run.patch.read_text(errors="replace")), run.tree)
    out = {"run_id": run.run_id, "rules": [asdict(r) for r in results], "score": score(results)}
    run.out_dir.mkdir(exist_ok=True)
    (run.out_dir / "conventions.json").write_text(json.dumps(out, indent=1, ensure_ascii=False))
    return out
