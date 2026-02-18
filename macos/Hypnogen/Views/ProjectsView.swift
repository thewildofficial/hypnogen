// ProjectsView.swift
// Hypnogen
//
// Standalone projects list view (used in toolbar/popover contexts).
// The primary projects list is integrated into the sidebar of ContentView.

import SwiftUI

struct ProjectsView: View {
    @Bindable var viewModel: ProjectsViewModel

    @State private var isHoveringAdd = false
    @Environment(\.accessibilityReduceMotion) private var reduceMotion

    var body: some View {
        VStack(spacing: 0) {
            toolbar
            Divider()
                .overlay(Color.accentViolet.opacity(0.15))

            if viewModel.projects.isEmpty {
                emptyState
            } else {
                projectList
            }
        }
        .background(backgroundLayer)
        .frame(minWidth: 300, minHeight: 200)
    }

    // MARK: - Toolbar

    private var toolbar: some View {
        HStack(spacing: Spacing.sm) {
            Image(systemName: "folder.fill")
                .font(.system(size: 14, weight: .medium))
                .foregroundStyle(Color.accentViolet)
                .symbolRenderingMode(.hierarchical)

            Text("Projects")
                .font(Typography.bodyBold)
                .foregroundStyle(Color.textPrimary)

            Spacer()

            Button {
                viewModel.createProject()
            } label: {
                HStack(spacing: Spacing.xs) {
                    Image(systemName: "plus")
                        .font(.system(size: 11, weight: .semibold))
                    Text("New")
                        .font(Typography.label)
                }
                .foregroundStyle(isHoveringAdd ? Color.textPrimary : Color.textAccent)
                .padding(.horizontal, Spacing.sm + 2)
                .padding(.vertical, Spacing.xs + 1)
                .background(
                    RoundedRectangle(cornerRadius: Radius.sm, style: .continuous)
                        .fill(Color.accentViolet.opacity(isHoveringAdd ? 0.25 : 0.12))
                )
                .overlay(
                    RoundedRectangle(cornerRadius: Radius.sm, style: .continuous)
                        .strokeBorder(
                            Color.accentViolet.opacity(isHoveringAdd ? 0.5 : 0.2),
                            lineWidth: 0.5
                        )
                )
            }
            .buttonStyle(.plain)
            .onHover { hovering in isHoveringAdd = hovering }
            .animation(
                MotionSensitiveAnimation.resolve(AnimationTokens.easeInOut, reduceMotion: reduceMotion),
                value: isHoveringAdd
            )
            .accessibilityIdentifier(Constants.Accessibility.newProjectButton)
        }
        .padding(.horizontal, Spacing.md)
        .padding(.vertical, Spacing.sm + 2)
    }

    // MARK: - List

    private var projectList: some View {
        List(selection: $viewModel.selectedProject) {
            ForEach(viewModel.projects) { project in
                ProjectRowView(project: project)
                    .tag(project)
                    .listRowBackground(Color.clear)
                    .listRowSeparator(.hidden)
                    .listRowInsets(EdgeInsets(
                        top: 2,
                        leading: Spacing.sm,
                        bottom: 2,
                        trailing: Spacing.sm
                    ))
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
        .accessibilityIdentifier(Constants.Accessibility.projectsList)
    }

    // MARK: - Empty State

    private var emptyState: some View {
        EmptyStateView(
            icon: "doc.badge.plus",
            title: "No Projects",
            description: "Create your first hypnosis project",
            ctaTitle: "New Project",
            ctaAction: { viewModel.createProject() }
        )
    }

    // MARK: - Background

    private var backgroundLayer: some View {
        ZStack {
            Color.backgroundDeep

            RadialGradient(
                colors: [
                    Color.accentIndigo.opacity(0.04),
                    Color.clear,
                ],
                center: .top,
                startRadius: 0,
                endRadius: 400
            )
        }
    }
}
