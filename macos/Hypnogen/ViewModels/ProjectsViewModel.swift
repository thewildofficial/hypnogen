// ProjectsViewModel.swift
// Hypnogen
//
// Manages the list of projects and CRUD operations.

import Foundation
import Observation

@Observable
final class ProjectsViewModel {
    var projects: [Project] = []
    var selectedProject: Project?
    var errorMessage: String?

    private let store = ProjectStore()

    // MARK: - Loading

    func loadProjects() {
        projects = store.loadProjects()
    }

    // MARK: - CRUD

    func createProject() {
        let project = Project(
            name: Constants.Defaults.projectName,
            scriptText: "",
            affirmations: [""]
        )
        projects.insert(project, at: 0)
        selectedProject = project
        saveProject(project)
    }

    func deleteProject(_ project: Project) {
        do {
            try store.delete(project)
            projects.removeAll { $0.id == project.id }
            if selectedProject?.id == project.id {
                selectedProject = projects.first
            }
        } catch {
            errorMessage = "Failed to delete project: \(error.localizedDescription)"
        }
    }

    func saveProject(_ project: Project) {
        project.touch()
        do {
            try store.save(project)
            errorMessage = nil
        } catch {
            errorMessage = "Failed to save project: \(error.localizedDescription)"
        }
    }

    func duplicateProject(_ project: Project) {
        let duplicate = Project(
            name: "\(project.name) Copy",
            scriptText: project.scriptText,
            affirmations: project.affirmations,
            settings: project.settings
        )
        projects.insert(duplicate, at: 0)
        selectedProject = duplicate
        saveProject(duplicate)
    }
}
