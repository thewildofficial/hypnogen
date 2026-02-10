// OnboardingTests.swift
// HypnogenUITests
//
// Tests for the onboarding flow: appearance on fresh launch, skip, "Don't show again",
// and navigation through tour pages.

import XCTest

final class OnboardingTests: HypnogenUITestCase {

    // MARK: - Tests

    func testOnboardingAppearsOnFreshLaunch() {
        let onboarding = app.otherElements["onboardingView"]
        waitForElement(onboarding)
        screenshot("Onboarding_Appears")

        // Verify key elements are present
        XCTAssertTrue(app.buttons["skipButton"].exists, "Skip button should be visible")
        XCTAssertTrue(app.buttons["doneButton"].exists, "Done button should be visible")
        XCTAssertTrue(app.checkBoxes["dontShowAgainCheckbox"].exists
                      || app.toggles["dontShowAgainCheckbox"].exists,
                      "Don\u{2019}t show again checkbox should be visible")
    }

    func testSkipOnboardingShowsMainApp() {
        let onboarding = app.otherElements["onboardingView"]
        waitForElement(onboarding)

        // Tap skip
        app.buttons["skipButton"].tap()
        screenshot("Onboarding_Skipped")

        // Onboarding should dismiss
        let dismissed = onboarding.waitForNonExistence(timeout: Self.defaultTimeout)
        XCTAssertTrue(dismissed, "Onboarding should be dismissed after skip")

        // Main sidebar should appear
        let sidebar = app.otherElements["sidebar"]
        waitForElement(sidebar, Self.defaultTimeout, "Sidebar should appear after onboarding skip")
    }

    func testDoneButtonDismissesOnboarding() {
        let onboarding = app.otherElements["onboardingView"]
        waitForElement(onboarding)

        // Tap Done
        app.buttons["doneButton"].tap()
        screenshot("Onboarding_Done")

        let dismissed = onboarding.waitForNonExistence(timeout: Self.defaultTimeout)
        XCTAssertTrue(dismissed, "Onboarding should be dismissed after Done")

        let sidebar = app.otherElements["sidebar"]
        waitForElement(sidebar, Self.defaultTimeout, "Sidebar should appear after onboarding Done")
    }

    func testDontShowAgainPreventsReappearance() {
        let onboarding = app.otherElements["onboardingView"]
        waitForElement(onboarding)

        // Check "Don't show again"
        let checkbox = app.checkBoxes["dontShowAgainCheckbox"]
        let toggle = app.toggles["dontShowAgainCheckbox"]
        if checkbox.exists {
            checkbox.tap()
        } else if toggle.exists {
            toggle.tap()
        }

        screenshot("Onboarding_DontShowAgain_Checked")

        // Dismiss
        app.buttons["skipButton"].tap()
        let dismissed = onboarding.waitForNonExistence(timeout: Self.defaultTimeout)
        XCTAssertTrue(dismissed, "Onboarding should dismiss after skip")

        // Relaunch the app (without --resetdefaults to preserve UserDefaults)
        app.terminate()
        let freshApp = XCUIApplication()
        freshApp.launchArguments = ["--uitesting"]
        freshApp.launch()

        // Onboarding should NOT appear
        let relaunchedOnboarding = freshApp.otherElements["onboardingView"]
        let appeared = relaunchedOnboarding.waitForExistence(timeout: 3)
        XCTAssertFalse(appeared, "Onboarding should not reappear when 'Don\u{2019}t show again' was checked")

        screenshot("Onboarding_NotShown_SecondLaunch")
        freshApp.terminate()
    }

    func testFeatureTourNavigation() {
        let onboarding = app.otherElements["onboardingView"]
        waitForElement(onboarding)

        // Feature tour should be visible initially
        let tourContainer = app.otherElements["featureTourContainer"]
        waitForElement(tourContainer)
        screenshot("FeatureTour_Page1")

        // Navigate forward through pages
        let nextButton = app.buttons["nextButton"]
        if nextButton.exists {
            nextButton.tap()
            screenshot("FeatureTour_Page2")
        }

        // Navigate back
        let previousButton = app.buttons["previousButton"]
        if previousButton.exists {
            previousButton.tap()
            screenshot("FeatureTour_BackToPage1")
        }
    }
}
