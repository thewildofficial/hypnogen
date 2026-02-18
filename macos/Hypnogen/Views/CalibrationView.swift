// CalibrationView.swift
// Hypnogen
//
// Subliminal audibility calibration flow.
// Guides the user through 5 gain levels to determine optimal subliminal volume.

import SwiftUI

struct CalibrationView: View {
    @Bindable var viewModel: CalibrationViewModel

    @Environment(\.accessibilityReduceMotion) private var reduceMotion
    @State private var appeared = false

    var body: some View {
        ZStack {
            backgroundLayer

            VStack(spacing: 0) {
                content
                    .frame(maxWidth: .infinity, maxHeight: .infinity)

                if viewModel.phase != .complete {
                    separatorLine
                    bottomBar
                        .padding(.horizontal, Spacing.lg)
                        .padding(.vertical, Spacing.md)
                }
            }
            .frostedGlass(.prominent, cornerRadius: Radius.lg)
            .padding(Spacing.md)
            .shadow(ShadowTokens.modal)
            .opacity(appeared ? 1 : 0)
            .scaleEffect(appeared ? 1 : 0.96)
            .animation(
                MotionSensitiveAnimation.resolve(
                    .spring(response: 0.5, dampingFraction: 0.8),
                    reduceMotion: reduceMotion
                ),
                value: appeared
            )
        }
        .frame(width: 520, height: 420)
        .accessibilityIdentifier(Constants.Accessibility.Calibration.calibrationView)
        .onAppear {
            appeared = true
        }
    }

    // MARK: - Background Layer

    private var backgroundLayer: some View {
        ZStack {
            GradientTokens.heroGradient
                .ignoresSafeArea()

            Circle()
                .fill(
                    RadialGradient.fade(
                        Color.accentViolet.opacity(0.12),
                        radius: 180
                    )
                )
                .frame(width: 360, height: 360)
                .offset(x: -100, y: -120)
                .blur(radius: 50)

            Circle()
                .fill(
                    RadialGradient.fade(
                        Color.accentIndigo.opacity(0.08),
                        radius: 160
                    )
                )
                .frame(width: 320, height: 320)
                .offset(x: 120, y: 100)
                .blur(radius: 40)
        }
    }

    // MARK: - Separator

    private var separatorLine: some View {
        Rectangle()
            .fill(
                LinearGradient(
                    colors: [
                        Color.accentViolet.opacity(0),
                        Color.accentViolet.opacity(0.3),
                        Color.accentViolet.opacity(0),
                    ],
                    startPoint: .leading,
                    endPoint: .trailing
                )
            )
            .frame(height: 1)
            .padding(.horizontal, Spacing.md)
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
        VStack(spacing: Spacing.md) {
            Spacer()

            ZStack {
                Circle()
                    .fill(Color.accentViolet.opacity(0.15))
                    .frame(width: 88, height: 88)
                    .blur(radius: 12)

                Image(systemName: "ear.and.waveform")
                    .font(.system(size: 40, weight: .light))
                    .foregroundStyle(Color.accentGlow)
                    .shadow(color: Color.accentGlow.opacity(0.5), radius: 8, x: 0, y: 0)
            }

            Text("Audibility Calibration")
                .font(Typography.pageTitle)
                .foregroundStyle(Color.textPrimary)

            Text("We\u{2019}ll play short audio samples at different volume levels. For each one, tell us if you can hear the words clearly.")
                .font(Typography.bodyText)
                .foregroundStyle(Color.textSecondary)
                .multilineTextAlignment(.center)
                .lineSpacing(3)
                .frame(maxWidth: 380)

            Text("This helps Hypnogen set the right subliminal volume for your listening environment.")
                .font(Typography.bodySmall)
                .foregroundStyle(Color.textSecondary.opacity(0.8))
                .multilineTextAlignment(.center)
                .frame(maxWidth: 380)

            Spacer()

            Button {
                viewModel.beginTesting()
            } label: {
                ButtonLabel("Begin Calibration", icon: "waveform.path", size: .large)
            }
            .buttonStyle(PrimaryButtonStyle(size: .large))
            .keyboardShortcut(.defaultAction)

            Spacer()
        }
        .padding(Spacing.lg)
    }

    // MARK: - Testing

