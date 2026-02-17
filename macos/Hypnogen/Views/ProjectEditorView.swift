// ProjectEditorView.swift
// Hypnogen
//
// Editor for a single project: script text, affirmations list, render settings.


import SwiftUI

// MARK: - Editor Tab

private enum EditorTab: String, CaseIterable, Identifiable {
    case script = "Script"
    case affirmations = "Affirmations"
    case settings = "Settings"

    var id: String { rawValue }

    var icon: String {
        switch self {
        case .script: return "doc.text"
        case .affirmations: return "list.bullet.indent"
        case .settings: return "slider.horizontal.3"
        }
    }
}

// MARK: - ProjectEditorView

struct ProjectEditorView: View {
    @Bindable var project: Project
    let onSave: () -> Void
    let onRender: () -> Void

    @State private var newAffirmation = ""
    @State private var selectedTab: EditorTab = .script
    @State private var cardAppeared = false

    @Environment(\.accessibilityReduceMotion) private var reduceMotion

    var body: some View {
        VStack(spacing: 0) {
            projectNameHeader
            tabBar
            tabContent
                .padding(.horizontal, Spacing.lg)
                .padding(.bottom, Spacing.lg)
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
        .background(GradientTokens.backgroundGradient)
        .toolbar {
            ToolbarItemGroup(placement: .primaryAction) {
                Button(action: onRender) {
                    Label("Render", systemImage: "waveform")
                }
                .buttonStyle(PrimaryButtonStyle())
                .accessibilityIdentifier(Constants.Accessibility.renderButton)
                .disabled(
                    project.scriptText.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty
                        || project.affirmations.filter({ !$0.isEmpty }).isEmpty
                )
            }
        }
        .navigationTitle(project.name)
        .onChange(of: project.scriptText) { _, _ in onSave() }
        .onChange(of: project.affirmations) { _, _ in onSave() }
        .onChange(of: project.settings) { _, _ in onSave() }
        .onAppear {
            withAnimation(
                MotionSensitiveAnimation.resolve(AnimationTokens.springCard, reduceMotion: reduceMotion)
            ) {
                cardAppeared = true
            }
        }
    }

    // MARK: - Project Name Header

    private var projectNameHeader: some View {
        VStack(spacing: Spacing.xs) {
            TextField("Project Name", text: $project.name)
                .textFieldStyle(.plain)
                .font(Typography.pageTitle)
                .tracking(Typography.trackingTight)
                .foregroundColor(.textPrimary)
                .multilineTextAlignment(.center)
                .accessibilityIdentifier(Constants.Accessibility.projectNameField)
                .onChange(of: project.name) { _, _ in onSave() }

            RoundedRectangle(cornerRadius: 1)
                .fill(
                    LinearGradient(
                        colors: [
                            Color.accentViolet.opacity(0),
                            Color.accentViolet.opacity(0.6),
                            Color.accentIndigo.opacity(0.6),
                            Color.accentViolet.opacity(0),
                        ],
                        startPoint: .leading,
                        endPoint: .trailing
                    )
                )
                .frame(width: 180, height: 2)
        }
        .padding(.top, Spacing.lg)
        .padding(.bottom, Spacing.md)
    }

    // MARK: - Tab Bar

    private var tabBar: some View {
        HStack(spacing: Spacing.xs) {
            ForEach(EditorTab.allCases) { tab in
                tabButton(for: tab)
            }
        }
        .padding(3)
        .background(Color.surfacePrimary.opacity(0.5))
        .clipShape(RoundedRectangle(cornerRadius: Radius.sm + 3, style: .continuous))
        .overlay(
            RoundedRectangle(cornerRadius: Radius.sm + 3, style: .continuous)
                .strokeBorder(Color.surfaceSecondary.opacity(0.3), lineWidth: 0.5)
        )
        .padding(.horizontal, Spacing.lg)
        .padding(.bottom, Spacing.md)
    }

    private func tabButton(for tab: EditorTab) -> some View {
        let isSelected = selectedTab == tab

        return Button {
            withTokenAnimation(AnimationTokens.easeInOut, reduceMotion: reduceMotion) {
                selectedTab = tab
            }
        } label: {
            HStack(spacing: 6) {
                Image(systemName: tab.icon)
                    .font(.system(size: 12, weight: .medium))
                Text(tab.rawValue)
                    .font(Typography.bodyBold)

                if tab == .affirmations {
                    Text("\(nonEmptyAffirmationCount)")
                        .font(Typography.label)
                        .monospacedDigit()
                        .foregroundStyle(isSelected ? Color.textPrimary : Color.textSecondary)
                        .padding(.horizontal, 5)
                        .padding(.vertical, 1)
                        .background(
                            Capsule()
                                .fill(isSelected ? Color.accentViolet.opacity(0.3) : Color.surfaceSecondary.opacity(0.4))
                        )
                }
            }
            .foregroundStyle(isSelected ? Color.textPrimary : Color.textSecondary)
            .padding(.horizontal, Spacing.md)
            .padding(.vertical, Spacing.sm)
            .background(
                Group {
                    if isSelected {
                        RoundedRectangle(cornerRadius: Radius.sm, style: .continuous)
                            .fill(Color.surfaceSecondary.opacity(0.6))
                            .shadow(color: Color.accentGlow.opacity(0.15), radius: 8, x: 0, y: 0)
                    }
                }
            )
            .contentShape(Rectangle())
        }
        .buttonStyle(.plain)
    }

    // MARK: - Tab Content

    @ViewBuilder
    private var tabContent: some View {
        Group {
            switch selectedTab {
            case .script:
                scriptTab
            case .affirmations:
                affirmationsTab
            case .settings:
                settingsTab
            }
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
        .frostedGlass(.standard, cornerRadius: Radius.lg)
        .overlay(
            RoundedRectangle(cornerRadius: Radius.lg, style: .continuous)
                .strokeBorder(Color.surfaceSecondary.opacity(0.3), lineWidth: 0.5)
        )
        .shadow(ShadowTokens.card)
        .scaleEffect(cardAppeared ? 1.0 : 0.96)
        .opacity(cardAppeared ? 1.0 : 0)
        .animation(
            MotionSensitiveAnimation.resolve(AnimationTokens.easeInOut, reduceMotion: reduceMotion),
            value: selectedTab
        )
    }

    // MARK: - Script Tab

    private var scriptTab: some View {
        VStack(alignment: .leading, spacing: Spacing.sm) {
            Text("Script")
                .font(Typography.sectionTitle)
                .foregroundColor(.textSecondary)

            TextEditor(text: $project.scriptText)
                .font(Typography.monospaceText)
                .foregroundColor(.textPrimary)
                .scrollContentBackground(.hidden)
                .padding(Spacing.sm)
                .background(
                    RoundedRectangle(cornerRadius: Radius.md, style: .continuous)
                        .fill(Color.accentViolet.opacity(0.04))
                )
                .overlay(
                    HStack(spacing: 0) {
                        RoundedRectangle(cornerRadius: 2)
                            .fill(
                                LinearGradient(
                                    colors: [Color.accentIndigo.opacity(0.7), Color.accentViolet.opacity(0.4)],
                                    startPoint: .top,
                                    endPoint: .bottom
                                )
                            )
                            .frame(width: 3)
                            .padding(.vertical, 6)
                        Spacer()
                    }
                )
                .overlay(
                    RoundedRectangle(cornerRadius: Radius.md, style: .continuous)
                        .strokeBorder(Color.surfaceSecondary.opacity(0.25), lineWidth: 0.5)
                )
                .clipShape(RoundedRectangle(cornerRadius: Radius.md, style: .continuous))
                .accessibilityIdentifier(Constants.Accessibility.scriptEditor)
        }
        .padding(Spacing.lg)
    }

    // MARK: - Affirmations Tab

    private var affirmationsTab: some View {
        VStack(alignment: .leading, spacing: Spacing.sm) {
            HStack {
                Text("Affirmations")
                    .font(Typography.sectionTitle)
                    .foregroundColor(.textSecondary)
                Spacer()
                Text("\(nonEmptyAffirmationCount)")
                    .font(Typography.captionText)
                    .monospacedDigit()
                    .foregroundColor(.textSecondary)
                    .padding(.horizontal, 8)
                    .padding(.vertical, 2)
                    .background(
                        Capsule()
                            .fill(Color.accentViolet.opacity(0.15))
                    )
            }

            List {
                ForEach(project.affirmations.indices, id: \.self) { index in
                    AffirmationRow(
                        text: Binding(
                            get: { project.affirmations[index] },
                            set: { project.affirmations[index] = $0 }
                        ),
                        index: index,
                        onRemove: { removeAffirmation(at: index) }
                    )
                    .listRowBackground(Color.clear)
                    .listRowSeparator(.hidden)
                }
            }
            .listStyle(.plain)
            .scrollContentBackground(.hidden)
            .accessibilityIdentifier(Constants.Accessibility.affirmationsList)

            addAffirmationBar
        }
        .padding(Spacing.lg)
    }

    private var addAffirmationBar: some View {
        HStack(spacing: Spacing.sm) {
            TextField("Add affirmation...", text: $newAffirmation)
                .textFieldStyle(.plain)
                .font(Typography.bodyText)
                .foregroundColor(.textPrimary)
                .padding(.horizontal, Spacing.sm)
                .padding(.vertical, 6)
                .background(
                    RoundedRectangle(cornerRadius: Radius.sm, style: .continuous)
                        .fill(Color.surfacePrimary.opacity(0.5))
                )
                .overlay(
                    RoundedRectangle(cornerRadius: Radius.sm, style: .continuous)
                        .strokeBorder(Color.surfaceSecondary.opacity(0.3), lineWidth: 0.5)
                )
                .onSubmit { addAffirmation() }

            Button {
                addAffirmation()
            } label: {
                Image(systemName: "plus.circle.fill")
                    .font(.system(size: 20))
                    .foregroundColor(.accentViolet)
            }
            .buttonStyle(.borderless)
            .disabled(newAffirmation.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty)
            .accessibilityIdentifier(Constants.Accessibility.addAffirmationButton)
        }
    }

    // MARK: - Settings Tab

    private var settingsTab: some View {
        VStack(alignment: .leading, spacing: Spacing.md) {
            Text("Render Settings")
                .font(Typography.sectionTitle)
                .foregroundColor(.textSecondary)

            VStack(spacing: Spacing.md) {
                settingsField(label: "Voice", icon: "mic.fill") {
                    TextField("Voice", text: $project.settings.voice)
                        .textFieldStyle(.plain)
                        .font(Typography.bodyText)
                        .foregroundColor(.textPrimary)
                        .accessibilityIdentifier(Constants.Accessibility.voicePicker)
                }

                settingsField(label: "Swarm Voice", icon: "person.2.fill") {
                    TextField("Swarm Voice", text: Binding(
                        get: { project.settings.swarmVoice ?? "" },
                        set: { project.settings.swarmVoice = $0.isEmpty ? nil : $0 }
                    ))
                    .textFieldStyle(.plain)
                    .font(Typography.bodyText)
                    .foregroundColor(.textPrimary)
                }

                settingsField(label: "Seed", icon: "number") {
                    TextField("Seed", value: $project.settings.seed, format: .number)
                        .textFieldStyle(.plain)
                        .font(Typography.bodyText)
                        .foregroundColor(.textPrimary)
                }

                settingsField(label: "Length (sec)", icon: "clock.fill") {
                    TextField("Length", value: $project.settings.lengthSec, format: .number)
                        .textFieldStyle(.plain)
                        .font(Typography.bodyText)
                        .foregroundColor(.textPrimary)
                }

                HStack {
                    Image(systemName: "tuningfork")
                        .font(.system(size: 14, weight: .medium))
                        .foregroundColor(.accentViolet)
                        .frame(width: 24)

                    Toggle("Export Stems", isOn: $project.settings.exportStems)
                        .font(Typography.bodyBold)
                        .foregroundColor(.textPrimary)
                        .toggleStyle(.switch)
                        .tint(Color.accentViolet)
                }
                .padding(.horizontal, Spacing.sm)
                .padding(.vertical, Spacing.sm)
                .background(
                    RoundedRectangle(cornerRadius: Radius.sm, style: .continuous)
                        .fill(Color.surfacePrimary.opacity(0.3))
                )
                .overlay(
                    RoundedRectangle(cornerRadius: Radius.sm, style: .continuous)
                        .strokeBorder(Color.surfaceSecondary.opacity(0.2), lineWidth: 0.5)
                )
            }

            Spacer()
        }
        .padding(Spacing.lg)
    }

    private func settingsField<Content: View>(
        label: String,
        icon: String,
        @ViewBuilder content: () -> Content
    ) -> some View {
        HStack(spacing: Spacing.sm) {
            Image(systemName: icon)
                .font(.system(size: 14, weight: .medium))
                .foregroundColor(.accentViolet)
                .frame(width: 24)

            Text(label)
                .font(Typography.bodyBold)
                .foregroundColor(.textSecondary)
                .frame(width: 100, alignment: .leading)

            content()
                .padding(.horizontal, Spacing.sm)
                .padding(.vertical, 6)
                .background(
                    RoundedRectangle(cornerRadius: Radius.sm, style: .continuous)
                        .fill(Color.surfacePrimary.opacity(0.5))
                )
                .overlay(
                    RoundedRectangle(cornerRadius: Radius.sm, style: .continuous)
                        .strokeBorder(Color.surfaceSecondary.opacity(0.3), lineWidth: 0.5)
                )
        }
        .padding(.horizontal, Spacing.sm)
    }

    // MARK: - Actions

    private func addAffirmation() {
        let trimmed = newAffirmation.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !trimmed.isEmpty else { return }
        withAnimation(
            MotionSensitiveAnimation.resolve(AnimationTokens.springCard, reduceMotion: reduceMotion)
        ) {
            project.affirmations.append(trimmed)
        }
        newAffirmation = ""
    }

    private func removeAffirmation(at index: Int) {
        guard project.affirmations.indices.contains(index) else { return }
        withAnimation(
            MotionSensitiveAnimation.resolve(AnimationTokens.springCard, reduceMotion: reduceMotion)
        ) {
            project.affirmations.remove(at: index)
            if project.affirmations.isEmpty {
                project.affirmations = [""]
            }
        }
    }

    private var nonEmptyAffirmationCount: Int {
        project.affirmations.filter { !$0.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty }.count
    }
}

// MARK: - Affirmation Row

private struct AffirmationRow: View {
    @Binding var text: String
    let index: Int
    let onRemove: () -> Void

    @State private var isHovered = false

    var body: some View {
        HStack(spacing: Spacing.sm) {
            Text("\(index + 1)")
                .font(Typography.label)
                .monospacedDigit()
                .foregroundColor(.textSecondary)
                .frame(width: 20)

            TextField(
                "Affirmation \(index + 1)",
                text: $text
            )
            .textFieldStyle(.plain)
            .font(Typography.bodyText)
            .foregroundColor(.textPrimary)
            .accessibilityIdentifier("\(Constants.Accessibility.affirmationField)_\(index)")

            Spacer()

            Button {
                onRemove()
            } label: {
                Image(systemName: "minus.circle.fill")
                    .font(.system(size: 16))
                    .foregroundColor(isHovered ? Color.accentViolet : Color.textSecondary.opacity(0.5))
            }
            .buttonStyle(.borderless)
            .accessibilityIdentifier("\(Constants.Accessibility.removeAffirmationButton)_\(index)")
            .opacity(isHovered ? 1 : 0.6)
        }
        .padding(.horizontal, Spacing.sm)
        .padding(.vertical, 6)
        .background(
            RoundedRectangle(cornerRadius: Radius.sm, style: .continuous)
                .fill(isHovered ? Color.accentViolet.opacity(0.06) : Color.clear)
        )
        .animation(AnimationTokens.easeInOut, value: isHovered)
        .onHover { hovering in
            isHovered = hovering
        }
    }
}
