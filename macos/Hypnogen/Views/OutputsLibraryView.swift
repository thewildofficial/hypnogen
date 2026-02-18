// OutputsLibraryView.swift
// Hypnogen
//
// Premium grid view of completed render outputs with preview and Finder reveal.

import SwiftUI

private let gridItemMinWidth: CGFloat = 240

struct OutputsLibraryView: View {
    var viewModel: OutputsLibraryViewModel

    private let columns = [
        GridItem(.adaptive(minimum: gridItemMinWidth), spacing: Spacing.lg)
    ]

    var body: some View {
        VStack(spacing: 0) {
            if viewModel.outputs.isEmpty {
                emptyState
            } else {
                outputsGrid
            }
        }
        .background(LinearGradient.canvasGradient)
        .navigationTitle("Outputs Library")
        .accessibilityIdentifier(Constants.Accessibility.outputsGrid)
    }

    // MARK: - Grid Header

    private var gridHeader: some View {
        HStack(spacing: Spacing.sm) {
            Text("\(viewModel.outputs.count) Output\(viewModel.outputs.count == 1 ? "" : "s")")
                .font(Typography.bodyBold)
                .foregroundStyle(Color.textPrimary)

            Spacer()

            // Placeholder filter/sort controls
            HStack(spacing: Spacing.xs) {
                Button {
                    // Sort — placeholder
                } label: {
                    Label("Sort", systemImage: "arrow.up.arrow.down")
                }
                .ghostButtonStyle(size: .small)

                Button {
                    // Filter — placeholder
                } label: {
                    Label("Filter", systemImage: "line.3.horizontal.decrease")
                }
                .ghostButtonStyle(size: .small)
            }
        }
        .padding(.horizontal, Spacing.lg)
        .padding(.top, Spacing.lg)
        .padding(.bottom, Spacing.sm)
    }

    // MARK: - Grid

    private var outputsGrid: some View {
        ScrollView {
            VStack(spacing: 0) {
                gridHeader

                LazyVGrid(columns: columns, spacing: Spacing.lg) {
                    ForEach(viewModel.outputs) { output in
                        OutputCardView(output: output, onReveal: {
                            if let url = output.mixURL {
                                viewModel.revealInFinder(url)
                            }
                        })
                        .accessibilityIdentifier("\(Constants.Accessibility.outputItem)_\(output.id)")
                    }
                }
                .padding(.horizontal, Spacing.lg)
                .padding(.bottom, Spacing.lg)
            }
        }
    }

    // MARK: - Empty State

    private var emptyState: some View {
        EmptyStateView(
            icon: "music.note.list",
            title: "No Outputs",
            description: "Completed renders will appear here"
        )
    }
}

// MARK: - Output Card

struct OutputCardView: View {
    let output: RenderOutput
    let onReveal: () -> Void

    var body: some View {
        VStack(alignment: .leading, spacing: Spacing.sm) {
            waveformPlaceholder
            cardContent
            cardActions
        }
        .interactiveCardStyle()
    }

    // MARK: - Waveform Visualization

    private var waveformPlaceholder: some View {
        RoundedRectangle(cornerRadius: Radius.sm, style: .continuous)
            .fill(
                LinearGradient(
                    colors: [
                        Color.accentViolet.opacity(0.25),
                        Color.accentIndigo.opacity(0.18),
                        Color.accentViolet.opacity(0.12),
                    ],
                    startPoint: .leading,
                    endPoint: .trailing
                )
            )
            .frame(height: 88)
            .overlay {
                Image(systemName: "waveform")
                    .font(.system(size: 28, weight: .light))
                    .foregroundStyle(
                        LinearGradient(
                            colors: [Color.accentGlow, Color.accentViolet.opacity(0.7)],
                            startPoint: .leading,
                            endPoint: .trailing
                        )
                    )
                    .shadow(color: Color.accentGlow.opacity(0.4), radius: 8, x: 0, y: 0)
            }
    }

    // MARK: - Content

    private var cardContent: some View {
        VStack(alignment: .leading, spacing: Spacing.xs) {
            Text(output.projectName)
                .font(Typography.sectionTitle)
                .foregroundStyle(Color.textPrimary)
                .tracking(Typography.trackingNormal)
                .lineLimit(1)

            Text(output.completedAtFormatted)
                .font(Typography.captionText)
                .foregroundStyle(Color.textSecondary.opacity(0.7))
                .tracking(Typography.trackingWide)
        }
    }

    // MARK: - Actions

    private var cardActions: some View {
        HStack(spacing: Spacing.sm) {
            if output.mixURL != nil {
                Button {
                    // Playback will be implemented in a future task
                } label: {
                    ButtonLabel("Play", icon: "play.fill", size: .small)
                }
                .primaryButtonStyle(size: .small)
                .accessibilityIdentifier("\(Constants.Accessibility.playOutputButton)_\(output.id)")
            }

            Button(action: onReveal) {
                ButtonLabel("Reveal", icon: "folder", size: .small)
            }
            .secondaryButtonStyle(size: .small)
            .accessibilityIdentifier("\(Constants.Accessibility.revealInFinderButton)_\(output.id)")

            Spacer()
        }
    }
}
