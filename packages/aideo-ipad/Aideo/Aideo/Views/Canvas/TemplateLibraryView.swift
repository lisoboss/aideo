import SwiftUI

// MARK: - Template

/// 节点模板
struct NodeTemplate: Identifiable {
    let id = UUID()
    let name: String
    let category: TemplateCategory
    let type: BlockType
    let content: String
    let params: GenerationParams
    let icon: String
}

enum TemplateCategory: String, CaseIterable, Identifiable {
    case nature = "自然风光"
    case urban = "城市生活"
    case action = "动作场景"
    case scifi = "科幻奇幻"
    case emotion = "情感氛围"
    case abstract = "抽象创意"

    var id: String { rawValue }
    var icon: String {
        switch self {
        case .nature: "leaf"
        case .urban: "building.2"
        case .action: "figure.run"
        case .scifi: "sparkles"
        case .emotion: "heart"
        case .abstract: "circle.hexagonpath"
        }
    }
}

// MARK: - Library

/// 预设模板库
enum TemplateLibrary {
    static let all: [NodeTemplate] = [
        // 自然风光
        NodeTemplate(name: "金色日落", category: .nature, type: .scene,
                     content: "海边金色日落，海浪轻拍沙滩，天空从橙渐变到紫，飞鸟掠过",
                     params: GenerationParams(duration: 10, resolution: "1080p", style: "cinematic"),
                     icon: "sunset"),
        NodeTemplate(name: "森林清晨", category: .nature, type: .scene,
                     content: "晨雾中的松树林，阳光穿透薄雾，露珠在叶子上闪烁",
                     params: GenerationParams(duration: 10, style: "cinematic"),
                     icon: "tree"),
        NodeTemplate(name: "雪山之巅", category: .nature, type: .scene,
                     content: "巍峨雪山顶峰，云海翻腾，鹰在天空盘旋",
                     params: GenerationParams(duration: 5, resolution: "1080p"),
                     icon: "mountain.2"),
        NodeTemplate(name: "樱花飘落", category: .nature, type: .scene,
                     content: "樱花树下，花瓣随风飘落，阳光透过花瓣形成光斑",
                     params: GenerationParams(duration: 10, style: "anime"),
                     icon: "camera.macro"),

        // 城市生活
        NodeTemplate(name: "霓虹雨夜", category: .urban, type: .scene,
                     content: "雨夜的东京小巷，霓虹灯倒映在水洼中，路人撑着透明伞走过",
                     params: GenerationParams(duration: 10, resolution: "1080p", style: "cyberpunk"),
                     icon: "cloud.rain"),
        NodeTemplate(name: "晨间都市", category: .urban, type: .scene,
                     content: "清晨城市天际线，上班族匆匆走过，咖啡店蒸汽升腾",
                     params: GenerationParams(duration: 10, style: "cinematic"),
                     icon: "building"),
        NodeTemplate(name: "夜市烟火", category: .urban, type: .scene,
                     content: "夜市小吃摊烟火气，人们围坐吃烧烤，暖黄灯光",
                     params: GenerationParams(duration: 10, style: "realistic"),
                     icon: "flame"),

        // 动作场景
        NodeTemplate(name: "追车戏", category: .action, type: .action,
                     content: "城市街头高速追车，漂移过弯，火花四溅",
                     params: GenerationParams(duration: 10, style: "cinematic", fps: 30),
                     icon: "car"),
        NodeTemplate(name: "武打对决", category: .action, type: .action,
                     content: "两个武者在天台对决，慢镜头拳头擦过脸颊，汗珠飞溅",
                     params: GenerationParams(duration: 10, fps: 60),
                     icon: "figure.martial.arts"),
        NodeTemplate(name: "极限运动", category: .action, type: .action,
                     content: "滑板手在城市台阶上跳跃，慢镜头捕捉空中姿态",
                     params: GenerationParams(duration: 5, fps: 60),
                     icon: "skateboard"),

        // 科幻奇幻
        NodeTemplate(name: "太空站", category: .scifi, type: .scene,
                     content: "国际空间站内部，宇航员漂浮着工作，窗外是地球和星空",
                     params: GenerationParams(duration: 10, style: "3d-render"),
                     icon: "sparkles"),
        NodeTemplate(name: "赛博朋克市场", category: .scifi, type: .scene,
                     content: "赛博朋克地下市场，全息投影广告，cyborg商贩",
                     params: GenerationParams(duration: 10, style: "cyberpunk"),
                     icon: "cpu"),
        NodeTemplate(name: "魔法森林", category: .scifi, type: .scene,
                     content: "发光蘑菇森林，精灵飞舞，魔法粒子漂浮",
                     params: GenerationParams(duration: 10, style: "anime"),
                     icon: "wand.and.stars"),

        // 情感氛围
        NodeTemplate(name: "温馨一家", category: .emotion, type: .mood,
                     content: "一家人在客厅围坐，暖黄灯光，欢声笑语，温馨氛围",
                     params: GenerationParams(duration: 10, style: "cinematic"),
                     icon: "house"),
        NodeTemplate(name: "孤独旅人", category: .emotion, type: .mood,
                     content: "一个人站在火车站月台，列车远去，夕阳余晖拉长身影",
                     params: GenerationParams(duration: 10, style: "cinematic"),
                     icon: "figure.walk"),
        NodeTemplate(name: "浪漫相遇", category: .emotion, type: .mood,
                     content: "咖啡店里两人对视，慢镜头捕捉微妙表情，暖色调",
                     params: GenerationParams(duration: 10, style: "cinematic"),
                     icon: "heart"),

        // 抽象创意
        NodeTemplate(name: "几何时空", category: .abstract, type: .style,
                     content: "抽象几何体在空间中旋转变换，色彩流动，超现实风格",
                     params: GenerationParams(duration: 10, style: "3d-render"),
                     icon: "triangle"),
        NodeTemplate(name: "水墨意境", category: .abstract, type: .style,
                     content: "水墨风格动画，笔触流动，山水渐显，留白艺术",
                     params: GenerationParams(duration: 10, style: "anime"),
                     icon: "paintbrush.pointed"),
        NodeTemplate(name: "粒子舞蹈", category: .abstract, type: .style,
                     content: "万千光粒子随音乐律动，色彩渐变，梦幻效果",
                     params: GenerationParams(duration: 10, style: "3d-render"),
                     icon: "circle.dotted"),
    ]
}

