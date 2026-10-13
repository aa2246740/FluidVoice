# Linux cross-build research: omarchy-apple-dev

Research date: **2026-10-13**. Scope: whether an existing Omarchy Linux machine
can build/package FluidVoice, and what still needs macOS for validation.

## Evidence and snapshot

- Public `joshuaswarren/omarchy-apple-dev` `main` inspected at
  **`7837b6885e209f06d1b040cc7f40282cf6858102`**, committed
  **2026-10-12T08:55:19-05:00**. The supplied GitHub page and a read-only source
  checkout agreed on this head. References below pin that snapshot, rather than
  floating `main`. [O1]
- Its installer pins the maintainer's `xtool` fork to
  **`f0a1f90efdbb0dc023e276ff529da92618da7a87`**, committed
  **2026-10-06T13:04:23-05:00**. That revision was also inspected as source.
  README's abbreviated “1.20.1 + 4 fixes” is not the complete pin description:
  the installer mentions additional fixes. [O2]
- Evidence levels: **reported execution** means a dated first-party receipt,
  not a run independently reproduced here; **implemented** means inspected
  source; **unknown** means no sufficient evidence was found. Search results
  were discovery aids, not proof. No downloaded project code was executed.
- The research worker is the parent's background research agent. Only this
  report is added to the FluidVoice checkout. No remote machine inspection,
  installation, app build, push, workflow run, purchase, or signing/upload
  operation was performed.

## Bottom line

**“Linux cannot build macOS apps” is too broad and is contradicted by this
project's primary evidence.** This is not merely an iOS packaging project:
the maintainer reports compiling a SwiftUI macOS app on **x86_64 Arch Linux**,
signing and notarizing it there, and subsequently launching it on a Mac.
A larger **AppKit NetNewsWire Mac app targeting macOS 15** was also built,
bundled, signed and notarized on Linux, then exercised on an M1 Max Mac.
[O3][O4]

The narrower, defensible statement is:

> Linux can cross-compile and package some native SwiftUI/AppKit macOS apps
> using Linux tools plus Apple SDK material. omarchy-apple-dev supplies such
> a path. It is not an unchanged `xcodebuild -project … -scheme …` replacement,
> and it does not establish that FluidVoice's exact project, dependency graph,
> native XCTest suite, or microphone workflow works on Linux.

This distinction follows from the converter and shipping implementation,
not merely from the repository description. [O5][O6]

## Capability matrix

| Question | Evidence at the inspected snapshot |
|---|---|
| Native macOS SwiftUI executable built on Linux? | **Reported execution:** MacHello, Swift 6.4.0, MacOSX27.0 SDK, `arm64-apple-macosx14.0`; build reported 20.16 seconds. Signing/notarization occurred on Linux; runtime checks occurred on macOS. [O3] |
| Native macOS AppKit application built on Linux? | **Reported execution with an adapter and compatibility edits:** NetNewsWire at `8c322c287bec510a2ee0ebd0487e0481ad45ad82`; final receipt reports `arm64-apple-macosx15.0`, 35 compiled app xibs, two bundled extensions, notarization, and exercised windows on macOS 26.6.2. Not evidence of unmodified-project compatibility. [O4][O7] |
| SwiftUI iOS app built on Linux? | **Reported execution:** normal/full mode cross-builds arm64 iOS apps and deploys to physical devices. README distinguishes the older M1 device/debugger run from the newer toolchain installation verification. [O1] |
| No Apple Xcode archive at all? | **Experimental iOS-only alternative:** Objective-C/C, Swift/Foundation and a small SwiftUI subset from reconstructed declarations and link stubs. Its matrix explicitly excludes macOS apps, widgets and extensions. **Not a FluidVoice macOS build route.** [O8] |
| Run a full native macOS AppKit/SwiftUI app on Linux? | **Not demonstrated by these macOS receipts.** Their runtime verification is on a Mac. Linux simulation work is explicitly limited and is not Apple's UI framework/runtime. [O3][O4][O9] |
| Run Apple's iOS Simulator on Linux? | The implemented fallback builds on Linux, then uses a **Mac with Xcode over SSH** to install, launch and screenshot in the Simulator. [O10] |
| Run FluidVoice's existing macOS XCTest integration suite on Linux? | **Not established.** SDK construction exposes XCTest/Testing frameworks for cross-compilation, but the project converter does not reproduce the scheme's XCTest targets or execution, and no Linux native-macOS XCTest receipt was found. [O5][O11] |
| Sign/package without a remote Mac? | **Implemented and reported:** Linux macOS `.app`/`.zip`, ad hoc or Developer ID signing, optional Apple notarization and stapling. iOS has separate `.ipa`, provisioning, signing and upload paths. Apple services are still involved in notarization/uploads; a Mac is not the compiler in those receipts. [O3][O4][O6][O12] |

