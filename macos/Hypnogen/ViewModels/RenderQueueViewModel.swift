// RenderQueueViewModel.swift
// Hypnogen
//
// Manages render jobs: submission, polling, cancellation.

import Foundation
import Observation

/// Interval between status polls for active render jobs.
private let pollingIntervalSeconds: TimeInterval = 2.0

@Observable
final class RenderQueueViewModel {
    var jobs: [RenderJob] = []
    var errorMessage: String?

    private let apiClient: APIClient
    private var pollingTasks: [String: Task<Void, Never>] = [:]

    init(apiClient: APIClient = APIClient()) {
        self.apiClient = apiClient
    }

    // MARK: - Computed

    var activeJobs: [RenderJob] {
        jobs.filter { !$0.isTerminal }
    }

    var completedJobs: [RenderJob] {
        jobs.filter { $0.status == .completed }
    }

    var activeJobCount: Int {
        activeJobs.count
    }

    // MARK: - Job Submission

    func submitRender(for project: Project) async {
        let request = APIRenderJobSubmit(
            script: project.scriptText,
            affirmations: project.affirmations,
            voice: project.settings.voice,
            swarmVoice: project.settings.swarmVoice,
            seed: project.settings.seed,
            lengthSec: project.settings.lengthSec,
            exportStems: project.settings.exportStems,
            gainDb: project.settings.gainDb
        )

        do {
            let status = try await apiClient.submitRenderJob(request)
            let job = RenderJob(
                id: status.jobId,
                projectId: project.id,
                projectName: project.name,
                status: jobStatusFromString(status.status),
                stage: status.stage,
                progress: status.progress,
                etaSec: status.etaSec
            )
            jobs.insert(job, at: 0)
            startPolling(jobId: status.jobId)
            errorMessage = nil
        } catch {
            errorMessage = "Failed to submit render: \(error.localizedDescription)"
        }
    }

    // MARK: - Cancellation

    func cancelJob(_ job: RenderJob) async {
        do {
            try await apiClient.cancelRenderJob(jobId: job.id)
            job.status = .cancelled
            stopPolling(jobId: job.id)
        } catch {
            errorMessage = "Failed to cancel job: \(error.localizedDescription)"
        }
    }

    // MARK: - Polling

    private func startPolling(jobId: String) {
        let task = Task { [weak self] in
            guard let self else { return }
            while !Task.isCancelled {
                try? await Task.sleep(for: .seconds(pollingIntervalSeconds))
                guard !Task.isCancelled else { break }
                await self.pollJobStatus(jobId: jobId)

                if let job = self.jobs.first(where: { $0.id == jobId }), job.isTerminal {
                    break
                }
            }
        }
        pollingTasks[jobId] = task
    }

    private func stopPolling(jobId: String) {
        pollingTasks[jobId]?.cancel()
        pollingTasks.removeValue(forKey: jobId)
    }

    private func pollJobStatus(jobId: String) async {
        guard let job = jobs.first(where: { $0.id == jobId }) else { return }

        do {
            let status = try await apiClient.getRenderJobStatus(jobId: jobId)
            job.status = jobStatusFromString(status.status)
            job.stage = status.stage
            job.progress = status.progress
            job.etaSec = status.etaSec
            job.error = status.error

            if job.status == .completed {
                job.completedAt = Date()
                await fetchArtifacts(for: job)
                stopPolling(jobId: jobId)
            } else if job.status == .failed {
                stopPolling(jobId: jobId)
            }
        } catch {
            // Silently retry on transient errors; the next poll will try again.
        }
    }

    private func fetchArtifacts(for job: RenderJob) async {
        do {
            let artifacts = try await apiClient.getRenderJobArtifacts(jobId: job.id)
            var urls: [String: URL] = [:]
            if let mixURL = URL(string: artifacts.mixWavUrl) {
                urls["mix"] = mixURL
            }
            for (name, path) in artifacts.stems {
                if let stemURL = URL(string: path) {
                    urls[name] = stemURL
                }
            }
            job.outputURLs = urls
        } catch {
            // Artifact fetch failure is non-fatal; user can retry.
        }
    }

    // MARK: - Helpers

    private func jobStatusFromString(_ string: String) -> JobStatus {
        JobStatus(rawValue: string) ?? .pending
    }

    func stopAllPolling() {
        for (_, task) in pollingTasks {
            task.cancel()
        }
        pollingTasks.removeAll()
    }
}
