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
    @State private var isInitialLoadComplete = false

    /// Whether the hero welcome should be shown instead of the selected destination.
    private var shouldShowHero: Bool {
        if selectedDestination == nil { return true }
        if case .projectEditor = selectedDestination, projectsViewModel.projects.isEmpty {
            return true
        }
        return false
    }

    var body: some View {
        NavigationSplitView(columnVisibility: $columnVisibility) {
            sidebar
                .accessibilityIdentifier(Constants.Accessibility.sidebar)
        } detail: {
            detailView
        }
        .navigationSplitViewStyle(.balanced)
        .onChange(of: projectsViewModel.selectedProject) { _, newValue in
            guard isInitialLoadComplete else { return }
            if let project = newValue {
                selectedDestination = .projectEditor(project)
            }
        }
        .onChange(of: projectsViewModel.projects.count) { _, newCount in
            if newCount == 0 {
                selectedDestination = nil
            }
        }
        .task {
            isInitialLoadComplete = true
        }
        .sheet(isPresented: $onboardingViewModel.isPresented) {
            OnboardingView(viewModel: onboardingViewModel)
        }
    }

    // MARK: - Sidebar

    @ViewBuilder
    private var sidebar: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 0) {
                // ── Create ──────────────────────────────────
                createSection

                SidebarDivider()

                // ── Studio ──────────────────────────────────
                studioSection

                SidebarDivider()

                // ── Library ─────────────────────────────────
                librarySection
            }
            .padding(.vertical, Spacing.sm)
        }
        .scrollContentBackground(.hidden)
        .background(GradientTokens.sidebarGradient)
        .navigationSplitViewColumnWidth(min: 200, ideal: 260, max: 350)
        .accessibilityIdentifier(Constants.Accessibility.projectsList)
    }

    // MARK: - Create Section (Projects)

    @ViewBuilder
    private var createSection: some View {
        HStack(spacing: Spacing.xs) {
            SidebarSectionHeader(title: "Create")

            Spacer(minLength: 0)

            Button {
                projectsViewModel.createProject()
            } label: {
                Image(systemName: "plus.circle.fill")
                    .font(.system(size: 16, weight: .medium))
                    .foregroundStyle(Color.accentGlow)
                    .symbolRenderingMode(.hierarchical)
            }
            .buttonStyle(.borderless)
            .padding(.trailing, Spacing.sm + 2)
            .padding(.top, Spacing.md)
            .padding(.bottom, Spacing.xs)
            .accessibilityIdentifier(Constants.Accessibility.newProjectButton)
        }
        .accessibilityIdentifier(Constants.Accessibility.sidebarProjectsSection)

        VStack(alignment: .leading, spacing: 2) {
            ForEach(projectsViewModel.projects) { project in
                ProjectRowView(
                    project: project,
                    isSelected: selectedDestination == .projectEditor(project)
                )
                .accessibilityIdentifier("\(Constants.Accessibility.projectRow)_\(project.id)")
                .contentShape(RoundedRectangle(cornerRadius: Radius.sm))
                .onTapGesture {
                    withAnimation(AnimationTokens.springTransition) {
                        selectedDestination = .projectEditor(project)
                        projectsViewModel.selectedProject = project
                    }
                }
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
        }
    }

    // MARK: - Studio Section (Render Queue + Worker Status)

    @ViewBuilder
    private var studioSection: some View {
        SidebarSectionHeader(title: "Studio")

        VStack(alignment: .leading, spacing: 2) {
            SidebarRowView(
                icon: "list.bullet.clipboard",
                label: "Render Queue",
                badge: renderQueueViewModel.activeJobCount,
                isSelected: selectedDestination == .renderQueue
            )
            .accessibilityIdentifier(Constants.Accessibility.sidebarRenderQueueSection)
            .contentShape(RoundedRectangle(cornerRadius: Radius.sm))
            .onTapGesture {
                withAnimation(AnimationTokens.springTransition) {
                    selectedDestination = .renderQueue
                }
            }

            SidebarRowView(
                icon: "gearshape.2",
                label: "Worker Status",
                isSelected: false
            )
            .opacity(0.5)
            .allowsHitTesting(false)
            .accessibilityLabel("Worker Status — Coming soon")
        }
    }

    // MARK: - Library Section (Outputs)

    @ViewBuilder
    private var librarySection: some View {
        SidebarSectionHeader(title: "Library")

        VStack(alignment: .leading, spacing: 2) {
            SidebarRowView(
                icon: "music.note.list",
                label: "Outputs",
                isSelected: selectedDestination == .outputsLibrary
            )
            .accessibilityIdentifier(Constants.Accessibility.sidebarOutputsSection)
            .contentShape(RoundedRectangle(cornerRadius: Radius.sm))
            .onTapGesture {
                withAnimation(AnimationTokens.springTransition) {
                    selectedDestination = .outputsLibrary
                }
            }
        }
    }

    // MARK: - Detail

    @ViewBuilder
    private var detailView: some View {
        ZStack {
            detailBackground
                .ignoresSafeArea()

            Group {
                if shouldShowHero {
                    heroWelcomeView
                } else {
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
                    .padding(Spacing.sm)
                    .id(project.id)

                    case .renderQueue:
                        RenderQueueView(viewModel: renderQueueViewModel)
                            .padding(Spacing.sm)

                    case .outputsLibrary:
                        OutputsLibraryView(viewModel: outputsLibraryViewModel)
                            .onAppear {
                                outputsLibraryViewModel.refreshFromJobs(renderQueueViewModel.jobs)
                            }
                            .padding(Spacing.sm)

                    case nil:
                        heroWelcomeView
                    }
                }
            }
            .transition(
                .asymmetric(
                    insertion: .opacity
                        .combined(with: .offset(y: 6))
                        .combined(with: .scale(scale: 0.995, anchor: .center)),
                    removal: .opacity.combined(with: .offset(y: -4))
                )
            )
            .animation(AnimationTokens.springTransition, value: selectedDestination)
        }
    }

    @ViewBuilder
    private var detailBackground: some View {
        Group {
            if shouldShowHero {
                GradientTokens.heroGradient
            } else {
                GradientTokens.backgroundGradient
            }
        }
        .transition(.opacity)
        .animation(AnimationTokens.springTransition, value: selectedDestination)
    }

    private var recentProjects: [Project] {
        Array(
            projectsViewModel.projects
                .sorted { $0.modifiedAt > $1.modifiedAt }
                .prefix(3)
        )
    }

    private var heroWelcomeView: some View {
        HeroWelcomeView(
            recentProjects: recentProjects,
            onNewSession: {
                projectsViewModel.createProject()
            },
            onSelectProject: { project in
                selectedDestination = .projectEditor(project)
                projectsViewModel.selectedProject = project
            }
        )
        .transition(.opacity.combined(with: .scale(scale: 0.98, anchor: .center)))
    }
}
