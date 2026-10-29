<?php
// Cyclomatic complexity per function/method, from the PHP tokenizer (no dependencies).
// Usage: php complexity.php <file>...   -> JSON {"<file>": {"<Class::method|function>": cc, ...}}
// cc = 1 + decision points (if/elseif/for/foreach/while/case/catch/&&/||/and/or/?:/??/match arm).

$decision = [T_IF, T_ELSEIF, T_FOR, T_FOREACH, T_WHILE, T_CASE, T_CATCH,
             T_BOOLEAN_AND, T_BOOLEAN_OR, T_LOGICAL_AND, T_LOGICAL_OR, T_COALESCE];
$out = [];
foreach (array_slice($argv, 1) as $file) {
    if (!is_file($file)) { continue; }
    $tokens = token_get_all(file_get_contents($file));
    $n = count($tokens);
    $class = null; $classDepth = -1; $depth = 0; $result = [];
    for ($i = 0; $i < $n; $i++) {
        $t = $tokens[$i];
        if ($t === '{' || (is_array($t) && in_array($t[0], [T_CURLY_OPEN, T_DOLLAR_OPEN_CURLY_BRACES], true))) { $depth++; continue; }
        if ($t === '}') { $depth--; if ($depth === $classDepth) { $class = null; $classDepth = -1; } continue; }
        if (!is_array($t)) { continue; }
        if (in_array($t[0], [T_CLASS, T_TRAIT, T_ENUM, T_INTERFACE], true)) {
            $p = $i - 1;
            while ($p >= 0 && is_array($tokens[$p]) && $tokens[$p][0] === T_WHITESPACE) { $p--; }
            if ($p >= 0 && is_array($tokens[$p]) && $tokens[$p][0] === T_DOUBLE_COLON) { continue; }  // Foo::class
            for ($j = $i + 1; $j < $n; $j++) {
                if (is_array($tokens[$j]) && $tokens[$j][0] === T_STRING) { $class = $tokens[$j][1]; $classDepth = $depth; break; }
                if ($tokens[$j] === '{' || $tokens[$j] === '(') { break; }   // anonymous class
            }
            continue;
        }
        if ($t[0] !== T_FUNCTION) { continue; }
        $name = null;
        for ($j = $i + 1; $j < $n && $tokens[$j] !== '(' ; $j++) {
            if (is_array($tokens[$j]) && $tokens[$j][0] === T_STRING) { $name = $tokens[$j][1]; break; }
        }
        if ($name === null) { continue; }                  // closure: counted in its parent
        for ($j = $i; $j < $n && $tokens[$j] !== '{' && $tokens[$j] !== ';'; $j++);
        if ($j >= $n || $tokens[$j] === ';') { continue; } // abstract / interface method
        $cc = 1; $d = 0;
        for ($k = $j; $k < $n; $k++) {
            $u = $tokens[$k];
            if ($u === '{' || (is_array($u) && in_array($u[0], [T_CURLY_OPEN, T_DOLLAR_OPEN_CURLY_BRACES], true))) { $d++; }
            elseif ($u === '}') { if (--$d === 0) { break; } }
            elseif ($u === '?') {
                // ternary, not a nullable type (?Foo after '(' ',' ':' or a modifier)
                $p = $k - 1;
                while ($p >= 0 && is_array($tokens[$p]) && $tokens[$p][0] === T_WHITESPACE) { $p--; }
                $prev = $tokens[$p] ?? null;
                $typed = in_array($prev, ['(', ',', ':'], true) || (is_array($prev) && in_array($prev[0],
                    [T_PUBLIC, T_PROTECTED, T_PRIVATE, T_READONLY, T_STATIC, T_VAR], true));
                if (!$typed) { $cc++; }
            }
            elseif (is_array($u) && in_array($u[0], $decision, true)) { $cc++; }
        }
        $result[($class ? "$class::" : '') . $name] = $cc;
    }
    $out[$file] = $result;
}
echo json_encode($out, JSON_UNESCAPED_SLASHES), "\n";
