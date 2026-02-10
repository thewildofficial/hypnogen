// ProjectEditorView.swift
// Hypnogen
//
// Editor for a single project: script text, affirmations list, render settings.

import SwiftUI

struct ProjectEditorView: View {
    @Bindable var project: Project
    let onSave: () -> Void
    let onRender: () -> Void

    @State private var newAffirmation = ""
    @State private var showSettings = false

    var body: some View {
        HSplitView {
            scriptPanel
                .frame(minWidth: 300)

            affirmationsPanel
                .frame(minWidth: 250, maxWidth: 400)
        }
        .toolbar {
            ToolbarItemGroup(placement: .primaryAction) {
                Button {
                    showSettings.toggle()
                } label: {
                    Label("Settings", systemImage: "slider.horizontal.3")
                }
                .accessibilityIdentifier("settingsButton")
                .popover(isPresented: $showSettings) {
                    settingsPopover
                }

                Button(action: onRender) {
                    Label("Render", systemImage: "waveform")
                }
                .buttonStyle(.borderedProminent)
                .accessibilityIdentifier(Constants.Accessibility.renderButton)
                .disabled(project.scriptText.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty
                          || project.affirmations.filter({ !$0.isEmpty }).isEmpty)
            }
        }
        .navigationTitle(project.name)
        .onChange(of: project.scriptText) { _, _ in onSave() }
        .onChange(of: project.affirmations) { _, _ in onSave() }
    }

    // MARK: - Script Panel

    private var scriptPanel: some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack {
                TextField("Project Name", text: $project.name)
                    .textFieldStyle(.plain)
                    .font(.title2.bold())
                    .accessibilityIdentifier(Constants.Accessibility.projectNameField)
                    .onChange(of: project.name) { _, _ in onSave() }
            }
            .padding(.horizontal)
            .padding(.top, 12)

            Text("Script")
                .font(.headline)
                .foregroundStyle(.secondary)
                .padding(.horizontal)

            TextEditor(text: $project.scriptText)
                .font(.body.monospaced())
                .scrollContentBackground(.hidden)
                .padding(8)
                .background(Color(nsColor: .textBackgroundColor))
                .clipShape(RoundedRectangle(cornerRadius: 6))
                .padding(.horizontal)
                .padding(.bottom, 12)
                .accessibilityIdentifier(Constants.Accessibility.scriptEditor)
        }
    }

    // MARK: - Affirmations Panel

    private var affirmationsPanel: some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack {
                Text("Affirmations")
                    .font(.headline)
                    .foregroundStyle(.secondary)
                Spacer()
                Text("\(nonEmptyAffirmationCount)")
                    .font(.caption)
                    .foregroundStyle(.tertiary)
                    .monospacedDigit()
            }
            .padding(.horizontal)
            .padding(.top, 12)

            List {
                ForEach(project.affirmations.indices, id: \.self) { index in
                    HStack {
                        TextField(
                            "Affirmation \(index + 1)",
                            text: Binding(
                                get: { project.affirmations[index] },
                                set: { project.affirmations[index] = $0 }
                            )
                        )
                        .textFieldStyle(.plain)
                        .accessibilityIdentifier("\(Constants.Accessibility.affirmationField)_\(index)")

                        Button {
                            removeAffirmation(at: index)
                        } label: {
                            Image(systemName: "minus.circle.fill")
                                .foregroundStyle(.secondary)
                        }
                        .buttonStyle(.borderless)
                        .accessibilityIdentifier("\(Constants.Accessibility.removeAffirmationButton)_\(index)")
                    }
                }
            }
            .listStyle(.plain)
            .accessibilityIdentifier(Constants.Accessibility.affirmationsList)

            HStack {
                TextField("Add affirmation...", text: $newAffirmation)
                    .textFieldStyle(.roundedBorder)
                    .onSubmit { addAffirmation() }

                Button {
                    addAffirmation()
                } label: {
                    Image(systemName: "plus.circle.fill")
                }
                .buttonStyle(.borderless)
                .disabled(newAffirmation.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty)
                .accessibilityIdentifier(Constants.Accessibility.addAffirmationButton)
            }
            .padding(.horizontal)
            .padding(.bottom, 12)
        }
    }

    // MARK: - Settings Popover

    private var settingsPopover: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text("Render Settings")
                .font(.headline)

            Form {
                TextField("Voice:", text: $project.settings.voice)
                    .accessibilityIdentifier(Constants.Accessibility.voicePicker)

                TextField("Swarm Voice:", text: Binding(
                    get: { project.settings.swarmVoice ?? "" },
                    set: { project.settings.swarmVoice = $0.isEmpty ? nil : $0 }
                ))

                TextField("Seed:", value: $project.settings.seed, format: .number)

                TextField("Length (sec):", value: $project.settings.lengthSec, format: .number)

                Toggle("Export Stems", isOn: $project.settings.exportStems)
            }
        }
        .padding()
        .frame(width: 300)
        .onChange(of: project.settings) { _, _ in onSave() }
    }

    // MARK: - Actions

    private func addAffirmation() {
        let trimmed = newAffirmation.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !trimmed.isEmpty else { return }
        project.affirmations.append(trimmed)
        newAffirmation = ""
    }

    private func removeAffirmation(at index: Int) {
        guard project.affirmations.indices.contains(index) else { return }
        project.affirmations.remove(at: index)
        if project.affirmations.isEmpty {
            project.affirmations = [""]
        }
    }

    private var nonEmptyAffirmationCount: Int {
        project.affirmations.filter { !$0.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty }.count
    }
}
