import AppKit
import SwiftUI

/// Sheet for entering credentials and options for a cloud speech-to-text vendor.
struct CloudASRConfigView: View {
    let vendor: CloudASRVendor
    let onSave: (CloudASRConfiguration) -> Void

    @Environment(\.dismiss) private var dismiss
    @State private var configuration: CloudASRConfiguration
    @State private var testStatus: String?
    @State private var testSucceeded = false
    @State private var isTesting = false

    init(vendor: CloudASRVendor, onSave: @escaping (CloudASRConfiguration) -> Void) {
        self.vendor = vendor
        self.onSave = onSave
        self._configuration = State(initialValue: CloudASRSettings.shared.configuration(for: vendor))
    }

    var body: some View {
        VStack(alignment: .leading, spacing: 14) {
            HStack {
                Text(self.vendor.displayName.fluidLocalized)
                    .font(.headline)
                Spacer()
                if let url = self.vendor.consoleURL {
                    Button("Get API Key") { NSWorkspace.shared.open(url) }
                        .buttonStyle(.link)
                }
            }

            Form {
                SecureField("API Key", text: self.$configuration.apiKey)

                if self.vendor == .volcengine {
                    Text("New Volcengine console: paste the API Key. Legacy console: leave API Key empty and fill App ID + Access Token.")
                        .font(.caption)
                        .foregroundStyle(.secondary)
                    TextField("App ID (legacy, optional)", text: self.$configuration.appID)
                    SecureField("Access Token (legacy, optional)", text: self.$configuration.accessToken)
                    TextField("Resource ID", text: self.$configuration.model, prompt: Text(CloudASRConfiguration.defaultModel(for: .volcengine).fluidLocalized))
                }

                if self.vendor == .dashscope {
                    Picker("Region", selection: self.$configuration.region) {
                        Text("China (Beijing)").tag(CloudASRRegion.china)
                        Text("International (Singapore)").tag(CloudASRRegion.international)
                    }
                    TextField("Model", text: self.$configuration.model, prompt: Text(CloudASRConfiguration.defaultModel(for: .dashscope).fluidLocalized))
                }

                TextField("Language (optional, e.g. zh, en)", text: self.$configuration.language, prompt: Text("Auto detect"))
                TextField("Endpoint override (optional)", text: self.$configuration.baseURLOverride, prompt: Text(self.defaultEndpoint.fluidLocalized))
            }
            .formStyle(.grouped)

            Text("Keys are stored in the macOS Keychain. Audio is uploaded to the vendor when you finish dictating; usage is billed to your account.")
                .font(.caption)
                .foregroundStyle(.secondary)

            if let testStatus {
                Text(testStatus.fluidLocalized)
                    .font(.caption)
                    .foregroundStyle(self.testSucceeded ? Color.green : Color.red)
                    .textSelection(.enabled)
            }

            HStack {
                Button((self.isTesting ? "Testing…" : "Test Connection").fluidLocalized) {
                    self.runTest()
                }
                .disabled(self.isTesting || !self.configuration.hasCredentials)
                Spacer()
                Button("Cancel") { self.dismiss() }
                    .keyboardShortcut(.cancelAction)
                Button("Save") {
                    self.onSave(self.configuration)
                    self.dismiss()
                }
                .keyboardShortcut(.defaultAction)
            }
        }
        .padding(20)
        .frame(width: 480)
    }

    private var defaultEndpoint: String {
        var copy = self.configuration
        copy.baseURLOverride = ""
        return copy.endpoint?.absoluteString ?? ""
    }

    private func runTest() {
        self.isTesting = true
        self.testStatus = nil
        let configuration = self.configuration
        Task {
            do {
                let silence = [Float](repeating: 0, count: 16_000)
                let text = try await CloudASRClient().transcribe(samples: silence, configuration: configuration)
                self.testSucceeded = true
                self.testStatus = text.isEmpty ? "Connected. Credentials accepted." : String.fluidLocalizedFormat("Connected. Response: %@", String(describing: text))
            } catch {
                self.testSucceeded = false
                self.testStatus = error.localizedDescription
            }
            self.isTesting = false
        }
    }
}
