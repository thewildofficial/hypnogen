// ContentView.swift
// Hypnogen
//
// Main container view with NavigationSplitView for sidebar + detail layout.

import SwiftUI

/// Navigation destinations available from the sidebar.
enum NavigationDestination: Hashable {
    case projectEditor(Project)
    case renderQueue
    case outputsLibrary
}

struct ContentView: View {
    @Bindable var projectsViewModel: ProjectsViewModel
    @Bindable var renderQueueViewModel: RenderQueueViewModel
    @Bindable var outputsLibraryViewModel: OutputsLibraryViewModel
    @Bindable var onboardingViewModel: OnboardingViewModel

    @State private var selectedDestination: NavigationDestination?
    @State private var columnVisibility: NavigationSplitViewVisibility = .all

    var body: some View {
        NavigationSplitView(columnVisibility: $columnVisibility) {
            sidebar
                .accessibilityIdentifier(Constants.Accessibility.sidebar)
        } detail: {
            detailView
        }
        .navigationSplitViewStyle(.balanced)
        .onChange(of: projectsViewModel.selectedProject) { _, newValue in
            if let project = newValue {
                selectedDestination = .projectEditor(project)
            }
        }
        .sheet(isPresented: $onboardingViewModel.isPresented) {
            OnboardingView(viewModel: onboardingViewModel)
        }
    }

    // MARK: - Sidebar

    @ViewBuilder
    private var sidebar: some View {
        List(selection: $selectedDestination) {
            Section {
                ForEach(projectsViewModel.projects) { project in
                    NavigationLink(value: NavigationDestination.projectEditor(project)) {
                        ProjectRowView(project: project)
                    }
                    .accessibilityIdentifier("\(Constants.Accessibility.projectRow)_\(project.id)")
                    .contextMenu {
                        Button("Duplicate") {
                            projectsViewModel.duplicateProject(project)
                        }
                        Divider()
                        Button("Delete", role: .destructive) {
                            projectsViewModel.deleteProject(project)
                        }
                    }
                }
            } header: {
                HStack {
                    Text("Projects")
                    Spacer()
                    Button {
                        projectsViewModel.createProject()
                    } label: {
                        Image(systemName: "plus")
                    }
                    .buttonStyle(.borderless)
                    .accessibilityIdentifier(Constants.Accessibility.newProjectButton)
                }
                .accessibilityIdentifier(Constants.Accessibility.sidebarProjectsSection)
            }

            Section {
                NavigationLink(value: NavigationDestination.renderQueue) {
                    Label {
                        Text("Render Queue")
                    } icon: {
                        Image(systemName: "list.bullet.clipboard")
                    }
                    .badge(renderQueueViewModel.activeJobCount)
                }
                .accessibilityIdentifier(Constants.Accessibility.sidebarRenderQueueSection)
            }

            Section {
                NavigationLink(value: NavigationDestination.outputsLibrary) {
                    Label("Outputs Library", systemImage: "music.note.list")
                }
                .accessibilityIdentifier(Constants.Accessibility.sidebarOutputsSection)
            }
        }
        .listStyle(.sidebar)
        .scrollContentBackground(.hidden)
        .background(Color.canvas)
        .navigationSplitViewColumnWidth(min: 200, ideal: 250, max: 350)
        .accessibilityIdentifier(Constants.Accessibility.projectsList)
    }

    // MARK: - Detail

    @ViewBuilder
    private var detailView: some View {
        switch selectedDestination {
        case .projectEditor(let project):
            ProjectEditorView(
                project: project,
                onSave: { projectsViewModel.saveProject(project) },
                onRender: {
                    Task {
                        await renderQueueViewModel.submitRender(for: project)
                    }
                }
            )

        case .renderQueue:
            RenderQueueView(viewModel: renderQueueViewModel)

        case .outputsLibrary:
            OutputsLibraryView(viewModel: outputsLibraryViewModel)
                .onAppear {
                    outputsLibraryViewModel.refreshFromJobs(renderQueueViewModel.jobs)
                }

        case nil:
            emptyStateView
        }
    }

    private var emptyStateView: some View {
        VStack(spacing: 16) {
            Image(systemName: "waveform.circle")
                .font(.system(size: 64))
                .foregroundStyle(Color.textSecondary)
            Text("Select or create a project to get started")
                .font(.title2)
                .foregroundStyle(Color.textSecondary)
            Button("New Project") {
                projectsViewModel.createProject()
            }
            .buttonStyle(.borderedProminent)
            .accessibilityIdentifier(Constants.Accessibility.newProjectButton)
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
        .background(Color.canvas)
    }
}

// MARK: - Project Row

struct ProjectRowView: View {
    let project: Project

    var body: some View {
        VStack(alignment: .leading, spacing: 2) {
            Text(project.name)
                .font(.headline)
                .lineLimit(1)
            Text(project.modifiedAt.formatted(date: .abbreviated, time: .shortened))
                .font(.caption)
                .foregroundStyle(Color.textSecondary)
        }
        .padding(.vertical, 2)
    }
}
