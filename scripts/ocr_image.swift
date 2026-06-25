import AppKit
import Foundation
import Vision

struct Line {
    let text: String
    let x: Double
    let y: Double
}

if CommandLine.arguments.count < 2 {
    fputs("Usage: swift scripts/ocr_image.swift <image>\n", stderr)
    exit(2)
}

let imageURL = URL(fileURLWithPath: CommandLine.arguments[1])
guard let image = NSImage(contentsOf: imageURL),
      let tiff = image.tiffRepresentation,
      let bitmap = NSBitmapImageRep(data: tiff),
      let cgImage = bitmap.cgImage else {
    fputs("Could not read image: \(imageURL.path)\n", stderr)
    exit(1)
}

let request = VNRecognizeTextRequest()
request.recognitionLevel = .accurate
request.recognitionLanguages = ["ja-JP", "en-US"]
request.usesLanguageCorrection = true

let handler = VNImageRequestHandler(cgImage: cgImage, options: [:])
try handler.perform([request])

let lines = (request.results ?? [])
    .compactMap { observation -> Line? in
        guard let candidate = observation.topCandidates(1).first else { return nil }
        let text = candidate.string.trimmingCharacters(in: .whitespacesAndNewlines)
        if text.isEmpty { return nil }
        return Line(text: text, x: observation.boundingBox.minX, y: observation.boundingBox.midY)
    }
    .sorted { lhs, rhs in
        if abs(lhs.y - rhs.y) > 0.012 {
            return lhs.y > rhs.y
        }
        return lhs.x < rhs.x
    }

for line in lines {
    print(line.text)
}
