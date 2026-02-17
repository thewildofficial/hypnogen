// FeatureTourView.swift
// Hypnogen
//
// Paginated feature tour with navigation controls and page indicators.

import SwiftUI

struct FeatureTourView: View {
    @Bindable var viewModel: OnboardingViewModel

    var body: some View {
        VStack(spacing: 0) {
            tourPageContent
            Spacer(minLength: Spacing.md)
            pageIndicator
                .padding(.bottom, Spacing.sm)
            navigationButtons
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
        .accessibilityIdentifier(Constants.Accessibility.Onboarding.featureTourContainer)
    }

    // MARK: - Tour Page

    @ViewBuilder
    private var tourPageContent: some View {
        let page = FeatureTourContent.pages[viewModel.currentTourPage]

        VStack(spacing: Spacing.md) {
            ZStack {
                Circle()
                    .fill(Color.accentPrimary.opacity(0.12))
                    .frame(width: 96, height: 96)

                Circle()
                    .fill(Color.accentPrimary.opacity(0.06))
                    .frame(width: 120, height: 120)

                Image(systemName: page.sfSymbol)
                    .font(.system(size: 44, weight: .medium))
                    .foregroundStyle(LinearGradient.accentGradient)
                    .symbolRenderingMode(.hierarchical)
            }
            .shadow(color: Color.accentPrimary.opacity(0.3), radius: 16, x: 0, y: 4)
            .accessibilityHidden(true)

            Text(page.title)
                .font(.system(size: 22, weight: .bold))
                .foregroundStyle(Color.textPrimary)
                .multilineTextAlignment(.center)

            Text(page.subtitle)
                .font(.system(size: 15, weight: .medium))
                .foregroundStyle(Color.accentSecondary)
                .multilineTextAlignment(.center)

            VStack {
                Text(page.body)
                    .font(.system(size: 13))
                    .foregroundStyle(Color.textSecondary)
                    .multilineTextAlignment(.center)
                    .lineSpacing(5)
            }
            .frame(maxWidth: 420)
            .padding(Spacing.md)
            .background(Color.surface.opacity(0.5))
            .cornerRadius(Radius.md)
            .overlay(
                RoundedRectangle(cornerRadius: Radius.md)
                    .stroke(Color.stroke.opacity(0.3), lineWidth: 1)
            )
        }
        .padding(.horizontal, Spacing.xl)
        .padding(.top, Spacing.lg)
        .accessibilityIdentifier(
            "\(Constants.Accessibility.Onboarding.featureTourPage)_\(viewModel.currentTourPage)"
        )
        .animation(.easeInOut(duration: 0.25), value: viewModel.currentTourPage)
    }

    // MARK: - Page Indicator

    private var pageIndicator: some View {
        HStack(spacing: Spacing.sm) {
            ForEach(0..<viewModel.tourPageCount, id: \.self) { index in
                let isActive = index == viewModel.currentTourPage
                Capsule()
                    .fill(isActive ? Color.accentPrimary : Color.stroke)
                    .frame(width: isActive ? 20 : 8, height: 8)
                    .animation(.easeInOut(duration: 0.25), value: viewModel.currentTourPage)
            }
        }
        .accessibilityElement(children: .ignore)
        .accessibilityLabel("Page \(viewModel.currentTourPage + 1) of \(viewModel.tourPageCount)")
    }

    // MARK: - Navigation Buttons

    private var navigationButtons: some View {
        HStack {
            Button("Previous") {
                viewModel.previousTourPage()
            }
            .buttonStyle(SecondaryButtonStyle())
            .disabled(viewModel.isOnFirstTourPage)
            .accessibilityIdentifier(Constants.Accessibility.Onboarding.previousButton)

            Spacer()

            Button(viewModel.isOnLastTourPage ? "Continue to Tips" : "Next") {
                viewModel.nextTourPage()
            }
            .buttonStyle(PrimaryButtonStyle())
            .accessibilityIdentifier(Constants.Accessibility.Onboarding.nextButton)
        }
        .padding(.horizontal, Spacing.xl)
        .padding(.bottom, Spacing.sm)
    }
}
