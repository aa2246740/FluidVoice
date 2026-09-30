import Foundation

/// Cloud speech-to-text vendors reachable over HTTPS.
nonisolated enum CloudASRVendor: String, CaseIterable, Codable, Sendable {
    case volcengine
    case dashscope
    case fishAudio = "fishaudio"

    var displayName: String {
        switch self {
        case .volcengine: return "Volcengine Doubao ASR"
        case .dashscope: return "Alibaba Bailian Qwen3-ASR"
        case .fishAudio: return "Fish Audio ASR"
        }
    }

    var consoleURL: URL? {
        switch self {
        case .volcengine: return URL(string: "https://console.volcengine.com/speech/new/setting/apikeys")
        case .dashscope: return URL(string: "https://bailian.console.aliyun.com/?tab=model#/api-key")
        case .fishAudio: return URL(string: "https://fish.audio/app/api-keys")
        }
    }
}

nonisolated enum CloudASRRegion: String, CaseIterable, Codable, Sendable {
    case china = "cn"
    case international = "intl"
}

/// Credentials and options for a single cloud ASR request.
nonisolated struct CloudASRConfiguration: Equatable, Sendable {
    var vendor: CloudASRVendor
    /// Volcengine new-console API key, DashScope API key, or Fish Audio API key.
    var apiKey: String = ""
    /// Volcengine legacy-console App ID. When set together with `accessToken`, legacy auth headers are used.
    var appID: String = ""
    /// Volcengine legacy-console Access Token.
    var accessToken: String = ""
    /// Model identifier. Volcengine: resource id; DashScope: model name. Unused for Fish Audio.
    var model: String = ""
    var region: CloudASRRegion = .china
    /// Optional language hint (ISO code such as `zh`, `en`). Empty means auto-detect.
    var language: String = ""
    var baseURLOverride: String = ""

    static func defaultModel(for vendor: CloudASRVendor) -> String {
        switch vendor {
        case .volcengine: return "volc.bigasr.auc_turbo"
        case .dashscope: return "qwen3-asr-flash"
        case .fishAudio: return ""
        }
    }

    var resolvedModel: String {
        let trimmed = self.model.trimmingCharacters(in: .whitespacesAndNewlines)
        return trimmed.isEmpty ? Self.defaultModel(for: self.vendor) : trimmed
    }

    var usesVolcengineLegacyAuth: Bool {
        !self.appID.trimmed.isEmpty && !self.accessToken.trimmed.isEmpty
    }

    var hasCredentials: Bool {
        switch self.vendor {
        case .volcengine: return !self.apiKey.trimmed.isEmpty || self.usesVolcengineLegacyAuth
        case .dashscope, .fishAudio: return !self.apiKey.trimmed.isEmpty
        }
    }

    var endpoint: URL? {
        let override = self.baseURLOverride.trimmed
        if !override.isEmpty {
            return URL(string: override)
        }
        switch self.vendor {
        case .volcengine:
            return URL(string: "https://openspeech.bytedance.com/api/v3/auc/bigmodel/recognize/flash")
        case .dashscope:
            let host = self.region == .international ? "dashscope-intl.aliyuncs.com" : "dashscope.aliyuncs.com"
            return URL(string: "https://\(host)/compatible-mode/v1/chat/completions")
        case .fishAudio:
            return URL(string: "https://api.fish.audio/v1/asr")
        }
    }
}

nonisolated enum CloudASRError: LocalizedError, Equatable {
    case missingCredentials(CloudASRVendor)
    case invalidEndpoint
    case http(status: Int, message: String)
    case vendor(code: String, message: String)
    case malformedResponse(String)

    var errorDescription: String? {
        switch self {
        case let .missingCredentials(vendor):
            return "\(vendor.displayName): API key is not configured. Open Voice Engine settings and enter your key."
        case .invalidEndpoint:
            return "Cloud ASR endpoint URL is invalid."
        case let .http(status, message):
            return "Cloud ASR request failed (HTTP \(status)): \(message)"
        case let .vendor(code, message):
            return "Cloud ASR error \(code): \(message)"
        case let .malformedResponse(detail):
            return "Cloud ASR returned an unexpected response: \(detail)"
        }
    }
}

