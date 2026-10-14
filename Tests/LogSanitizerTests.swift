import Foundation

@main
struct LogSanitizerTests {
    static func main() {
        let cases: [(String, String)] = [
            ("Authorization: Bearer sensitive-access-token", "sensitive-access-token"),
            (#"{"api_key":"secret-provider-key"}"#, "secret-provider-key"),
            ("url=https://example.test/?access_token=query-secret&other=1", "query-secret"),
            ("PASSWORD=secret-password", "secret-password"),
            ("Cookie: secret-session-cookie", "secret-session-cookie"),
            ("Cookie: session=first-secret; csrf=second-secret", "second-secret"),
            ("Authorization: Basic c2VjcmV0LXVzZXItcGFzcw==", "c2VjcmV0LXVzZXItcGFzcw=="),
            ("https://alice:secret-password@example.test/path", "secret-password"),
            ("key sk-123456789012345678901234567890", "sk-123456789012345678901234567890"),
            ("Bearer eyJ1234567890.abcdefghijk.abcdefghijkl", "eyJ1234567890.abcdefghijk.abcdefghijkl"),
            ("email person@example.test", "person@example.test"),
            (#"{"rawText":"private voice transcript"}"#, "private voice transcript"),
            ("prompt=private multi word content\nstatus=400", "private multi word content"),
            ("Transcribed text: private voice content", "private voice content"),
            (#"file="/Users/person/Documents/private-file.txt""#, "private-file.txt"),
            ("transcript=中文私人听写内容", "中文私人听写内容"),
        ]
        for (input, secret) in cases {
            let sanitized = LogSanitizer.sanitize(input)
            precondition(!sanitized.contains(secret), "Sensitive field was not redacted")
            precondition(LogSanitizer.sanitize(sanitized) == sanitized, "Redaction must be idempotent")
        }
        let safe = "pipelineID=abc-123 durationMs=123.5 model=whisper-small status=503"
        precondition(LogSanitizer.sanitize(safe) == safe, "Preserve technical diagnostics")
        precondition(LogSanitizer.sanitize("").isEmpty)
        let multiline = LogSanitizer.sanitize("api_key=secret-value\nstatus=503")
        precondition(multiline.contains("status=503"), "Keep unrelated lines")
        print("PASS: secret, auth, cookie, URL, email, transcript, Unicode, path, idempotence and diagnostic retention")
    }
}
