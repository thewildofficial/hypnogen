// HeroWelcomeView.swift
// Hypnogen

import SwiftUI

// MARK: - Hero Welcome View

struct HeroWelcomeView: View {
    @Environment(\.accessibilityReduceMotion) private var reduceMotion

    let recentProjects: [Project]
    var onNewSession: () -> Void
    var onSelectProject: (Project) -> Void

    @State private var breathPhase = false
    @State private var appeared = false

    var body: some View {
        ZStack {
            heroBackground
            heroContent
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
        .onAppear {
            if !reduceMotion {
                breathPhase = true
                withAnimation(.easeOut(duration: 0.8)) {
                    appeared = true
                }
            } else {
                appeared = true
            }
        }
    }

    // MARK: - Background

    private var heroBackground: some View {
        ZStack {
            GradientTokens.heroGradient
                .ignoresSafeArea()

            Circle()
                .fill(
                    RadialGradient.fade(
                        Color.accentViolet.opacity(breathPhase ? 0.18 : 0.08),
                        radius: breathPhase ? 280 : 200
                    )
                )
                .frame(width: 560, height: 560)
                .offset(y: 60)
                .breathingAnimation(reduceMotion: reduceMotion, value: breathPhase)

            Circle()
                .fill(
                    RadialGradient.fade(
                        Color.accentIndigo.opacity(breathPhase ? 0.12 : 0.05),
                        radius: breathPhase ? 180 : 120
                    )
                )
                .frame(width: 360, height: 360)
                .offset(x: 160, y: -140)
                .breathingAnimation(reduceMotion: reduceMotion, value: breathPhase)
        }
    }

    // MARK: - Content

    private var heroContent: some View {
        VStack(spacing: 0) {
            Spacer()

            hypnoticWaveform
                .opacity(appeared ? 1 : 0)
                .offset(y: appeared ? 0 : 20)

            Spacer()
                .frame(height: Spacing.xl)

            brandingSection
                .opacity(appeared ? 1 : 0)
                .offset(y: appeared ? 0 : 12)

            Spacer()
                .frame(height: Spacing.xl + Spacing.sm)

            ctaSection
                .opacity(appeared ? 1 : 0)
                .offset(y: appeared ? 0 : 8)

            if !recentProjects.isEmpty {
                Spacer()
                    .frame(height: Spacing.xl)

                recentProjectsSection
                    .opacity(appeared ? 1 : 0)
                    .offset(y: appeared ? 0 : 8)
            }

            Spacer()
        }
        .animation(
            reduceMotion ? nil : .easeOut(duration: 0.8),
            value: appeared
        )
    }

    // MARK: - Hypnotic Waveform

    private var hypnoticWaveform: some View {
        HypnoticWaveformView(breathPhase: breathPhase, reduceMotion: reduceMotion)
            .frame(width: 200, height: 200)
    }

    // MARK: - Branding

    private var brandingSection: some View {
        VStack(spacing: Spacing.sm) {
            HStack(spacing: Spacing.md) {
                Image("hypnogen_logo")
                    .resizable()
                    .aspectRatio(contentMode: .fit)
                    .frame(width: 48, height: 48)

                Text("Hypnogen")
                    .heroTitle()
                    .foregroundStyle(
                        LinearGradient(
                            colors: [Color.textPrimary, Color.accentGlow],
                            startPoint: .leading,
                            endPoint: .trailing
                        )
                    )
            }

            Text("Create personalized hypnosis sessions")
                .font(Typography.bodyText)
                .tracking(Typography.trackingWide)
                .foregroundStyle(Color.textSecondary)
        }
    }

    // MARK: - CTA

    private var ctaSection: some View {
        Button {
            onNewSession()
        } label: {
            ButtonLabel(
                "New Session",
                icon: "plus.circle.fill",
                size: .large
            )
        }
        .buttonStyle(PrimaryButtonStyle(size: .large))
        .shadow(
            color: Color.accentViolet.opacity(breathPhase ? 0.4 : 0.15),
            radius: breathPhase ? 24 : 8,
            x: 0,
            y: 0
        )
        .pulseAnimation(reduceMotion: reduceMotion, value: breathPhase)
    }

    // MARK: - Recent Projects

    private var recentProjectsSection: some View {
        VStack(spacing: Spacing.sm) {
            Text("RECENT")
                .font(Typography.label)
                .tracking(Typography.trackingWide)
                .foregroundStyle(Color.textSecondary.opacity(0.7))

            VStack(spacing: Spacing.xs) {
                ForEach(recentProjects.prefix(3)) { project in
                    RecentProjectRow(project: project) {
                        onSelectProject(project)
                    }
                }
            }
            .frame(maxWidth: 320)
        }
    }
}

// MARK: - Recent Project Row

private struct RecentProjectRow: View {
    let project: Project
    let onSelect: () -> Void