## Hosts, targets and toolchain

### Architecture is two different questions

- **Linux host:** the installer supports `x86_64` and `aarch64`/Apple Silicon
  Linux. Current full-mode fresh-user installation was verified on x86_64
  Arch on 2026-10-03; the older physical-device and LLDB run was on an M1
  on 2026-09-09. These are not interchangeable verification records. [O1][O2]
- **macOS target:** `ship-mac.sh` currently hard-codes
  **`arm64-apple-macosx<minimum>`**, independently of Linux host architecture.
  It defaults to the generated Info.plist's `LSMinimumSystemVersion`, otherwise
  14.0, with a `MACOS_MIN` override. No architecture selector or universal
  binary assembly is implemented in that script. [O6]
- The pinned SDK builder declares both **`arm64-apple-macosx`** and
  **`x86_64-apple-macosx`**, plus arm64 iOS and arm64/x86_64 iOS Simulator
  triples. That is configuration-level support for an Intel macOS target,
  **not a verified Intel or universal `ship-mac.sh` deliverable**. The concrete
  macOS receipts examined are arm64 builds on x86_64 Linux and runs on an
  Apple Silicon Mac. [O3][O4][O11]

### Full mode is SDK extraction, not Xcode running on Linux

The working full-mode stack is Linux Swift **6.4.0**, the patched xtool fork,
SwiftPM's **SwiftBuild** backend, Linux Darwin LLVM tools including
`ld64.lld`/the librarian, and SDK/framework/compiler-support material from
**Xcode 27.0**, including **MacOSX27.0.sdk**. The macOS script invokes
`swift build --build-system swiftbuild --toolset …/toolset-swb.json`,
`XCODE_EXTRA_PLATFORM_FOLDERS`, and the SDK toolset's `bin` directory.
It does not invoke Apple `xcodebuild`. [O1][O3][O6][O11]

The normal setup takes a user-downloaded matching **`Xcode.xip`** from Apple;
no existing Mac is required for that extraction route. Streaming only the
needed parts from an existing matching Mac/Xcode installation is an optional
alternative. The project says about **3 GB** of the archive's material is used,
which is **not** the full archive/download size or total setup disk requirement.
It caches an SDK bundle and source/build artifacts. [O1][O2]

Version matching matters: the installer maps Swift 6.4 to Xcode 27 and
Swift 6.3 to Xcode 26. Its own Swift-toolchain clang must precede a different
system clang; the README records SwiftUI header failures from a mismatch.
The SDK registration and `$XDG_CONFIG_HOME`/`~/.swiftpm` location also matter.
A user's installed state cannot be inferred from a successful public receipt.
[O1][O2]

## Xcode project import: what is actually converted

`tools/xcodeproj2xtool.py` reads the OpenStep `project.pbxproj` and xcconfig
settings, selects **one application target**, and writes a **new SwiftPM
adapter** with source/resource symlinks, generated Info.plist and xtool metadata.
It now detects macOS from `SUPPORTED_PLATFORMS`/`SDKROOT`, writes a macOS
executable product, and includes embedded app extensions. Some README/header
wording still calls it an “iOS app target” converter; current code and the
macOS receipt demonstrate broader support. [O5][O4]

Important limits from current source:

- **Targets, not schemes/workspaces:** target selection is by target name.
  The implementation does not import an `.xcscheme`'s build/test actions or
  create the existing XCTest target graph. Other application targets and
  non-embedded extensions are skipped. [O5]
