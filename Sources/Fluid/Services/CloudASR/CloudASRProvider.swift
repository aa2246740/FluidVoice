import Foundation

/// TranscriptionProvider backed by a cloud speech-to-text API.
final class CloudASRProvider: TranscriptionProvider {
    let vendor: CloudASRVendor
    private let settings: CloudASRSettings
    private let client: CloudASRClient

    init(vendor: CloudASRVendor, settings: CloudASRSettings = .shared, client: CloudASRClient = CloudASRClient()) {
        self.vendor = vendor
        self.settings = settings
        self.client = client
    }

    var name: String {
        self.vendor.displayName
    }

    var isAvailable: Bool {
        true
    }

    private(set) var isReady: Bool = false

    func prepare(progressHandler: ((ModelPreparationProgress) -> Void)?) async throws {
        guard self.settings.hasCredentials(for: self.vendor) else {
            self.isReady = false
            throw CloudASRError.missingCredentials(self.vendor)
        }
        self.isReady = true
    }

    func modelsExistOnDisk() -> Bool {
        true
    }

    var shouldClearCacheAfterCancellation: Bool {
        false
    }

    /// Live previews would bill a request every few hundred milliseconds; only the final pass hits the network.
    func transcribeStreaming(_ samples: [Float]) async throws -> ASRTranscriptionResult {
        ASRTranscriptionResult(text: "", confidence: 0)
    }

    func transcribe(_ samples: [Float]) async throws -> ASRTranscriptionResult {
        guard samples.count >= 16_000 / 4 else {
            return ASRTranscriptionResult(text: "", confidence: 0)
        }
        let configuration = self.settings.configuration(for: self.vendor)
        let started = Date()
        let text = try await self.client.transcribe(samples: samples, configuration: configuration)
        let elapsed = Int(Date().timeIntervalSince(started) * 1000)
        DebugLogger.shared.info(
            "CloudASRProvider[\(self.vendor.rawValue)]: \(samples.count) samples -> \(text.count) chars in \(elapsed)ms",
            source: "CloudASR"
        )
        return ASRTranscriptionResult(text: text, confidence: 1.0)
    }
}
