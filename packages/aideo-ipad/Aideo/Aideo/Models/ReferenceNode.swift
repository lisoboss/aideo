import Foundation
import CoreGraphics
import UIKit

enum ReferenceMediaType: String, Codable {
    case image, video
}

struct ReferenceNode: Identifiable, Codable, Equatable {
    var id: UUID = UUID()
    var position: CGPoint = .zero
    var nodeSize: CGSize = CGSize(width: 180, height: 120)
    var mediaType: ReferenceMediaType = .image
    var localPath: String = ""
    var sourceLabel: String = ""

    var thumbnail: UIImage? {
        guard !localPath.isEmpty else { return nil }
        return UIImage(contentsOfFile: localPath)
    }

    init(id: UUID = UUID(), position: CGPoint = .zero, nodeSize: CGSize = CGSize(width: 180, height: 120),
         mediaType: ReferenceMediaType = .image, localPath: String = "", sourceLabel: String = "") {
        self.id = id; self.position = position; self.nodeSize = nodeSize
        self.mediaType = mediaType; self.localPath = localPath; self.sourceLabel = sourceLabel
    }

    enum CodingKeys: String, CodingKey { case id, mediaType, localPath, sourceLabel, x, y, w, h }

    init(from decoder: Decoder) throws {
        let c = try decoder.container(keyedBy: CodingKeys.self)
        id = try c.decode(UUID.self, forKey: .id)
        mediaType = try c.decode(ReferenceMediaType.self, forKey: .mediaType)
        localPath = try c.decode(String.self, forKey: .localPath)
        sourceLabel = try c.decode(String.self, forKey: .sourceLabel)
        position = CGPoint(x: try c.decode(CGFloat.self, forKey: .x), y: try c.decode(CGFloat.self, forKey: .y))
        nodeSize = CGSize(width: try c.decodeIfPresent(CGFloat.self, forKey: .w) ?? 180,
                          height: try c.decodeIfPresent(CGFloat.self, forKey: .h) ?? 120)
    }

    func encode(to encoder: Encoder) throws {
        var c = encoder.container(keyedBy: CodingKeys.self)
        try c.encode(id, forKey: .id); try c.encode(mediaType, forKey: .mediaType)
        try c.encode(localPath, forKey: .localPath); try c.encode(sourceLabel, forKey: .sourceLabel)
        try c.encode(position.x, forKey: .x); try c.encode(position.y, forKey: .y)
        try c.encode(nodeSize.width, forKey: .w); try c.encode(nodeSize.height, forKey: .h)
    }
}
