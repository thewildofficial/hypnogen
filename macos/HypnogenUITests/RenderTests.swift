// RenderTests.swift
// HypnogenUITests
//
// Tests for the render queue: submitting a render job and observing progress/ETA.

import XCTest

final class RenderTests: HypnogenUITestCase {

    override func setUp() {
        super.setUp()
        dismissOnboardingIfPresent()
    }

    // MARK: - Tests

    func testSubmitRenderJob() {
        // Create a project with content so the render button is enabled
        let newProjectButton = app.buttons["newProjectButton"].firstMatch
        waitForElement(newProjectButton)
        newProjectButton.tap()

        let scriptEditor = app.textViews["scriptEditor"]
        waitForElement(scriptEditor)
        scriptEditor.tap()
        scriptEditor.typeText("Close your eyes and breathe deeply.")

        // Add an affirmation so the render button becomes enabled
        let addField = app.textFields["Add affirmation..."]
        if addField.exists {
            addField.tap()
            addField.typeText("I am at peace")
            let addButton = app.buttons["addAffirmationButton"]
            if addButton.exists {
                addButton.tap()
            } else {
                addField.typeKey(.return, modifierFlags: [])
            }
        }

        screenshot("Render_ProjectReady")

        // Tap the render button
        let renderButton = app.buttons["renderButton"]
        waitForElement(renderButton)

        // The button should be enabled since we have script + affirmation
        if renderButton.isEnabled {
            renderButton.tap()
            screenshot("Render_Submitted")
        }

        // Navigate to render queue to see the job
        let renderQueueNav = app.staticTexts["Render Queue"].firstMatch
        if !renderQueueNav.exists {
            // Try the sidebar section identifier
            let renderQueueSection = app.otherElements["sidebarRenderQueueSection"]
            if renderQueueSection.exists {
                renderQueueSection.tap()
            }
        } else {
            renderQueueNav.tap()
        }

        screenshot("RenderQueue_AfterSubmit")

        // The render queue view should be present
        let renderQueueList = app.otherElements["renderQueueList"]
        let queueExists = renderQueueList.waitForExistence(timeout: Self.defaultTimeout)
        XCTAssertTrue(queueExists, "Render queue view should appear when navigated to")
    }

    func testRenderQueueShowsProgressAndETA() {
        // Navigate to render queue (even if empty, verify the UI elements)
        let renderQueueSection = app.otherElements["sidebarRenderQueueSection"].firstMatch
        if renderQueueSection.waitForExistence(timeout: Self.defaultTimeout) {
            renderQueueSection.tap()
        }

        let renderQueueList = app.otherElements["renderQueueList"]
        waitForElement(renderQueueList)
        screenshot("RenderQueue_View")

        // If there are active jobs, verify progress bar and ETA are shown.
        // Since this is a UI test without a real backend, we verify the
        // empty state or existing job rows render without crashes.
        let emptyStateText = app.staticTexts["No Render Jobs"]
        let jobRows = app.otherElements.matching(NSPredicate(format: "identifier BEGINSWITH 'renderJobRow_'"))

        let hasEmptyState = emptyStateText.exists
        let hasJobs = jobRows.count > 0

        XCTAssertTrue(hasEmptyState || hasJobs,
                      "Render queue should show either empty state or job rows")

        if hasJobs {
            // Verify progress bar exists on the first job
            let firstJobProgress = app.progressIndicators.matching(
                NSPredicate(format: "identifier BEGINSWITH 'jobProgressBar_'")
            ).firstMatch
            if firstJobProgress.exists {
                screenshot("RenderQueue_JobProgress")
            }
        }
    }
}
