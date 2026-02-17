// OnboardingView.swift
// Hypnogen
//
// Main onboarding container: tab-based layout with Skip / Done controls and persistence toggle.


import SwiftUI

struct OnboardingView: View {
    @Bindable var viewModel: OnboardingViewModel

    @Environment(\.accessibilityReduceMotion) private var reduceMotion
    @State private var appeared = false
    @Namespace private var tabNamespace

    var body: some View {
        ZStack {
            backgroundLayer

            VStack(spacing: 0) {
                styledTabBar
                    .padding(.top, Spacing.md)
                    .padding(.horizontal, Spacing.lg)

                separatorLine
                    .padding(.top, Spacing.sm)

                tabContent
                    .frame(maxWidth: .infinity, maxHeight: .infinity)

                separatorLine

                bottomBar
                    .padding(.horizontal, Spacing.lg)
                    .padding(.vertical, Spacing.md)
            }
            .frostedGlass(.prominent, cornerRadius: Radius.lg)
            .padding(Spacing.md)
            .shadow(ShadowTokens.modal)
            .opacity(appeared ? 1 : 0)
            .scaleEffect(appeared ? 1 : 0.96)
            .animation(
                MotionSensitiveAnimation.resolve(
                    .spring(response: 0.5, dampingFraction: 0.8),
                    reduceMotion: reduceMotion
                ),
                value: appeared
            )
        }
        .frame(width: 620, height: 540)
        .accessibilityIdentifier(Constants.Accessibility.Onboarding.onboardingView)
        .onAppear {
            appeared = true
        }
    }

    // MARK: - Background Layer

    private var backgroundLayer: some View {
        ZStack {
            GradientTokens.heroGradient
                .ignoresSafeArea()

            Circle()
                .fill(
                    RadialGradient.fade(
                        Color.accentViolet.opacity(0.15),
                        radius: 200
                    )
                )
                .frame(width: 400, height: 400)
                .offset(x: -120, y: -160)
                .blur(radius: 60)

            Circle()
                .fill(
                    RadialGradient.fade(
                        Color.accentIndigo.opacity(0.1),
                        radius: 180
                    )
                )
                .frame(width: 360, height: 360)
                .offset(x: 140, y: 120)
                .blur(radius: 50)
        }
    }

    // MARK: - Styled Tab Bar

    private var styledTabBar: some View {
        HStack(spacing: Spacing.xs) {
            ForEach(OnboardingTab.allCases) { tab in
                tabButton(for: tab)
            }
        }
        .padding(Spacing.xs)
        .background(Color.surfacePrimary.opacity(0.3))
        .clipShape(RoundedRectangle(cornerRadius: Radius.sm + 2, style: .continuous))
    }

    private func tabButton(for tab: OnboardingTab) -> some View {
        let isSelected = viewModel.selectedTab == tab

        return Button {
            withTokenAnimation(AnimationTokens.springCard, reduceMotion: reduceMotion) {
                viewModel.selectedTab = tab
            }
        } label: {
            HStack(spacing: 6) {
                Image(systemName: tab.sfSymbol)
                    .font(.system(size: 12, weight: .medium))
                    .foregroundStyle(isSelected ? Color.textPrimary : Color.textSecondary)

                Text(tab.title)
                    .font(.system(size: 13, weight: isSelected ? .semibold : .medium))
                    .foregroundStyle(isSelected ? Color.textPrimary : Color.textSecondary)
            }
            .padding(.horizontal, Spacing.md)
            .padding(.vertical, Spacing.sm)
            .background {
                if isSelected {
                    RoundedRectangle(cornerRadius: Radius.sm, style: .continuous)
                        .fill(Color.accentViolet.opacity(0.25))
                        .overlay(
                            RoundedRectangle(cornerRadius: Radius.sm, style: .continuous)
                                .strokeBorder(Color.accentViolet.opacity(0.4), lineWidth: 1)
                        )
                        .matchedGeometryEffect(id: "activeTab", in: tabNamespace)
                }
            }
            .contentShape(RoundedRectangle(cornerRadius: Radius.sm))
        }
        .buttonStyle(.plain)
    }

    // MARK: - Separator

    private var separatorLine: some View {
        Rectangle()
            .fill(
                LinearGradient(
                    colors: [
                        Color.accentViolet.opacity(0),
                        Color.accentViolet.opacity(0.3),
                        Color.accentViolet.opacity(0),
                    ],
                    startPoint: .leading,
                    endPoint: .trailing
                )
            )
            .frame(height: 1)
            .padding(.horizontal, Spacing.md)
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
            .font(.system(size: 12))
            .foregroundStyle(Color.textSecondary)
            .accessibilityIdentifier(Constants.Accessibility.Onboarding.dontShowAgainCheckbox)

            Spacer()

            Button("Skip") {
                viewModel.skipOnboarding()
            }
            .buttonStyle(GhostButtonStyle(size: .medium))
            .keyboardShortcut(.cancelAction)
            .accessibilityIdentifier(Constants.Accessibility.Onboarding.skipButton)

            Button("Done") {
                viewModel.finishOnboarding()
            }
            .buttonStyle(PrimaryButtonStyle(size: .medium))
            .keyboardShortcut(.defaultAction)
            .accessibilityIdentifier(Constants.Accessibility.Onboarding.doneButton)
        }
    }
}
