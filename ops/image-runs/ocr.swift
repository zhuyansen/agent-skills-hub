// Literal text in an image, one recognised line per output line (macOS Vision).
// Language correction is off: it would "fix" a misspelt word into the one the brief asked for.
// Build: swiftc -O ops/image-runs/ocr.swift -o ops/image-runs/bin/ocr    Run: ocr <image> [languages, default zh-Hans,en-US]
// An English-only pass reads Latin text better than the mixed one (it read "Elm" as "Em" or "Eim").
import AppKit
import Vision

let path = CommandLine.arguments[1]
guard let image = NSImage(contentsOfFile: path),
      let cg = image.cgImage(forProposedRect: nil, context: nil, hints: nil) else {
    FileHandle.standardError.write("cannot read \(path)\n".data(using: .utf8)!)
    exit(1)
}
let request = VNRecognizeTextRequest()
request.recognitionLevel = .accurate
request.usesLanguageCorrection = false
request.recognitionLanguages = CommandLine.arguments.count > 2
    ? CommandLine.arguments[2].split(separator: ",").map(String.init) : ["zh-Hans", "en-US"]
try VNImageRequestHandler(cgImage: cg, options: [:]).perform([request])
for observation in request.results ?? [] {
    if let best = observation.topCandidates(1).first { print(best.string) }
}
