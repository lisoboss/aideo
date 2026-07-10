import Foundation

/// 视频生成参数
struct GenerationParams: Codable, Equatable {
    var duration: Int?          // 5, 10
    var resolution: String?     // "720p", "1080p"
    var style: String?          // "cinematic", "anime", "realistic"
    var seed: Int?
    var fps: Int?               // 24, 30
    var cfgScale: Double?       // 7.5
    var steps: Int?             // 50

    // 图片生成
    var aspectRatio: String?    // "16:9", "4:3", "1:1", "3:2", "9:16"
    var imageQuality: String?   // "standard", "high", "ultra"

    enum CodingKeys: String, CodingKey {
        case duration, resolution, style, seed, fps
        case cfgScale = "cfg_scale"
        case steps
        case aspectRatio = "aspect_ratio"
        case imageQuality = "image_quality"
    }

    /// 参数是否全部为 nil（即用户未设置任何参数）
    var isEmpty: Bool {
        duration == nil && resolution == nil && style == nil
            && seed == nil && fps == nil && cfgScale == nil && steps == nil
            && aspectRatio == nil && imageQuality == nil
    }

    /// 预定义分辨率选项
    static let resolutionOptions = ["720p", "1080p"]

    /// 预定义风格选项
    static let styleOptions = ["cinematic", "anime", "realistic", "oil-painting", "3d-render", "cyberpunk"]

    /// 预定义时长选项（秒）
    static let durationOptions = [5, 10]

    /// 转换为字典（用于 JSON body）
    func asDictionary() -> [String: Any] {
        var dict: [String: Any] = [:]
        if let v = duration   { dict["duration"] = v }
        if let v = resolution { dict["resolution"] = v }
        if let v = style      { dict["style"] = v }
        if let v = seed       { dict["seed"] = v }
        if let v = fps        { dict["fps"] = v }
        if let v = cfgScale   { dict["cfg_scale"] = v }
        if let v = steps      { dict["steps"] = v }
        return dict
    }
}
