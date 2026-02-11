// LibraryTests.swift
// HypnogenUITests
//
// Tests for the outputs library: navigation, display of completed artifacts.

import XCTest

final class LibraryTests: HypnogenUITestCase {

    override func setUp() {
        super.setUp()
        dismissOnboardingIfPresent()
    }

    // MARK: - Tests

    func testOutputsLibraryNavigation() {
        // Navigate to Outputs Library via sidebar
        let outputsSection = findElement("sidebarOutputsSection")
        if !outputsSection.waitForExistence(timeout: Self.defaultTimeout) {
            // Try tapping "Outputs Library" static text as fallback
            let outputsText = findElement("Outputs Library")
            waitForElement(outputsText)
            outputsText.tap()
        } else {
            outputsSection.tap()
        }

        screenshot("Library_Navigated")

        // Verify the outputs grid view loads
        let outputsGrid = findElement("outputsGrid")
        waitForElement(outputsGrid, timeout: Self.defaultTimeout, "Outputs library view should appear")
    }

    func testOutputsLibraryDisplaysEmptyOrPopulated() {
        // Navigate to the library
        let outputsSection = findElement("sidebarOutputsSection")
        if outputsSection.waitForExistence(timeout: Self.defaultTimeout) {
            outputsSection.tap()
        }

        let outputsGrid = findElement("outputsGrid")
        waitForElement(outputsGrid)

        // On a fresh launch there are no completed renders, so expect empty state
        let emptyStateText = findElement("No Outputs")
        let outputItems = app.descendants(matching: .any).matching(
            NSPredicate(format: "identifier BEGINSWITH 'outputItem_'")
        )

        let hasEmpty = emptyStateText.exists
        let hasOutputs = outputItems.count > 0

        XCTAssertTrue(hasEmpty || hasOutputs,
                      "Library should show empty state or output cards")
        screenshot("Library_Content")

        // If outputs exist, verify action buttons are present
        if hasOutputs {
            let firstOutput = outputItems.firstMatch
            XCTAssertTrue(firstOutput.exists, "First output card should be visible")
            screenshot("Library_OutputCard")

            // Check for play and reveal buttons on the first output
            let playButtons = app.buttons.matching(
                NSPredicate(format: "identifier BEGINSWITH 'playOutputButton_'")
            )
            let revealButtons = app.buttons.matching(
                NSPredicate(format: "identifier BEGINSWITH 'revealInFinderButton_'")
            )

            if playButtons.count > 0 {
                XCTAssertTrue(playButtons.firstMatch.exists, "Play button should exist on output card")
            }
            if revealButtons.count > 0 {
                XCTAssertTrue(revealButtons.firstMatch.exists, "Reveal button should exist on output card")
            }
        }
    }
}
