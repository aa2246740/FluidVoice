import Foundation
import IOKit

// Matches the production observer's default actor isolation without audio hardware.
final class AudioHardwareObserver {
    private(set) var messageCount = 0

    func handleClamshellInterestMessage() {
        self.messageCount += 1
    }
}

@main
struct ClamshellCallbackIsolationTests {
    @MainActor
    static func main() {
        // The real IOKit ABI must accept the production callback.
        let callback: IOServiceInterestCallback = clamshellStateInterestCallback
        let observer = AudioHardwareObserver()
        let refcon = Unmanaged.passUnretained(observer).toOpaque()
        callback(refcon, io_service_t(IO_OBJECT_NULL), natural_t(0), nil)
        precondition(observer.messageCount == 1, "Main-queue callback must deliver synchronously")
        callback(nil, io_service_t(IO_OBJECT_NULL), natural_t(0), nil)
        precondition(observer.messageCount == 1, "Missing observer must be ignored")
        print("PASS: production IOKit callback ABI, MainActor delivery and null context")
    }
}
