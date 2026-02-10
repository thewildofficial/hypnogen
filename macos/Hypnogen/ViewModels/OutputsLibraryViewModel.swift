// OutputsLibraryViewModel.swift
// Hypnogen
//
// Manages the library of completed render outputs.

import AppKit
import Foundation
import Observation

/// Represents a completed render output for display in the library.
struct RenderOutput: Identifiable, Hashable {
    let id: String
    let projectName: String
    let completedAt: Date
    let mixURL: URL?
    let stems: [String: URL]

    var completedAtFormatted: String {
        completedAt.formatted(date: .abbreviated, time: .shortened)
    }

    var durationDisplay: String {
        guard let url = mixURL, let _ = try? Data(contentsOf: url) else {
            return "—"
        }
        return "—" // Duration requires audio inspection; placeholder for now
    }
}

@Observable
final class OutputsLibraryViewModel {
    var outputs: [RenderOutput] = []

    /// Build the outputs list from completed render jobs.
    func refreshFromJobs(_ jobs: [RenderJob]) {
        outputs = jobs
            .filter { $0.status == .completed }
            .sorted { ($0.completedAt ?? .distantPast) > ($1.completedAt ?? .distantPast) }
            .map { job in
                RenderOutput(
                    id: job.id,
                    projectName: job.projectName,
                    completedAt: job.completedAt ?? Date(),
                    mixURL: job.outputURLs["mix"],
                    stems: job.outputURLs.filter { $0.key != "mix" }
                )
            }
    }

    /// Reveal a file in Finder.
    func revealInFinder(_ url: URL) {
        NSWorkspace.shared.activateFileViewerSelecting([url])
    }
}