- **Release-centric settings:** the converter's settings merge is explicitly
  for Release; conversion does not establish Debug/Release equivalence or
  arbitrary configuration support. [O5]
- **Package dependencies:** remote/local SwiftPM products and multiple
  requirement kinds are mapped. Some directly imported transitive products
  are inferred. Declared branches remain branches; a pinned revision in
  `Package.resolved` does **not** automatically replace that requirement.
  Do not assume the resulting build preserves FluidVoice's resolved graph
  without an explicit lock/pin comparison. [O5]
- **Application source in C/Objective-C/C++:** the converter groups
  `.m`, `.mm`, `.h`, `.hpp`, `.c`, `.cpp` as unsupported/excluded files,
  including file-system-synchronized groups. This is a **converter limit**,
  not evidence that Linux clang cannot target Darwin or that package-based
  C/Objective-C/C++ never builds. NetNewsWire needed Swift shims and explicit
  imports for bridging-header behavior. [O5][O7]
- **Build settings:** Swift 5/6 language mode, default MainActor isolation,
  approachable-concurrency features, upcoming features and compilation
  conditions are mapped. `OTHER_SWIFT_FLAGS` is explicitly warned as unmapped.
  In the inspected `swift_settings`/`target_block` implementation there is no
  mapping of **`SWIFT_STRICT_CONCURRENCY`**, **`SWIFT_OBJC_BRIDGING_HEADER`**,
  arbitrary C/C++ settings, or the app target's general linker settings.
  Therefore the presence of some concurrency mappings is not full Xcode
  settings parity. [O5]
- **Run-script phases and CocoaPods:** explicitly unsupported by the converter;
  code generation or packaging done there needs separate review/adaptation.
  Not every unmapped setting is proven to produce its own warning. [O5]
- **Interface Builder:** files are probed with the Linux replacement `ibtool`;
  supported ones become processed resources, unsupported ones are excluded
  with warnings. Shipping also warns and skips failed nib compilation.
  A successful process exit is not proof that every UI resource shipped.
  The final NetNewsWire receipt supersedes earlier reports of missing app
  nibs, but the compatibility script still contains older exclusions for
  local-package nibs. [O5][O6][O4][O7]

This is an adapter workflow with real successes, not transparent execution
of arbitrary Xcode projects or preservation of every Apple build phase.

## Dependency and resource support relevant to FluidVoice

