// OnboardingView.swift
// Hypnogen
//
// Main onboarding container: tab-based layout with Skip / Done controls and persistence toggle.

import SwiftUI

struct OnboardingView: View {
    @Bindable var viewModel: OnboardingViewModel

    var body: some View {
        ZStack {
            LinearGradient.canvasGradient
                .ignoresSafeArea()

            VStack(spacing: 0) {
                tabPicker
                    .padding(.top, Spacing.md)
                    .padding(.horizontal, Spacing.lg)

                Rectangle()
                    .fill(Color.stroke.opacity(0.4))
                    .frame(height: 1)
                    .padding(.top, Spacing.sm)

                tabContent
                    .frame(maxWidth: .infinity, maxHeight: .infinity)

                Rectangle()
                    .fill(Color.stroke.opacity(0.4))
                    .frame(height: 1)

                bottomBar
                    .padding(.horizontal, Spacing.lg)
                    .padding(.vertical, Spacing.md)
            }
        }
        .frame(width: 600, height: 520)
        .accessibilityIdentifier(Constants.Accessibility.Onboarding.onboardingView)
    }

    // MARK: - Tab Picker

    private var tabPicker: some View {
        HStack(spacing: Spacing.xs) {
            ForEach(OnboardingTab.allCases) { tab in
                tabButton(for: tab)
            }
        }
    }

    private func tabButton(for tab: OnboardingTab) -> some View {
        let isSelected = viewModel.selectedTab == tab

        return Button {
            withAnimation(.easeInOut(duration: 0.25)) {
                viewModel.selectedTab = tab
            }
        } label: {
            HStack(spacing: Spacing.sm) {
                Image(systemName: tab.sfSymbol)
                    .font(.system(size: 13, weight: .medium))
                    .foregroundStyle(isSelected ? Color.canvas : Color.accentSecondary)
                Text(tab.title)
                    .font(.system(size: 13, weight: .semibold))
                    .foregroundStyle(isSelected ? Color.canvas : Color.textPrimary)
            }
            .padding(.horizontal, Spacing.md)
            .padding(.vertical, Spacing.sm)
            .background(
                Group {
                    if isSelected {
                        LinearGradient.accentGradient
                    } else {
                        Color.surface.opacity(0.6)
                    }
                }
            )
            .cornerRadius(Radius.sm)
            .overlay(
                RoundedRectangle(cornerRadius: Radius.sm)
                    .stroke(isSelected ? Color.clear : Color.stroke.opacity(0.5), lineWidth: 1)
            )
        }
        .buttonStyle(.plain)
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
            .font(.system(size: 13))
            .foregroundStyle(Color.textSecondary)
            .accessibilityIdentifier(Constants.Accessibility.Onboarding.dontShowAgainCheckbox)

            Spacer()

            Button("Skip") {
                viewModel.skipOnboarding()
            }
            .buttonStyle(SecondaryButtonStyle())
            .keyboardShortcut(.cancelAction)
            .accessibilityIdentifier(Constants.Accessibility.Onboarding.skipButton)

            Button("Done") {
                viewModel.finishOnboarding()
            }
            .buttonStyle(PrimaryButtonStyle())
            .keyboardShortcut(.defaultAction)
            .accessibilityIdentifier(Constants.Accessibility.Onboarding.doneButton)
        }
    }
}