// MARK: - View

/// 模板库 Sheet
struct TemplateLibraryView: View {
    let onSelect: (NodeTemplate) -> Void
    @Environment(\.dismiss) private var dismiss

    @State private var selectedCategory: TemplateCategory?

    private var filtered: [NodeTemplate] {
        if let cat = selectedCategory {
            return TemplateLibrary.all.filter { $0.category == cat }
        }
        return TemplateLibrary.all
    }

    var body: some View {
        NavigationStack {
            ScrollView {
                // 分类筛选
                ScrollView(.horizontal, showsIndicators: false) {
                    HStack(spacing: 8) {
                        FilterChip(label: "全部", isSelected: selectedCategory == nil) {
                            selectedCategory = nil
                        }
                        ForEach(TemplateCategory.allCases) { cat in
                            FilterChip(label: cat.rawValue, icon: cat.icon, isSelected: selectedCategory == cat) {
                                selectedCategory = cat
                            }
                        }
                    }
                    .padding(.horizontal)
                }
                .padding(.vertical, 8)

                // 模板网格
                LazyVGrid(columns: [.init(.adaptive(minimum: 160))], spacing: 12) {
                    ForEach(filtered) { template in
                        TemplateCard(template: template) {
                            onSelect(template)
                            dismiss()
                        }
                    }
                }
                .padding(.horizontal)
            }
            .navigationTitle("模板库")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .confirmationAction) {
                    Button("完成") { dismiss() }
                }
            }
        }
    }
}

// MARK: - Card

private struct TemplateCard: View {
    let template: NodeTemplate
    let onTap: () -> Void

    var body: some View {
        Button(action: onTap) {
            VStack(alignment: .leading, spacing: 6) {
                HStack {
                    Image(systemName: template.icon)
                        .font(.title3)
                    Spacer()
                    Text(template.category.rawValue)
                        .font(.caption2)
                        .foregroundStyle(.secondary)
                }

                Text(template.name)
                    .font(.subheadline.weight(.semibold))
                    .foregroundStyle(.primary)

                Text(template.content)
                    .font(.caption)
                    .foregroundStyle(.secondary)
                    .lineLimit(2)

                HStack(spacing: 4) {
                    if let d = template.params.duration { Tag("\(d)s") }
                    if let r = template.params.resolution { Tag(r) }
                    if let s = template.params.style { Tag(s) }
                }
            }
            .padding(12)
            .background(Color(uiColor: .systemBackground))
            .clipShape(RoundedRectangle(cornerRadius: 10))
            .shadow(color: .black.opacity(0.05), radius: 4, y: 2)
        }
        .buttonStyle(.plain)
    }
}

private struct Tag: View {
    let text: String
    init(_ t: String) { text = t }
    var body: some View {
        Text(text)
            .font(.caption2)
            .padding(.horizontal, 6).padding(.vertical, 2)
            .background(Color(uiColor: .systemGray5))
            .clipShape(Capsule())
    }
}

private struct FilterChip: View {
    let label: String
    var icon: String? = nil
    let isSelected: Bool
    let action: () -> Void

    var body: some View {
        Button(action: action) {
            HStack(spacing: 4) {
                if let icon { Image(systemName: icon).font(.caption) }
                Text(label).font(.caption)
            }
            .padding(.horizontal, 12).padding(.vertical, 6)
            .background(isSelected ? Color.accentColor : Color(uiColor: .systemGray5))
            .foregroundStyle(isSelected ? .white : .primary)
            .clipShape(Capsule())
        }
        .buttonStyle(.plain)
    }
}
