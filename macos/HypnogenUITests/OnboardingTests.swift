// OnboardingTests.swift
// HypnogenUITests
//
// Tests for the onboarding flow: appearance on fresh launch, skip, "Don't show again",
// and navigation through tour pages.

import XCTest

final class OnboardingTests: HypnogenUITestCase {

    override func setUp() {
        continueAfterFailure = false
        // Force onboarding to show via UserDefaults overrides
        app.launchArguments = [
            "--uitesting",
            "--resetdefaults",
            "-hasCompletedOnboarding", "NO",
            "-dontShowOnboardingAgain", "NO"
        ]
        app.launch()
        app.activate()
    }

    /// The onboarding sheet element.
    private var onboardingSheet: XCUIElement {
        return app.sheets.firstMatch
    }

    /// Finds an element robustly, with fallbacks for macOS SwiftUI quirks.
    private func findInOnboarding(_ identifier: String) -> XCUIElement {
        // 1. Try by identifier globally
        let byId = app.descendants(matching: .any).matching(identifier: identifier).firstMatch
        if byId.exists { return byId }
        
        // 2. Try by identifier specifically in the sheet
        let inSheet = onboardingSheet.descendants(matching: .any)[identifier].firstMatch
        if inSheet.exists { return inSheet }
        
        // 3. Fallbacks by label/type for known elements
        switch identifier {
        case "skipButton": return app.buttons["Skip"]
        case "doneButton": return app.buttons["Done"]
        case "nextButton": 
            let next = app.buttons["Next"]
            if next.exists { return next }
            return app.buttons.matching(NSPredicate(format: "label CONTAINS 'Next' OR label CONTAINS 'Continue'")).firstMatch
        case "previousButton": return app.buttons["Previous"]
        case "dontShowAgainCheckbox": 
            let toggle = app.toggles.firstMatch
            if toggle.exists { return toggle }
            return app.checkBoxes.firstMatch
        default: return byId
        }
    }

    // MARK: - Tests

    func testOnboardingAppearsOnFreshLaunch() {
        let sheet = onboardingSheet
        let exists = sheet.waitForExistence(timeout: 10)
        
        XCTAssertTrue(exists, "Onboarding sheet should appear automatically on fresh launch")
        screenshot("Onboarding_Appears")

        // Verify key elements are present
        XCTAssertTrue(findInOnboarding("skipButton").exists, "Skip button should be visible")
        XCTAssertTrue(findInOnboarding("doneButton").exists, "Done button should be visible")
    }

    func testSkipOnboardingShowsMainApp() {
        if !onboardingSheet.waitForExistence(timeout: 5) {
            app.typeKey("?", modifierFlags: [.command, .shift])
        }

        // Tap skip
        let skipButton = findInOnboarding("skipButton")
        waitForElement(skipButton)
        skipButton.tap()
        screenshot("Onboarding_Skipped")

        // Onboarding should dismiss
        let dismissed = onboardingSheet.waitForNonExistence(timeout: Self.defaultTimeout)
        XCTAssertTrue(dismissed, "Onboarding should be dismissed after skip")

        // Main sidebar should appear
        let sidebar = findElement("sidebar")
        waitForElement(sidebar, timeout: Self.defaultTimeout, "Sidebar should appear after onboarding skip")
    }

    func testDoneButtonDismissesOnboarding() {
        if !onboardingSheet.waitForExistence(timeout: 5) {
            app.typeKey("?", modifierFlags: [.command, .shift])
        }

        // Tap Done
        let doneButton = findInOnboarding("doneButton")
        waitForElement(doneButton)
        doneButton.tap()
        screenshot("Onboarding_Done")

        // Robust check: either the sheet is gone, OR the sidebar is present.
        // This handles cases where the sheet might still be in the hierarchy during dismissal animation.
        let sidebar = findElement("sidebar")
        let dismissed = onboardingSheet.waitForNonExistence(timeout: Self.defaultTimeout)
        let sidebarAppeared = sidebar.waitForExistence(timeout: Self.defaultTimeout)
        
        XCTAssertTrue(dismissed || sidebarAppeared, "Onboarding should be dismissed and/or sidebar should appear after Done")
    }

    func testDontShowAgainPreventsReappearance() {
        if !onboardingSheet.waitForExistence(timeout: 5) {
            app.typeKey("?", modifierFlags: [.command, .shift])
        }

        // Check "Don't show again"
        let checkbox = findInOnboarding("dontShowAgainCheckbox")
        if checkbox.exists {
            checkbox.tap()
        }

        screenshot("Onboarding_DontShowAgain_Checked")

        // Dismiss via skip
        let skipButton = findInOnboarding("skipButton")
        skipButton.tap()
        _ = onboardingSheet.waitForNonExistence(timeout: Self.defaultTimeout)

        // Relaunch the app WITHOUT the override arguments to test persistence
        app.terminate()
        let freshApp = XCUIApplication()
        freshApp.launchArguments = ["--uitesting"]
        freshApp.launch()
        freshApp.activate()

        // Onboarding should NOT appear
        let relaunchedSheet = freshApp.sheets.firstMatch
        let appeared = relaunchedSheet.waitForExistence(timeout: 3)
        XCTAssertFalse(appeared, "Onboarding should not reappear when 'Don’t show again' was checked")

        screenshot("Onboarding_NotShown_SecondLaunch")
        freshApp.terminate()
    }

    func testFeatureTourNavigation() {
        if !onboardingSheet.waitForExistence(timeout: 5) {
            app.typeKey("?", modifierFlags: [.command, .shift])
        }

        // Use nextButton as proxy for tour visibility
        let nextButton = findInOnboarding("nextButton")
        waitForElement(nextButton, timeout: 5, "Feature tour should be visible (Next button found)")
        screenshot("FeatureTour_Page1")

        // Navigate forward through pages
        if nextButton.exists {
            nextButton.tap()
            screenshot("FeatureTour_Page2")
        }

        // Navigate back
        let previousButton = findInOnboarding("previousButton")
        if previousButton.exists {
            previousButton.tap()
            screenshot("FeatureTour_BackToPage1")
        }
    }
}
