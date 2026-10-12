import Darwin
import Foundation

@main
struct LogSinkIntegrationTests {
    static func main() throws {
        let logURL = FileLogger.shared.currentLogFileURL()
        let root = logURL.deletingLastPathComponent().deletingLastPathComponent().deletingLastPathComponent()
        precondition(root.lastPathComponent.hasPrefix("FluidASRBaseline-"), "Test must not write to user Library")
        defer { try? FileManager.default.removeItem(at: root) }
        let directory = logURL.deletingLastPathComponent()
        try FileManager.default.setAttributes([.posixPermissions: 0o755], ofItemAtPath: directory.path)
        try FileManager.default.setAttributes([.posixPermissions: 0o644], ofItemAtPath: logURL.path)
        for index in 0..<30 {
            DebugLogger.shared.info("step=\(index) api_key=synthetic-secret-\(index)", source: "PrivacyTests")
        }
        DebugLogger.shared.error("status=503 prompt=synthetic private prompt", source: "PrivacyTests")
        DebugLogger.shared.flush()
        FileLogger.shared.appendSync(line: "Authorization: Bearer synthetic-access-secret")
        let log = try String(contentsOf: logURL, encoding: .utf8)
        precondition(!log.contains("synthetic-secret") && !log.contains("synthetic private prompt"))
        precondition(!log.contains("synthetic-access-secret"))
        precondition(log.contains("[CONTEXT]") && log.contains("[STACK]"))
        precondition(log.components(separatedBy: "[BREADCRUMB]").count - 1 == 20, "Breadcrumbs must be bounded")
        let permissions = try FileManager.default.attributesOfItem(atPath: logURL.path)[.posixPermissions] as? Int
        precondition(permissions == 0o600, "Existing support log permissions must be repaired")
        let directoryPermissions = try FileManager.default.attributesOfItem(atPath: directory.path)[.posixPermissions] as? Int
        precondition(directoryPermissions == 0o700, "Existing log directory permissions must be repaired")
        FileLogger.writeCrashLineDirect("api_key=synthetic-crash-secret")
        FileLogger.writeCrashSignalLine(SIGTRAP)
        let crash = try String(contentsOf: logURL.deletingLastPathComponent().appendingPathComponent("Fluid.crash.log"), encoding: .utf8)
        precondition(!crash.contains("synthetic-crash-secret"))
        precondition(crash.contains("SIGTRAP"))
        print("PASS: real log sinks, strict concurrency, redaction, bounded breadcrumbs, caller stacks, private permissions and crash sink")
    }
}
