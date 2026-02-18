// HypnogenApp.swift
// Hypnogen
//
// App entry point. Sets up the main window with navigation and menu commands.

import AppKit
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
            .background(WindowAccessor())
            .background(Color.backgroundDeep)
        }
        .windowToolbarStyle(.unified(showsTitle: false))
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

// MARK: - Window Accessor

/// Transparent NSView that configures its hosting window for a seamless dark titlebar.
/// The view itself is invisible; it only exists to access the `NSWindow` at runtime.
private struct WindowAccessor: NSViewRepresentable {
    func makeNSView(context: Context) -> NSView {
        let view = NSView()
        DispatchQueue.main.async {
            configureWindow(view.window)
        }
        return view
    }

    func updateNSView(_ nsView: NSView, context: Context) {
        configureWindow(nsView.window)
    }

    private func configureWindow(_ window: NSWindow?) {
        guard let window else { return }
        window.titlebarAppearsTransparent = true
        window.isMovableByWindowBackground = true
        window.backgroundColor = NSColor(Color.backgroundDeep)

        if !window.styleMask.contains(.fullSizeContentView) {
            window.styleMask.insert(.fullSizeContentView)
        }
    }
}

// MARK: - Settings Tab

/// Settings navigation tabs
private enum SettingsTab: String, CaseIterable, Identifiable {
    case general
    case worker
    case calibration

    var id: String { rawValue }

    var label: String {
        switch self {
        case .general:     return "General"
        case .worker:      return "Worker"
        case .calibration: return "Calibration"
        }
    }

    var icon: String {
        switch self {
        case .general:     return "gear"
        case .worker:      return "server.rack"
        case .calibration: return "ear.and.waveform"
        }
    }
}

// MARK: - Settings View

struct SettingsView: View {
    @Bindable var calibrationViewModel: CalibrationViewModel
    @State private var selectedTab: SettingsTab = .general

    var body: some View {
        HStack(spacing: 0) {
            // ── Sidebar ─────────────────────────────────
            settingsSidebar

            // ── Divider ─────────────────────────────────
            Rectangle()
                .fill(Color.surfaceSecondary.opacity(0.25))
                .frame(width: 1)

            // ── Content pane ────────────────────────────
            settingsContent
                .frame(maxWidth: .infinity, maxHeight: .infinity)
                .background(Color.backgroundDeep)
        }
        .frame(width: 560, height: 340)
        .background(Color.backgroundDeep)
    }

    // MARK: - Sidebar

    @ViewBuilder
    private var settingsSidebar: some View {
        VStack(alignment: .leading, spacing: Spacing.xs) {
            ForEach(SettingsTab.allCases) { tab in
                SettingsTabButton(
                    tab: tab,
                    isSelected: selectedTab == tab
                ) {
                    withAnimation(AnimationTokens.springTransition) {
                        selectedTab = tab
                    }
                }
            }

            Spacer()
        }
        .padding(.vertical, Spacing.md)
        .padding(.horizontal, Spacing.sm)
        .frame(width: 160)
        .background(
            LinearGradient(
                colors: [
                    Color.backgroundMid.opacity(0.6),
                    Color.backgroundDeep.opacity(0.8),
                ],
                startPoint: .top,
                endPoint: .bottom
            )
        )
    }

    // MARK: - Content

    @ViewBuilder
    private var settingsContent: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 0) {
                // Page title
                HStack(spacing: Spacing.sm) {
                    Image(systemName: selectedTab.icon)
                        .font(.system(size: 16, weight: .semibold))
                        .foregroundStyle(Color.accentViolet)
                    Text(selectedTab.label)
                        .font(Typography.sectionTitle)
                        .foregroundStyle(Color.textPrimary)
                }
                .padding(.bottom, Spacing.lg)

                // Tab content
                Group {
                    switch selectedTab {
                    case .general:
                        GeneralSettingsView()
                    case .worker:
                        WorkerSettingsView()
                    case .calibration:
                        CalibrationSettingsView(calibrationViewModel: calibrationViewModel)
                    }
                }
                .transition(.opacity.combined(with: .offset(y: 4)))
            }
            .padding(Spacing.lg)
            .animation(AnimationTokens.springTransition, value: selectedTab)
        }
    }
}

// MARK: - Settings Tab Button

/// Navigation button in the settings sidebar.
private struct SettingsTabButton: View {
    let tab: SettingsTab
    let isSelected: Bool
    let action: () -> Void

    @State private var isHovered = false

    var body: some View {
        Button(action: action) {
            HStack(spacing: Spacing.sm) {
                Image(systemName: tab.icon)
                    .font(.system(size: 13, weight: isSelected ? .semibold : .regular))
                    .foregroundStyle(
                        isSelected ? Color.accentViolet : Color.textSecondary
                    )
                    .frame(width: 18)

                Text(tab.label)
                    .font(isSelected ? Typography.bodyBold : Typography.bodyText)
                    .foregroundStyle(
                        isSelected ? Color.textPrimary : Color.textSecondary
                    )

                Spacer()
            }
            .padding(.horizontal, Spacing.sm + 2)
            .padding(.vertical, Spacing.sm)
            .background(
                RoundedRectangle(cornerRadius: Radius.sm, style: .continuous)
                    .fill(backgroundColor)
            )
            .overlay(
                RoundedRectangle(cornerRadius: Radius.sm, style: .continuous)
                    .strokeBorder(
                        isSelected
                            ? Color.accentViolet.opacity(0.3)
                            : Color.clear,
                        lineWidth: 0.5
                    )
            )
        }
        .buttonStyle(.plain)
        .onHover { hovering in isHovered = hovering }
    }

