import SwiftUI

// MARK: - Sidebar Row

struct SidebarRowView: View {
    let icon: String
    let label: String
    var badge: Int = 0
    var isSelected: Bool = false

    @State private var isHovered = false
    @Environment(\.accessibilityReduceMotion) private var reduceMotion

    var body: some View {
        HStack(spacing: Spacing.sm) {
            iconView
            labelView
            Spacer(minLength: 0)
            if badge > 0 {
                badgeView
            }
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
        .accessibilityLabel(label)
        .accessibilityValue(badge > 0 ? "\(badge)" : "")
        .accessibilityAddTraits(isSelected ? .isSelected : [])
    }

    // MARK: - Icon

    private var iconView: some View {
        Image(systemName: icon)
            .font(.system(size: 16, weight: .medium))
            .foregroundStyle(isSelected ? Color.textPrimary : Color.accentViolet)
            .frame(width: 24, height: 24)
            .symbolRenderingMode(.hierarchical)
    }

    // MARK: - Label

    private var labelView: some View {
        Text(label)
            .font(Typography.bodyText)
            .foregroundStyle(isSelected ? Color.textPrimary : Color.textSecondary)
            .lineLimit(1)
    }

    // MARK: - Badge

    private var badgeView: some View {
        Text("\(badge)")
            .font(Typography.label)
            .foregroundStyle(isSelected ? Color.textPrimary : Color.textAccent)
            .padding(.horizontal, 6)
            .padding(.vertical, 2)
            .background(
                Capsule()
                    .fill(isSelected ? Color.white.opacity(0.15) : Color.accentViolet.opacity(0.2))
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
                .fill(Color.accentGlow.opacity(0.08))
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

// MARK: - Section Header

struct SidebarSectionHeader: View {
    let title: String
    var isCollapsible: Bool = false
    @Binding var isExpanded: Bool

    var body: some View {
        HStack(spacing: Spacing.xs) {
            if isCollapsible {
                Image(systemName: "chevron.right")
                    .font(.system(size: 10, weight: .semibold))
                    .foregroundStyle(Color.textSecondary)
                    .rotationEffect(.degrees(isExpanded ? 90 : 0))
                    .animation(AnimationTokens.easeInOut, value: isExpanded)
            }

            Text(title.uppercased())
                .font(Typography.label)
                .tracking(Typography.trackingWide)
                .foregroundStyle(Color.textSecondary)

            Spacer(minLength: 0)
        }
        .padding(.horizontal, Spacing.sm + 2)
        .padding(.top, Spacing.md)
        .padding(.bottom, Spacing.xs)
        .contentShape(Rectangle())
        .onTapGesture {
            if isCollapsible {
                withAnimation(AnimationTokens.springCard) {
                    isExpanded.toggle()
                }
            }
        }
        .accessibilityElement(children: .combine)
        .accessibilityLabel(title)
        .accessibilityAddTraits(isCollapsible ? .isButton : [])
        .accessibilityValue(isCollapsible ? (isExpanded ? "expanded" : "collapsed") : "")
    }
}

extension SidebarSectionHeader {
    init(title: String) {
        self.title = title
        self.isCollapsible = false
        self._isExpanded = .constant(true)
    }
}

// MARK: - Collapsible Section

struct SidebarCollapsibleSection<Content: View>: View {
    let title: String
    @State private var isExpanded: Bool = true
    @ViewBuilder let content: () -> Content

    var body: some View {
        VStack(alignment: .leading, spacing: 0) {
            SidebarSectionHeader(
                title: title,
                isCollapsible: true,
                isExpanded: $isExpanded
            )

            if isExpanded {
                VStack(alignment: .leading, spacing: 2) {
                    content()
                }
                .transition(.opacity.combined(with: .move(edge: .top)))
            }
        }
    }
}

// MARK: - Section Divider

struct SidebarDivider: View {
    var body: some View {
        Rectangle()
            .fill(Color.surfaceSecondary.opacity(0.4))
            .frame(height: 0.5)
            .padding(.horizontal, Spacing.md)
            .padding(.vertical, Spacing.xs)
    }
}

// MARK: - Preview

#Preview("Sidebar Rows") {
    VStack(alignment: .leading, spacing: 2) {
        SidebarSectionHeader(title: "Projects")

        SidebarRowView(icon: "waveform", label: "Ambient Forest")
        SidebarRowView(icon: "waveform", label: "Deep Focus", isSelected: true)
        SidebarRowView(icon: "waveform", label: "Night Rain")

        SidebarDivider()

        SidebarCollapsibleSection(title: "Tools") {
            SidebarRowView(icon: "list.bullet.clipboard", label: "Render Queue", badge: 3)
            SidebarRowView(icon: "music.note.list", label: "Outputs Library")
        }

        SidebarDivider()

        SidebarSectionHeader(title: "Settings")
        SidebarRowView(icon: "gearshape", label: "Preferences")
        SidebarRowView(icon: "questionmark.circle", label: "Help & Tips")
    }
    .padding(Spacing.sm)
    .frame(width: 260, height: 500)
    .background(GradientTokens.sidebarGradient)
}
