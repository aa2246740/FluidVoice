import Foundation

extension String {
    /// Looks up this string in Localizable.xcstrings (en → zh-Hans), falling back to itself.
    /// Safe for dynamic values: a missing key returns the original string.
    var fluidLocalized: String {
        Bundle.main.localizedString(forKey: self, value: nil, table: nil)
    }

    /// Like `fluidLocalized`, but for format strings containing %@ placeholders.
    static func fluidLocalizedFormat(_ key: String, _ args: CVarArg...) -> String {
        String(format: key.fluidLocalized, arguments: args)
    }
}
