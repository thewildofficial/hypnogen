// HypnogenApp.swift
// Hypnogen
//
// App entry point. Sets up the main window with navigation and menu commands.

import SwiftUI

// MARK: - Design System Color Tokens (Temporary - until DesignSystem files added to Xcode project)

extension Color {
    static let canvas = Color("Canvas")
    static let surface = Color("Surface")
    static let stroke = Color("Stroke")
    static let accentPrimary = Color("AccentPrimary")
    static let accentSecondary = Color("AccentSecondary")
    static let textPrimary = Color("TextPrimary")
    static let textSecondary = Color("TextSecondary")
}

enum Radius {
    static let sm: CGFloat = 6
    static let md: CGFloat = 12
    static let lg: CGFloat = 18
}

struct PrimaryButtonStyle: ButtonStyle {
    func makeBody(configuration: Configuration) -> some View {
        configuration.label
            .padding(.horizontal, 16)
            .padding(.vertical, 8)
            .background(Color.accentPrimary)
            .foregroundColor(Color.canvas)
            .cornerRadius(6)
    }
}

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
            .frame(minWidth: 800, minHeight: 500)
            .onAppear {
                projectsViewModel.loadProjects()
                if onboardingViewModel.shouldShowOnLaunch {
                    onboardingViewModel.showOnboarding()
                }
            }
            // Show calibration after onboarding dismisses (first launch only)
            .onChange(of: onboardingViewModel.isPresented) { _, isPresented in
                if !isPresented && calibrationViewModel.shouldShowOnFirstLaunch {
                    calibrationViewModel.startCalibration()
                }
            }
            .sheet(isPresented: $calibrationViewModel.isPresented) {
                CalibrationView(viewModel: calibrationViewModel)
            }
            .preferredColorScheme(.dark)
            .background(Color.canvas)
        }
        .windowToolbarStyle(.unified)
        .defaultSize(width: 1100, height: 700)
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
        .frame(width: 450, height: 250)
    }
}

struct GeneralSettingsView: View {
    @AppStorage("defaultVoice") private var defaultVoice = Constants.Defaults.voice

    var body: some View {
        Form {
            TextField("Default Voice:", text: $defaultVoice)
                .accessibilityIdentifier("defaultVoiceField")
        }
        .padding()
    }
}

struct WorkerSettingsView: View {
    @AppStorage("workerHost") private var workerHost = Constants.API.defaultHost
    @AppStorage("workerPort") private var workerPort = Constants.API.defaultPort

    var body: some View {
        Form {
            TextField("Host:", text: $workerHost)
                .accessibilityIdentifier("workerHostField")
            TextField("Port:", value: $workerPort, format: .number)
                .accessibilityIdentifier("workerPortField")
        }
        .padding()
    }
}

struct CalibrationSettingsView: View {
    @Bindable var calibrationViewModel: CalibrationViewModel

    var body: some View {
        Form {
            if let result = calibrationViewModel.savedResult {
                let level = CalibrationLevels.level(forGainDb: result.gainDb)
                LabeledContent("Current Level:") {
                    Text(level.map { "\($0.label) (\(Int($0.gainDb)) dB)" } ?? "\(Int(result.gainDb)) dB")
                        .foregroundStyle(.secondary)
                }
                LabeledContent("Calibrated:") {
                    Text(result.completedAt.formatted(date: .abbreviated, time: .shortened))
                        .foregroundStyle(.secondary)
                }
                if result.wasSkipped {
                    Text("Calibration was skipped (using default level).")
                        .font(.caption)
                        .foregroundStyle(.tertiary)
                }
            } else {
                Text("No calibration data. Run calibration to set your subliminal level.")
                    .foregroundStyle(.secondary)
            }

            Button("Recalibrate") {
                calibrationViewModel.startCalibration()
            }
            .accessibilityIdentifier(Constants.Accessibility.Calibration.recalibrateButton)
        }
        .padding()
        .sheet(isPresented: $calibrationViewModel.isPresented) {
            CalibrationView(viewModel: calibrationViewModel)
        }
    }
}
