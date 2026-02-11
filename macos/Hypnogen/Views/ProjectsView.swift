// ProjectsView.swift
// Hypnogen
//
// Standalone projects list view (used in toolbar/popover contexts).
// The primary projects list is integrated into the sidebar of ContentView.

import SwiftUI

struct ProjectsView: View {
    @Bindable var viewModel: ProjectsViewModel

    var body: some View {
        VStack(spacing: 0) {
            toolbar

            if viewModel.projects.isEmpty {
                emptyState
            } else {
                projectList
            }
        }
        .background(Color.canvas)
        .frame(minWidth: 300, minHeight: 200)
    }

    // MARK: - Toolbar

    private var toolbar: some View {
        HStack {
            Text("Projects")
                .font(.headline)
            Spacer()
            Button {
                viewModel.createProject()
            } label: {
                Label("New Project", systemImage: "plus")
            }
            .accessibilityIdentifier(Constants.Accessibility.newProjectButton)
        }
        .padding(.horizontal)
        .padding(.vertical, 8)
    }

    // MARK: - List

    private var projectList: some View {
        List(selection: $viewModel.selectedProject) {
            ForEach(viewModel.projects) { project in
                ProjectRowView(project: project)
                    .tag(project)
                    .accessibilityIdentifier("\(Constants.Accessibility.projectRow)_\(project.id)")
                    .contextMenu {
                        Button("Duplicate") {
                            viewModel.duplicateProject(project)
                        }
                        Divider()
                        Button("Delete", role: .destructive) {
                            viewModel.deleteProject(project)
                        }
                        .accessibilityIdentifier(Constants.Accessibility.deleteProjectButton)
                    }
            }
        }
        .listStyle(.sidebar)
        .scrollContentBackground(.hidden)
        .background(Color.canvas)
        .accessibilityIdentifier(Constants.Accessibility.projectsList)
    }

    // MARK: - Empty State

    private var emptyState: some View {
        VStack(spacing: 12) {
            Image(systemName: "doc.badge.plus")
                .font(.system(size: 40))
                .foregroundStyle(Color.textSecondary)
            Text("No Projects")
                .font(.title3)
                .foregroundStyle(Color.textSecondary)
            Text("Create your first hypnosis project")
                .font(.caption)
                .foregroundStyle(Color.textSecondary)
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
        .background(Color.canvas)
    }
}
