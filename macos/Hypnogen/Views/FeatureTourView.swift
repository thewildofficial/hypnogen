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
            Spacer(minLength: 16)
            pageIndicator
                .padding(.bottom, 8)
            navigationButtons
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
        .accessibilityIdentifier(Constants.Accessibility.Onboarding.featureTourContainer)
    }

    // MARK: - Tour Page

    @ViewBuilder
    private var tourPageContent: some View {
        let page = FeatureTourContent.pages[viewModel.currentTourPage]

        VStack(spacing: 16) {
            Image(systemName: page.sfSymbol)
                .font(.system(size: 56))
                .foregroundStyle(.accent)
                .symbolRenderingMode(.hierarchical)
                .accessibilityHidden(true)

            Text(page.title)
                .font(.title)
                .fontWeight(.semibold)
                .multilineTextAlignment(.center)

            Text(page.subtitle)
                .font(.title3)
                .foregroundStyle(.secondary)
                .multilineTextAlignment(.center)

            Text(page.body)
                .font(.body)
                .foregroundStyle(.secondary)
                .multilineTextAlignment(.center)
                .lineSpacing(4)
                .frame(maxWidth: 420)
        }
        .padding(.horizontal, 32)
        .padding(.top, 24)
        .accessibilityIdentifier(
            "\(Constants.Accessibility.Onboarding.featureTourPage)_\(viewModel.currentTourPage)"
        )
        .animation(.easeInOut(duration: 0.25), value: viewModel.currentTourPage)
    }

    // MARK: - Page Indicator

    private var pageIndicator: some View {
        HStack(spacing: 8) {
            ForEach(0..<viewModel.tourPageCount, id: \.self) { index in
                Circle()
                    .fill(index == viewModel.currentTourPage ? Color.accentColor : Color.secondary.opacity(0.3))
                    .frame(width: 8, height: 8)
                    .animation(.easeInOut(duration: 0.2), value: viewModel.currentTourPage)
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
            .disabled(viewModel.isOnFirstTourPage)
            .accessibilityIdentifier(Constants.Accessibility.Onboarding.previousButton)

            Spacer()

            Button(viewModel.isOnLastTourPage ? "Continue to Tips" : "Next") {
                viewModel.nextTourPage()
            }
            .buttonStyle(.borderedProminent)
            .accessibilityIdentifier(Constants.Accessibility.Onboarding.nextButton)
        }
        .padding(.horizontal, 32)
        .padding(.bottom, 8)
    }
}