| Area | What is supported/proven | Precise limit or unknown |
|---|---|---|
| SwiftPM source packages | The converter maps product dependencies and the maintainer built substantial package-based applications. [O5][O12] | FluidVoice's exact transitive graph, pins, conditional manifests and compiler settings were not resolved or built here. Existing Xcode pins must remain authoritative. |
| Swift macros | A pinned Linux OpenAppleMacros server replaces Apple's host plugin path. A 2026-10-06 receipt compares expansions for `@Observable`, `@Model`, `@Query`, `#Predicate`, `@Entry`, `#Preview` and Swift Testing macros with Xcode; the probes target iOS. [O2][O13] | The receipt explicitly says none of those apps' 62 package dependencies declared its own macro. It does **not** prove arbitrary third-party macros or every macOS macro expansion. |
| SwiftPM build-tool/command plugins | Standard SwiftPM remains the build entry point; known resource tools and Apple macros are specially provided. [O6][O2] | No sufficient general build-plugin compatibility receipt was found. A plugin invoking Xcode-only executables or a Darwin host binary needs a Linux-host alternative; exact FluidVoice plugin requirements remain unknown. Do not confuse Flutter native plugins with SwiftPM build plugins. |
| Objective-C, C, C++ | Full-mode README lists these languages, and the Flutter pipeline documents native Runner/package-plugin builds against Apple frameworks. [O1][O14] | The Xcode adapter excludes such **app-target source files**. Mixed source, bridging headers and C++ interoperability need package/adapter-specific review; general “supported languages” does not remove that blocker. [O5] |
| Binary targets / `.xcframework` | Pinned xtool recognizes binary-target resources; its iOS packer distinguishes static archives from frameworks to embed. macOS ship code copies built `.framework` and `.dylib` products. NetNewsWire bundled Sparkle. [O15][O6][O16] | No FluidAEC3, TranscribeCpp or arbitrary macOS xcframework compatibility receipt was found. Inspect target platform/slices, headers/modules, linkage, embedding, nested signatures and resources. This is **not** a universal xcframework guarantee. |
| Metal | Apple framework declarations/link material are supplied in full mode; the project distinguishes real device/Mac GPU validation from software simulation. [O1][O9][O17] | No Linux Metal shader compiler, `.metal` → `.metallib` pipeline, or MLX build receipt was found in the inspected project. Linking a framework or copying precompiled shaders is different from compiling new shaders, and neither proves runtime GPU operation. |
| CoreML | Full mode provides Apple SDK frameworks; copying model resources is separate from compiling or running them. [O1][O5] | No `coremlc`, model-code-generation, `.mlmodel`/`.mlpackage` compilation or native CoreML/ANE Linux runtime proof was found. Precompiled `.mlmodelc` resources could avoid a build-time compiler requirement, but exact app behavior must be checked on macOS. |
| Ordinary resources / Bundle lookup | Converter emits `.process`/`.copy` resources; macOS shipping keeps SwiftPM bundles and flattens app resources into `Contents/Resources` for both `Bundle.module` and `Bundle.main`. [O5][O6] | Exact paths, names, nested bundles, Info.plist expansion, privacy/usage keys and dependency-owned resources need artifact inspection; an adapter build alone does not prove lookup parity. |
| `.xcassets` / app icons | Linux `actool` and AssetKit are installed for both iOS and macOS; macOS ship recompiles the icon into `.icns`/`Assets.car` and merges icon plist keys. [O2][O6][O18] | Real applications previously exposed catalog/symbol incompatibilities; the NetNewsWire receipt records the fixes. Treat support as tested formats/cases, not all future asset schemas. [O4][O16] |
| `.xcstrings`, `.strings`, `.stringsdict` | Linux `xcstringstool` implements compilation and Swift symbol generation; installed into both platforms. The implementation handles plural/device variations and is described as checked against Xcode 27 outputs. [O2][O19] | FluidVoice's English/Simplified Chinese catalogs and `InfoPlist.xcstrings` output/placement were not compiled or exercised here. They are **not automatically unsupported**, but app-specific parity is unverified. |
| Core Data / nibs / storyboards / intents | Linux replacement `momc`, `ibtool`/`ibmac`, and intent-generation tooling exist; resource import selects the appropriate supported cases. [O2][O5][O4] | They are reimplementations rather than Apple executables running on Linux. Unsupported UI files may be excluded; functionality beyond their implemented/tested cases is not established. |

“No receipt found” above is an evidence boundary, **not proof of impossibility**.
This research did not execute a compatibility probe against FluidVoice.

## Running and testing: a build is not acceptance

The strongest macOS execution evidence is explicitly **on macOS**:
MacHello was opened on `macstudio`; NetNewsWire was exercised on an
**M1 Max, macOS 26.6.2**, including Gatekeeper, signatures, extension
registration, windows and sandboxed networking. macOS 15 is a demonstrated
**deployment target**, not the runtime OS used in that final receipt.
Consequently Linux could replace the build host for a compatible app without
replacing the local/remote Mac used for runtime verification. [O3][O4]

Two Linux runtime research efforts do not change that conclusion:

- `machoload` ran a **C-level arm64 iOS Mach-O hello** under QEMU and later
  natively on arm64 Linux. Its documentation expressly says this proves the
  loader/syscall shims only—not Objective-C, dyld shared-cache loading, or any
  Apple framework. [O9]
- `simview` recompiles a small SwiftUI-like view vocabulary against the
  project's **own** Linux `SwiftUI` module and software PNG renderer.
  Navigation/scroll demos work within its limited model; the README says
  this is not real SwiftUI layout, fonts, animation or Metal. It does not run
  an unchanged FluidVoice macOS binary, microphone pipeline, Keychain,
  accessibility system or CoreML runtime. [O9][O20]

