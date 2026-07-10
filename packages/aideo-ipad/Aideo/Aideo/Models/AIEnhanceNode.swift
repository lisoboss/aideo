import Foundation
import CoreGraphics

enum AIStatus: String, Codable { case idle, processing, done, error }

struct AIEnhanceNode: Identifiable, Codable, Equatable {
    var id: UUID = UUID()
    var position: CGPoint = .zero
    var nodeSize: CGSize = CGSize(width: 200, height: 120)
    var inputText: String = ""
    var outputText: String = ""
    var status: AIStatus = .idle
    var errorMessage: String?

    init(id: UUID = UUID(), position: CGPoint = .zero, nodeSize: CGSize = CGSize(width: 200, height: 120),
         inputText: String = "", outputText: String = "", status: AIStatus = .idle, errorMessage: String? = nil) {
        self.id = id; self.position = position; self.nodeSize = nodeSize
        self.inputText = inputText; self.outputText = outputText
        self.status = status; self.errorMessage = errorMessage
    }

    enum CodingKeys: String, CodingKey { case id, inputText, outputText, status, errorMessage, x, y, w, h }

    init(from decoder: Decoder) throws {
        let c = try decoder.container(keyedBy: CodingKeys.self)
        id = try c.decode(UUID.self, forKey: .id)
        inputText = try c.decode(String.self, forKey: .inputText)
        outputText = try c.decode(String.self, forKey: .outputText)
        status = try c.decode(AIStatus.self, forKey: .status)
        errorMessage = try c.decodeIfPresent(String.self, forKey: .errorMessage)
        position = CGPoint(x: try c.decode(CGFloat.self, forKey: .x), y: try c.decode(CGFloat.self, forKey: .y))
        nodeSize = CGSize(width: try c.decodeIfPresent(CGFloat.self, forKey: .w) ?? 200,
                          height: try c.decodeIfPresent(CGFloat.self, forKey: .h) ?? 120)
    }

    func encode(to encoder: Encoder) throws {
        var c = encoder.container(keyedBy: CodingKeys.self)
        try c.encode(id, forKey: .id); try c.encode(inputText, forKey: .inputText)
        try c.encode(outputText, forKey: .outputText); try c.encode(status, forKey: .status)
        try c.encodeIfPresent(errorMessage, forKey: .errorMessage)
        try c.encode(position.x, forKey: .x); try c.encode(position.y, forKey: .y)
        try c.encode(nodeSize.width, forKey: .w); try c.encode(nodeSize.height, forKey: .h)
    }
}
