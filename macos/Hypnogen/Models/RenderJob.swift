// RenderJob.swift
// Hypnogen
//
// Data model for a render job, mirroring the FastAPI Render Job contract.

import Foundation
import Observation

/// Lifecycle states of a render job (mirrors Python JobStatus enum).
enum JobStatus: String, Codable, Sendable {
    case pending
    case running
    case completed
    case failed
    case cancelled
}

/// A render job tracked by the app, corresponding to a backend render-job resource.
@Observable
final class RenderJob: Identifiable, Hashable {
    let id: String
    let projectId: UUID
    let projectName: String
    var status: JobStatus
    var stage: String?
    var progress: Double
    var etaSec: Int?
    var error: String?
    var outputURLs: [String: URL]
    let submittedAt: Date
    var completedAt: Date?

    init(
        id: String = UUID().uuidString,
        projectId: UUID,
        projectName: String,
        status: JobStatus = .pending,
        stage: String? = nil,
        progress: Double = 0.0,
        etaSec: Int? = nil,
        error: String? = nil,
        outputURLs: [String: URL] = [:],
        submittedAt: Date = Date(),
        completedAt: Date? = nil
    ) {
        self.id = id
        self.projectId = projectId
        self.projectName = projectName
        self.status = status
        self.stage = stage
        self.progress = progress
        self.etaSec = etaSec
        self.error = error
        self.outputURLs = outputURLs
        self.submittedAt = submittedAt
        self.completedAt = completedAt
    }

    // MARK: - Computed Properties

    /// Whether the job is in a terminal state.
    var isTerminal: Bool {
        status == .completed || status == .failed || status == .cancelled
    }

    /// Formatted ETA string for display.
    var etaDisplay: String {
        guard let eta = etaSec, eta > 0 else { return "" }
        let minutes = eta / 60
        let seconds = eta % 60
        if minutes > 0 {
            return "\(minutes)m \(seconds)s remaining"
        }
        return "\(seconds)s remaining"
    }

    // MARK: - Hashable / Equatable

    static func == (lhs: RenderJob, rhs: RenderJob) -> Bool {
        lhs.id == rhs.id
    }

    func hash(into hasher: inout Hasher) {
        hasher.combine(id)
    }
}
