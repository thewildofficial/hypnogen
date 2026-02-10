// ScreenshotHelper.swift
// HypnogenUITests
//
// Reusable screenshot capture and attachment utilities for XCUITests.

import XCTest

/// Provides reusable screenshot helpers for UI tests.
enum ScreenshotHelper {
    /// Captures a screenshot and attaches it to the given test activity with `.keepAlways` lifetime.
    /// - Parameters:
    ///   - name: Descriptive name for the screenshot attachment (e.g. "Onboarding_Appears").
    ///   - testCase: The `XCTestCase` instance to attach the screenshot to.
    static func capture(_ name: String, in testCase: XCTestCase) {
        let screenshot = XCUIScreen.main.screenshot()
        let attachment = XCTAttachment(screenshot: screenshot)
        attachment.name = name
        attachment.lifetime = .keepAlways
        testCase.add(attachment)
    }

    /// Captures a screenshot of a specific element and attaches it.
    /// - Parameters:
    ///   - element: The `XCUIElement` to screenshot.
    ///   - name: Descriptive name for the attachment.
    ///   - testCase: The `XCTestCase` instance to attach the screenshot to.
    static func capture(element: XCUIElement, name: String, in testCase: XCTestCase) {
        let screenshot = element.screenshot()
        let attachment = XCTAttachment(screenshot: screenshot)
        attachment.name = name
        attachment.lifetime = .keepAlways
        testCase.add(attachment)
    }
}
