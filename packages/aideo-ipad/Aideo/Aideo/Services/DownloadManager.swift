import Foundation

// MARK: - Model

/// 已下载视频文件描述
struct DownloadedFile: Identifiable, Codable, Equatable {
    var id: UUID { taskId }
    let taskId: UUID
    let fileName: String
    let fileSize: Int64
    let downloadDate: Date
    let localPath: String

    var fileSizeFormatted: String {
        ByteCountFormatter.string(fromByteCount: fileSize, countStyle: .file)
    }
}

// MARK: - Manager

/// 文件下载管理器
actor DownloadManager {
    let downloadDir: URL

    init() {
        let docs = FileManager.default.urls(for: .documentDirectory, in: .userDomainMask)[0]
        self.downloadDir = docs.appendingPathComponent("AideoDownloads", isDirectory: true)
        try? FileManager.default.createDirectory(at: downloadDir, withIntermediateDirectories: true)
    }

    // MARK: - Download

    /// 下载视频（含进度回调），返回保存的本地文件
    func download(
        taskId: UUID,
        from url: URL,
        onProgress: @Sendable @escaping (Double) -> Void = { _ in }
    ) async throws -> DownloadedFile {
        let fileName = "\(taskId.uuidString).mp4"
        let destination = downloadDir.appendingPathComponent(fileName)

        // 已存在则跳过
        if FileManager.default.fileExists(atPath: destination.path) {
            let attr = try? FileManager.default.attributesOfItem(atPath: destination.path)
            let size = (attr?[.size] as? Int64) ?? 0
            onProgress(1.0)
            return DownloadedFile(
                taskId: taskId, fileName: fileName, fileSize: size,
                downloadDate: Date(), localPath: destination.path
            )
        }

        return try await withCheckedThrowingContinuation { continuation in
            let task = URLSession.shared.downloadTask(with: url) { tmpURL, _, error in
                if let error {
                    continuation.resume(throwing: error)
                    return
                }
                guard let tmpURL else {
                    continuation.resume(throwing: URLError(.badServerResponse))
                    return
                }
                do {
                    try? FileManager.default.removeItem(at: destination)
                    try FileManager.default.moveItem(at: tmpURL, to: destination)
                    let attr = try FileManager.default.attributesOfItem(atPath: destination.path)
                    let size = (attr[.size] as? Int64) ?? 0
                    let file = DownloadedFile(
                        taskId: taskId, fileName: fileName, fileSize: size,
                        downloadDate: Date(), localPath: destination.path
                    )
                    continuation.resume(returning: file)
                } catch {
                    continuation.resume(throwing: error)
                }
            }

            let obs = task.progress.observe(\.fractionCompleted, options: [.new]) { progress, _ in
                onProgress(progress.fractionCompleted)
            }

            task.resume()

            // 保持 observation 存活直到下载完成
            withExtendedLifetime(obs) {}
        }
    }

    // MARK: - List

    func listDownloads() -> [DownloadedFile] {
        guard let contents = try? FileManager.default.contentsOfDirectory(
            at: downloadDir,
            includingPropertiesForKeys: [.fileSizeKey, .creationDateKey],
            options: .skipsHiddenFiles
        ) else { return [] }

        return contents.compactMap { url -> DownloadedFile? in
            guard url.pathExtension == "mp4",
                  let attr = try? FileManager.default.attributesOfItem(atPath: url.path),
                  let size = attr[.size] as? Int64,
                  let date = attr[.creationDate] as? Date else { return nil }

            let name = url.deletingPathExtension().lastPathComponent
            guard UUID(uuidString: name) != nil else { return nil }

            return DownloadedFile(
                taskId: UUID(uuidString: name)!,
                fileName: url.lastPathComponent,
                fileSize: size,
                downloadDate: date,
                localPath: url.path
            )
        }
        .sorted { $0.downloadDate > $1.downloadDate }
    }

    // MARK: - Delete

    func deleteDownload(taskId: UUID) throws {
        let url = downloadDir.appendingPathComponent("\(taskId.uuidString).mp4")
        if FileManager.default.fileExists(atPath: url.path) {
            try FileManager.default.removeItem(at: url)
        }
    }
}
