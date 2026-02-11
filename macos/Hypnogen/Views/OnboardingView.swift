// OnboardingView.swift
// Hypnogen
//
// Main onboarding container: tab-based layout with Skip / Done controls and persistence toggle.

import SwiftUI

struct OnboardingView: View {
    @Bindable var viewModel: OnboardingViewModel

    var body: some View {
        VStack(spacing: 0) {
            tabPicker
                .padding(.top, 12)
                .padding(.horizontal, 24)

            Divider()
                .padding(.top, 8)

            tabContent
                .frame(maxWidth: .infinity, maxHeight: .infinity)

            Divider()

            bottomBar
                .padding(.horizontal, 24)
                .padding(.vertical, 12)
        }
        .background(Color.canvas)
        .frame(width: 600, height: 520)
        .accessibilityIdentifier(Constants.Accessibility.Onboarding.onboardingView)
    }

    // MARK: - Tab Picker

    private var tabPicker: some View {
        Picker("Section", selection: $viewModel.selectedTab) {
            ForEach(OnboardingTab.allCases) { tab in
                Label(tab.title, systemImage: tab.sfSymbol)
                    .tag(tab)
            }
        }
        .pickerStyle(.segmented)
        .labelsHidden()
    }

    // MARK: - Tab Content

    @ViewBuilder
    private var tabContent: some View {
        switch viewModel.selectedTab {
        case .featureTour:
            FeatureTourView(viewModel: viewModel)
        case .tipsGlossary:
            TipsGlossaryView()
        case .troubleshooting:
            TroubleshootingView()
        }
    }

    // MARK: - Bottom Bar

    private var bottomBar: some View {
        HStack {
            Toggle("Don\u{2019}t show this again", isOn: Binding(
                get: { viewModel.dontShowOnboardingAgain },
                set: { viewModel.dontShowOnboardingAgain = $0 }
            ))
            .toggleStyle(.checkbox)
            .accessibilityIdentifier(Constants.Accessibility.Onboarding.dontShowAgainCheckbox)

            Spacer()

            Button("Skip") {
                viewModel.skipOnboarding()
            }
            .keyboardShortcut(.cancelAction)
            .accessibilityIdentifier(Constants.Accessibility.Onboarding.skipButton)

            Button("Done") {
                viewModel.finishOnboarding()
            }
            .buttonStyle(.borderedProminent)
            .keyboardShortcut(.defaultAction)
            .accessibilityIdentifier(Constants.Accessibility.Onboarding.doneButton)
        }
    }
}
