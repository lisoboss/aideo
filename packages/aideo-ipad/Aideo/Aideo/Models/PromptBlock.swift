import Foundation
import CoreGraphics

/// 卡片块类型
enum BlockType: String, Codable, CaseIterable {
    case scene       // 场景
    case character   // 角色
    case action      // 动作
    case style       // 风格
    case camera      // 镜头
    case mood        // 氛围
    case custom      // 自定义

    var displayName: String {
        switch self {
        case .scene:     "场景"
        case .character: "角色"
        case .action:    "动作"
        case .style:     "风格"
        case .camera:    "镜头"
        case .mood:      "氛围"
        case .custom:    "自定义"
        }
    }

    var iconName: String {
        switch self {
        case .scene:     "mountain.2"
        case .character: "person.fill"
        case .action:    "figure.run"
        case .style:     "paintpalette"
        case .camera:    "camera.fill"
        case .mood:      "theatermasks"
        case .custom:    "text.bubble"
        }
    }

    var defaultColor: String {
        switch self {
        case .scene:     "#4A90D9"
        case .character: "#E85D75"
        case .action:    "#F5A623"
        case .style:     "#7B61FF"
        case .camera:    "#50C878"
        case .mood:      "#FF6B9D"
        case .custom:    "#8E8E93"
        }
    }
}

/// 画布提示词卡片
struct PromptBlock: Identifiable, Codable, Equatable {
    var id: UUID = UUID()
    var type: BlockType = .custom
    var content: String = ""
    var position: CGPoint = .zero
    var params: GenerationParams = GenerationParams()
    var sceneTag: Int?      // 故事板场景编号，nil=未分配
    var cardSize: CGSize = CGSize(width: 180, height: 120)

    /// 卡片颜色（默认按类型）
    var colorHex: String { type.defaultColor }

    // MARK: - Codable

    enum CodingKeys: String, CodingKey {
        case id, type, content, params, sceneTag, x, y, w, h
    }

    init(id: UUID = UUID(), type: BlockType = .custom, content: String = "",
         position: CGPoint = .zero, params: GenerationParams = GenerationParams(),
         sceneTag: Int? = nil, cardSize: CGSize = CGSize(width: 180, height: 120)) {
        self.id = id; self.type = type; self.content = content
        self.position = position; self.params = params; self.sceneTag = sceneTag
        self.cardSize = cardSize
    }

    init(from decoder: Decoder) throws {
        let c = try decoder.container(keyedBy: CodingKeys.self)
        id = try c.decode(UUID.self, forKey: .id)
        type = try c.decode(BlockType.self, forKey: .type)
        content = try c.decode(String.self, forKey: .content)
        params = try c.decodeIfPresent(GenerationParams.self, forKey: .params) ?? GenerationParams()
        sceneTag = try c.decodeIfPresent(Int.self, forKey: .sceneTag)
        let x = try c.decode(CGFloat.self, forKey: .x)
        let y = try c.decode(CGFloat.self, forKey: .y)
        position = CGPoint(x: x, y: y)
        let w = try c.decodeIfPresent(CGFloat.self, forKey: .w) ?? 180
        let h = try c.decodeIfPresent(CGFloat.self, forKey: .h) ?? 120
        cardSize = CGSize(width: w, height: h)
    }

    func encode(to encoder: Encoder) throws {
        var c = encoder.container(keyedBy: CodingKeys.self)
        try c.encode(id, forKey: .id)
        try c.encode(type, forKey: .type)
        try c.encode(content, forKey: .content)
        try c.encode(params, forKey: .params)
        try c.encodeIfPresent(sceneTag, forKey: .sceneTag)
        try c.encode(position.x, forKey: .x)
        try c.encode(position.y, forKey: .y)
        try c.encode(cardSize.width, forKey: .w)
        try c.encode(cardSize.height, forKey: .h)
    }
}

// MARK: - Connection
