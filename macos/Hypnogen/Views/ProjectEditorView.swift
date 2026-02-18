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

    @State private var selectedTab: EditorTab = .script
    @State private var cardAppeared = false

    // Affirmation focus tracking for Enter-to-add flow
    @FocusState private var focusedAffirmationIndex: Int?

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
                    HStack(spacing: 6) {
                        Image(systemName: "waveform")
                            .font(.system(size: 11, weight: .semibold))
                            .frame(width: 14, height: 14)
                        Text("Render")
                            .font(.system(size: 13, weight: .semibold))
                    }
                    .frame(minWidth: 80, minHeight: 28)
                }
                .buttonStyle(PrimaryButtonStyle(size: .small))
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
        .padding(.top, Spacing.xl)
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
        VStack(alignment: .leading, spacing: Spacing.md) {
            HStack(alignment: .firstTextBaseline) {
                Text("Script")
                    .font(Typography.sectionTitle)
                    .foregroundColor(.textSecondary)

                Spacer()

                let wordCount = project.scriptText
                    .split(whereSeparator: { $0.isWhitespace || $0.isNewline })
                    .count
                Text("\(wordCount) words")
                    .font(Typography.captionText)
                    .foregroundColor(.textSecondary.opacity(0.6))
                    .monospacedDigit()
            }
            .padding(.horizontal, Spacing.xs)

            TextEditor(text: $project.scriptText)
                .font(Typography.monospaceText)
                .foregroundColor(.textPrimary)
                .scrollContentBackground(.hidden)
                .padding(.leading, Spacing.md + 4)
                .padding(.trailing, Spacing.md)
                .padding(.vertical, Spacing.md)
                .frame(maxWidth: .infinity, maxHeight: .infinity)
                .background(
                    RoundedRectangle(cornerRadius: Radius.md, style: .continuous)
                        .fill(Color.backgroundDeep.opacity(0.4))
                )
                .overlay(alignment: .leading) {
                    RoundedRectangle(cornerRadius: 2)
                        .fill(
                            LinearGradient(
                                colors: [Color.accentIndigo.opacity(0.7), Color.accentViolet.opacity(0.3)],
                                startPoint: .top,
                                endPoint: .bottom
                            )
                        )
                        .frame(width: 3)
                        .padding(.vertical, Spacing.sm)
                        .padding(.leading, Spacing.sm)
                }
                .overlay(
                    RoundedRectangle(cornerRadius: Radius.md, style: .continuous)
                        .strokeBorder(Color.surfaceSecondary.opacity(0.2), lineWidth: 0.5)
                )
                .clipShape(RoundedRectangle(cornerRadius: Radius.md, style: .continuous))
                .accessibilityIdentifier(Constants.Accessibility.scriptEditor)
        }
        .padding(Spacing.lg)
    }

    // MARK: - Affirmations Tab

    private var affirmationsTab: some View {
        VStack(alignment: .leading, spacing: 0) {
            HStack(alignment: .firstTextBaseline) {
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
            .padding(.horizontal, Spacing.xs)
            .padding(.bottom, Spacing.md)

            ScrollView {
                LazyVStack(spacing: 2) {
                    ForEach(Array(project.affirmations.enumerated()), id: \.offset) { index, _ in
                        AffirmationRow(
                            text: Binding(
                                get: { project.affirmations[index] },
                                set: { project.affirmations[index] = $0 }
                            ),
                            index: index,
                            isFocused: focusedAffirmationIndex == index,
                            onRemove: { removeAffirmation(at: index) },
                            onSubmit: { handleAffirmationSubmit(at: index) }
                        )
                        .focused($focusedAffirmationIndex, equals: index)
                        .transition(
                            .asymmetric(
                                insertion: .move(edge: .top)
                                    .combined(with: .opacity)
                                    .combined(with: .scale(scale: 0.95, anchor: .top)),
                                removal: .opacity.combined(with: .scale(scale: 0.95))
                            )
                        )
                        .id("affirmation-\(index)")
                    }

                    Button {
                        addEmptyAffirmation()
                    } label: {
                        HStack(spacing: Spacing.sm) {
                            Image(systemName: "plus")
                                .font(.system(size: 11, weight: .semibold))
                                .foregroundColor(.accentViolet.opacity(0.7))
                                .frame(width: 20, height: 20)
                                .background(
                                    Circle()
                                        .fill(Color.accentViolet.opacity(0.1))
                                )

                            Text("Add affirmation")
                                .font(Typography.bodySmall)
                                .foregroundColor(.textSecondary.opacity(0.6))
                        }
                        .frame(maxWidth: .infinity, alignment: .leading)
                        .padding(.horizontal, Spacing.md)
                        .padding(.vertical, Spacing.sm)
                        .contentShape(Rectangle())
                    }
                    .buttonStyle(.plain)
                    .accessibilityIdentifier(Constants.Accessibility.addAffirmationButton)
                    .padding(.top, Spacing.sm)
                }
                .padding(.vertical, Spacing.xs)
            }
            .accessibilityIdentifier(Constants.Accessibility.affirmationsList)
        }
        .padding(Spacing.lg)
    }

    // MARK: - Settings Tab

    private var settingsTab: some View {
        VStack(alignment: .leading, spacing: Spacing.md) {
            Text("Render Settings")
                .font(Typography.sectionTitle)
                .foregroundColor(.textSecondary)
                .padding(.horizontal, Spacing.xs)

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

    private func addEmptyAffirmation() {
        let newIndex = project.affirmations.count
        withAnimation(
            MotionSensitiveAnimation.resolve(
                .spring(response: 0.35, dampingFraction: 0.8),
                reduceMotion: reduceMotion
            )
        ) {
            project.affirmations.append("")
        }
        DispatchQueue.main.asyncAfter(deadline: .now() + 0.1) {
            focusedAffirmationIndex = newIndex
        }
    }

    private func handleAffirmationSubmit(at index: Int) {
        let trimmed = project.affirmations[index].trimmingCharacters(in: .whitespacesAndNewlines)
        if !trimmed.isEmpty {
            let newIndex = index + 1
            withAnimation(
                MotionSensitiveAnimation.resolve(
                    .spring(response: 0.35, dampingFraction: 0.8),
                    reduceMotion: reduceMotion
                )
            ) {
                if newIndex >= project.affirmations.count {
                    project.affirmations.append("")
                } else {
                    project.affirmations.insert("", at: newIndex)
                }
            }
            DispatchQueue.main.asyncAfter(deadline: .now() + 0.1) {
                focusedAffirmationIndex = newIndex
            }
        } else if index + 1 < project.affirmations.count {
            focusedAffirmationIndex = index + 1
        }
    }

    private func removeAffirmation(at index: Int) {
        guard project.affirmations.indices.contains(index) else { return }
        withAnimation(
            MotionSensitiveAnimation.resolve(
                .spring(response: 0.3, dampingFraction: 0.8),
                reduceMotion: reduceMotion
            )
        ) {
            project.affirmations.remove(at: index)
            if project.affirmations.isEmpty {
                project.affirmations = [""]
            }
        }
        DispatchQueue.main.asyncAfter(deadline: .now() + 0.1) {
            let focusIndex = max(0, index - 1)
            if project.affirmations.indices.contains(focusIndex) {
                focusedAffirmationIndex = focusIndex
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
    let isFocused: Bool
    let onRemove: () -> Void
    let onSubmit: () -> Void

    @State private var isHovered = false

    var body: some View {
        HStack(spacing: 0) {
            Text("\(index + 1)")
                .font(Typography.label)
                .monospacedDigit()
                .foregroundColor(isFocused ? Color.accentViolet : Color.textSecondary.opacity(0.4))
                .frame(width: 28, alignment: .trailing)
                .padding(.trailing, Spacing.sm)
                .animation(AnimationTokens.easeInOut, value: isFocused)

            VStack(spacing: 0) {
                TextField("Type an affirmation…", text: $text)
                    .textFieldStyle(.plain)
                    .font(Typography.bodyText)
                    .foregroundColor(.textPrimary)
                    .accessibilityIdentifier("\(Constants.Accessibility.affirmationField)_\(index)")
                    .onSubmit { onSubmit() }
                    .padding(.vertical, 8)

                Rectangle()
                    .fill(
                        isFocused
                            ? Color.accentViolet.opacity(0.6)
                            : (isHovered ? Color.surfaceSecondary.opacity(0.5) : Color.surfaceSecondary.opacity(0.2))
                    )
                    .frame(height: isFocused ? 1.5 : 0.5)
                    .animation(.spring(response: 0.3, dampingFraction: 0.8), value: isFocused)
            }

            Button {
                onRemove()
            } label: {
                Image(systemName: "xmark")
                    .font(.system(size: 10, weight: .semibold))
                    .foregroundColor(.textSecondary.opacity(0.5))
                    .frame(width: 20, height: 20)
                    .background(
                        Circle()
                            .fill(Color.surfaceSecondary.opacity(isHovered ? 0.3 : 0))
                    )
            }
            .buttonStyle(.borderless)
            .accessibilityIdentifier("\(Constants.Accessibility.removeAffirmationButton)_\(index)")
            .opacity(isHovered || isFocused ? 1 : 0)
            .animation(AnimationTokens.easeInOut, value: isHovered)
            .animation(AnimationTokens.easeInOut, value: isFocused)
            .padding(.leading, Spacing.sm)
        }
        .padding(.horizontal, Spacing.md)
        .padding(.vertical, 2)
        .background(
            RoundedRectangle(cornerRadius: Radius.sm, style: .continuous)
                .fill(isHovered && !isFocused ? Color.accentViolet.opacity(0.03) : Color.clear)
        )
        .animation(AnimationTokens.easeInOut, value: isHovered)
        .onHover { hovering in
            isHovered = hovering
        }
    }
}