The SDK builder deliberately exposes XCTest/Testing/XCUIAutomation framework
paths, so claiming “even compiling anything using XCTest is impossible” would
also be too strong. But these are target SDK inputs, **not Linux implementations
of Apple's native test runner and app runtime**. Neither inspected macOS
receipt runs a native XCTest suite on Linux. Dependency-free logic tests
ported to a Linux harness remain a separate kind of evidence. [O11][O3][O4]

For FluidVoice, native integration tests, GUI behavior, CoreAudio/audio routing,
permission prompts, real microphone dictation, and accelerator-backed ASR
therefore still require an actual compatible macOS runtime unless a specific
alternative is separately demonstrated. The repository's acceptance recipe
already separates building from microphone acceptance. [F1]

## Build, signing and distribution

### macOS

`ship-mac.sh` implements a **Release SwiftPM build**, bundle assembly into
`build/<PRODUCT>.app`, dylib/framework embedding, resource flattening,
nib/icon processing, Info.plist construction, extension assembly, inside-out
signing, and final **`.zip`** packaging. There is no demonstrated `.dmg`,
installer `.pkg`, Xcode `.xcarchive`, or Mac App Store upload path in this
script; its distribution route is Developer ID direct distribution. [O6]

Without a Developer ID identity it can sign ad hoc; with an identity it uses
`rcodesign sign --for-notarization` for hardened runtime and timestamps.
`--notarize` additionally submits to **Apple's remote notary service** and
staples the ticket using an App Store Connect API key. The maintainer's receipts
report Accepted notarizations and Mac Gatekeeper acceptance. This is not “fully
offline distribution,” but it is **not a remote Mac build**. [O6][O3][O4]

The project's Developer ID certificate creation required the Account Holder
in Apple's portal; its API-key attempt was refused. macOS restricted
entitlements require suitable provisioning. The NetNewsWire run dropped
unbacked iCloud/app-group claims; this is a feature/configuration difference,
not a fidelity guarantee. Shipping may sign without automatically detected
restricted entitlements when no profile exists, with a warning. [O6][O21]

### iOS, a separate path

`ship.sh` produces `.ipa` files, handles icons/framework layout and provisioning,
performs offline validation, and optionally uploads through App Store Connect.
The maintainer reports `VALID` processing for real SwiftUI apps with extensions.
A local TEST identity without the required credentials proves the pipeline
only; Apple rejects that signature. `VALID` processing is **not App Store
review approval**, and the script does not submit for review. Free-account
device installation is supported by the normal full-mode path. These iOS
facts must not be relabeled as macOS XCTest or Mac App Store evidence. [O1][O12]

## Setup, license and cost caveats

- **Project cost:** the project is MIT licensed and described as free, with
  optional donations/sponsorship. It does not require purchasing a hosted Mac
  build service to perform the evidenced Linux build. Existing Linux compute,
  bandwidth, storage, and a Mac for runtime acceptance still have whatever
  costs their owner incurs; no total FluidVoice migration estimate is justified
  by the Hello/NetNewsWire timings. [O22][O1][O3][O4]
- **Apple membership:** Apple's enrollment page, read on 2026-10-13, states
  **99 USD per membership year**, region-dependent local pricing and possible
  qualifying fee waivers. The project distinguishes free Apple ID device
  installs from paid-account distribution workflows. Do not purchase a new
  membership or assume the user needs one merely to investigate a build.
  [A1][O1]
- **Setup is not zero-install:** the full-mode installer installs/builds
  Linux packages and tools, fetches pinned xtool/OpenAppleMacros source,
  installs replacement resource tools and patches SDK/SwiftBuild settings.
  Its default Arch route includes privileged package steps; `--user-only`
  skips sudo but depends on prerequisites already being present. These are
  changes that require separate approval on the user's machine. [O2]
- **Download/access:** full mode needs Apple-account access to obtain a
  matching Xcode archive; an installed Xcode application is unnecessary for
  the extraction route. Experimental no-Xcode mode needs around **7 GB
  temporary setup disk** and does not support macOS. This does not justify
  downloading Xcode onto the space-constrained local Mac. [O1][O8]
