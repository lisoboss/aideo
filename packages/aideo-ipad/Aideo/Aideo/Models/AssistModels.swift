import Foundation

// MARK: - Structurize (自动结构化) — v2 /canvas/structure

struct StructurizeRequest: Codable, Sendable {
    let description: String
    let ai_provider: String?
    let language: String?  // zh/en/ja/ko，nil=自动
}

struct StructurizeResponse: Codable, Sendable {
    let blocks: [AssistBlock]
}

/// AI 生成的画布卡片块 — 可直接落画布
struct AssistBlock: Codable, Sendable {
    let type: String    // scene | character | action | style | camera | mood
    let content: String
    let params: GenerationParams?  // v2: 可选参数建议
}

// MARK: - Complete (智能补全) — v2 /canvas/complete

struct CompletionRequest: Codable, Sendable {
    let context: String
    let mode: String
    let existing_blocks: [PromptBlockDTO]?
    let ai_provider: String?
    let language: String?
}

struct CompletionResponse: Codable, Sendable {
    let suggestions: [CompletionSuggestion]
}

/// v2: 补全建议 — 含标题 + 可直接落画布的 block 组
struct CompletionSuggestion: Codable, Sendable {
    let title: String
    let blocks: [AssistBlock]
}

// MARK: - Inspire (灵感探索) — v2 /canvas/inspire

struct InspireRequest: Codable, Sendable {
    let theme: String?
    let ai_provider: String?
    let language: String?
}

struct InspireResponse: Codable, Sendable {
    let themes: [InspireTheme]
}

/// v2: 灵感主题 — 含 blocks 可直接落画布
struct InspireTheme: Codable, Sendable {
    let title: String
    let prompt: String
    let styleHint: String
    let tags: [String]
    let blocks: [AssistBlock]?   // v2: 结构化卡片

    enum CodingKeys: String, CodingKey {
        case title, prompt, tags, blocks
        case styleHint = "style_hint"
    }
}
