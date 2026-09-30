import Foundation

@main
struct CloudASRClientTests {
    static var failures = 0

    static func check(_ condition: @autoclosure () -> Bool, _ message: String) {
        if !condition() {
            self.failures += 1
            print("FAIL: \(message)")
        }
    }

    static func json(_ request: URLRequest) -> [String: Any] {
        guard let body = request.httpBody, let object = try? JSONSerialization.jsonObject(with: body) as? [String: Any] else { return [:] }
        return object
    }

    static let testURL = URL(fileURLWithPath: "/")

    static func response(_ status: Int, headers: [String: String] = [:]) -> URLResponse {
        HTTPURLResponse(url: self.testURL, statusCode: status, httpVersion: nil, headerFields: headers) ?? URLResponse()
    }

    static func request(_ wav: Data, _ configuration: CloudASRConfiguration, requestID: String = "rid") -> URLRequest {
        do {
            return try CloudASRClient.makeRequest(wav: wav, configuration: configuration, requestID: requestID)
        } catch {
            self.check(false, "makeRequest threw \(error)")
            return URLRequest(url: self.testURL)
        }
    }

    static func text(_ data: Data) -> String {
        String(bytes: data, encoding: .isoLatin1) ?? ""
    }

    static func main() async {
        // WAV encoding
        let wav = CloudASRClient.wavData(samples: [0, 1, -1, 0.5], sampleRate: 16_000)
        self.check(wav.count == 44 + 8, "wav size")
        self.check(self.text(wav.prefix(4)) == "RIFF", "RIFF header")
        self.check(self.text(wav[8..<16]) == "WAVEfmt ", "WAVE fmt")
        let sampleRate = wav[24..<28].withUnsafeBytes { $0.loadUnaligned(as: UInt32.self) }
        self.check(UInt32(littleEndian: sampleRate) == 16_000, "sample rate")
        let second = wav[46..<48].withUnsafeBytes { $0.loadUnaligned(as: Int16.self) }
        self.check(Int16(littleEndian: second) == Int16.max, "max sample")

        // Volcengine request
        var volc = CloudASRConfiguration(vendor: .volcengine)
        volc.apiKey = " key-123 "
        volc.language = "zh"
        let volcRequest = self.request(wav, volc)
        self.check(volcRequest.url?.absoluteString == "https://openspeech.bytedance.com/api/v3/auc/bigmodel/recognize/flash", "volc url")
        self.check(volcRequest.value(forHTTPHeaderField: "X-Api-Key") == "key-123", "volc api key")
        self.check(volcRequest.value(forHTTPHeaderField: "X-Api-Resource-Id") == "volc.bigasr.auc_turbo", "volc resource")
        self.check(volcRequest.value(forHTTPHeaderField: "X-Api-Request-Id") == "rid", "volc request id")
        let volcAudio = self.json(volcRequest)["audio"] as? [String: Any]
        self.check(volcAudio?["data"] as? String == wav.base64EncodedString(), "volc audio base64")
        self.check(volcAudio?["language"] as? String == "zh-CN", "volc language")

        var volcLegacy = CloudASRConfiguration(vendor: .volcengine)
        volcLegacy.appID = "app"
        volcLegacy.accessToken = "token"
        let legacyRequest = self.request(wav, volcLegacy)
        self.check(legacyRequest.value(forHTTPHeaderField: "X-Api-App-Key") == "app", "volc legacy app key")
        self.check(legacyRequest.value(forHTTPHeaderField: "X-Api-Access-Key") == "token", "volc legacy access key")
        self.check(legacyRequest.value(forHTTPHeaderField: "X-Api-Key") == nil, "volc legacy no api key")

        // DashScope request
        var dash = CloudASRConfiguration(vendor: .dashscope)
        dash.apiKey = "sk-x"
        dash.region = .international
        let dashRequest = self.request(wav, dash)
        self.check(dashRequest.url?.absoluteString == "https://dashscope-intl.aliyuncs.com/compatible-mode/v1/chat/completions", "dash url")
        self.check(dashRequest.value(forHTTPHeaderField: "Authorization") == "Bearer sk-x", "dash auth")
        let dashBody = self.json(dashRequest)
        self.check(dashBody["model"] as? String == "qwen3-asr-flash", "dash model")
        let content = ((dashBody["messages"] as? [[String: Any]])?.first?["content"] as? [[String: Any]])?.first
        let audioData = (content?["input_audio"] as? [String: Any])?["data"] as? String
        self.check(audioData?.hasPrefix("data:audio/wav;base64,") == true, "dash data uri")

        // Fish Audio request
        var fish = CloudASRConfiguration(vendor: .fishAudio)
        fish.apiKey = "fa"
        fish.language = "en"
        let fishRequest = self.request(wav, fish, requestID: "b")
        self.check(fishRequest.url?.absoluteString == "https://api.fish.audio/v1/asr", "fish url")
        self.check(fishRequest.value(forHTTPHeaderField: "Content-Type") == "multipart/form-data; boundary=FluidVoice-b", "fish content type")
        let fishBody = self.text(fishRequest.httpBody ?? Data())
        self.check(fishBody.contains("name=\"audio\"; filename=\"audio.wav\""), "fish audio part")
        self.check(fishBody.contains("name=\"language\"\r\n\r\nen\r\n"), "fish language part")
        self.check(fishBody.hasSuffix("--FluidVoice-b--\r\n"), "fish closing boundary")

        // Missing credentials
        do {
            _ = try CloudASRClient.makeRequest(wav: wav, configuration: CloudASRConfiguration(vendor: .fishAudio))
            self.check(false, "missing key should throw")
        } catch {
            self.check(error as? CloudASRError == .missingCredentials(.fishAudio), "missing key error")
        }

        // Response parsing
        let ok = ["X-Api-Status-Code": "20000000"]
        let volcText = try? CloudASRClient.parseResponse(data: Data(#"{"result":{"text":" 你好 "}}"#.utf8), response: self.response(200, headers: ok), vendor: .volcengine)
        self.check(volcText == "你好", "volc parse")
        let silent = try? CloudASRClient.parseResponse(data: Data(), response: self.response(200, headers: ["X-Api-Status-Code": "20000003"]), vendor: .volcengine)
        self.check(silent == "", "volc silence")
        do {
            _ = try CloudASRClient.parseResponse(data: Data(), response: self.response(200, headers: ["X-Api-Status-Code": "45000001", "X-Api-Message": "bad"]), vendor: .volcengine)
            self.check(false, "volc error should throw")
        } catch {
            self.check(error as? CloudASRError == .vendor(code: "45000001", message: "bad"), "volc error")
        }
        let dashText = try? CloudASRClient.parseResponse(data: Data(#"{"choices":[{"message":{"content":"hello"}}]}"#.utf8), response: self.response(200), vendor: .dashscope)
        self.check(dashText == "hello", "dash parse")
        do {
            _ = try CloudASRClient.parseResponse(data: Data(#"{"error":{"message":"Invalid API-key"}}"#.utf8), response: self.response(401), vendor: .dashscope)
            self.check(false, "dash 401 should throw")
        } catch {
            self.check(error as? CloudASRError == .http(status: 401, message: "Invalid API-key"), "dash 401")
        }
        let fishText = try? CloudASRClient.parseResponse(data: Data(#"{"text":"hi","duration":1.0}"#.utf8), response: self.response(200), vendor: .fishAudio)
        self.check(fishText == "hi", "fish parse")

        // Transport injection
        let client = CloudASRClient { _ in
            (Data(#"{"text":"via transport"}"#.utf8), self.response(200))
        }
        let transported = try? await client.transcribe(samples: [0, 0], configuration: fish)
        self.check(transported == "via transport", "transport")

        if self.failures > 0 {
            print("\(self.failures) failure(s)")
            exit(1)
        }
        print("CloudASRClientTests: all passed")
    }
}
