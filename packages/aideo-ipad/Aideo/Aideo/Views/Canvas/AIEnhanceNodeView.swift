import SwiftUI

/// AI 增强节点 — 简单描述 → LLM 详细提示词
struct AIEnhanceNodeView: View {
    @Environment(AppState.self) private var appState
    let node: AIEnhanceNode
    let isConnectMode: Bool
    let onDelete: () -> Void
    let onConnect: () -> Void
    let onUpdate: (AIEnhanceNode) -> Void
    let onResize: (CGSize) -> Void
    let onProcess: (String) async -> [AssistBlock]?  // input → blocks, nil = error
    let onDrag: (CGPoint) -> Void

    @State private var dragOffset: CGSize = .zero
    @State private var inputText: String = ""
    @State private var isProcessing: Bool = false
    @State private var isRecording: Bool = false
    @State private var isTranscribing: Bool = false
    @FocusState private var isFocused: Bool

    var body: some View {
        VStack(alignment: .leading, spacing: 4) {
            // 头部
            HStack {
                Image(systemName: "sparkles").font(.caption)
                Text("AI 增强").font(.caption).fontWeight(.medium)
                Spacer()
                Button(action: onConnect) {
                    Image(systemName: "arrow.triangle.pull")
                        .font(.caption2).foregroundStyle(.white.opacity(0.6))
                }.buttonStyle(.plain)
                Button(action: onDelete) {
                    Image(systemName: "xmark.circle.fill")
                        .font(.caption).foregroundStyle(.white.opacity(0.7))
                }.buttonStyle(.plain)
            }.foregroundStyle(.white)

            // 输入区
            if node.status == .idle || node.status == .error {
                TextField("简单描述...", text: $inputText, axis: .vertical)
                    .focused($isFocused)
                    .font(.caption).foregroundStyle(.white)
                    .padding(6)
                    .background(RoundedRectangle(cornerRadius: 6).fill(.white.opacity(0.15)))
                    .lineLimit(6)

                HStack {
                    if node.status == .error {
                        Image(systemName: "exclamationmark.triangle")
                            .font(.caption2).foregroundStyle(.yellow)
                        if let err = node.errorMessage {
                            Text(err).font(.caption2).foregroundStyle(.white.opacity(0.6)).lineLimit(1)
                        }
                    }
                    Spacer()
                    // 语音输入
                    Button {
                        handleVoiceInput()
                    } label: {
                        if isTranscribing {
                            ProgressView().scaleEffect(0.6).tint(.white)
                        } else {
                            Image(systemName: isRecording ? "mic.fill" : "mic")
                                .font(.caption2)
                        }
                    }
                    .foregroundStyle(isRecording ? .red : .white.opacity(0.8))
                    .buttonStyle(.plain).disabled(isProcessing || isTranscribing)
                    Button {
                        guard !inputText.isEmpty else { return }
                        let text = inputText
                        isProcessing = true
                        var updated = node; updated.status = .processing
                        onUpdate(updated)
                        Task {
                            let result = await onProcess(text)
                            await MainActor.run {
                                var done = node; done.inputText = text
                                if let blocks = result {
                                    // 格式化为可读字符串展示
                                    done.outputText = blocks.map { "[\($0.type)]: \($0.content)" }.joined(separator: "\n")
                                    done.status = .done
                                } else {
                                    done.status = .error; done.errorMessage = "处理失败"
                                }
                                onUpdate(done); isProcessing = false
                            }
                        }
                    } label: {
                        Label("生成", systemImage: "sparkles")
                            .font(.caption2.weight(.semibold)).foregroundStyle(.white)
                            .padding(.horizontal, 12).padding(.vertical, 5)
                            .background(Capsule().fill(.white.opacity(0.25)))
                    }
                    .buttonStyle(.plain).disabled(inputText.isEmpty || isProcessing)
                }
            }

            // 处理中
            if node.status == .processing {
                HStack(spacing: 6) {
                    ProgressView().tint(.white).scaleEffect(0.7)
                    Text("AI 思考中...").font(.caption2).foregroundStyle(.white.opacity(0.7))
                }.padding(.vertical, 8)
            }

            // 完成态 — 显示输出
            if node.status == .done, !node.outputText.isEmpty {
                ScrollView(.vertical) {
                    Text(node.outputText)
                        .font(.caption).foregroundStyle(.white)
                        .frame(maxWidth: .infinity, alignment: .leading)
                }
                .padding(6)
                .background(RoundedRectangle(cornerRadius: 6).fill(.white.opacity(0.15)))

                HStack {
                    Spacer()
                    Button {
                        UIPasteboard.general.string = node.outputText
                    } label: {
                        Label("已复制", systemImage: "doc.on.doc")
                            .font(.caption2).foregroundStyle(.white.opacity(0.6))
                    }.buttonStyle(.plain)
                }
            }

            // 撑满剩余空间
            Spacer(minLength: 0)
        }
        .padding(10)
        .frame(width: max(node.nodeSize.width, 100), height: max(node.nodeSize.height, 80))
        .background(RoundedRectangle(cornerRadius: 12).fill(Color(hex: "#9B59B6")))
        .overlay(alignment: .bottomTrailing) {
            ResizeHandle(canvasScale: 1.0, currentSize: node.nodeSize, onResize: onResize)
        }
        .shadow(color: .black.opacity(0.2), radius: 4, y: 2)
        .onAppear { inputText = node.inputText }
        .offset(dragOffset)
        .gesture(
            DragGesture()
                .onChanged { dragOffset = $0.translation }
                .onEnded { v in
                    let n = CGPoint(x: node.position.x + v.translation.width,
                                    y: node.position.y + v.translation.height)
                    dragOffset = .zero; onDrag(n)
                }
        )
    }

    // MARK: - Voice Input

    private func handleVoiceInput() {
        guard !isRecording else {
            Task { await appState.speechRecognizer.stopRecording() }
            isRecording = false
            isTranscribing = true
            return
        }
        isRecording = true
        isTranscribing = false
        Task {
            do {
                let stream = try await appState.speechRecognizer.startRecording()
                for await event in stream {
                    await MainActor.run {
                        switch event {
                        case .transcribing:
                            isRecording = false
                            isTranscribing = true
                        case .result(let text):
                            if inputText.isEmpty { inputText = text }
                            else { inputText += " " + text }
                            isRecording = false
                            isTranscribing = false
                        case .error:
                            isRecording = false
                            isTranscribing = false
                        }
                    }
                }
            } catch {
                await MainActor.run {
                    isRecording = false
                    isTranscribing = false
                }
            }
        }
    }
}
