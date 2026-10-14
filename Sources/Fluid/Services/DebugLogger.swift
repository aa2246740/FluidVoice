import Foundation

final nonisolated class DebugLogger: @unchecked Sendable {
    static let shared = DebugLogger()

    /// Production builds exclude verbose diagnostics; local Release investigations
    /// explicitly opt in with FLUIDVOICE_DIAGNOSTICS at compile time.
    static let diagnosticsEnabled: Bool = {
        #if DEBUG || FLUIDVOICE_DIAGNOSTICS
        true
        #else
        false
        #endif
    }()

    /// Request-local correlation survives actor hops without mutable global state.
    /// Capture explicitly before handing work to a DispatchQueue or detached task.
    @TaskLocal static var pipelineID: String?

    private let queue = DispatchQueue(label: "debug.logger", qos: .utility)
    private var breadcrumbs: [String] = []
    private let diagnosticSessionID = UUID().uuidString

    private static let logFormatter: DateFormatter = {
        let formatter = DateFormatter()
        formatter.dateFormat = "HH:mm:ss.SSS"
        formatter.locale = Locale(identifier: "en_US_POSIX")
        formatter.timeZone = TimeZone.current
        return formatter
    }()

    enum LogLevel: String {
        case info = "INFO"
        case warning = "WARN"
        case error = "ERROR"
        case debug = "DEBUG"
    }

    private init() {}

    /// A support-export/test barrier; ordinary logging stays asynchronous.
    func flush() {
        self.queue.sync { FileLogger.shared.flush() }
    }

    func log(_ message: @autoclosure () -> String, level: LogLevel = .info, source: String = "App") {
        guard level != .debug || Self.diagnosticsEnabled else { return }
        let message = message()
        let pipelineID = Self.pipelineID
        let stack = level == .error ? Thread.callStackSymbols : []
        self.queue.async {
            self.write(message, level: level, source: source, pipelineID: pipelineID, stack: stack)
        }
    }

    /// Defers expensive diagnostic string construction until after latency-sensitive
    /// work has continued on the caller's executor.
    func logLazy(
        level: LogLevel = .info,
        source: String = "App",
        _ message: @escaping @Sendable () -> String
    ) {
        guard level != .debug || Self.diagnosticsEnabled else { return }
        let pipelineID = Self.pipelineID
        let stack = level == .error ? Thread.callStackSymbols : []
        self.queue.async {
            self.write(message(), level: level, source: source, pipelineID: pipelineID, stack: stack)
        }
    }

    private func write(_ message: String, level: LogLevel, source: String, pipelineID: String?, stack: [String]) {
        let timestampString = Self.logFormatter.string(from: Date())
        let formattedLine = self.formatLogLine(
            timestamp: timestampString,
            level: level,
            source: source,
            message: message,
            pipelineID: pipelineID
        )

        // Context stays on-device and uses a per-run identifier, not user identity.
        if level == .error {
            let version = Bundle.main.object(forInfoDictionaryKey: "CFBundleShortVersionString") as? String ?? "unknown"
            FileLogger.shared.append(line: "[CONTEXT] session=\(self.diagnosticSessionID) version=\(version) OS=\(ProcessInfo.processInfo.operatingSystemVersionString)")
            for breadcrumb in self.breadcrumbs {
                FileLogger.shared.append(line: "[BREADCRUMB] \(breadcrumb)")
            }
            for frame in stack.prefix(30) {
                FileLogger.shared.append(line: "[STACK] \(frame)")
            }
        }
        self.breadcrumbs.append(formattedLine)
        if self.breadcrumbs.count > 20 { self.breadcrumbs.removeFirst(self.breadcrumbs.count - 20) }

        // Retain ordinary support logs in production; verbose diagnostics are gated before enqueueing.
        FileLogger.shared.append(line: formattedLine)
        #if DEBUG || FLUIDVOICE_DIAGNOSTICS
        print(formattedLine)
        #endif
    }

    private func formatLogLine(timestamp: String, level: LogLevel, source: String, message: String, pipelineID: String?) -> String {
        let correlation = pipelineID.map { "pipelineID=\($0) " } ?? ""
        return LogSanitizer.sanitize("[\(timestamp)] [\(level.rawValue)] [\(source)] \(correlation)\(message)")
    }
}

// Convenience functions for easier logging
nonisolated extension DebugLogger {
    func info(_ message: String, source: String = "App") {
        self.log(message, level: .info, source: source)
    }

    func benchmark(_ marker: String, message: @autoclosure () -> String, source: String = "Benchmark") {
        guard Self.diagnosticsEnabled else { return }
        let now = ProcessInfo.processInfo.systemUptime
        self.info("\(marker) t=\(String(format: "%.6f", now)) \(message())", source: source)
    }

    func warning(_ message: String, source: String = "App") {
        self.log(message, level: .warning, source: source)
    }

    func error(_ message: String, source: String = "App") {
        self.log(message, level: .error, source: source)
    }

    func debug(_ message: @autoclosure () -> String, source: String = "App") {
        guard Self.diagnosticsEnabled else { return }
        self.log(message(), level: .debug, source: source)
    }
}