- **Licensing is separate from technical capability:** the project's MIT
  license does not grant rights to Apple's SDKs/frameworks/runtime. Apple's
  agreements page explicitly requires applicable terms and links the
  **Xcode and Apple SDKs Agreement**. Review the user's actual accepted SDK,
  Developer Program and distribution terms before deployment or redistribution.
  This report does **not** determine whether using extracted SDK components
  on a particular Linux/Apple-branded/non-Apple host complies with those
  agreements; the full Xcode/SDK PDF was not examined here. Do not infer legal
  permission from a successful build or notarization. [A2][O22]
- **Secrets:** development/distribution signing and notarization involve
  identities, private keys/profiles or Apple account/API-key credentials.
  They are distinct from ASR provider keys. The user's already-authorized
  unsigned macOS build evidence did not require ASR keys. No credentials
  were requested or read in this research. [O6][O12][F1]

## FluidVoice: what is known, what would need adaptation

These observations are **static inspection of this checkout**, not a migration
or build attempt:

1. **Use the supported graph, not a shortcut.** `AGENTS.md` defines
   `Fluid.xcodeproj`, scheme **`Fluid`**, as the supported app/XCTest entry;
   the root `Package.swift` is not that contract. The scheme's application
   target is named **`fluid`** (lowercase), distinct from scheme `Fluid` and
   product `FluidVoice`. A future converter investigation would select the
   target, not pass the scheme name blindly. [F1][F2]
2. **The C/bridging-header seam is a concrete adapter gap.**
   The Xcode app compiles the synchronized `Sources/Fluid` tree, whose
   `CoreAudioCaptureSupportBridge.c` includes the single-sourced C capture
   implementation; `Fluid-Bridging-Header.h` exposes its header to Swift.
   The app explicitly sets `SWIFT_OBJC_BRIDGING_HEADER`. The inspected converter
   excludes the C/header files and does not map that setting. An unmodified
   generated adapter therefore does **not preserve this seam**; a separately
   modeled C target/import bridge or equivalent adaptation is needed before
   claiming compatibility. This is not evidence that CoreAudio C code cannot
   be cross-compiled. [F3][F4][O5]
3. **Concurrency settings need comparison.** Deployment target 15.0, Swift
   language mode 5.0, default MainActor, approachable concurrency and complete
   strict concurrency are set in Xcode. The converter maps several of those,
   but not `SWIFT_STRICT_CONCURRENCY`; it uses a newer Linux compiler/SDK stack.
   Compiling the adapter is not evidence of identical actor diagnostics or
   runtime behavior. [F4][O5]
4. **AEC3 has a promising target slice, not a proven Linux cross-build.**
   The local package declares `FluidAEC3Binary` at
   `Artifacts/FluidAEC3.xcframework` and a `FluidAEC3Bridge` target.
   Its Info.plist contains **macOS arm64 and x86_64** static-library slices.
   Those are Apple target artifacts; the Linux host need not execute the
   archive to link it. Correct bridge compilation, module import and linkage
   in this specific SwiftBuild cross-toolchain remain unverified. [F5][O6]
5. **Whisper/FluidAudio/MLX must be checked individually.** The supported
   checked-in lock pins `FluidAudio` to
   `09c23cce76126920b3ff6710cdb154bdf9c126b8` and `transcribe-cpp-swift`
   0.1.2 to `a16df2905f9c715344374fd2d8dd97c2712a6d96`.
   `WhisperProvider` requests the Metal backend on Apple Silicon.
   FluidVoice imports CoreML and downloads precompiled `.mlmodelc` model
   directories, so it is not correct to assume every model needs build-time
   `coremlc`. Their pinned package build scripts/plugins, binary contents,
   shader assets and runtime behavior were not audited here. No MLX package
   appears in the inspected supported Xcode lock; any MLX-related additional
   graph referenced in session context needs its exact source/pin identified
   before assessing it. No private runtime is implied to be available. [F6][F7][F8]