    private var backgroundColor: Color {
        if isSelected {
            return Color.accentViolet.opacity(0.12)
        } else if isHovered {
            return Color.surfacePrimary.opacity(0.4)
        }
        return .clear
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
            .padding(.horizontal, Spacing.sm + 2)
            .padding(.vertical, Spacing.sm)
            .focused($isFocused)
            .background(
                RoundedRectangle(cornerRadius: Radius.sm, style: .continuous)
                    .fill(Color.surfacePrimary.opacity(0.4))
            )
            .overlay(
                RoundedRectangle(cornerRadius: Radius.sm, style: .continuous)
                    .strokeBorder(
                        isFocused
                            ? Color.accentViolet.opacity(0.6)
                            : Color.surfaceSecondary.opacity(0.2),
                        lineWidth: isFocused ? 1.5 : 1
                    )
                    .animation(.easeInOut(duration: 0.15), value: isFocused)
            )
    }
}

private extension View {
    func settingsField() -> some View {
        modifier(SettingsFieldStyle())
    }
}

// MARK: - Settings Section

/// A labeled group within a settings pane.
private struct SettingsSection<Content: View>: View {
    let title: String
    let icon: String
    @ViewBuilder var content: () -> Content

    var body: some View {
        VStack(alignment: .leading, spacing: Spacing.sm + 2) {
            HStack(spacing: Spacing.xs + 2) {
                Image(systemName: icon)
                    .font(.system(size: 12, weight: .semibold))
                    .foregroundStyle(Color.accentGlow)
                Text(title.uppercased())
                    .font(Typography.label)
                    .tracking(Typography.trackingExtraWide)
                    .foregroundStyle(Color.textSecondary)
            }

            VStack(alignment: .leading, spacing: Spacing.sm + 2) {
                content()
            }
            .padding(Spacing.md)
            .background(
                RoundedRectangle(cornerRadius: Radius.md, style: .continuous)
                    .fill(Color.backgroundMid.opacity(0.5))
            )
            .overlay(
                RoundedRectangle(cornerRadius: Radius.md, style: .continuous)
                    .strokeBorder(
                        LinearGradient(
                            colors: [
                                Color.surfaceSecondary.opacity(0.2),
                                Color.surfaceSecondary.opacity(0.08),
                            ],
                            startPoint: .topLeading,
                            endPoint: .bottomTrailing
                        ),
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
                .font(Typography.bodySmall)
                .foregroundStyle(Color.textSecondary)
            Spacer()
            Text(value)
                .font(Typography.bodyText)
                .foregroundStyle(Color.textPrimary)
        }
    }
}

// MARK: - Settings Label

/// Consistent label above a form field.
private struct SettingsLabel: View {
    let text: String

    var body: some View {
        Text(text)
            .font(Typography.captionText)
            .foregroundStyle(Color.textSecondary)
    }
}

// MARK: - General Settings

struct GeneralSettingsView: View {
    @AppStorage("defaultVoice") private var defaultVoice = Constants.Defaults.voice

    var body: some View {
        VStack(alignment: .leading, spacing: Spacing.lg) {
            SettingsSection(title: "Voice", icon: "waveform") {
                VStack(alignment: .leading, spacing: Spacing.xs) {
                    SettingsLabel(text: "Default Voice")
                    TextField("Enter voice name", text: $defaultVoice)
                        .settingsField()
                        .accessibilityIdentifier("defaultVoiceField")
                }
            }
        }
        .frame(maxWidth: .infinity, alignment: .topLeading)
    }
}

// MARK: - Worker Settings

struct WorkerSettingsView: View {
    @AppStorage("workerHost") private var workerHost = Constants.API.defaultHost
    @AppStorage("workerPort") private var workerPort = Constants.API.defaultPort

    var body: some View {
        VStack(alignment: .leading, spacing: Spacing.lg) {
            SettingsSection(title: "Connection", icon: "network") {
                VStack(alignment: .leading, spacing: Spacing.sm + 2) {
                    VStack(alignment: .leading, spacing: Spacing.xs) {
                        SettingsLabel(text: "Host")
                        TextField("Worker host address", text: $workerHost)
                            .settingsField()
                            .accessibilityIdentifier("workerHostField")
                    }

                    VStack(alignment: .leading, spacing: Spacing.xs) {
                        SettingsLabel(text: "Port")
                        TextField("Port", value: $workerPort, format: .number)
                            .settingsField()
                            .accessibilityIdentifier("workerPortField")
                    }
                }
            }
        }
        .frame(maxWidth: .infinity, alignment: .topLeading)
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
        .frame(maxWidth: .infinity, alignment: .topLeading)
        .sheet(isPresented: $calibrationViewModel.isPresented) {
            CalibrationView(viewModel: calibrationViewModel)
        }
    }
}
