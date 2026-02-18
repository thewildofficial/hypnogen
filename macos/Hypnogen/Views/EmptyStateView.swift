import SwiftUI

struct EmptyStateView: View {
    let icon: String
    let title: String
    let description: String
    var ctaTitle: String?
    var ctaAction: (() -> Void)?

    @State private var glowPhase = false
    @Environment(\.accessibilityReduceMotion) private var reduceMotion

    var body: some View {
        VStack(spacing: Spacing.lg) {
            iconView
            textContent
            ctaButton
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
        .background(backgroundGradient)
    }

    // MARK: - Icon with Glow

    private var iconView: some View {
        ZStack {
            Circle()
                .fill(
                    RadialGradient.fade(
                        Color.accentViolet.opacity(glowPhase ? 0.25 : 0.12),
                        radius: 80
                    )
                )
                .frame(width: 160, height: 160)
                .breathingAnimation(reduceMotion: reduceMotion, value: glowPhase)

            Circle()
                .strokeBorder(
                    LinearGradient(
                        colors: [
                            Color.accentViolet.opacity(0.3),
                            Color.accentIndigo.opacity(0.15),
                            Color.accentGlow.opacity(0.2),
                        ],
                        startPoint: .topLeading,
                        endPoint: .bottomTrailing
                    ),
                    lineWidth: 1
                )
                .frame(width: 96, height: 96)

            Image(systemName: icon)
                .font(.system(size: 40, weight: .light))
                .foregroundStyle(
                    LinearGradient(
                        colors: [Color.accentGlow, Color.accentViolet],
                        startPoint: .topLeading,
                        endPoint: .bottomTrailing
                    )
                )
                .shadow(color: Color.accentGlow.opacity(0.5), radius: 12, x: 0, y: 0)
        }
        .onAppear {
            glowPhase = true
        }
    }

    // MARK: - Text

    private var textContent: some View {
        VStack(spacing: Spacing.sm) {
            Text(title)
                .font(Typography.sectionTitle)
                .foregroundStyle(Color.textPrimary)
                .tracking(Typography.trackingNormal)

            Text(description)
                .font(Typography.bodySmall)
                .foregroundStyle(Color.textSecondary)
                .multilineTextAlignment(.center)
                .frame(maxWidth: 280)
        }
    }

    // MARK: - CTA Button

    @ViewBuilder
    private var ctaButton: some View {
        if let ctaTitle, let ctaAction {
            Button(action: ctaAction) {
                HStack(spacing: Spacing.xs) {
                    Image(systemName: "plus")
                        .font(.system(size: 12, weight: .semibold))
                    Text(ctaTitle)
                        .font(Typography.bodyBold)
                }
                .foregroundStyle(Color.textPrimary)
                .padding(.horizontal, Spacing.lg)
                .padding(.vertical, Spacing.sm + 2)
                .background(
                    RoundedRectangle(cornerRadius: Radius.sm, style: .continuous)
                        .fill(Color.accentViolet.opacity(0.25))
                )
                .overlay(
                    RoundedRectangle(cornerRadius: Radius.sm, style: .continuous)
                        .strokeBorder(
                            Color.accentViolet.opacity(0.5),
                            lineWidth: 1
                        )
                )
            }
            .buttonStyle(.plain)
            .shadow(color: Color.accentViolet.opacity(0.2), radius: 8, x: 0, y: 2)
        }
    }

    // MARK: - Background

    private var backgroundGradient: some View {
        ZStack {
            Color.canvas

            RadialGradient(
                colors: [
                    Color.accentViolet.opacity(0.04),
                    Color.clear,
                ],
                center: .center,
                startRadius: 0,
                endRadius: 300
            )
        }
    }
}

extension EmptyStateView {
    init(icon: String, title: String, description: String) {
        self.icon = icon
        self.title = title
        self.description = description
        self.ctaTitle = nil
        self.ctaAction = nil
    }
}
