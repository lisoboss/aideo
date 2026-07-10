import Foundation

/// WebSocket 实时推送事件
struct WSEvent: Codable, Identifiable, @unchecked Sendable {
    var id: String { "\(type)-\(timestamp.timeIntervalSince1970)" }

    let type: String            // status_change | progress | preview | completed | error
    let taskId: String
    let data: [String: AnyCodable]?
    let timestamp: Date

    enum CodingKeys: String, CodingKey {
        case type
        case taskId = "task_id"
        case data
        case timestamp
    }

    /// 从 data 字典提取进度值
    var progressValue: Double? {
        data?["progress"]?.doubleValue
    }

    /// 从 data 字典提取状态值
    var statusValue: String? {
        data?["status"]?.stringValue
    }

    /// 从 data 字典提取错误消息
    var errorMessage: String? {
        data?["message"]?.stringValue
    }
}

// MARK: - AnyCodable (用于解码动态 JSON)

/// 支持解码任意 JSON 值的包装器
enum AnyCodable: Codable {
    case string(String)
    case int(Int)
    case double(Double)
    case bool(Bool)
    case dict([String: AnyCodable])
    case array([AnyCodable])
    case null

    var stringValue: String? {
        if case .string(let v) = self { return v }; return nil
    }
    var doubleValue: Double? {
        switch self {
        case .double(let v): return v
        case .int(let v): return Double(v)
        default: return nil
        }
    }

    init(from decoder: Decoder) throws {
        let container = try decoder.singleValueContainer()
        if let v = try? container.decode(String.self) { self = .string(v) }
        else if let v = try? container.decode(Int.self) { self = .int(v) }
        else if let v = try? container.decode(Double.self) { self = .double(v) }
        else if let v = try? container.decode(Bool.self) { self = .bool(v) }
        else if let v = try? container.decode([String: AnyCodable].self) { self = .dict(v) }
        else if let v = try? container.decode([AnyCodable].self) { self = .array(v) }
        else if container.decodeNil() { self = .null }
        else { throw DecodingError.dataCorruptedError(in: container, debugDescription: "Unknown JSON value") }
    }

    func encode(to encoder: Encoder) throws {
        var container = encoder.singleValueContainer()
        switch self {
        case .string(let v): try container.encode(v)
        case .int(let v): try container.encode(v)
        case .double(let v): try container.encode(v)
        case .bool(let v): try container.encode(v)
        case .dict(let v): try container.encode(v)
        case .array(let v): try container.encode(v)
        case .null: try container.encodeNil()
        }
    }
}
