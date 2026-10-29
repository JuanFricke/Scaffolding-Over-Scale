"""Layer 2 rules on synthetic patches. Run from benchmark/: python -m unittest discover -s quality/tests -t ."""
from __future__ import annotations

import unittest

from quality import conventions as cv, patch as pt


def diff(path: str, lines: list[str], new: bool = True) -> str:
    head = f"diff --git a/{path} b/{path}\n" + ("new file mode 100644\n" if new else "")
    return head + f"--- a/{path}\n+++ b/{path}\n@@ -0,0 +1,{len(lines)} @@\n" + "".join(f"+{l}\n" for l in lines)


def rules(*parts: str) -> dict[str, cv.RuleResult]:
    return {r.rule: r for r in cv.check(pt.parse("".join(parts)))}


class PatchTests(unittest.TestCase):
    def test_parse_and_filter_harness(self):
        files = pt.parse(diff("app/X.php", ["<?php"]) + diff("AGENTS.md", ["x"]) + diff("composer.lock", ["{}"]))
        self.assertEqual([f.path for f in files], ["app/X.php", "AGENTS.md", "composer.lock"])
        self.assertEqual([f.path for f in pt.relevant(files)], ["app/X.php"])
        self.assertEqual(files[0].status, "added")


class RuleTests(unittest.TestCase):
    def test_c1_tests_required(self):
        self.assertFalse(rules(diff("app/A.php", ["<?php"]))["C1"].ok)
        self.assertTrue(rules(diff("app/A.php", ["<?php"]), diff("tests/Feature/ATest.php", ["<?php"]))["C1"].ok)
        self.assertFalse(rules(diff("docs/a.md", ["x"]))["C1"].applies)

    def test_c2_livewire_validate_attribute(self):
        inline = ["class C extends Component {", "public function save() { $this->validate(['a' => 'required']); }", "}"]
        attr = ["class C extends Component {", "#[Validate('required')]", "public $a;",
                "public function save() { $this->validate(); }", "}"]
        self.assertFalse(rules(diff("app/Livewire/C.php", inline))["C2"].ok)
        self.assertTrue(rules(diff("app/Livewire/C.php", attr))["C2"].ok)

    def test_c3_writes_need_authorization_or_action(self):
        bad = ["public function remove($id) {", "Queue::find($id)->delete();", "}"]
        good = ["public function remove($id) {", "$this->authorize('delete', $q);", "$q->delete();", "}"]
        action = ["public function issue() {", "app(IssueTicket::class)->handle($this->queue);", "}"]
        toggle = ["public function openCreate() {", "$this->showCreate = true;", "}"]
        self.assertFalse(rules(diff("app/Livewire/Q.php", bad))["C3"].ok)
        self.assertTrue(rules(diff("app/Livewire/Q.php", good))["C3"].ok)
        self.assertTrue(rules(diff("app/Livewire/Q.php", action))["C3"].ok)
        self.assertFalse(rules(diff("app/Livewire/Q.php", toggle))["C3"].applies)

    def test_c4_writes_belong_in_actions(self):
        self.assertFalse(rules(diff("app/Http/Controllers/QController.php", ["Queue::create($data);"]))["C4"].ok)
        self.assertTrue(rules(diff("app/Http/Controllers/QController.php", ["app(CreateQueue::class)->handle($d);"]))["C4"].ok)

    def test_c5_migrations(self):
        good = ["return new class extends Migration {", "public function up(): void { Schema::create('x', fn ($t) => $t->id()); }",
                "public function down(): void { Schema::dropIfExists('x'); }", "};"]
        empty_down = good[:2] + ["public function down(): void { // }", "};"]
        self.assertTrue(rules(diff("database/migrations/2026_10_29_120000_create_x.php", good))["C5"].ok)
        self.assertFalse(rules(diff("database/migrations/create_x.php", good))["C5"].ok)
        self.assertFalse(rules(diff("database/migrations/2026_10_29_120000_create_x.php", empty_down))["C5"].ok)

    def test_c6_c8(self):
        self.assertFalse(rules(diff("app/Services/QueueService.php", ["<?php"]))["C6"].ok)
        self.assertFalse(rules(diff("app/Models/Q.php", ["class Q extends Model {}"]))["C8"].ok)
        self.assertTrue(rules(diff("app/Models/Q.php", ["class Q extends Model {", "protected $fillable = ['a'];", "}"]))["C8"].ok)

    def test_c7_c9_blade(self):
        self.assertFalse(rules(diff("resources/views/a.blade.php", ["{!! $x !!}"]))["C7"].ok)
        bulma = ['<div class="is-flex is-justify-content-space-between mb-3 px-4 has-text-grey title is-6">']
        tailwind = ['<div class="flex items-center justify-between bg-gray-100 rounded-lg">']
        self.assertTrue(rules(diff("resources/views/a.blade.php", bulma))["C9"].ok)
        self.assertFalse(rules(diff("resources/views/a.blade.php", tailwind))["C9"].ok)

    def test_c10_manual_role_checks(self):
        self.assertFalse(rules(diff("resources/views/a.blade.php", ["@if ($m->role === Role::Owner)"]))["C10"].ok)
        self.assertTrue(rules(diff("resources/views/a.blade.php", ["@can('update', $queue)"]))["C10"].ok)

    def test_score_ignores_rules_that_do_not_apply(self):
        res = cv.check(pt.parse(diff("app/A.php", ["<?php"]) + diff("tests/ATest.php", ["<?php"])))
        self.assertEqual(cv.score(res), 1.0)


if __name__ == "__main__":
    unittest.main()
