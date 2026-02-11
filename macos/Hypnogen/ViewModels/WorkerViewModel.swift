// WorkerViewModel.swift
// Hypnogen
//
// View-facing state and actions for managing the local worker process.

import Foundation
import Observation

@MainActor
@Observable
final class WorkerViewModel {
    private let workerManager: WorkerManager
    
    // MARK: - State (MainActor-isolated, synced from actor)
    
    private var _state: WorkerState = .stopped
    private var _port: Int?
    private var _pythonExecutablePath: String?
    
    init() {
        self.workerManager = WorkerManager()
        syncStateFromManager()
    }
    
    private func syncStateFromManager() {
        Task { @MainActor in
            _state = await workerManager.state
            _port = await workerManager.activePort
            _pythonExecutablePath = await workerManager.pythonExecutablePath
        }
    }
    
    var state: WorkerState {
        _state
    }
    
    var port: Int? {
        _port
    }
    
    var pythonExecutablePath: String? {
        _pythonExecutablePath
    }
    
    var canStart: Bool {
        switch state {
        case .stopped, .error:
            return true
        case .starting, .warmingUp, .ready:
            return false
        }
    }
    
    var canStop: Bool {
        switch state {
        case .stopped:
            return false
        case .starting, .warmingUp, .ready:
            return true
        case .error:
            return false
        }
    }
    
    var isBusy: Bool {
        switch state {
        case .starting, .warmingUp:
            return true
        case .stopped, .ready, .error:
            return false
        }
    }
    
    var stateTitle: String {
        switch state {
        case .stopped:
            return "Stopped"
        case .starting:
            return "Starting"
        case .warmingUp:
            return "Warming Up"
        case .ready:
            return "Ready"
        case .error:
            return "Error"
        }
    }
    
    var statusDescription: String {
        switch state {
        case .stopped:
            return "Worker is not running."
        case .starting:
            return "Launching Python process."
        case .warmingUp:
            return "Process started. Waiting for healthy API response."
        case .ready:
            if let port {
                return "Worker is healthy on port \(port)."
            }
            return "Worker is healthy."
        case .error(let message):
            return message
        }
    }
    
    var primaryActionTitle: String {
        canStop ? "Stop Worker" : "Start Worker"
    }
    
    // MARK: - Actions
    
    func startWorker() {
        Task {
            do {
                try await workerManager.start()
                await syncState()
            } catch {
                await syncState()
            }
        }
    }
    
    func stopWorker() {
        Task {
            await workerManager.stop()
            await syncState()
        }
    }
    
    func restartWorker() {
        Task {
            await workerManager.stop()
            do {
                try await workerManager.start()
            } catch {
                // Error state is set by manager
            }
            await syncState()
        }
    }
    
    func toggleWorker() {
        if canStop {
            stopWorker()
        } else {
            startWorker()
        }
    }
    
    private func syncState() async {
        _state = await workerManager.state
        _port = await workerManager.activePort
        _pythonExecutablePath = await workerManager.pythonExecutablePath
    }
}
