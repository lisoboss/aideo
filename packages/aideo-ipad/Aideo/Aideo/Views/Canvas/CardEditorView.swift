import SwiftUI

/// 卡片编辑浮层 — 修改类型/内容/参数
struct CardEditorView: View {
    @Binding var block: PromptBlock
    let onDelete: () -> Void
    let onDone: () -> Void

    @FocusState private var isFocused: Bool

    var body: some View {
        NavigationStack {
            Form {
                // 类型选择
                Section("类型") {
                    LazyVGrid(columns: Array(repeating: .init(.flexible()), count: 4), spacing: 8) {
                        ForEach(BlockType.allCases, id: \.rawValue) { type in
                            Button {
                                block.type = type
                            } label: {
                                VStack(spacing: 4) {
                                    Image(systemName: type.iconName).font(.title3)
                                    Text(type.displayName).font(.caption2)
                                }
                                .frame(maxWidth: .infinity).padding(.vertical, 8)
                                .background(
                                    RoundedRectangle(cornerRadius: 8)
                                        .fill(block.type == type
                                            ? Color(hex: type.defaultColor)
                                            : Color(uiColor: .systemGray6))
                                )
                                .foregroundStyle(block.type == type ? .white : .primary)
                            }
                            .buttonStyle(.plain)
                        }
                    }
                }

                // 内容编辑
                Section("内容") {
                    TextEditor(text: $block.content)
                        .focused($isFocused).frame(minHeight: 80)
                }

                // 生成参数（内嵌到卡片）
                Section("生成参数") {
                    Picker("时长", selection: Binding(
                        get: { block.params.duration ?? 5 },
                        set: { block.params.duration = $0 }
                    )) {
                        ForEach(GenerationParams.durationOptions, id: \.self) { d in
                            Text("\(d) 秒").tag(d)
                        }
                    }

                    Picker("分辨率", selection: Binding(
                        get: { block.params.resolution ?? "1080p" },
                        set: { block.params.resolution = $0 }
                    )) {
                        ForEach(GenerationParams.resolutionOptions, id: \.self) { r in
                            Text(r).tag(r)
                        }
                    }

                    Picker("风格", selection: Binding(
                        get: { block.params.style ?? "cinematic" },
                        set: { block.params.style = $0 }
                    )) {
                        ForEach(GenerationParams.styleOptions, id: \.self) { s in
                            Text(s).tag(s)
                        }
                    }

                    HStack {
                        Text("种子 (seed)")
                        Spacer()
                        TextField("随机", value: Binding(
                            get: { block.params.seed },
                            set: { block.params.seed = $0 }
                        ), format: .number)
                        .keyboardType(.numberPad).multilineTextAlignment(.trailing)
                        .frame(width: 80)
                    }
                }
            }
            .navigationTitle("编辑卡片")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button(role: .destructive) { onDelete() } label: {
                        Image(systemName: "trash")
                    }
                }
                ToolbarItem(placement: .confirmationAction) {
                    Button("完成") { onDone() }
                }
                ToolbarItem(placement: .keyboard) { Spacer() }
            }
            .onAppear { isFocused = true }
        }
        .presentationDetents([.large])
    }
}
