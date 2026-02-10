// CalibrationResult.swift
// Hypnogen
//
// Data model for subliminal audibility calibration results.
// Persisted via UserDefaults for cross-launch persistence.

import Foundation

/// A single calibration level with its dB gain and human-readable description.
struct CalibrationLevel: Identifiable, Equatable, Sendable {
    let id: Int
    let gainDb: Double
    let label: String
    let description: String

    /// Index-based identity matching CALIBRATION_LEVELS order.
    init(index: Int, gainDb: Double, label: String, description: String) {
        self.id = index
        self.gainDb = gainDb
        self.label = label
        self.description = description
    }
}

/// All available calibration levels, mirroring Python's CALIBRATION_LEVELS.
enum CalibrationLevels {
    static let all: [CalibrationLevel] = [
        CalibrationLevel(index: 0, gainDb: -30, label: "Very Subtle", description: "Barely perceptible"),
        CalibrationLevel(index: 1, gainDb: -24, label: "Subtle", description: "Quiet background"),
        CalibrationLevel(index: 2, gainDb: -18, label: "Balanced", description: "Optimal for most"),
        CalibrationLevel(index: 3, gainDb: -12, label: "Audible", description: "Clearly hear words"),
        CalibrationLevel(index: 4, gainDb: -6, label: "Clear", description: "Very audible"),
    ]

    static let defaultLevel = all[2] // -18 dB

    static func level(forGainDb gainDb: Double) -> CalibrationLevel? {
        all.first { $0.gainDb == gainDb }
    }
}

/// Persisted calibration result.
struct CalibrationResult: Codable, Equatable, Sendable {
    /// The chosen subliminal gain level in dB.
    let gainDb: Double
    /// When calibration was completed.
    let completedAt: Date
    /// Whether the user completed the full flow (vs skipping with default).
    let wasSkipped: Bool

    enum CodingKeys: String, CodingKey {
        case gainDb = "gain_db"
        case completedAt = "completed_at"
        case wasSkipped = "was_skipped"
    }
}

// MARK: - UserDefaults Persistence

enum CalibrationStore {
    private static let storageKey = "calibrationResult"

    /// Load the persisted calibration result, if any.
    static func load() -> CalibrationResult? {
        guard let data = UserDefaults.standard.data(forKey: storageKey) else { return nil }
        return try? JSONDecoder.iso8601.decode(CalibrationResult.self, from: data)
    }

    /// Save a calibration result to UserDefaults.
    static func save(_ result: CalibrationResult) {
        if let data = try? JSONEncoder.iso8601.encode(result) {
            UserDefaults.standard.set(data, forKey: storageKey)
        }
    }

    /// Whether a calibration has been completed (or skipped).
    static var hasCalibrated: Bool {
        load() != nil
    }

    /// Clear stored calibration (for testing).
    static func clear() {
        UserDefaults.standard.removeObject(forKey: storageKey)
    }
}

// MARK: - JSON Coding Helpers

private extension JSONDecoder {
    static let iso8601: JSONDecoder = {
        let decoder = JSONDecoder()
        decoder.dateDecodingStrategy = .iso8601
        return decoder
    }()
}

private extension JSONEncoder {
    static let iso8601: JSONEncoder = {
        let encoder = JSONEncoder()
        encoder.dateEncodingStrategy = .iso8601
        return encoder
    }()
}
