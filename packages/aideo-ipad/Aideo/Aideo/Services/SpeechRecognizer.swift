import Foundation
import AVFoundation

// MARK: - Events

enum SpeechEvent: Sendable {
    case transcribing(String)   // 实时中间结果
    case result(String)         // 最终转录文本
    case error(String)          // 失败
}

// MARK: - Recognizer

/// 语音识别器 — 录音积攒 PCM → 停止时发送完整 WAV → 等待转录结果
actor SpeechRecognizer {
    private let serverURL: String
    private nonisolated(unsafe) var engine: AVAudioEngine?
    private nonisolated(unsafe) var wsTask: URLSessionWebSocketTask?
    private nonisolated(unsafe) var wsSession: URLSession?
    private nonisolated(unsafe) var isRecording = false
    private nonisolated(unsafe) var pcmBuffer = Data()

    init(serverURL: String) {
        self.serverURL = serverURL
    }

    // MARK: - Permissions

    func requestPermission() async -> Bool {
        await AVAudioApplication.requestRecordPermission()
    }

    // MARK: - Record & Transcribe

    func startRecording() async throws -> AsyncStream<SpeechEvent> {
        guard !isRecording else { throw SpeechError.alreadyRecording }

        fullCleanup()
        pcmBuffer = Data()

        let granted = await requestPermission()
        guard granted else { throw SpeechError.permissionDenied }

        let session = AVAudioSession.sharedInstance()
        try session.setCategory(.record, mode: .measurement, options: .duckOthers)
        try session.setActive(true)

        // 先只连 WS（不录音），等 stop 时才发数据
        let wsURLStr = serverURL
            .replacingOccurrences(of: "http://", with: "ws://")
            .replacingOccurrences(of: "https://", with: "wss://")
            + "/api/v1/ws/transcribe"
        guard let wsURL = URL(string: wsURLStr) else { throw SpeechError.invalidURL }

        let urlSession = URLSession(configuration: .default)
        let task = urlSession.webSocketTask(with: wsURL)
        self.wsSession = urlSession
        self.wsTask = task
        task.resume()

        // 设置音频引擎
        let audioEngine = AVAudioEngine()
        let inputNode = audioEngine.inputNode
        let inputFormat = inputNode.outputFormat(forBus: 0)

        guard let recordingFormat = AVAudioFormat(
            commonFormat: .pcmFormatInt16,
            sampleRate: 16000, channels: 1, interleaved: true
        ) else { throw SpeechError.audioEngineSetupFailed }

        guard let converter = AVAudioConverter(from: inputFormat, to: recordingFormat) else {
            throw SpeechError.audioEngineSetupFailed
        }

        isRecording = true
        self.engine = audioEngine

        return AsyncStream { continuation in
            self.transcriptContinuation = continuation
            // 安装音频 tap — 只积攒 PCM，不发送
            inputNode.installTap(onBus: 0, bufferSize: 4096, format: inputFormat) { [weak self] buffer, _ in
                guard let self else { return }
                let converted = self.convertBuffer(buffer, from: inputFormat, to: recordingFormat, converter: converter)
                if let channelData = converted.int16ChannelData {
                    let samples = Data(bytes: channelData.pointee, count: Int(converted.frameLength) * 2)
                    self.pcmBuffer.append(samples)
                }
            }

            do {
                audioEngine.prepare()
                try audioEngine.start()
            } catch {
                continuation.yield(.error(error.localizedDescription))
                continuation.finish()
                fullCleanup()
            }

            continuation.onTermination = { [weak self] _ in
                guard let self else { return }
                self.fullCleanup()
            }
        }
    }

    func stopRecording() {
        stopEngine()

        // 积攒的 PCM → 完整 WAV → 发送 → 等待结果
        let wav = buildWAV(from: pcmBuffer)
        pcmBuffer = Data()

        guard !wav.isEmpty, let ws = wsTask else {
            fullCleanup()
            return
        }

        Task {
            do {
                try await ws.send(.data(wav))
                // 发送完后等结果 — receiveTranscriptionLoop 会处理
            } catch {
                fullCleanup()
            }
        }

        // 启动接收 loop
        Task { [weak self] in
            await self?.receiveTranscriptionLoop()
        }
    }

    // MARK: - Private

    private var transcriptContinuation: AsyncStream<SpeechEvent>.Continuation?

    private func receiveTranscriptionLoop() async {
        guard let ws = wsTask else { return }
        let decoder = JSONDecoder()

        while let wsTask = self.wsTask, !Task.isCancelled {
            do {
                let message = try await wsTask.receive()
                switch message {
                case .string(let text):
                    guard let data = text.data(using: .utf8),
                          let event = try? decoder.decode(TranscribeEvent.self, from: data)
                    else { continue }
                    switch event.type {
                    case "progress":
                        if let partial = event.data?["message"]?.stringValue {
                            transcriptContinuation?.yield(.transcribing(partial))
                        }
                    case "result":
                        if let fullText = event.data?["full_text"]?.stringValue {
                            transcriptContinuation?.yield(.result(fullText))
                        }
                        transcriptContinuation?.finish()
                        transcriptContinuation = nil
                        fullCleanup()
                        return
                    case "error":
                        let msg = event.data?["message"]?.stringValue ?? "Transcription failed"
                        transcriptContinuation?.yield(.error(msg))
                        transcriptContinuation?.finish()
                        transcriptContinuation = nil
                        fullCleanup()
                        return
                    default: break
                    }
                case .data: break
                @unknown default: break
                }
            } catch {
                transcriptContinuation?.yield(.error(error.localizedDescription))
                transcriptContinuation?.finish()
                transcriptContinuation = nil
                fullCleanup()
                return
            }
        }
    }

    private nonisolated func stopEngine() {
        engine?.inputNode.removeTap(onBus: 0)
        engine?.stop()
        engine = nil
        isRecording = false
    }

    private nonisolated func fullCleanup() {
        stopEngine()
        wsTask?.cancel(with: .normalClosure, reason: nil)
        wsTask = nil
        wsSession = nil
    }

    private nonisolated func convertBuffer(_ buffer: AVAudioPCMBuffer, from inputFormat: AVAudioFormat, to outputFormat: AVAudioFormat, converter: AVAudioConverter) -> AVAudioPCMBuffer {
        let cap = AVAudioFrameCount(outputFormat.sampleRate / inputFormat.sampleRate * Double(buffer.frameLength)) + 1024
        guard let output = AVAudioPCMBuffer(pcmFormat: outputFormat, frameCapacity: cap) else { return buffer }
        var error: NSError?
        converter.convert(to: output, error: &error, withInputFrom: { _, outStatus in outStatus.pointee = .haveData; return buffer })
        return output
    }

    private nonisolated func buildWAV(from pcm: Data) -> Data {
        guard !pcm.isEmpty else { return Data() }
        let dataSize = UInt32(pcm.count)
        var sampleRate: UInt32 = 16000
        var channels: UInt16 = 1
        var bitsPerSample: UInt16 = 16
        var byteRate = sampleRate * UInt32(channels) * UInt32(bitsPerSample / 8)
        var blockAlign = channels * (bitsPerSample / 8)
        var fileSize = dataSize + 36
        var dsz = dataSize

        var header = Data()
        header.append("RIFF".data(using: .ascii)!)
        header.append(Data(bytes: &fileSize, count: 4))
        header.append("WAVE".data(using: .ascii)!)
        header.append("fmt ".data(using: .ascii)!)
        header.append(Data([16, 0, 0, 0]))
        header.append(Data([1, 0]))
        header.append(Data(bytes: &channels, count: 2))
        header.append(Data(bytes: &sampleRate, count: 4))
        header.append(Data(bytes: &byteRate, count: 4))
        header.append(Data(bytes: &blockAlign, count: 2))
        header.append(Data(bytes: &bitsPerSample, count: 2))
        header.append("data".data(using: .ascii)!)
        header.append(Data(bytes: &dsz, count: 4))
        return header + pcm
    }
}

// MARK: - Errors

enum SpeechError: LocalizedError {
    case permissionDenied, alreadyRecording, audioEngineSetupFailed, invalidURL
    var errorDescription: String? {
        switch self {
        case .permissionDenied: "麦克风权限未授权"
        case .alreadyRecording: "已在录音中"
        case .audioEngineSetupFailed: "音频引擎初始化失败"
        case .invalidURL: "无效的服务器地址"
        }
    }
}

private struct TranscribeEvent: Codable {
    let type: String?
    let task_id: String?
    let data: [String: AnyCodable]?
}
