// HypnogenUITests.swift
// HypnogenUITests
//
// Base class for all Hypnogen UI tests. Provides common setup (app launch with
// --uitesting and --resetdefaults flags) and shared helpers.

import XCTest

/// Base class that all Hypnogen UI test classes inherit from.
/// Handles app launch configuration and state reset between tests.
class HypnogenUITestCase: XCTestCase {
    let app = XCUIApplication()

    /// Standard element existence timeout used across all UI tests.
    static let defaultTimeout: TimeInterval = 5

    override func setUp() {
        super.setUp()
        continueAfterFailure = false
        app.launchArguments = ["--uitesting", "--resetdefaults"]
        app.launch()
    }

    override func tearDown() {
        app.terminate()
        super.tearDown()
    }

    // MARK: - Convenience Helpers

    /// Robustly finds an element by its accessibility identifier, regardless of its type.
    func findElement(_ identifier: String) -> XCUIElement {
        return app.descendants(matching: .any)[identifier].firstMatch
    }

    /// Waits for an element to exist, failing with a descriptive message if it doesn't.
    func waitForElement(
        _ element: XCUIElement,
        timeout: TimeInterval = HypnogenUITestCase.defaultTimeout,
        _ message: String? = nil
    ) {
        let exists = element.waitForExistence(timeout: timeout)
        XCTAssertTrue(exists, message ?? "Expected element \(element.identifier) to exist within \(timeout)s")
    }

    /// Dismisses onboarding by tapping Skip, if the onboarding sheet is visible.
    func dismissOnboardingIfPresent() {
        let onboarding = findElement("onboardingView")
        if onboarding.waitForExistence(timeout: 3) {
            let skipButton = findElement("skipButton")
            if skipButton.exists {
                skipButton.tap()
            }
        }
        // Wait for the main sidebar to be ready
        let sidebar = findElement("sidebar")
        _ = sidebar.waitForExistence(timeout: Self.defaultTimeout)
    }

    /// Takes a screenshot with the given name and attaches it to this test case.
    func screenshot(_ name: String) {
        ScreenshotHelper.capture(name, in: self)
    }
}
