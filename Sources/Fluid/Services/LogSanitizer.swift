import Foundation

/// Defense in depth at log sinks. Never use this as permission to log user content.
nonisolated enum LogSanitizer {
    private struct Rule: Sendable {
        let expression: NSRegularExpression
        let replacement: String

        init(_ pattern: String, replacement: String) {
            guard let expression = try? NSRegularExpression(pattern: pattern) else {
                preconditionFailure("Invalid log redaction expression")
            }
            self.expression = expression
            self.replacement = replacement
        }
    }

    private static let rules: [Rule] = [
        Rule(#"(?i)(https?://)[^/\s:@]+:[^/\s@]+@"#, replacement: "$1[redacted]@"),
        Rule(#"(?i)(\b(?:authorization|set-cookie|cookie)\b["']?\s*[:=]\s*)[^\r\n]*"#, replacement: "$1[redacted]"),
        Rule(#"(?i)(\b(?:rawText|processedText|originalText|finalText|transcript|prompt|content|audioBase64|windowTitle)\b["']?\s*[:=]\s*)("(?:[^"\\]|\\.)*"|'[^']*'|[^\r\n]*)"#, replacement: "$1\"[redacted]\""),
        Rule(#"(?i)((?:transcribed(?:\s+text)?|raw\s+text|recognized\s+text|AI\s+(?:response|prompt))\s*[:=]\s*)[^\r\n]*"#, replacement: "$1[redacted]"),
        Rule(#"(?i)(\b(?:api[_-]?key|access[_-]?token|refresh[_-]?token|authorization|password|secret|token|cookie)\b["']?\s*[:=]\s*["']?)(?:Bearer\s+)?[^\s,"';}\]\[]+"#, replacement: "$1[redacted]"),
        Rule(#"(?i)(\bBearer\s+)[A-Za-z0-9._~+/=-]+"#, replacement: "$1[redacted]"),
        Rule(#"\b(?:sk|ak|pk)[-_][A-Za-z0-9_-]{16,}\b"#, replacement: "[redacted]"),
        Rule(#"\beyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\b"#, replacement: "[redacted]"),
        Rule(#"(?i)\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b"#, replacement: "[email]"),
        Rule(#"(?:file://)?/(?:Users|home)/[^\r\n"']+"#, replacement: "[private-path]"),
    ]

    static func sanitize(_ input: String) -> String {
        self.rules.reduce(input) { value, rule in
            rule.expression.stringByReplacingMatches(
                in: value,
                range: NSRange(value.startIndex..., in: value),
                withTemplate: rule.replacement
            )
        }
    }
}
