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
                .background(Color.canvas)

            affirmationsPanel
                .frame(minWidth: 250, maxWidth: 400)
                .background(Color.surface)
        }
        .background(Color.canvas)
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
                .buttonStyle(PrimaryButtonStyle())
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
                    .foregroundColor(.textPrimary)
                    .accessibilityIdentifier(Constants.Accessibility.projectNameField)
                    .onChange(of: project.name) { _, _ in onSave() }
            }
            .padding(.horizontal)
            .padding(.top, 12)

            Text("Script")
                .font(.headline)
                .foregroundColor(.textSecondary)
                .padding(.horizontal)

            TextEditor(text: $project.scriptText)
                .font(.body.monospaced())
                .foregroundColor(.textPrimary)
                .scrollContentBackground(.hidden)
                .padding(8)
                .background(Color.surface)
                .overlay(
                    RoundedRectangle(cornerRadius: Radius.md)
                        .stroke(Color.stroke, lineWidth: 1)
                )
                .clipShape(RoundedRectangle(cornerRadius: Radius.md))
                .padding(.horizontal)
                .padding(.bottom, 12)
                .accessibilityIdentifier(Constants.Accessibility.scriptEditor)
        }
        .background(Color.canvas)
    }

    // MARK: - Affirmations Panel

    private var affirmationsPanel: some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack {
                Text("Affirmations")
                    .font(.headline)
                    .foregroundColor(.textSecondary)
                Spacer()
                Text("\(nonEmptyAffirmationCount)")
                    .font(.caption)
                    .foregroundColor(.textSecondary)
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
                        .foregroundColor(.textPrimary)
                        .accessibilityIdentifier("\(Constants.Accessibility.affirmationField)_\(index)")

                        Button {
                            removeAffirmation(at: index)
                        } label: {
                            Image(systemName: "minus.circle.fill")
                                .foregroundColor(.textSecondary)
                        }
                        .buttonStyle(.borderless)
                        .accessibilityIdentifier("\(Constants.Accessibility.removeAffirmationButton)_\(index)")
                    }
                    .listRowBackground(Color.surface)
                }
            }
            .listStyle(.plain)
            .background(Color.surface)
            .accessibilityIdentifier(Constants.Accessibility.affirmationsList)

            HStack {
                TextField("Add affirmation...", text: $newAffirmation)
                    .textFieldStyle(.roundedBorder)
                    .onSubmit { addAffirmation() }

                Button {
                    addAffirmation()
                } label: {
                    Image(systemName: "plus.circle.fill")
                        .foregroundColor(.accentPrimary)
                }
                .buttonStyle(.borderless)
                .disabled(newAffirmation.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty)
                .accessibilityIdentifier(Constants.Accessibility.addAffirmationButton)
            }
            .padding(.horizontal)
            .padding(.bottom, 12)
        }
        .background(Color.surface)
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
