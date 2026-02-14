// WorkerManager.swift
// Hypnogen
//
// Launches and monitors the local Python FastAPI worker process.

import Foundation
import Observation

/// Runtime lifecycle for the local render worker process.
enum WorkerState: Equatable, Sendable {
    case stopped
    case starting
    case warmingUp
    case ready
    case error(String)
}

/// Errors that can occur while launching or monitoring the worker process.
enum WorkerManagerError: LocalizedError, Sendable {
    case pythonNotFound
    case workerModuleNotFound
    case launchFailed(String)

    var errorDescription: String? {
        switch self {
        case .pythonNotFound:
            return "Python executable was not found. Install Python 3 and ensure it is on PATH."
        case .workerModuleNotFound:
            return "Could not locate the repository root for `hypnogen.api.app`."
        case .launchFailed(let detail):
            return "Failed to launch worker: \(detail)"
        }
    }
}

actor WorkerManager {
    private enum Configuration {
        static let workerModule = "hypnogen.api.app"
        static let startupTimeout: TimeInterval = 30.0
    }

    // MARK: - State

    private(set) var state: WorkerState = .stopped
    private(set) var activePort: Int?
    private(set) var pythonExecutablePath: String?

    // MARK: - Private State

    private var process: Process?
    private var healthPollTask: Task<Void, Never>?
    private var outputPipe: Pipe?
    private var outputHandle: FileHandle?
    private var outputBuffer = ""

    // MARK: - Initialization

    init() {}

    // MARK: - Public API

    func start() async throws {
        guard state == .stopped else { return }

        state = .starting

        do {
            // Find Python executable
            guard let pythonPath = findPythonExecutable() else {
                throw WorkerManagerError.pythonNotFound
            }
            pythonExecutablePath = pythonPath

            // Launch worker process
            let port = try await launchWorkerProcess(pythonPath: pythonPath)
            activePort = port

            // Wait for worker to be ready
            state = .warmingUp
            let isReady = await waitForWorkerReady(timeout: Configuration.startupTimeout)

            if isReady {
                state = .ready
            } else {
                await stop()
                state = .error("Worker failed to start within \(Int(Configuration.startupTimeout))s")
            }
        } catch {
            await stop()
            state = .error(error.localizedDescription)
            throw error
        }
    }

    func stop() async {
        guard state != .stopped else { return }

        healthPollTask?.cancel()
        healthPollTask = nil

        process?.terminate()
        process = nil

        clearReferences()
        state = .stopped
    }

    // MARK: - Private Methods

    private func findPythonExecutable() -> String? {
        let task = Process()
        task.executableURL = URL(fileURLWithPath: "/usr/bin/env")
        task.arguments = ["which", "python3"]

        let pipe = Pipe()
        task.standardOutput = pipe
        task.standardError = Pipe()

        try? task.run()
        task.waitUntilExit()

        guard task.terminationStatus == 0 else { return nil }

        let data = pipe.fileHandleForReading.readDataToEndOfFile()
        return String(data: data, encoding: .utf8)?.trimmingCharacters(in: .whitespacesAndNewlines)
    }

    private func launchWorkerProcess(pythonPath: String) async throws -> Int {
        let task = Process()
        task.executableURL = URL(fileURLWithPath: pythonPath)
        task.arguments = ["-m", Configuration.workerModule]
        task.currentDirectoryPath = FileManager.default.currentDirectoryPath

        let outputPipe = Pipe()
        task.standardOutput = outputPipe
        task.standardError = outputPipe
        self.outputPipe = outputPipe
        self.outputHandle = outputPipe.fileHandleForReading
        self.outputHandle?.readabilityHandler = { [weak self] handle in
            let data = handle.availableData
            guard !data.isEmpty, let chunk = String(data: data, encoding: .utf8) else {
                return
            }
            Task {
                await self?.appendOutputChunk(chunk)
            }
        }

        try task.run()
        process = task

        // Wait for port
        let port = try await waitForPort(timeout: Configuration.startupTimeout)

        return port
    }

    private func waitForPort(timeout: TimeInterval) async throws -> Int {
        let deadline = Date().addingTimeInterval(timeout)

        while Date() < deadline {
            try Task.checkCancellation()

            if let port = extractPort(from: outputBuffer) {
                return port
            }

            if let process, !process.isRunning {
                throw WorkerManagerError.launchFailed(
                    "Worker process exited before reporting port (status \(process.terminationStatus))."
                )
            }
            try await Task.sleep(nanoseconds: 100_000_000)
        }

        throw WorkerManagerError.launchFailed("Timeout waiting for port")
    }

    private func appendOutputChunk(_ chunk: String) {
        outputBuffer.append(chunk)
    }

    private func extractPort(from output: String) -> Int? {
        let pattern = #"http://127\.0\.0\.1:(\d+)"#
        if let regex = try? NSRegularExpression(pattern: pattern),
           let match = regex.firstMatch(in: output, range: NSRange(output.startIndex..., in: output)),
           let range = Range(match.range(at: 1), in: output) {
            return Int(output[range])
        }
        return nil
    }

    private func waitForWorkerReady(timeout: TimeInterval) async -> Bool {
        let deadline = Date().addingTimeInterval(timeout)

        while Date() < deadline {
            try? Task.checkCancellation()

            if let port = activePort {
                do {
                    let url = URL(string: "http://127.0.0.1:\(port)/health")
                    let (_, response) = try await URLSession.shared.data(from: url!)
                    if let httpResponse = response as? HTTPURLResponse, httpResponse.statusCode == 200 {
                        return true
                    }
                } catch {
                    // Not ready yet
                }
            }

            try? await Task.sleep(nanoseconds: 500_000_000)
        }

        return false
    }

    private func clearReferences() {
        process = nil
        outputHandle?.readabilityHandler = nil
        outputHandle = nil
        outputPipe = nil
        outputBuffer = ""
        activePort = nil
    }
}
