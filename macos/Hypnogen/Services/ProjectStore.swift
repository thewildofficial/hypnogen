// ProjectStore.swift
// Hypnogen
//
// File-based persistence for projects.
// Projects are stored as JSON files in ~/Library/Application Support/Hypnogen/projects/.

import Foundation

/// Manages loading and saving projects to disk.
final class ProjectStore {
    private let fileManager = FileManager.default
    private let encoder: JSONEncoder
    private let decoder: JSONDecoder

    /// Root directory for project storage.
    private var projectsDirectory: URL {
        let appSupport = fileManager.urls(for: .applicationSupportDirectory, in: .userDomainMask).first!
        return appSupport
            .appendingPathComponent(Constants.Storage.appSupportSubdirectory)
            .appendingPathComponent("projects")
    }

    init() {
        encoder = JSONEncoder()
        encoder.outputFormatting = [.prettyPrinted, .sortedKeys]
        encoder.dateEncodingStrategy = .iso8601

        decoder = JSONDecoder()
        decoder.dateDecodingStrategy = .iso8601
    }

    // MARK: - Public API

    /// Load all projects from disk.
    func loadProjects() -> [Project] {
        ensureDirectoryExists()

        guard let contents = try? fileManager.contentsOfDirectory(
            at: projectsDirectory,
            includingPropertiesForKeys: [.isDirectoryKey],
            options: .skipsHiddenFiles
        ) else {
            return []
        }

        return contents.compactMap { url in
            let projectFile = url.appendingPathComponent(Constants.Storage.projectFileName)
            guard let data = try? Data(contentsOf: projectFile) else { return nil }
            return try? decoder.decode(Project.self, from: data)
        }
        .sorted { $0.modifiedAt > $1.modifiedAt }
    }

    /// Save a project to disk.
    func save(_ project: Project) throws {
        ensureDirectoryExists()

        let projectDir = projectsDirectory.appendingPathComponent(project.id.uuidString)
        try fileManager.createDirectory(at: projectDir, withIntermediateDirectories: true)

        let data = try encoder.encode(project)
        let fileURL = projectDir.appendingPathComponent(Constants.Storage.projectFileName)
        try data.write(to: fileURL, options: .atomic)
    }

    /// Delete a project from disk.
    func delete(_ project: Project) throws {
        let projectDir = projectsDirectory.appendingPathComponent(project.id.uuidString)
        if fileManager.fileExists(atPath: projectDir.path) {
            try fileManager.removeItem(at: projectDir)
        }
    }

    // MARK: - Private

    private func ensureDirectoryExists() {
        try? fileManager.createDirectory(
            at: projectsDirectory,
            withIntermediateDirectories: true
        )
    }
}