6. **Resources and app identity need artifact verification.**
   `Localizable.xcstrings`, `InfoPlist.xcstrings`, resource lookup through
   `Bundle.main`, microphone usage text, runpaths and `Fluid.entitlements`
   must retain their intended outputs/behavior. omarchy-apple-dev has relevant
   implementations, but no FluidVoice receipt verifies them. English and
   Simplified Chinese need acceptance on macOS. [F4][F9][O6][O19]
7. **Existing XCTest/ASR evidence does not transfer.** Scheme `Fluid` references
   `FluidDictationIntegrationTests.xctest`; the adapter does not reproduce that
   TestAction. The session's previous macOS build/launch and hung mocked meeting
   ASR integration test are parent-supplied context, not a new run in this
   research. A Linux packaging attempt would neither explain that hang nor
   turn it into a passing native test result. [F2][O5]

**Compatibility status: credible candidate for an additional Linux build host,
not a verified replacement for FluidVoice's supported macOS build/test workflow.**
There is a specific import gap to investigate, not grounds for dismissing Linux
cross-building as impossible or guaranteeing that this app builds unchanged.

## Required follow-ups, only after new authorization

No follow-up below has been performed or authorized by this report.

1. Obtain a non-secret user-provided inventory of the existing Linux host's
   architecture, Swift/clang versions, omarchy-apple-dev revision, installed
   Darwin SDK/mode, free space and desired **macOS target** architecture.
   Ask whether it already builds macOS `.app` files or only iOS `.ipa` files.
2. In an explicitly approved disposable copy, evaluate conversion of the
   **`fluid`** app target; retain every warning and compare all effective
   build settings, app metadata, package pins and resources against the
   supported graph. Address the C capture/bridging seam without weakening
   concurrency or removing production functionality.
3. Audit the pinned package manifests/tools and binary slices for SwiftPM
   plugin, C/C++, Metal/CoreML and embedding requirements. Separate
   compilation, packaging, ad hoc signing, Developer ID signing and
   notarization into distinct checks; signing/service submissions require
   their own approval.
4. Only if a build is authorized, retain exact app commit/toolchain/target,
   artifact hashes, package-lock comparison and all warning/failure evidence.
   Then exercise the Linux-built artifact on an existing compatible Mac,
   without claiming that packaging proved XCTest or microphone operation.
5. Keep native XCTest/hang diagnosis and actual microphone/permission/ASR
   acceptance on macOS as separate validation work. Local Xcode absence need
   not block opening a compatible remotely built `.app`. [F1]

The session context says the two authorized cloud rounds are consumed.
Nothing here grants another cloud run, push, merge, installation, signing
submission, or service purchase. Existing uncommitted product/workflow/tooling
changes are outside this assignment.

## Primary sources

All upstream source links below are pinned to the inspected commits.
Dates in receipt titles describe the maintainer's runs, not independently
reproduced results. Apple pages were read as current public page content,
not search snippets.

