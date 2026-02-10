// OnboardingViewModel.swift
// Hypnogen
//
// State management for the onboarding flow: tracks current tab, tour page, and persistence.

import SwiftUI
import Observation

/// Sections available in the onboarding sheet.
enum OnboardingTab: Int, CaseIterable, Identifiable {
    case featureTour = 0
    case tipsGlossary = 1
    case troubleshooting = 2

    var id: Int { rawValue }

    var title: String {
        switch self {
        case .featureTour: "Feature Tour"
        case .tipsGlossary: "Tips & Glossary"
        case .troubleshooting: "Troubleshooting"
        }
    }

    var sfSymbol: String {
        switch self {
        case .featureTour: "sparkles"
        case .tipsGlossary: "lightbulb"
        case .troubleshooting: "wrench.and.screwdriver"
        }
    }
}

@Observable
final class OnboardingViewModel {
    // MARK: - Navigation State

    var selectedTab: OnboardingTab = .featureTour
    var currentTourPage: Int = 0
    var isPresented: Bool = false

    // MARK: - Persistence Keys

    private static let hasCompletedKey = "hasCompletedOnboarding"
    private static let dontShowAgainKey = "dontShowOnboardingAgain"

    // MARK: - Computed Properties

    var isOnFirstTourPage: Bool {
        currentTourPage == 0
    }

    var isOnLastTourPage: Bool {
        currentTourPage == FeatureTourContent.pages.count - 1
    }

    var tourPageCount: Int {
        FeatureTourContent.pages.count
    }

    var hasCompletedOnboarding: Bool {
        get { UserDefaults.standard.bool(forKey: Self.hasCompletedKey) }
        set { UserDefaults.standard.set(newValue, forKey: Self.hasCompletedKey) }
    }

    var dontShowOnboardingAgain: Bool {
        get { UserDefaults.standard.bool(forKey: Self.dontShowAgainKey) }
        set { UserDefaults.standard.set(newValue, forKey: Self.dontShowAgainKey) }
    }

    /// Whether onboarding should appear automatically on launch.
    var shouldShowOnLaunch: Bool {
        !hasCompletedOnboarding && !dontShowOnboardingAgain
    }

    // MARK: - Actions

    /// Show onboarding (used by Help menu re-entry).
    func showOnboarding() {
        currentTourPage = 0
        selectedTab = .featureTour
        isPresented = true
    }

    /// Advance to the next tour page, or move to Tips & Glossary if on the last page.
    func nextTourPage() {
        if isOnLastTourPage {
            selectedTab = .tipsGlossary
        } else {
            currentTourPage += 1
        }
    }

    /// Go back to the previous tour page.
    func previousTourPage() {
        if currentTourPage > 0 {
            currentTourPage -= 1
        }
    }

    /// Complete onboarding and dismiss the sheet.
    func finishOnboarding() {
        hasCompletedOnboarding = true
        isPresented = false
    }

    /// Skip onboarding immediately.
    func skipOnboarding() {
        hasCompletedOnboarding = true
        isPresented = false
    }
}
