// Project.swift
// Hypnogen
//
// Data model for a Hypnogen project (script + affirmations + settings).
// Persisted as file-based portable folders under ~/Library/Application Support/Hypnogen/.

import Foundation
import Observation

/// Render settings for a project.
struct RenderSettings: Codable, Equatable, Sendable {
    var voice: String = Constants.Defaults.voice
    var swarmVoice: String?
    var seed: Int?
    var lengthSec: Int?
    var exportStems: Bool = false
    var gainDb: [String: Double]?

    enum CodingKeys: String, CodingKey {
        case voice
        case swarmVoice = "swarm_voice"
        case seed
        case lengthSec = "length_sec"
        case exportStems = "export_stems"
        case gainDb = "gain_db"
    }
}

/// A Hypnogen project containing a script, affirmations, and render settings.
@Observable
final class Project: Identifiable, Codable, Hashable {
    let id: UUID
    var name: String
    var createdAt: Date
    var modifiedAt: Date
    var scriptText: String
    var affirmations: [String]
    var settings: RenderSettings

    init(
        id: UUID = UUID(),
        name: String = "Untitled Project",
        createdAt: Date = Date(),
        modifiedAt: Date = Date(),
        scriptText: String = "",
        affirmations: [String] = [],
        settings: RenderSettings = RenderSettings()
    ) {
        self.id = id
        self.name = name
        self.createdAt = createdAt
        self.modifiedAt = modifiedAt
        self.scriptText = scriptText
        self.affirmations = affirmations
        self.settings = settings
    }

    // MARK: - Codable

    enum CodingKeys: String, CodingKey {
        case id, name
        case createdAt = "created_at"
        case modifiedAt = "modified_at"
        case scriptText = "script_text"
        case affirmations, settings
    }

    required init(from decoder: Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        id = try container.decode(UUID.self, forKey: .id)
        name = try container.decode(String.self, forKey: .name)
        createdAt = try container.decode(Date.self, forKey: .createdAt)
        modifiedAt = try container.decode(Date.self, forKey: .modifiedAt)
        scriptText = try container.decode(String.self, forKey: .scriptText)
        affirmations = try container.decode([String].self, forKey: .affirmations)
        settings = try container.decode(RenderSettings.self, forKey: .settings)
    }

    func encode(to encoder: Encoder) throws {
        var container = encoder.container(keyedBy: CodingKeys.self)
        try container.encode(id, forKey: .id)
        try container.encode(name, forKey: .name)
        try container.encode(createdAt, forKey: .createdAt)
        try container.encode(modifiedAt, forKey: .modifiedAt)
        try container.encode(scriptText, forKey: .scriptText)
        try container.encode(affirmations, forKey: .affirmations)
        try container.encode(settings, forKey: .settings)
    }

    // MARK: - Hashable / Equatable

    static func == (lhs: Project, rhs: Project) -> Bool {
        lhs.id == rhs.id
    }

    func hash(into hasher: inout Hasher) {
        hasher.combine(id)
    }

    // MARK: - Helpers

    /// Mark the project as modified (updates timestamp).
    func touch() {
        modifiedAt = Date()
    }
}
