// RenderQueueView.swift
// Hypnogen
//
// Displays active and recent render jobs with progress bars, ETA, and cancel.

import SwiftUI

struct RenderQueueView: View {
    var viewModel: RenderQueueViewModel

    var body: some View {
        VStack(spacing: 0) {
            if viewModel.jobs.isEmpty {
                emptyState
            } else {
                jobsList
            }
        }
        .background(LinearGradient.canvasGradient)
        .navigationTitle("Render Queue")
        .accessibilityIdentifier(Constants.Accessibility.renderQueueList)
    }

    // MARK: - Jobs List

    private var jobsList: some View {
        ScrollView {
            LazyVStack(spacing: Spacing.md) {
                if !viewModel.activeJobs.isEmpty {
                    sectionBlock(title: "Active") {
                        ForEach(viewModel.activeJobs) { job in
                            RenderJobRowView(job: job, onCancel: {
                                Task { await viewModel.cancelJob(job) }
                            })
                            .accessibilityIdentifier("\(Constants.Accessibility.renderJobRow)_\(job.id)")
                        }
                    }
                }

                let terminalJobs = viewModel.jobs.filter { $0.isTerminal }
                if !terminalJobs.isEmpty {
                    sectionBlock(title: "Completed") {
                        ForEach(terminalJobs) { job in
                            RenderJobRowView(job: job, onCancel: nil)
                                .accessibilityIdentifier("\(Constants.Accessibility.renderJobRow)_\(job.id)")
                        }
                    }
                }
            }
            .padding(Spacing.lg)
        }
    }

    // MARK: - Section Block

    private func sectionBlock<Content: View>(
        title: String,
        @ViewBuilder content: () -> Content
    ) -> some View {
        VStack(alignment: .leading, spacing: Spacing.sm) {
            Text(title.uppercased())
                .font(Typography.label)
                .foregroundStyle(Color.textSecondary)
                .tracking(Typography.trackingWide + 0.5)
                .padding(.leading, Spacing.xs)

            content()
        }
    }

    // MARK: - Empty State

    private var emptyState: some View {
        EmptyStateView(
            icon: "list.bullet.clipboard",
            title: "No Render Jobs",
            description: "Open a project and click Render to start"
        )
    }
}

// MARK: - Job Row

struct RenderJobRowView: View {
    let job: RenderJob
    let onCancel: (() -> Void)?

    @State private var pulsePhase = false
    @State private var cancelHovered = false
    @Environment(\.accessibilityReduceMotion) private var reduceMotion

    var body: some View {
        VStack(alignment: .leading, spacing: Spacing.sm) {
            headerRow
            if !job.isTerminal {
                progressSection
            }
            if let error = job.error, job.status == .failed {
                Text(error)
                    .font(Typography.captionText)
                    .foregroundStyle(Color.red)
                    .lineLimit(2)
            }
        }
        .interactiveCardStyle()
        .overlay(activePulseBorder)
        .onAppear {
            if !job.isTerminal {
                pulsePhase = true
            }
        }
    }

    // MARK: - Header Row

    private var headerRow: some View {
        HStack(spacing: Spacing.sm) {
            statusIcon
            VStack(alignment: .leading, spacing: 2) {
                Text(job.projectName)
                    .font(Typography.bodyBold)
                    .foregroundStyle(Color.textPrimary)
                Text(job.submittedAt.formatted(date: .abbreviated, time: .shortened))
                    .font(Typography.captionText)
                    .foregroundStyle(Color.textSecondary)
            }
            Spacer()
            if let onCancel, !job.isTerminal {
                cancelButton(action: onCancel)
            }
        }
    }

    // MARK: - Cancel Button (Ghost Style)

    private func cancelButton(action: @escaping () -> Void) -> some View {
        Button(action: action) {
            Text("Cancel")
                .font(Typography.label)
                .foregroundStyle(cancelHovered ? Color.red : Color.textSecondary)
                .padding(.horizontal, Spacing.sm)
                .padding(.vertical, Spacing.xs)
                .background(
                    RoundedRectangle(cornerRadius: Radius.sm, style: .continuous)
                        .fill(cancelHovered ? Color.red.opacity(0.12) : Color.clear)
                )
                .overlay(
                    RoundedRectangle(cornerRadius: Radius.sm, style: .continuous)
                        .strokeBorder(
                            cancelHovered ? Color.red.opacity(0.4) : Color.surfaceSecondary.opacity(0.4),
                            lineWidth: 1
                        )
                )
        }
        .buttonStyle(.plain)
        .onHover { hovering in cancelHovered = hovering }
        .accessibilityIdentifier("\(Constants.Accessibility.cancelJobButton)_\(job.id)")
    }

    // MARK: - Progress

    private var progressSection: some View {
        VStack(alignment: .leading, spacing: Spacing.xs) {
            GeometryReader { geo in
                ZStack(alignment: .leading) {
                    RoundedRectangle(cornerRadius: 3, style: .continuous)
                        .fill(Color.surfacePrimary)
                        .frame(height: 6)

                    RoundedRectangle(cornerRadius: 3, style: .continuous)
                        .fill(
                            LinearGradient(
                                colors: [Color.accentViolet, Color.accentIndigo],
                                startPoint: .leading,
                                endPoint: .trailing
                            )
                        )
                        .frame(width: max(0, geo.size.width * job.progress), height: 6)
                        .shadow(color: Color.accentViolet.opacity(0.4), radius: 4, x: 0, y: 0)
                }
            }
            .frame(height: 6)
            .accessibilityIdentifier("\(Constants.Accessibility.jobProgressBar)_\(job.id)")

            HStack {
                if let stage = job.stage {
                    Text(stage)
                        .font(Typography.captionText)
                        .foregroundStyle(Color.textSecondary)
                }
                Spacer()
                if !job.etaDisplay.isEmpty {
                    Text(job.etaDisplay)
                        .font(Typography.captionText)
                        .monospacedDigit()
                        .foregroundStyle(Color.textAccent)
                }
                Text("\(Int(job.progress * 100))%")
                    .font(Typography.captionText.monospacedDigit())
                    .foregroundStyle(Color.textAccent)
            }
        }
    }

    // MARK: - Status Icon

    private var statusIcon: some View {
        Group {
            switch job.status {
            case .pending:
                Image(systemName: "clock")
                    .foregroundStyle(Color.orange)
            case .running:
                Image(systemName: "play.circle.fill")
                    .foregroundStyle(Color.accentViolet)
            case .completed:
                Image(systemName: "checkmark.circle.fill")
                    .foregroundStyle(Color.green)
            case .failed:
                Image(systemName: "xmark.circle.fill")
                    .foregroundStyle(Color.red)
            case .cancelled:
                Image(systemName: "slash.circle")
                    .foregroundStyle(Color.textSecondary)
            }
        }
        .font(.title2)
    }

    // MARK: - Active Pulse Border

    @ViewBuilder
    private var activePulseBorder: some View {
        if !job.isTerminal {
            RoundedRectangle(cornerRadius: Radius.md, style: .continuous)
                .strokeBorder(
                    LinearGradient(
                        colors: [
                            Color.accentViolet.opacity(pulsePhase ? 0.7 : 0.2),
                            Color.accentGlow.opacity(pulsePhase ? 0.5 : 0.1),
                        ],
                        startPoint: .topLeading,
                        endPoint: .bottomTrailing
                    ),
                    lineWidth: 1.5
                )
                .pulseAnimation(reduceMotion: reduceMotion, value: pulsePhase)
        }
    }
}
