// CalibrationViewModel.swift
// Hypnogen
//
// State management for the subliminal audibility calibration flow.
// Steps through 5 gain levels, collects Yes/No responses, and determines
// the optimal subliminal level for the user.

import SwiftUI
import Observation

/// Phases of the calibration flow.
enum CalibrationPhase: Equatable {
    /// Welcome screen explaining what calibration does.
    case welcome
    /// Testing a specific level (index into CalibrationLevels.all).
    case testing(levelIndex: Int)
    /// Calibration complete, showing result.
    case complete
}

@Observable
final class CalibrationViewModel {
    // MARK: - Navigation State

    var phase: CalibrationPhase = .welcome
    var isPresented: Bool = false

    // MARK: - Test State

    /// User responses: true = "Yes, I could hear it", false = "No, I couldn't".
    /// Indexed by CalibrationLevels.all position.
    private(set) var responses: [Bool?] = Array(repeating: nil, count: CalibrationLevels.all.count)

    /// The determined optimal level after calibration completes.
    private(set) var chosenLevel: CalibrationLevel?

    // MARK: - Dependencies

    private let audioPlayer = AudioPlayer()

    // MARK: - Computed Properties

    var currentLevel: CalibrationLevel? {
        guard case .testing(let index) = phase,
              index < CalibrationLevels.all.count else { return nil }
        return CalibrationLevels.all[index]
    }

    var currentLevelIndex: Int? {
        guard case .testing(let index) = phase else { return nil }
        return index
    }

    var totalLevels: Int {
        CalibrationLevels.all.count
    }

    /// Progress fraction (0.0 to 1.0) through the calibration levels.
    var progress: Double {
        guard case .testing(let index) = phase else {
            if case .complete = phase { return 1.0 }
            return 0.0
        }
        return Double(index) / Double(totalLevels)
    }

    var isPlaying: Bool {
        audioPlayer.playbackState == .playing
    }

    var playbackError: String? {
        if case .error(let message) = audioPlayer.playbackState {
            return message
        }
        return nil
    }

    /// Whether calibration has ever been completed (reads from UserDefaults).
    var hasCalibrated: Bool {
        CalibrationStore.hasCalibrated
    }

    /// The persisted calibration result, if any.
    var savedResult: CalibrationResult? {
        CalibrationStore.load()
    }

    /// Whether calibration should be shown on first launch (no prior result).
    var shouldShowOnFirstLaunch: Bool {
        !hasCalibrated
    }

    // MARK: - Actions

    /// Begin the calibration flow.
    func startCalibration() {
        responses = Array(repeating: nil, count: CalibrationLevels.all.count)
        chosenLevel = nil
        phase = .welcome
        isPresented = true
    }

    /// Advance from welcome to the first test level.
    func beginTesting() {
        phase = .testing(levelIndex: 0)
    }

    /// Play the calibration sample for the current level.
    func playCurrentSample() {
        guard let level = currentLevel else { return }
        audioPlayer.playCalibrationSample(gainDb: level.gainDb)
    }

    /// Stop any currently playing audio.
    func stopPlayback() {
        audioPlayer.stop()
    }

    /// Record the user's response for the current level and advance.
    ///
    /// - Parameter couldHear: true if user could hear the words, false otherwise.
    func recordResponse(couldHear: Bool) {
        guard case .testing(let index) = phase else { return }
        stopPlayback()
        responses[index] = couldHear

        let nextIndex = index + 1
        if nextIndex < CalibrationLevels.all.count {
            phase = .testing(levelIndex: nextIndex)
        } else {
            finishCalibration()
        }
    }

    /// Skip calibration entirely, using the default level.
    func skipCalibration() {
        stopPlayback()
        chosenLevel = CalibrationLevels.defaultLevel
        let result = CalibrationResult(
            gainDb: CalibrationLevels.defaultLevel.gainDb,
            completedAt: Date(),
            wasSkipped: true
        )
        CalibrationStore.save(result)
        phase = .complete
    }

    /// Dismiss the calibration sheet.
    func dismiss() {
        stopPlayback()
        isPresented = false
    }

    // MARK: - Level Determination

    /// Determine the optimal level from collected responses.
    ///
    /// Strategy: Find the quietest level (lowest dB) where the user said "Yes".
    /// If no "Yes" responses, use the default (-18 dB).
    /// If all "Yes", use the quietest level (-30 dB).
    private func finishCalibration() {
        let optimal = determineOptimalLevel()
        chosenLevel = optimal

        let result = CalibrationResult(
            gainDb: optimal.gainDb,
            completedAt: Date(),
            wasSkipped: false
        )
        CalibrationStore.save(result)
        phase = .complete
    }

    /// Algorithm: the optimal level is the quietest one the user could hear.
    /// Levels are ordered from quietest (-30 dB) to loudest (-6 dB).
    private func determineOptimalLevel() -> CalibrationLevel {
        // Find the first (quietest) level where user said "Yes"
        for (index, response) in responses.enumerated() where response == true {
            return CalibrationLevels.all[index]
        }
        // If user never said "Yes", fall back to default
        return CalibrationLevels.defaultLevel
    }
}
