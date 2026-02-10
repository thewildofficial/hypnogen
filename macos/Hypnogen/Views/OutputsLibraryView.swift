// OutputsLibraryView.swift
// Hypnogen
//
// Grid view of completed render outputs with preview and Finder reveal.

import SwiftUI

private let gridItemMinWidth: CGFloat = 200

struct OutputsLibraryView: View {
    var viewModel: OutputsLibraryViewModel

    private let columns = [
        GridItem(.adaptive(minimum: gridItemMinWidth), spacing: 16)
    ]

    var body: some View {
        VStack(spacing: 0) {
            if viewModel.outputs.isEmpty {
                emptyState
            } else {
                outputsGrid
            }
        }
        .navigationTitle("Outputs Library")
        .accessibilityIdentifier(Constants.Accessibility.outputsGrid)
    }

    // MARK: - Grid

    private var outputsGrid: some View {
        ScrollView {
            LazyVGrid(columns: columns, spacing: 16) {
                ForEach(viewModel.outputs) { output in
                    OutputCardView(output: output, onReveal: {
                        if let url = output.mixURL {
                            viewModel.revealInFinder(url)
                        }
                    })
                    .accessibilityIdentifier("\(Constants.Accessibility.outputItem)_\(output.id)")
                }
            }
            .padding()
        }
    }

    // MARK: - Empty State

    private var emptyState: some View {
        VStack(spacing: 12) {
            Image(systemName: "music.note.list")
                .font(.system(size: 48))
                .foregroundStyle(.tertiary)
            Text("No Outputs")
                .font(.title3)
                .foregroundStyle(.secondary)
            Text("Completed renders will appear here")
                .font(.caption)
                .foregroundStyle(.tertiary)
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
    }
}

// MARK: - Output Card

struct OutputCardView: View {
    let output: RenderOutput
    let onReveal: () -> Void

    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            // Waveform placeholder
            RoundedRectangle(cornerRadius: 8)
                .fill(Color(nsColor: .controlBackgroundColor))
                .frame(height: 80)
                .overlay {
                    Image(systemName: "waveform")
                        .font(.title)
                        .foregroundStyle(.tertiary)
                }

            VStack(alignment: .leading, spacing: 4) {
                Text(output.projectName)
                    .font(.headline)
                    .lineLimit(1)

                Text(output.completedAtFormatted)
                    .font(.caption)
                    .foregroundStyle(.secondary)
            }

            HStack(spacing: 8) {
                if output.mixURL != nil {
                    Button {
                        // Playback will be implemented in a future task
                    } label: {
                        Label("Play", systemImage: "play.fill")
                    }
                    .buttonStyle(.bordered)
                    .controlSize(.small)
                    .accessibilityIdentifier("\(Constants.Accessibility.playOutputButton)_\(output.id)")
                }

                Button(action: onReveal) {
                    Label("Reveal", systemImage: "folder")
                }
                .buttonStyle(.bordered)
                .controlSize(.small)
                .accessibilityIdentifier("\(Constants.Accessibility.revealInFinderButton)_\(output.id)")
            }
        }
        .padding(12)
        .background(Color(nsColor: .controlBackgroundColor))
        .clipShape(RoundedRectangle(cornerRadius: 10))
        .shadow(color: .black.opacity(0.05), radius: 2, y: 1)
    }
}
