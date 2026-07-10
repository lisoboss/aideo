import Foundation

// MARK: - Structurize (自动结构化)

struct StructurizeRequest: Codable, Sendable {
    let description: String
}

struct StructurizeResponse: Codable, Sendable {
    let blocks: [AssistBlock]
}

struct AssistBlock: Codable, Sendable {
    let type: String    // scene | character | action | style | camera | mood
    let content: String
}

// MARK: - Complete (智能补全)

struct CompletionRequest: Codable, Sendable {
    let context: String
    let mode: String    // "suggestion" | "completion"
}

struct CompletionResponse: Codable, Sendable {
    let suggestions: [String]
}

// MARK: - Inspire (灵感探索)

struct InspireRequest: Codable, Sendable {
    let theme: String?
}

struct InspireResponse: Codable, Sendable {
    let themes: [InspireTheme]
}

struct InspireTheme: Codable, Sendable {
    let title: String
    let prompt: String
    let styleHint: String
    let tags: [String]

    enum CodingKeys: String, CodingKey {
        case title, prompt, tags
        case styleHint = "style_hint"
    }
}
