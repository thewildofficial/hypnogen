// ViewSnapshotTests.swift
// HypnogenSnapshotTests
//
// Snapshot tests for key redesigned views: OnboardingView, CalibrationView,
// EmptyStateView, HeroWelcomeView, ProjectEditorView, and component views.

import XCTest
import SnapshotTesting
import SwiftUI
@testable import Hypnogen

// MARK: - Onboarding View Snapshots

final class OnboardingSnapshotTests: SnapshotTestCase {

    func testOnboardingView_featureTour() {
        let viewModel = OnboardingViewModel()
        viewModel.selectedTab = .featureTour
        viewModel.currentTourPage = 0

        let view = OnboardingView(viewModel: viewModel)
            .frame(width: 620, height: 540)

        assertBothModesSnapshot(of: view, size: CGSize(width: 620, height: 540))
    }

    func testOnboardingView_tipsGlossary() {
        let viewModel = OnboardingViewModel()
        viewModel.selectedTab = .tipsGlossary

        let view = OnboardingView(viewModel: viewModel)
            .frame(width: 620, height: 540)

        assertBothModesSnapshot(of: view, size: CGSize(width: 620, height: 540))
    }

    func testOnboardingView_troubleshooting() {
        let viewModel = OnboardingViewModel()
        viewModel.selectedTab = .troubleshooting

        let view = OnboardingView(viewModel: viewModel)
            .frame(width: 620, height: 540)

        assertBothModesSnapshot(of: view, size: CGSize(width: 620, height: 540))
    }
}

// MARK: - Calibration View Snapshots

final class CalibrationSnapshotTests: SnapshotTestCase {

    func testCalibrationView_welcome() {
        let viewModel = CalibrationViewModel()

        let view = CalibrationView(viewModel: viewModel)
            .frame(width: 520, height: 420)

        assertBothModesSnapshot(of: view, size: CGSize(width: 520, height: 420))
    }

    func testCalibrationView_testing() {
        let viewModel = CalibrationViewModel()
        viewModel.beginTesting()

        let view = CalibrationView(viewModel: viewModel)
            .frame(width: 520, height: 420)

        assertBothModesSnapshot(of: view, size: CGSize(width: 520, height: 420))
    }

    func testCalibrationView_complete() {
        let viewModel = CalibrationViewModel()
        viewModel.skipCalibration()

        let view = CalibrationView(viewModel: viewModel)
            .frame(width: 520, height: 420)

        assertBothModesSnapshot(of: view, size: CGSize(width: 520, height: 420))
    }
}

// MARK: - Empty State View Snapshots

final class EmptyStateSnapshotTests: SnapshotTestCase {

    func testEmptyState_renderQueue() {
        let view = EmptyStateView(
            icon: "list.bullet.clipboard",
            title: "No Render Jobs",
            description: "Open a project and click Render to start"
        )

        assertBothModesSnapshot(of: view, size: CGSize(width: 600, height: 400))
    }

    func testEmptyState_outputsLibrary() {
        let view = EmptyStateView(
            icon: "music.note.list",
            title: "No Outputs",
            description: "Completed renders will appear here"
        )

        assertBothModesSnapshot(of: view, size: CGSize(width: 600, height: 400))
    }

    func testEmptyState_withCTA() {
        let view = EmptyStateView(
            icon: "waveform.path.ecg",
            title: "No Sessions",
            description: "Create your first hypnosis session",
            ctaTitle: "New Session",
            ctaAction: {}
        )

        assertBothModesSnapshot(of: view, size: CGSize(width: 600, height: 400))
    }
}

// MARK: - Hero Welcome View Snapshots

final class HeroWelcomeSnapshotTests: SnapshotTestCase {

    func testHeroWelcome_empty() {
        let view = HeroWelcomeView(
            recentProjects: [],
            onNewSession: {},
            onSelectProject: { _ in }
        )

        assertDarkModeSnapshot(of: view, size: CGSize(width: 800, height: 600))
    }

    func testHeroWelcome_withRecentProjects() {
        let projects = [
            Project(name: "Deep Sleep Relaxation"),
            Project(name: "Confidence Booster"),
            Project(name: "Morning Motivation"),
        ]

        let view = HeroWelcomeView(
            recentProjects: projects,
            onNewSession: {},
            onSelectProject: { _ in }
        )

        assertDarkModeSnapshot(of: view, size: CGSize(width: 800, height: 600))
    }
}

// MARK: - Project Editor View Snapshots

final class ProjectEditorSnapshotTests: SnapshotTestCase {

    func testProjectEditor_emptyProject() {
        let project = Project(
            name: "Untitled Project",
            scriptText: "",
            affirmations: [""]
        )

        let view = ProjectEditorView(
            project: project,
            onSave: {},
            onRender: {}
        )

        assertDarkModeSnapshot(of: view)
    }

    func testProjectEditor_withContent() {
        let project = Project(
            name: "Deep Relaxation Session",
            scriptText: "Close your eyes and begin to relax...\n\nAs you settle into comfort, notice the gentle rhythm of your breathing...",
            affirmations: [
                "I am calm and centered",
                "My mind is at peace",
                "I release all tension",
            ]
        )

        let view = ProjectEditorView(
            project: project,
            onSave: {},
            onRender: {}
        )

        assertDarkModeSnapshot(of: view)
    }
}

// MARK: - Render Queue View Snapshots

final class RenderQueueSnapshotTests: SnapshotTestCase {

    func testRenderQueue_empty() {
        let viewModel = RenderQueueViewModel()

        let view = RenderQueueView(viewModel: viewModel)

        assertDarkModeSnapshot(of: view)
    }
}

// MARK: - Outputs Library View Snapshots

final class OutputsLibrarySnapshotTests: SnapshotTestCase {

    func testOutputsLibrary_empty() {
        let viewModel = OutputsLibraryViewModel()

        let view = OutputsLibraryView(viewModel: viewModel)

        assertDarkModeSnapshot(of: view)
    }
}
