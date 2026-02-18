// HypnogenApp.swift
// Hypnogen
//
// App entry point. Sets up the main window with navigation and menu commands.

import SwiftUI

@main
struct HypnogenApp: App {
    @State private var projectsViewModel = ProjectsViewModel()
    @State private var renderQueueViewModel = RenderQueueViewModel()
    @State private var outputsLibraryViewModel = OutputsLibraryViewModel()
    @State private var onboardingViewModel = OnboardingViewModel()
    @State private var calibrationViewModel = CalibrationViewModel()

    var body: some Scene {
        WindowGroup {
            ContentView(
                projectsViewModel: projectsViewModel,
                renderQueueViewModel: renderQueueViewModel,
                outputsLibraryViewModel: outputsLibraryViewModel,
                onboardingViewModel: onboardingViewModel
            )
            .frame(minWidth: 900, minHeight: 560)
            .onAppear {
                projectsViewModel.loadProjects()
                if onboardingViewModel.shouldShowOnLaunch {
                    onboardingViewModel.showOnboarding()
                }
            }
            .onChange(of: onboardingViewModel.isPresented) { _, isPresented in
                if !isPresented && calibrationViewModel.shouldShowOnFirstLaunch {
                    calibrationViewModel.startCalibration()
                }
            }
            .sheet(isPresented: $calibrationViewModel.isPresented) {
                CalibrationView(viewModel: calibrationViewModel)
            }
            .preferredColorScheme(.dark)
            .background(Color.backgroundDeep)
        }
        .windowToolbarStyle(.unified(showsTitle: true))
        .defaultSize(width: 1120, height: 720)
        .defaultPosition(.center)
        .commands {
            CommandGroup(after: .newItem) {
                Button("New Project") {
                    projectsViewModel.createProject()
                }
                .keyboardShortcut("N", modifiers: [.command])
            }

            CommandMenu("Project") {
                Button("Render") {
                    if let project = projectsViewModel.selectedProject {
                        Task {
                            await renderQueueViewModel.submitRender(for: project)
                        }
                    }
                }
                .keyboardShortcut("R", modifiers: [.command])
                .disabled(projectsViewModel.selectedProject == nil)

                Divider()

                Button("Duplicate Project") {
                    if let project = projectsViewModel.selectedProject {
                        projectsViewModel.duplicateProject(project)
                    }
                }
                .keyboardShortcut("D", modifiers: [.command, .shift])
                .disabled(projectsViewModel.selectedProject == nil)
            }

            CommandGroup(replacing: .help) {
                Button("Onboarding Guide") {
                    onboardingViewModel.showOnboarding()
                }
                .keyboardShortcut("?", modifiers: [.command, .shift])
            }
        }

        Settings {
            SettingsView(calibrationViewModel: calibrationViewModel)
                .preferredColorScheme(.dark)
        }
    }
}

// MARK: - Settings View

struct SettingsView: View {
    @Bindable var calibrationViewModel: CalibrationViewModel

    var body: some View {
        TabView {
            GeneralSettingsView()
                .tabItem {
                    Label("General", systemImage: "gear")
                }

            WorkerSettingsView()
                .tabItem {
                    Label("Worker", systemImage: "server.rack")
                }

            CalibrationSettingsView(calibrationViewModel: calibrationViewModel)
                .tabItem {
                    Label("Calibration", systemImage: "ear.and.waveform")
                }
        }
        .frame(width: 480, height: 280)
        .background(Color.backgroundDeep)
    }
}

// MARK: - Settings Field Style

/// Styled text field for settings panels with violet accent border on focus.
private struct SettingsFieldStyle: ViewModifier {
    @FocusState private var isFocused: Bool

    func body(content: Content) -> some View {
        content
            .textFieldStyle(.plain)
            .font(Typography.bodyText)
            .foregroundStyle(Color.textPrimary)
            .padding(.horizontal, Spacing.sm)
            .padding(.vertical, Spacing.xs + 2)
            .focused($isFocused)
            .background(
                RoundedRectangle(cornerRadius: Radius.sm, style: .continuous)
                    .fill(Color.surfacePrimary.opacity(0.5))
            )
            .overlay(
                RoundedRectangle(cornerRadius: Radius.sm, style: .continuous)
                    .strokeBorder(
                        isFocused
                            ? Color.accentViolet.opacity(0.6)
                            : Color.surfaceSecondary.opacity(0.3),
                        lineWidth: 1
                    )
            )
    }
}

private extension View {
    func settingsField() -> some View {
        modifier(SettingsFieldStyle())
    }
}

// MARK: - Settings Section

/// A labeled group within a settings tab.
private struct SettingsSection<Content: View>: View {
    let title: String
    let icon: String
    @ViewBuilder var content: () -> Content

    var body: some View {
        VStack(alignment: .leading, spacing: Spacing.md) {
            HStack(spacing: Spacing.sm) {
                Image(systemName: icon)
                    .font(.system(size: 13, weight: .semibold))
                    .foregroundStyle(Color.accentViolet)
                Text(title)
                    .font(Typography.bodyBold)
                    .foregroundStyle(Color.textPrimary)
            }

            VStack(alignment: .leading, spacing: Spacing.sm) {
                content()
            }
            .padding(Spacing.md)
            .background(
                RoundedRectangle(cornerRadius: Radius.md, style: .continuous)
                    .fill(Color.backgroundMid.opacity(0.6))
            )
            .overlay(
                RoundedRectangle(cornerRadius: Radius.md, style: .continuous)
                    .strokeBorder(
                        Color.surfaceSecondary.opacity(0.2),
                        lineWidth: 0.5
                    )
            )
        }
    }
}

