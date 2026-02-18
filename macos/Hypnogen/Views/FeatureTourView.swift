// FeatureTourView.swift
// Hypnogen
//
// Paginated feature tour with navigation controls and page indicators.

import SwiftUI

struct FeatureTourView: View {
    @Bindable var viewModel: OnboardingViewModel

    @Environment(\.accessibilityReduceMotion) private var reduceMotion
    @State private var pulsePhase = false

    var body: some View {
        VStack(spacing: 0) {
            tourPageContent
            Spacer(minLength: Spacing.md)
            stepIndicator
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
        let isWelcome = viewModel.currentTourPage == 0

        VStack(spacing: Spacing.md) {
            if isWelcome {
                welcomeHero(page: page)
            } else {
                stepCard(page: page)
            }
        }
        .padding(.horizontal, Spacing.xl)
        .padding(.top, Spacing.lg)
        .accessibilityIdentifier(
            "\(Constants.Accessibility.Onboarding.featureTourPage)_\(viewModel.currentTourPage)"
        )
        .animation(
            MotionSensitiveAnimation.resolve(AnimationTokens.easeInOut, reduceMotion: reduceMotion),
            value: viewModel.currentTourPage
        )
    }

    // MARK: - Welcome Hero

    private func welcomeHero(page: TourPage) -> some View {
        VStack(spacing: Spacing.lg) {
            ZStack {
                Circle()
                    .fill(
                        RadialGradient.fade(
                            Color.accentViolet.opacity(pulsePhase ? 0.3 : 0.12),
                            radius: 60
                        )
                    )
                    .frame(width: 120, height: 120)
                    .breathingAnimation(reduceMotion: reduceMotion, value: pulsePhase)

                Circle()
                    .fill(
                        RadialGradient.fade(
                            Color.accentGlow.opacity(pulsePhase ? 0.2 : 0.08),
                            radius: 40
                        )
                    )
                    .frame(width: 80, height: 80)
                    .breathingAnimation(reduceMotion: reduceMotion, value: pulsePhase)

                Image(systemName: page.sfSymbol)
                    .font(.system(size: 40, weight: .light))
                    .foregroundStyle(LinearGradient.glowGradient)
                    .symbolRenderingMode(.hierarchical)
            }

            VStack(spacing: Spacing.sm) {
                Text(page.title)
                    .font(Typography.pageTitle)
                    .tracking(Typography.trackingTight)
                    .foregroundStyle(Color.textPrimary)
                    .multilineTextAlignment(.center)

                Text(page.subtitle)
                    .font(Typography.bodyBold)
                    .foregroundStyle(Color.textAccent)
                    .multilineTextAlignment(.center)
            }

            Text(page.body)
                .font(Typography.bodySmall)
                .foregroundStyle(Color.textSecondary)
                .multilineTextAlignment(.center)
                .lineSpacing(4)
                .frame(maxWidth: 400)
        }
        .onAppear { pulsePhase = true }
    }

    // MARK: - Step Card

    private func stepCard(page: TourPage) -> some View {
        VStack(spacing: Spacing.md) {
            Image(systemName: page.sfSymbol)
                .font(.system(size: 44, weight: .light))
                .foregroundStyle(LinearGradient.glowGradient)
                .symbolRenderingMode(.hierarchical)
                .shadow(color: Color.accentGlow.opacity(0.3), radius: 12, x: 0, y: 0)
                .accessibilityHidden(true)

            VStack(spacing: Spacing.xs) {
                Text(page.title)
                    .font(Typography.sectionTitle)
                    .foregroundStyle(Color.textPrimary)
                    .multilineTextAlignment(.center)

                Text(page.subtitle)
                    .font(Typography.bodyBold)
                    .foregroundStyle(Color.textAccent)
                    .multilineTextAlignment(.center)
            }

            Text(page.body)
                .font(Typography.bodySmall)
                .foregroundStyle(Color.textSecondary)
                .multilineTextAlignment(.center)
                .lineSpacing(4)
                .frame(maxWidth: 400)
        }
        .padding(Spacing.lg)
        .glassCardStyle(elevation: .raised)
    }

    // MARK: - Step Indicator

    private var stepIndicator: some View {
        HStack(spacing: Spacing.sm) {
            ForEach(0..<viewModel.tourPageCount, id: \.self) { index in
                let isCurrent = index == viewModel.currentTourPage
                let isPast = index < viewModel.currentTourPage

                Circle()
                    .fill(
                        isCurrent
                            ? Color.accentViolet
                            : (isPast ? Color.accentViolet.opacity(0.5) : Color.clear)
                    )
                    .overlay(
                        Circle()
                            .strokeBorder(
                                isCurrent
                                    ? Color.accentViolet
                                    : (isPast ? Color.accentViolet.opacity(0.4) : Color.textSecondary.opacity(0.3)),
                                lineWidth: 1.5
                            )
                    )
                    .frame(width: isCurrent ? 10 : 8, height: isCurrent ? 10 : 8)
                    .shadow(
                        color: isCurrent ? Color.accentGlow.opacity(0.5) : .clear,
                        radius: isCurrent ? 6 : 0,
                        x: 0,
                        y: 0
                    )
                    .animation(
                        MotionSensitiveAnimation.resolve(AnimationTokens.springCard, reduceMotion: reduceMotion),
                        value: viewModel.currentTourPage
                    )
            }
        }
        .accessibilityElement(children: .ignore)
        .accessibilityLabel("Page \(viewModel.currentTourPage + 1) of \(viewModel.tourPageCount)")
    }

    // MARK: - Navigation Buttons

    private var navigationButtons: some View {
        HStack {
            Button("Back") {
                viewModel.previousTourPage()
            }
            .buttonStyle(GhostButtonStyle(size: .medium))
            .disabled(viewModel.isOnFirstTourPage)
            .opacity(viewModel.isOnFirstTourPage ? 0.4 : 1)
            .accessibilityIdentifier(Constants.Accessibility.Onboarding.previousButton)

            Spacer()

            Button(viewModel.isOnLastTourPage ? "Continue to Tips" : "Next") {
                viewModel.nextTourPage()
            }
            .buttonStyle(PrimaryButtonStyle(size: .medium))
            .accessibilityIdentifier(Constants.Accessibility.Onboarding.nextButton)
        }
        .padding(.horizontal, Spacing.xl)
        .padding(.bottom, Spacing.sm)
    }
}