    private var testingContent: some View {
        VStack(spacing: Spacing.md) {
            // Progress
            progressHeader

            separatorLine

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
        .padding(Spacing.lg)
    }

    private var progressHeader: some View {
        VStack(spacing: Spacing.sm) {
            HStack {
                Text("Level \(viewModel.currentLevelIndex! + 1) of \(viewModel.totalLevels)")
                    .font(Typography.bodyBold)
                    .foregroundStyle(Color.textPrimary)
                Spacer()
                Text("\(Int(viewModel.progress * 100))%")
                    .font(Typography.captionText)
                    .foregroundStyle(Color.textSecondary)
            }

            GeometryReader { geometry in
                ZStack(alignment: .leading) {
                    RoundedRectangle(cornerRadius: 3, style: .continuous)
                        .fill(Color.surfacePrimary.opacity(0.5))
                        .frame(height: 6)

                    RoundedRectangle(cornerRadius: 3, style: .continuous)
                        .fill(GradientTokens.accentGradient)
                        .frame(
                            width: max(6, geometry.size.width * viewModel.progress),
                            height: 6
                        )
                        .shadow(color: Color.accentGlow.opacity(0.4), radius: 4, x: 0, y: 0)
                        .animation(
                            MotionSensitiveAnimation.resolve(
                                AnimationTokens.easeInOut,
                                reduceMotion: reduceMotion
                            ),
                            value: viewModel.progress
                        )
                }
            }
            .frame(height: 6)
            .accessibilityIdentifier(Constants.Accessibility.Calibration.progressIndicator)
        }
    }

    private func levelDisplay(_ level: CalibrationLevel) -> some View {
        VStack(spacing: Spacing.sm) {
            Text(level.label)
                .font(Typography.sectionTitle)
                .foregroundStyle(Color.textPrimary)
                .accessibilityIdentifier(Constants.Accessibility.Calibration.levelLabel)

            Text(level.description)
                .font(Typography.bodySmall)
                .foregroundStyle(Color.textSecondary)

            Text("\(Int(level.gainDb)) dB")
                .font(Typography.monospaceSmall)
                .foregroundStyle(Color.textAccent)
                .padding(.horizontal, Spacing.sm)
                .padding(.vertical, Spacing.xs)
                .background(Color.accentViolet.opacity(0.1))
                .clipShape(RoundedRectangle(cornerRadius: Radius.sm, style: .continuous))
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
            HStack(spacing: Spacing.sm) {
                Image(systemName: viewModel.isPlaying ? "stop.circle.fill" : "play.circle.fill")
                    .font(.system(size: 20, weight: .medium))
                Text(viewModel.isPlaying ? "Stop" : "Play Sample")
                    .font(Typography.bodyBold)
            }
            .foregroundStyle(viewModel.isPlaying ? Color.textPrimary : Color.textAccent)
            .padding(.horizontal, Spacing.lg)
            .padding(.vertical, Spacing.sm + 2)
        }
        .buttonStyle(SecondaryButtonStyle(size: .large))
        .accessibilityIdentifier(Constants.Accessibility.Calibration.playButton)

    }

    private var questionAndButtons: some View {
        VStack(spacing: Spacing.sm + 4) {
            Text("Could you hear the words clearly?")
                .font(Typography.bodyBold)
                .foregroundStyle(Color.textPrimary)

            if let error = viewModel.playbackError {
                Text(error)
                    .font(Typography.captionText)
                    .foregroundStyle(Color(red: 0.94, green: 0.27, blue: 0.27))
            }

            HStack(spacing: Spacing.md) {
                Button {
                    viewModel.recordResponse(couldHear: false)
                } label: {
                    ButtonLabel("No", icon: "xmark.circle", size: .large)
                        .frame(minWidth: 80)
                }
                .buttonStyle(SecondaryButtonStyle(size: .large))
                .accessibilityIdentifier(Constants.Accessibility.Calibration.noButton)

                Button {
                    viewModel.recordResponse(couldHear: true)
                } label: {
                    ButtonLabel("Yes", icon: "checkmark.circle", size: .large)
                        .frame(minWidth: 80)
                }
                .buttonStyle(PrimaryButtonStyle(size: .large))
                .accessibilityIdentifier(Constants.Accessibility.Calibration.yesButton)
            }
        }
    }

    // MARK: - Complete

    private var completeContent: some View {
        VStack(spacing: Spacing.md) {
            Spacer()

            ZStack {
                Circle()
                    .fill(Color.accentViolet.opacity(0.15))
                    .frame(width: 88, height: 88)
                    .blur(radius: 12)

                Image(systemName: "checkmark.seal.fill")
                    .font(.system(size: 40, weight: .light))
                    .foregroundStyle(Color.accentGlow)
                    .shadow(color: Color.accentGlow.opacity(0.5), radius: 8, x: 0, y: 0)
            }

            Text("Calibration Complete")
                .font(Typography.pageTitle)
                .foregroundStyle(Color.textPrimary)

            if let level = viewModel.chosenLevel {
                VStack(spacing: Spacing.xs) {
                    Text("Your optimal subliminal level:")
                        .font(Typography.bodyText)
                        .foregroundStyle(Color.textSecondary)

                    Text("\(level.label) (\(Int(level.gainDb)) dB)")
                        .font(Typography.sectionTitle)
                        .foregroundStyle(Color.textAccent)

                    Text(level.description)
                        .font(Typography.bodySmall)
                        .foregroundStyle(Color.textSecondary)
                }
                .padding(Spacing.md)
                .background(Color.surfacePrimary.opacity(0.4))
                .clipShape(RoundedRectangle(cornerRadius: Radius.md, style: .continuous))
                .overlay(
                    RoundedRectangle(cornerRadius: Radius.md, style: .continuous)
                        .strokeBorder(Color.accentViolet.opacity(0.2), lineWidth: 1)
                )
            }

            Text("You can recalibrate anytime from Settings.")
                .font(Typography.bodySmall)
                .foregroundStyle(Color.textSecondary.opacity(0.8))

            Spacer()

            Button {
                viewModel.dismiss()
            } label: {
                ButtonLabel("Done", icon: "checkmark", size: .large)
            }
            .buttonStyle(PrimaryButtonStyle(size: .large))
            .keyboardShortcut(.defaultAction)
            .accessibilityIdentifier(Constants.Accessibility.Calibration.doneButton)

            Spacer()
        }
        .padding(Spacing.lg)
    }

    // MARK: - Bottom Bar

    private var bottomBar: some View {
        HStack {
            Button("Skip") {
                viewModel.skipCalibration()
            }
            .buttonStyle(GhostButtonStyle(size: .medium))
            .keyboardShortcut(.cancelAction)
            .accessibilityIdentifier(Constants.Accessibility.Calibration.skipCalibrationButton)

            Spacer()

            if viewModel.phase == .welcome {
                Text("Uses default level if skipped")
                    .font(Typography.captionText)
                    .foregroundStyle(Color.textSecondary)
            }
        }
    }
}