/// Stateless HTTP client for cloud speech recognition.
nonisolated struct CloudASRClient: Sendable {
    typealias Transport = @Sendable (URLRequest) async throws -> (Data, URLResponse)

    static let volcengineSuccessCode = "20000000"
    static let volcengineSilenceCode = "20000003"

    let transport: Transport

    init(transport: Transport? = nil) {
        if let transport {
            self.transport = transport
        } else {
            let session = URLSession(configuration: .ephemeral)
            self.transport = { request in try await session.data(for: request) }
        }
    }

    func transcribe(samples: [Float], sampleRate: Int = 16_000, configuration: CloudASRConfiguration) async throws -> String {
        try await self.transcribe(wav: Self.wavData(samples: samples, sampleRate: sampleRate), configuration: configuration)
    }

    func transcribe(wav: Data, configuration: CloudASRConfiguration) async throws -> String {
        let request = try Self.makeRequest(wav: wav, configuration: configuration)
        let (data, response) = try await self.transport(request)
        return try Self.parseResponse(data: data, response: response, vendor: configuration.vendor)
    }

    // MARK: - Request Building

    static func makeRequest(wav: Data, configuration: CloudASRConfiguration, requestID: String = UUID().uuidString) throws -> URLRequest {
        guard configuration.hasCredentials else { throw CloudASRError.missingCredentials(configuration.vendor) }
        guard let url = configuration.endpoint else { throw CloudASRError.invalidEndpoint }

        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.timeoutInterval = 60

        switch configuration.vendor {
        case .volcengine:
            request.setValue("application/json", forHTTPHeaderField: "Content-Type")
            if configuration.usesVolcengineLegacyAuth {
                request.setValue(configuration.appID.trimmed, forHTTPHeaderField: "X-Api-App-Key")
                request.setValue(configuration.accessToken.trimmed, forHTTPHeaderField: "X-Api-Access-Key")
            } else {
                request.setValue(configuration.apiKey.trimmed, forHTTPHeaderField: "X-Api-Key")
            }
            request.setValue(configuration.resolvedModel, forHTTPHeaderField: "X-Api-Resource-Id")
            request.setValue(requestID, forHTTPHeaderField: "X-Api-Request-Id")
            request.setValue("-1", forHTTPHeaderField: "X-Api-Sequence")
            var audio: [String: Any] = ["data": wav.base64EncodedString(), "format": "wav"]
            if let language = self.volcengineLanguage(configuration.language) {
                audio["language"] = language
            }
            let uid = configuration.usesVolcengineLegacyAuth ? configuration.appID.trimmed : "fluidvoice"
            let body: [String: Any] = [
                "user": ["uid": uid],
                "audio": audio,
                "request": ["model_name": "bigmodel", "enable_itn": true, "enable_punc": true],
            ]
            request.httpBody = try JSONSerialization.data(withJSONObject: body)

        case .dashscope:
            request.setValue("application/json", forHTTPHeaderField: "Content-Type")
            request.setValue("Bearer \(configuration.apiKey.trimmed)", forHTTPHeaderField: "Authorization")
            var asrOptions: [String: Any] = ["enable_itn": true]
            let language = configuration.language.trimmed
            if !language.isEmpty {
                asrOptions["language"] = language
            }
            let body: [String: Any] = [
                "model": configuration.resolvedModel,
                "messages": [[
                    "role": "user",
                    "content": [[
                        "type": "input_audio",
                        "input_audio": ["data": "data:audio/wav;base64,\(wav.base64EncodedString())"],
                    ]],
                ]],
                "stream": false,
                "asr_options": asrOptions,
            ]
            request.httpBody = try JSONSerialization.data(withJSONObject: body)

        case .fishAudio:
            let boundary = "FluidVoice-\(requestID)"
            request.setValue("multipart/form-data; boundary=\(boundary)", forHTTPHeaderField: "Content-Type")
            request.setValue("Bearer \(configuration.apiKey.trimmed)", forHTTPHeaderField: "Authorization")
            var fields = [("ignore_timestamps", "true")]
            let language = configuration.language.trimmed
            if !language.isEmpty {
                fields.append(("language", language))
            }
            request.httpBody = self.multipartBody(boundary: boundary, fields: fields, fileField: "audio", fileName: "audio.wav", mimeType: "audio/wav", fileData: wav)
        }

        return request
    }

    /// Volcengine expects locale-style codes such as `zh-CN`; nil lets the service auto-detect.
    static func volcengineLanguage(_ language: String) -> String? {
        let trimmed = language.trimmed
        guard !trimmed.isEmpty else { return nil }
        if trimmed.contains("-") {
            return trimmed
        }
        let map = [
            "zh": "zh-CN", "en": "en-US", "ja": "ja-JP", "ko": "ko-KR", "es": "es-MX", "pt": "pt-BR",
            "de": "de-DE", "fr": "fr-FR", "it": "it-IT", "ru": "ru-RU", "id": "id-ID", "yue": "yue-CN",
        ]
        return map[trimmed.lowercased()]
    }

    static func multipartBody(boundary: String, fields: [(String, String)], fileField: String, fileName: String, mimeType: String, fileData: Data) -> Data {
        var body = Data()
        func append(_ string: String) {
            body.append(Data(string.utf8))
        }
        for (name, value) in fields {
            append("--\(boundary)\r\nContent-Disposition: form-data; name=\"\(name)\"\r\n\r\n\(value)\r\n")
        }
        append("--\(boundary)\r\nContent-Disposition: form-data; name=\"\(fileField)\"; filename=\"\(fileName)\"\r\nContent-Type: \(mimeType)\r\n\r\n")
        body.append(fileData)
        append("\r\n--\(boundary)--\r\n")
        return body
    }

    // MARK: - Response Parsing

    static func parseResponse(data: Data, response: URLResponse, vendor: CloudASRVendor) throws -> String {
        let http = response as? HTTPURLResponse
        let status = http?.statusCode ?? 200
        let json = (try? JSONSerialization.jsonObject(with: data) as? [String: Any]) ?? [:]

        if vendor == .volcengine, let code = http?.value(forHTTPHeaderField: "X-Api-Status-Code") {
            if code == Self.volcengineSilenceCode {
                return ""
            }
            if code != Self.volcengineSuccessCode {
                let message = http?.value(forHTTPHeaderField: "X-Api-Message") ?? Self.errorMessage(from: json, data: data)
                throw CloudASRError.vendor(code: code, message: message)
            }
        }

        guard (200..<300).contains(status) else {
            throw CloudASRError.http(status: status, message: Self.errorMessage(from: json, data: data))
        }
        guard !json.isEmpty else {
            throw CloudASRError.malformedResponse(Self.preview(data, limit: 200))
        }

        let text: String?
        switch vendor {
        case .volcengine:
            text = (json["result"] as? [String: Any])?["text"] as? String
        case .dashscope:
            let choices = json["choices"] as? [[String: Any]]
            let message = choices?.first?["message"] as? [String: Any]
            if let content = message?["content"] as? String {
                text = content
            } else if let parts = message?["content"] as? [[String: Any]] {
                text = parts.compactMap { $0["text"] as? String }.joined()
            } else {
                text = nil
            }
        case .fishAudio:
            text = json["text"] as? String
        }

        guard let text else {
            throw CloudASRError.malformedResponse(Self.preview(data, limit: 200))
        }
        return text.trimmingCharacters(in: .whitespacesAndNewlines)
    }

    private static func preview(_ data: Data, limit: Int) -> String {
        String(bytes: data.prefix(limit), encoding: .utf8) ?? "<\(data.count) bytes>"
    }

    private static func errorMessage(from json: [String: Any], data: Data) -> String {
        if let error = json["error"] as? [String: Any], let message = error["message"] as? String {
            return message
        }
        for key in ["message", "detail", "msg", "error"] {
            if let message = json[key] as? String {
                return message
            }
        }
        let raw = Self.preview(data, limit: 300).trimmed
        return raw.isEmpty ? "empty response" : raw
    }

    // MARK: - Audio Encoding

    /// Encodes mono float samples in [-1, 1] as 16-bit PCM WAV.
    static func wavData(samples: [Float], sampleRate: Int = 16_000) -> Data {
        let bytesPerSample = 2
        let dataSize = samples.count * bytesPerSample
        var data = Data(capacity: 44 + dataSize)
        func appendUInt32(_ value: UInt32) {
            withUnsafeBytes(of: value.littleEndian) { data.append(contentsOf: $0) }
        }
        func appendUInt16(_ value: UInt16) {
            withUnsafeBytes(of: value.littleEndian) { data.append(contentsOf: $0) }
        }

        data.append(Data("RIFF".utf8))
        appendUInt32(UInt32(36 + dataSize))
        data.append(Data("WAVEfmt ".utf8))
        appendUInt32(16)
        appendUInt16(1)
        appendUInt16(1)
        appendUInt32(UInt32(sampleRate))
        appendUInt32(UInt32(sampleRate * bytesPerSample))
        appendUInt16(UInt16(bytesPerSample))
        appendUInt16(16)
        data.append(Data("data".utf8))
        appendUInt32(UInt32(dataSize))
        for sample in samples {
            let clamped = max(-1.0, min(1.0, sample))
            appendUInt16(UInt16(bitPattern: Int16(clamped * Float(Int16.max))))
        }
        return data
    }
}

private extension String {
    nonisolated var trimmed: String {
        self.trimmingCharacters(in: .whitespacesAndNewlines)
    }
}
