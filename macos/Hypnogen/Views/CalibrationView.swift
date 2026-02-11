// CalibrationView.swift
// Hypnogen
//
// Subliminal audibility calibration flow.
// Guides the user through 5 gain levels to determine optimal subliminal volume.

import SwiftUI

struct CalibrationView: View {
    @Bindable var viewModel: CalibrationViewModel

    var body: some View {
        VStack(spacing: 0) {
            content
                .frame(maxWidth: .infinity, maxHeight: .infinity)

            if viewModel.phase != .complete {
                Divider()
                bottomBar
                    .padding(.horizontal, 24)
                    .padding(.vertical, 12)
            }
        }
        .frame(width: 520, height: 420)
        .accessibilityIdentifier(Constants.Accessibility.Calibration.calibrationView)
    }

    // MARK: - Phase Content

    @ViewBuilder
    private var content: some View {
        switch viewModel.phase {
        case .welcome:
            welcomeContent

        case .testing:
            testingContent

        case .complete:
            completeContent
        }
    }

    // MARK: - Welcome

    private var welcomeContent: some View {
        VStack(spacing: 20) {
            Spacer()

            Image(systemName: "ear.and.waveform")
                .font(.system(size: 48))
                .foregroundStyle(Color.accentColor)

            Text("Audibility Calibration")
                .font(.title)
                .fontWeight(.semibold)

            Text("We\u{2019}ll play short audio samples at different volume levels. For each one, tell us if you can hear the words clearly.")
                .font(.body)
                .foregroundStyle(.secondary)
                .multilineTextAlignment(.center)
                .frame(maxWidth: 380)

            Text("This helps Hypnogen set the right subliminal volume for your listening environment.")
                .font(.callout)
                .foregroundStyle(.tertiary)
                .multilineTextAlignment(.center)
                .frame(maxWidth: 380)

            Spacer()

            Button("Begin Calibration") {
                viewModel.beginTesting()
            }
            .buttonStyle(.borderedProminent)
            .controlSize(.large)
            .keyboardShortcut(.defaultAction)

            Spacer()
        }
        .padding(24)
    }

    // MARK: - Testing

    private var testingContent: some View {
        VStack(spacing: 16) {
            // Progress
            progressHeader

            Divider()

            Spacer()

            // Current level info
            if let level = viewModel.currentLevel {
                levelDisplay(level)
            }

            Spacer()

            // Play button
            playButton

            Spacer()

            // Question + Yes/No
            questionAndButtons

            Spacer()
        }
        .padding(24)
    }

    private var progressHeader: some View {
        VStack(spacing: 8) {
            HStack {
                Text("Level \(viewModel.currentLevelIndex! + 1) of \(viewModel.totalLevels)")
                    .font(.headline)
                Spacer()
                Text("\(Int(viewModel.progress * 100))%")
                    .font(.caption)
                    .foregroundStyle(.secondary)
            }

            ProgressView(value: viewModel.progress)
                .accessibilityIdentifier(Constants.Accessibility.Calibration.progressIndicator)
        }
    }

    private func levelDisplay(_ level: CalibrationLevel) -> some View {
        VStack(spacing: 6) {
            Text(level.label)
                .font(.title2)
                .fontWeight(.medium)
                .accessibilityIdentifier(Constants.Accessibility.Calibration.levelLabel)

            Text(level.description)
                .font(.subheadline)
                .foregroundStyle(.secondary)

            Text("\(Int(level.gainDb)) dB")
                .font(.caption)
                .foregroundStyle(.tertiary)
                .monospaced()
        }
    }

    private var playButton: some View {
        Button {
            if viewModel.isPlaying {
                viewModel.stopPlayback()
            } else {
                viewModel.playCurrentSample()
            }
        } label: {
            Label(
                viewModel.isPlaying ? "Stop" : "Play Sample",
                systemImage: viewModel.isPlaying ? "stop.circle.fill" : "play.circle.fill"
            )
            .font(.title3)
        }
        .buttonStyle(.bordered)
        .controlSize(.large)
        .accessibilityIdentifier(Constants.Accessibility.Calibration.playButton)
    }

    private var questionAndButtons: some View {
        VStack(spacing: 12) {
            Text("Could you hear the words clearly?")
                .font(.headline)

            if let error = viewModel.playbackError {
                Text(error)
                    .font(.caption)
                    .foregroundStyle(.red)
            }

            HStack(spacing: 16) {
                Button {
                    viewModel.recordResponse(couldHear: false)
                } label: {
                    Label("No", systemImage: "xmark.circle")
                        .frame(minWidth: 80)
                }
                .buttonStyle(.bordered)
                .controlSize(.large)
                .accessibilityIdentifier(Constants.Accessibility.Calibration.noButton)

                Button {
                    viewModel.recordResponse(couldHear: true)
                } label: {
                    Label("Yes", systemImage: "checkmark.circle")
                        .frame(minWidth: 80)
                }
                .buttonStyle(.borderedProminent)
                .controlSize(.large)
                .accessibilityIdentifier(Constants.Accessibility.Calibration.yesButton)
            }
        }
    }

    // MARK: - Complete

    private var completeContent: some View {
        VStack(spacing: 20) {
            Spacer()

            Image(systemName: "checkmark.seal.fill")
                .font(.system(size: 48))
                .foregroundStyle(.green)

            Text("Calibration Complete")
                .font(.title)
                .fontWeight(.semibold)

            if let level = viewModel.chosenLevel {
                VStack(spacing: 4) {
                    Text("Your optimal subliminal level:")
                        .font(.body)
                        .foregroundStyle(.secondary)

                    Text("\(level.label) (\(Int(level.gainDb)) dB)")
                        .font(.title3)
                        .fontWeight(.medium)
                        .foregroundStyle(Color.accentColor)

                    Text(level.description)
                        .font(.callout)
                        .foregroundStyle(.tertiary)
                }
            }

            Text("You can recalibrate anytime from Settings.")
                .font(.callout)
                .foregroundStyle(.tertiary)

            Spacer()

            Button("Done") {
                viewModel.dismiss()
            }
            .buttonStyle(.borderedProminent)
            .controlSize(.large)
            .keyboardShortcut(.defaultAction)
            .accessibilityIdentifier(Constants.Accessibility.Calibration.doneButton)

            Spacer()
        }
        .padding(24)
    }

    // MARK: - Bottom Bar

    private var bottomBar: some View {
        HStack {
            Button("Skip") {
                viewModel.skipCalibration()
            }
            .keyboardShortcut(.cancelAction)
            .accessibilityIdentifier(Constants.Accessibility.Calibration.skipCalibrationButton)

            Spacer()

            if viewModel.phase == .welcome {
                Text("Uses default level if skipped")
                    .font(.caption)
                    .foregroundStyle(.tertiary)
            }
        }
    }
}