// MARK: - Settings Row

/// A label + value row inside settings.
private struct SettingsRow: View {
    let label: String
    let value: String

    var body: some View {
        HStack {
            Text(label)
                .font(Typography.captionText)
                .foregroundStyle(Color.textSecondary)
            Spacer()
            Text(value)
                .font(Typography.bodyText)
                .foregroundStyle(Color.textPrimary)
        }
    }
}

// MARK: - General Settings

struct GeneralSettingsView: View {
    @AppStorage("defaultVoice") private var defaultVoice = Constants.Defaults.voice

    var body: some View {
        VStack(alignment: .leading, spacing: Spacing.lg) {
            SettingsSection(title: "Voice", icon: "waveform") {
                VStack(alignment: .leading, spacing: Spacing.xs) {
                    Text("Default Voice")
                        .font(Typography.captionText)
                        .foregroundStyle(Color.textSecondary)
                    TextField("Enter voice name", text: $defaultVoice)
                        .settingsField()
                        .accessibilityIdentifier("defaultVoiceField")
                }
            }
        }
        .padding(Spacing.lg)
        .frame(maxWidth: .infinity, maxHeight: .infinity, alignment: .topLeading)
        .background(Color.backgroundDeep)
    }
}

// MARK: - Worker Settings

struct WorkerSettingsView: View {
    @AppStorage("workerHost") private var workerHost = Constants.API.defaultHost
    @AppStorage("workerPort") private var workerPort = Constants.API.defaultPort

    var body: some View {
        VStack(alignment: .leading, spacing: Spacing.lg) {
            SettingsSection(title: "Connection", icon: "network") {
                VStack(alignment: .leading, spacing: Spacing.sm) {
                    VStack(alignment: .leading, spacing: Spacing.xs) {
                        Text("Host")
                            .font(Typography.captionText)
                            .foregroundStyle(Color.textSecondary)
                        TextField("Worker host address", text: $workerHost)
                            .settingsField()
                            .accessibilityIdentifier("workerHostField")
                    }

                    VStack(alignment: .leading, spacing: Spacing.xs) {
                        Text("Port")
                            .font(Typography.captionText)
                            .foregroundStyle(Color.textSecondary)
                        TextField("Port", value: $workerPort, format: .number)
                            .settingsField()
                            .accessibilityIdentifier("workerPortField")
                    }
                }
            }
        }
        .padding(Spacing.lg)
        .frame(maxWidth: .infinity, maxHeight: .infinity, alignment: .topLeading)
        .background(Color.backgroundDeep)
    }
}

// MARK: - Calibration Settings

struct CalibrationSettingsView: View {
    @Bindable var calibrationViewModel: CalibrationViewModel

    var body: some View {
        VStack(alignment: .leading, spacing: Spacing.lg) {
            SettingsSection(title: "Status", icon: "ear.and.waveform") {
                if let result = calibrationViewModel.savedResult {
                    let level = CalibrationLevels.level(forGainDb: result.gainDb)
                    SettingsRow(
                        label: "Current Level",
                        value: level.map {
                            "\($0.label) (\(Int($0.gainDb)) dB)"
                        } ?? "\(Int(result.gainDb)) dB"
                    )
                    SettingsRow(
                        label: "Calibrated",
                        value: result.completedAt.formatted(
                            date: .abbreviated, time: .shortened
                        )
                    )
                    if result.wasSkipped {
                        HStack(spacing: Spacing.xs) {
                            Image(systemName: "exclamationmark.triangle")
                                .font(.system(size: 11))
                                .foregroundStyle(Color.accentGlow)
                            Text("Calibration was skipped (using default level).")
                                .font(Typography.captionText)
                                .foregroundStyle(Color.textSecondary)
                        }
                    }
                } else {
                    HStack(spacing: Spacing.sm) {
                        Image(systemName: "info.circle")
                            .font(.system(size: 13))
                            .foregroundStyle(Color.accentIndigo)
                        Text(
                            "No calibration data. Run calibration to set your subliminal level."
                        )
                        .font(Typography.bodySmall)
                        .foregroundStyle(Color.textSecondary)
                    }
                }
            }

            Button {
                calibrationViewModel.startCalibration()
            } label: {
                ButtonLabel("Recalibrate", icon: "arrow.clockwise")
            }
            .buttonStyle(SecondaryButtonStyle(size: .medium))
            .accessibilityIdentifier(
                Constants.Accessibility.Calibration.recalibrateButton
            )
        }
        .padding(Spacing.lg)
        .frame(maxWidth: .infinity, maxHeight: .infinity, alignment: .topLeading)
        .background(Color.backgroundDeep)
        .sheet(isPresented: $calibrationViewModel.isPresented) {
            CalibrationView(viewModel: calibrationViewModel)
        }
    }
}
