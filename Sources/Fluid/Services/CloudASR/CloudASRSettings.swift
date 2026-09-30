import Foundation
import Security

/// Persists cloud ASR configuration. Secrets live in the Keychain; other options in UserDefaults.
final class CloudASRSettings {
    static let shared = CloudASRSettings()

    private let keychainService = "com.fluidvoice.cloud-asr-keys"
    private let defaults: UserDefaults
    private var credentialCache: [CloudASRVendor: Bool] = [:]

    init(defaults: UserDefaults = .standard) {
        self.defaults = defaults
    }

    private enum SecretField: String {
        case apiKey
        case accessToken
    }

    private enum OptionField: String {
        case appID
        case model
        case region
        case language
        case baseURL
    }

    func configuration(for vendor: CloudASRVendor) -> CloudASRConfiguration {
        var configuration = CloudASRConfiguration(vendor: vendor)
        configuration.apiKey = self.secret(.apiKey, vendor: vendor) ?? ""
        configuration.accessToken = self.secret(.accessToken, vendor: vendor) ?? ""
        configuration.appID = self.option(.appID, vendor: vendor)
        configuration.model = self.option(.model, vendor: vendor)
        configuration.region = CloudASRRegion(rawValue: self.option(.region, vendor: vendor)) ?? .china
        configuration.language = self.option(.language, vendor: vendor)
        configuration.baseURLOverride = self.option(.baseURL, vendor: vendor)
        return configuration
    }

    func save(_ configuration: CloudASRConfiguration) {
        let vendor = configuration.vendor
        self.setSecret(configuration.apiKey, field: .apiKey, vendor: vendor)
        self.setSecret(configuration.accessToken, field: .accessToken, vendor: vendor)
        self.setOption(configuration.appID, field: .appID, vendor: vendor)
        self.setOption(configuration.model, field: .model, vendor: vendor)
        self.setOption(configuration.region.rawValue, field: .region, vendor: vendor)
        self.setOption(configuration.language, field: .language, vendor: vendor)
        self.setOption(configuration.baseURLOverride, field: .baseURL, vendor: vendor)
        self.credentialCache[vendor] = configuration.hasCredentials
    }

    func hasCredentials(for vendor: CloudASRVendor) -> Bool {
        if let cached = self.credentialCache[vendor] {
            return cached
        }
        let value = self.configuration(for: vendor).hasCredentials
        self.credentialCache[vendor] = value
        return value
    }

    // MARK: - UserDefaults

    private func optionKey(_ field: OptionField, vendor: CloudASRVendor) -> String {
        "CloudASR.\(vendor.rawValue).\(field.rawValue)"
    }

    private func option(_ field: OptionField, vendor: CloudASRVendor) -> String {
        self.defaults.string(forKey: self.optionKey(field, vendor: vendor)) ?? ""
    }

    private func setOption(_ value: String, field: OptionField, vendor: CloudASRVendor) {
        let trimmed = value.trimmingCharacters(in: .whitespacesAndNewlines)
        let key = self.optionKey(field, vendor: vendor)
        if trimmed.isEmpty {
            self.defaults.removeObject(forKey: key)
        } else {
            self.defaults.set(trimmed, forKey: key)
        }
    }

    // MARK: - Keychain

    private func account(_ field: SecretField, vendor: CloudASRVendor) -> String {
        "\(vendor.rawValue).\(field.rawValue)"
    }

    private func baseQuery(_ field: SecretField, vendor: CloudASRVendor) -> [String: Any] {
        [
            kSecClass as String: kSecClassGenericPassword,
            kSecAttrService as String: self.keychainService,
            kSecAttrAccount as String: self.account(field, vendor: vendor),
        ]
    }

    private func secret(_ field: SecretField, vendor: CloudASRVendor) -> String? {
        var query = self.baseQuery(field, vendor: vendor)
        query[kSecReturnData as String] = true
        query[kSecMatchLimit as String] = kSecMatchLimitOne
        var item: CFTypeRef?
        guard SecItemCopyMatching(query as CFDictionary, &item) == errSecSuccess, let data = item as? Data else {
            return nil
        }
        return String(data: data, encoding: .utf8)
    }

    private func setSecret(_ value: String, field: SecretField, vendor: CloudASRVendor) {
        let trimmed = value.trimmingCharacters(in: .whitespacesAndNewlines)
        let query = self.baseQuery(field, vendor: vendor)
        guard !trimmed.isEmpty else {
            SecItemDelete(query as CFDictionary)
            return
        }
        let data = Data(trimmed.utf8)
        let status = SecItemUpdate(query as CFDictionary, [kSecValueData as String: data] as CFDictionary)
        if status == errSecItemNotFound {
            var insert = query
            insert[kSecValueData as String] = data
            insert[kSecAttrAccessible as String] = kSecAttrAccessibleAfterFirstUnlock
            let addStatus = SecItemAdd(insert as CFDictionary, nil)
            if addStatus != errSecSuccess {
                DebugLogger.shared.error("CloudASRSettings: failed to store \(field.rawValue) for \(vendor.rawValue) (OSStatus \(addStatus))", source: "CloudASR")
            }
        } else if status != errSecSuccess {
            DebugLogger.shared.error("CloudASRSettings: failed to update \(field.rawValue) for \(vendor.rawValue) (OSStatus \(status))", source: "CloudASR")
        }
    }
}
