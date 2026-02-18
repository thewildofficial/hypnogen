import SwiftUI

// MARK: - Project Row

struct ProjectRowView: View {
    let project: Project
    var isSelected: Bool = false

    @State private var isHovered = false
    @Environment(\.accessibilityReduceMotion) private var reduceMotion

    var body: some View {
        HStack(spacing: Spacing.sm) {
            iconView
            textContent
            Spacer(minLength: 0)
            if affirmationCount > 0 {
                affirmationBadge
            }
            chevronView
        }
        .padding(.horizontal, Spacing.sm + 2)
        .padding(.vertical, Spacing.sm)
        .background(backgroundLayer)
        .overlay(borderOverlay)
        .clipShape(RoundedRectangle(cornerRadius: Radius.sm))
        .shadow(
            color: isSelected
                ? Color.accentGlow.opacity(0.35)
                : (isHovered ? Color.accentViolet.opacity(0.15) : .clear),
            radius: isSelected ? 12 : (isHovered ? 10 : 0),
            x: 0,
            y: 0
        )
        .scaleEffect(isSelected ? 1.0 : (isHovered ? 1.01 : 1.0))
        .animation(
            MotionSensitiveAnimation.resolve(AnimationTokens.springCard, reduceMotion: reduceMotion),
            value: isSelected
        )
        .animation(
            MotionSensitiveAnimation.resolve(AnimationTokens.springGlow, reduceMotion: reduceMotion),
            value: isHovered
        )
        .onHover { hovering in
            isHovered = hovering
        }
        .contentShape(RoundedRectangle(cornerRadius: Radius.sm))
        .accessibilityElement(children: .combine)
        .accessibilityLabel("\(project.name), modified \(project.modifiedAt.formatted(date: .abbreviated, time: .shortened))")
        .accessibilityValue(affirmationCount > 0 ? "\(affirmationCount) affirmations" : "")
        .accessibilityAddTraits(isSelected ? .isSelected : [])
    }

    // MARK: - Affirmation Count

    private var affirmationCount: Int {
        project.affirmations.filter {
            !$0.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty
        }.count
    }

    // MARK: - Icon

    private var iconView: some View {
        Image(systemName: "doc.text.fill")
            .font(.system(size: 16, weight: .medium))
            .foregroundStyle(isSelected ? Color.textPrimary : Color.accentViolet)
            .frame(width: 24, height: 24)
            .symbolRenderingMode(.hierarchical)
    }

    // MARK: - Text Content

    private var textContent: some View {
        VStack(alignment: .leading, spacing: 2) {
            Text(project.name)
                .font(Typography.bodyBold)
                .foregroundStyle(isSelected ? Color.textPrimary : Color.textPrimary)
                .lineLimit(1)

            Text(project.modifiedAt.formatted(date: .abbreviated, time: .shortened))
                .font(Typography.captionText)
                .foregroundStyle(isSelected ? Color.textPrimary.opacity(0.7) : Color.textSecondary)
                .lineLimit(1)
        }
    }

    // MARK: - Affirmation Badge

    private var affirmationBadge: some View {
        Text("\(affirmationCount) affirm.")
            .font(Typography.label)
            .foregroundStyle(isSelected ? Color.textPrimary : Color.textAccent)
            .padding(.horizontal, 6)
            .padding(.vertical, 2)
            .background(
                Capsule()
                    .fill(isSelected ? Color.white.opacity(0.15) : Color.accentViolet.opacity(0.15))
            )
    }

    // MARK: - Chevron

    private var chevronView: some View {
        Image(systemName: "chevron.right")
            .font(.system(size: 10, weight: .semibold))
            .foregroundStyle(
                isSelected ? Color.textPrimary.opacity(0.6) : Color.textSecondary.opacity(isHovered ? 0.8 : 0.4)
            )
    }

    // MARK: - Background

    @ViewBuilder
    private var backgroundLayer: some View {
        if isSelected {
            RoundedRectangle(cornerRadius: Radius.sm)
                .fill(
                    LinearGradient(
                        colors: [
                            Color.accentViolet.opacity(0.55),
                            Color.accentIndigo.opacity(0.45),
                        ],
                        startPoint: .leading,
                        endPoint: .trailing
                    )
                )
        } else if isHovered {
            RoundedRectangle(cornerRadius: Radius.sm)
                .fill(Color.accentViolet.opacity(0.08))
        } else {
            Color.clear
        }
    }

    // MARK: - Border Overlay

    @ViewBuilder
    private var borderOverlay: some View {
        if isSelected {
            RoundedRectangle(cornerRadius: Radius.sm)
                .strokeBorder(
                    LinearGradient(
                        colors: [
                            Color.accentGlow.opacity(0.6),
                            Color.accentViolet.opacity(0.3),
                        ],
                        startPoint: .topLeading,
                        endPoint: .bottomTrailing
                    ),
                    lineWidth: 1
                )
        } else if isHovered {
            RoundedRectangle(cornerRadius: Radius.sm)
                .strokeBorder(Color.accentGlow.opacity(0.12), lineWidth: 0.5)
        }
    }
}

// MARK: - Preview

#Preview("Project Rows") {
    VStack(alignment: .leading, spacing: 2) {
        SidebarSectionHeader(title: "Projects")

        ProjectRowView(
            project: Project(
                name: "Deep Sleep Meditation",
                affirmations: ["I am calm", "I am relaxed", "I sleep deeply"]
            )
        )
        ProjectRowView(
            project: Project(
                name: "Morning Energy Boost",
                affirmations: ["I am energized", "Today is my day"]
            ),
            isSelected: true
        )
        ProjectRowView(
            project: Project(name: "Focus Session")
        )
    }
    .padding(Spacing.sm)
    .frame(width: 280, height: 300)
    .background(GradientTokens.sidebarGradient)
}
