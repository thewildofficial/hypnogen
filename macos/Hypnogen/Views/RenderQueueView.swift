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
        .background(Color.canvas)
        .navigationTitle("Render Queue")
        .accessibilityIdentifier(Constants.Accessibility.renderQueueList)
    }

    // MARK: - Jobs List

    private var jobsList: some View {
        List {
            if !viewModel.activeJobs.isEmpty {
                Section("Active") {
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
                Section("Completed") {
                    ForEach(terminalJobs) { job in
                        RenderJobRowView(job: job, onCancel: nil)
                            .accessibilityIdentifier("\(Constants.Accessibility.renderJobRow)_\(job.id)")
                    }
                }
            }
        }
        .listStyle(.inset(alternatesRowBackgrounds: true))
        .scrollContentBackground(.hidden)
        .background(Color.canvas)
    }

    // MARK: - Empty State

    private var emptyState: some View {
        VStack(spacing: 12) {
            Image(systemName: "list.bullet.clipboard")
                .font(.system(size: 48))
                .foregroundStyle(Color.textSecondary)
            Text("No Render Jobs")
                .font(.title3)
                .foregroundStyle(Color.textSecondary)
            Text("Open a project and click Render to start")
                .font(.caption)
                .foregroundStyle(Color.textSecondary)
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
        .background(Color.canvas)
    }
}

// MARK: - Job Row

struct RenderJobRowView: View {
    let job: RenderJob
    let onCancel: (() -> Void)?

    var body: some View {
        VStack(alignment: .leading, spacing: 6) {
            HStack {
                statusIcon
                VStack(alignment: .leading, spacing: 2) {
                    Text(job.projectName)
                        .font(.headline)
                    Text(job.submittedAt.formatted(date: .abbreviated, time: .shortened))
                        .font(.caption)
                        .foregroundStyle(Color.textSecondary)
                }
                Spacer()
                if let onCancel, !job.isTerminal {
                    Button("Cancel", role: .destructive, action: onCancel)
                        .buttonStyle(.bordered)
                        .controlSize(.small)
                        .accessibilityIdentifier("\(Constants.Accessibility.cancelJobButton)_\(job.id)")
                }
            }

            if !job.isTerminal {
                progressSection
            }

            if let error = job.error, job.status == .failed {
                Text(error)
                    .font(.caption)
                    .foregroundStyle(Color.red)
                    .lineLimit(2)
            }
        }
        .padding(.vertical, 4)
    }

    // MARK: - Progress

    private var progressSection: some View {
        VStack(alignment: .leading, spacing: 4) {
            ProgressView(value: job.progress, total: 1.0)
                .accessibilityIdentifier("\(Constants.Accessibility.jobProgressBar)_\(job.id)")

            HStack {
                if let stage = job.stage {
                    Text(stage)
                        .font(.caption)
                        .foregroundStyle(Color.textSecondary)
                }
                Spacer()
                if !job.etaDisplay.isEmpty {
                    Text(job.etaDisplay)
                        .font(.caption)
                        .foregroundStyle(Color.textSecondary)
                        .monospacedDigit()
                }
                Text("\(Int(job.progress * 100))%")
                    .font(.caption.monospacedDigit())
                    .foregroundStyle(Color.textSecondary)
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
                    .foregroundStyle(Color.blue)
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
}
