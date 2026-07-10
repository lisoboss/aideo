import Foundation

/// 转录文本后处理 — 完全由 AI 智能纠错（含繁简转换）
enum TranscriptPostProcessor {

    static func process(text: String, language: String?, client: APIClient) async -> String {
        guard !text.isEmpty else { return text }
        do {
            let response = try await client.correctTranscript(
                text: text, language: language
            )
            guard !response.corrected.isEmpty else { return text }
            return response.corrected
        } catch {
            // AI unavailable, keep original
            return text
        }
    }
}