    @State private var isHovered = false

    var body: some View {
        Button(action: onSelect) {
            HStack(spacing: Spacing.sm) {
                Image(systemName: "waveform")
                    .font(.system(size: 12, weight: .medium))
                    .foregroundStyle(Color.accentGlow)
                    .frame(width: 20)

                Text(project.name)
                    .font(Typography.bodySmall)
                    .foregroundStyle(Color.textPrimary)
                    .lineLimit(1)

                Spacer()

                Text(project.modifiedAt.formatted(.relative(presentation: .named)))
                    .font(Typography.captionText)
                    .foregroundStyle(Color.textSecondary)
            }
            .padding(.horizontal, Spacing.md)
            .padding(.vertical, Spacing.sm)
            .background(
                RoundedRectangle(cornerRadius: Radius.sm, style: .continuous)
                    .fill(isHovered ? Color.surfacePrimary.opacity(0.6) : Color.clear)
            )
            .overlay(
                RoundedRectangle(cornerRadius: Radius.sm, style: .continuous)
                    .strokeBorder(
                        isHovered ? Color.accentViolet.opacity(0.3) : Color.clear,
                        lineWidth: 1
                    )
            )
        }
        .buttonStyle(.plain)
        .onHover { hovering in isHovered = hovering }
        .animation(AnimationTokens.easeInOut, value: isHovered)
    }
}

// MARK: - Hypnotic Waveform Visual

/// Concentric rings with staggered duration/delay per ring index create organic phase-drift breathing.
private struct HypnoticWaveformView: View {
    let breathPhase: Bool
    let reduceMotion: Bool

    private let ringCount = 6

    var body: some View {
        ZStack {
            Circle()
                .fill(
                    RadialGradient.fade(
                        Color.accentGlow.opacity(breathPhase ? 0.2 : 0.08),
                        radius: 100
                    )
                )
                .breathingAnimation(reduceMotion: reduceMotion, value: breathPhase)

            ForEach(0..<ringCount, id: \.self) { index in
                concentricRing(index: index)
            }

            Circle()
                .fill(Color.accentGlow)
                .frame(width: 6, height: 6)
                .shadow(color: Color.accentGlow.opacity(0.8), radius: 8, x: 0, y: 0)
        }
    }

    private func concentricRing(index: Int) -> some View {
        let progress = Double(index) / Double(ringCount - 1)
        let baseSize: CGFloat = 30 + CGFloat(index) * 28
        let scaleBreath: CGFloat = breathPhase
            ? 1.0 + CGFloat(index) * 0.02
            : 1.0 - CGFloat(index) * 0.015

        return Circle()
            .strokeBorder(
                ringGradient(index: index),
                lineWidth: max(1.0, 2.0 - progress * 1.2)
            )
            .frame(width: baseSize, height: baseSize)
            .scaleEffect(scaleBreath)
            .opacity(breathPhase
                ? 0.8 - progress * 0.35
                : 0.4 - progress * 0.2
            )
            .rotationEffect(.degrees(breathPhase ? Double(index) * 8 : Double(index) * -4))
            .animation(
                reduceMotion
                    ? nil
                    : .easeInOut(duration: 4.0 + Double(index) * 0.3)
                        .repeatForever(autoreverses: true)
                        .delay(Double(index) * 0.15),
                value: breathPhase
            )
    }

    private func ringGradient(index: Int) -> some ShapeStyle {
        let t = Double(index) / Double(ringCount - 1)
        return Color.accentViolet.opacity(1.0 - t * 0.5)
            .blendMode(.normal)
    }
}

// MARK: - Preview

#if DEBUG
#Preview("Hero Welcome — Empty") {
    HeroWelcomeView(
        recentProjects: [],
        onNewSession: {},
        onSelectProject: { _ in }
    )
    .frame(width: 800, height: 600)
}

#Preview("Hero Welcome — With Recents") {
    HeroWelcomeView(
        recentProjects: [
            Project(name: "Deep Sleep Relaxation"),
            Project(name: "Confidence Booster"),
            Project(name: "Morning Motivation"),
        ],
        onNewSession: {},
        onSelectProject: { _ in }
    )
    .frame(width: 800, height: 600)
}
#endif