[O1]: https://github.com/joshuaswarren/omarchy-apple-dev/blob/7837b6885e209f06d1b040cc7f40282cf6858102/README.md
[O2]: https://github.com/joshuaswarren/omarchy-apple-dev/blob/7837b6885e209f06d1b040cc7f40282cf6858102/install-toolchain.sh
[O3]: https://github.com/joshuaswarren/omarchy-apple-dev/blob/7837b6885e209f06d1b040cc7f40282cf6858102/receipts/2026-10-06-macos-notarized.md
[O4]: https://github.com/joshuaswarren/omarchy-apple-dev/blob/7837b6885e209f06d1b040cc7f40282cf6858102/receipts/2026-10-07-nnw-mac-final.md
[O5]: https://github.com/joshuaswarren/omarchy-apple-dev/blob/7837b6885e209f06d1b040cc7f40282cf6858102/tools/xcodeproj2xtool.py
[O6]: https://github.com/joshuaswarren/omarchy-apple-dev/blob/7837b6885e209f06d1b040cc7f40282cf6858102/ship-mac.sh
[O7]: https://github.com/joshuaswarren/omarchy-apple-dev/blob/7837b6885e209f06d1b040cc7f40282cf6858102/compat/nnw-mac/setup.sh
[O8]: https://github.com/joshuaswarren/omarchy-apple-dev/blob/7837b6885e209f06d1b040cc7f40282cf6858102/docs/TEST-MATRIX.md
[O9]: https://github.com/joshuaswarren/omarchy-apple-dev/blob/7837b6885e209f06d1b040cc7f40282cf6858102/docs/IOS-SIMULATION-LINUX.md
[O10]: https://github.com/joshuaswarren/omarchy-apple-dev/blob/7837b6885e209f06d1b040cc7f40282cf6858102/tools/simctl-remote.sh
[O11]: https://github.com/joshuaswarren/xtool/blob/f0a1f90efdbb0dc023e276ff529da92618da7a87/Sources/XToolSupport/SDKBuilder.swift
[O12]: https://github.com/joshuaswarren/omarchy-apple-dev/blob/7837b6885e209f06d1b040cc7f40282cf6858102/ship.sh
[O13]: https://github.com/joshuaswarren/omarchy-apple-dev/blob/7837b6885e209f06d1b040cc7f40282cf6858102/receipts/2026-10-06-macro-parity.md
[O14]: https://github.com/joshuaswarren/omarchy-apple-dev/blob/7837b6885e209f06d1b040cc7f40282cf6858102/flutter/README.md
[O15]: https://github.com/joshuaswarren/xtool/blob/f0a1f90efdbb0dc023e276ff529da92618da7a87/Sources/PackLib/Packer.swift#L169-L194
[O16]: https://github.com/joshuaswarren/omarchy-apple-dev/blob/7837b6885e209f06d1b040cc7f40282cf6858102/receipts/2026-10-07-nnw-mac-ship.md
[O17]: https://github.com/joshuaswarren/omarchy-apple-dev/blob/7837b6885e209f06d1b040cc7f40282cf6858102/receipts/2026-10-10-testing-without-the-phone-plan.md
[O18]: https://github.com/joshuaswarren/omarchy-apple-dev/blob/7837b6885e209f06d1b040cc7f40282cf6858102/tools/darwin-tools/Package.swift
[O19]: https://github.com/joshuaswarren/omarchy-apple-dev/blob/7837b6885e209f06d1b040cc7f40282cf6858102/tools/xcstringstool
[O20]: https://github.com/joshuaswarren/omarchy-apple-dev/blob/7837b6885e209f06d1b040cc7f40282cf6858102/simview/README.md#limits
[O21]: https://github.com/joshuaswarren/omarchy-apple-dev/blob/7837b6885e209f06d1b040cc7f40282cf6858102/FINDINGS.md#developer-id-provisioning-for-that-mac-app-2026-10-07
[O22]: https://github.com/joshuaswarren/omarchy-apple-dev/blob/7837b6885e209f06d1b040cc7f40282cf6858102/LICENSE
[A1]: https://developer.apple.com/programs/enroll/
[A2]: https://developer.apple.com/support/terms/
[F1]: ../../AGENTS.md
[F2]: ../../Fluid.xcodeproj/xcshareddata/xcschemes/Fluid.xcscheme
[F3]: ../../Sources/Fluid/CoreAudioCaptureSupportBridge.c
[F4]: ../../Fluid.xcodeproj/project.pbxproj
[F5]: ../../Vendor/WebRTCAudioProcessing/Package.swift
[F6]: ../../Fluid.xcodeproj/project.xcworkspace/xcshareddata/swiftpm/Package.resolved
[F7]: ../../Sources/Fluid/Services/WhisperProvider.swift
[F8]: ../../Sources/Fluid/Networking/ModelDownloader.swift
[F9]: ../../Sources/Fluid/String%2BLocalization.swift

Local evidence also inspected:
`Sources/Fluid/Fluid-Bridging-Header.h`,
`Sources/Fluid/CoreAudioCaptureSupportBridge.h`,
`Vendor/WebRTCAudioProcessing/Artifacts/FluidAEC3.xcframework/Info.plist`,
`Fluid.entitlements`, and the two `Sources/Fluid/Resources/*.xcstrings` paths.
Local source citations describe the working checkout; they do not attribute
uncommitted session changes to the last committed SHA.
