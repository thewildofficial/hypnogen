import SwiftUI

// MARK: - Button Size

/// Size variants for button styles
enum ButtonSize {
    case small
    case medium
    case large

    var fontSize: CGFloat {
        switch self {
        case .small: 12
        case .medium: 14
        case .large: 16
        }
    }

    var fontWeight: Font.Weight {
        switch self {
        case .small: .medium
        case .medium: .semibold
        case .large: .semibold
        }
    }

    var horizontalPadding: CGFloat {
        switch self {
        case .small: Spacing.sm
        case .medium: Spacing.md
        case .large: Spacing.lg
        }
    }

    var verticalPadding: CGFloat {
        switch self {
        case .small: Spacing.xs
        case .medium: Spacing.sm
        case .large: Spacing.sm + 4
        }
    }

    var cornerRadius: CGFloat {
        switch self {
        case .small: Radius.sm
        case .medium: Radius.sm
        case .large: Radius.md
        }
    }

    var iconSize: CGFloat {
        switch self {
        case .small: 12
        case .medium: 14
        case .large: 16
        }
    }
}

// MARK: - Icon Position

/// Positioning for button icons
enum ButtonIconPosition {
    case leading
    case trailing
}

// MARK: - Button Label Builder

/// Composes a button label with optional icon at leading or trailing position
struct ButtonLabel: View {
    let text: String
    let icon: String?
    let iconPosition: ButtonIconPosition
    let size: ButtonSize

    init(
        _ text: String,
        icon: String? = nil,
        iconPosition: ButtonIconPosition = .leading,
        size: ButtonSize = .medium
    ) {
        self.text = text
        self.icon = icon
        self.iconPosition = iconPosition
        self.size = size
    }

    var body: some View {
        HStack(spacing: size == .small ? 4 : 6) {
            if let icon, iconPosition == .leading {
                Image(systemName: icon)
                    .font(.system(size: size.iconSize, weight: size.fontWeight))
            }

            Text(text)

            if let icon, iconPosition == .trailing {
                Image(systemName: icon)
                    .font(.system(size: size.iconSize, weight: size.fontWeight))
            }
        }
    }
}

// MARK: - Primary Button Style

/// Primary action button with gradient background, glow on hover, spring press animation
struct PrimaryButtonStyle: ButtonStyle {
    @Environment(\.isEnabled) private var isEnabled
    @Environment(\.accessibilityReduceMotion) private var reduceMotion
    @State private var isHovered = false

    var size: ButtonSize

    init(size: ButtonSize = .medium) {
        self.size = size
    }

    func makeBody(configuration: Configuration) -> some View {
        configuration.label
            .font(.system(size: size.fontSize, weight: size.fontWeight))
            .padding(.horizontal, size.horizontalPadding)
            .padding(.vertical, size.verticalPadding)
            .foregroundStyle(isEnabled ? Color.textPrimary : Color.textSecondary)
            .background(backgroundView(isPressed: configuration.isPressed))
            .clipShape(RoundedRectangle(cornerRadius: size.cornerRadius, style: .continuous))
            .shadow(
                color: glowColor(isPressed: configuration.isPressed),
                radius: isHovered && isEnabled ? 16 : 0,
                x: 0,
                y: 0
            )
            .scaleEffect(pressScale(configuration.isPressed))
            .animation(pressAnimation, value: configuration.isPressed)
            .animation(hoverAnimation, value: isHovered)
            .onHover { hovering in
                guard isEnabled else { return }
                isHovered = hovering
            }
    }

    @ViewBuilder
    private func backgroundView(isPressed: Bool) -> some View {
        if isEnabled {
            GradientTokens.accentGradient
                .opacity(isPressed ? 0.85 : (isHovered ? 1.0 : 0.9))
        } else {
            Color.surfaceSecondary.opacity(0.5)
        }
    }

    private func glowColor(isPressed: Bool) -> Color {
        guard isEnabled else { return .clear }
        if isPressed {
            return Color.accentViolet.opacity(0.3)
        }
        return isHovered ? Color.accentGlow.opacity(0.5) : .clear
    }

    private func pressScale(_ isPressed: Bool) -> CGFloat {
        guard isEnabled else { return 1.0 }
        return isPressed ? 0.96 : 1.0
    }

    private var pressAnimation: Animation {
        reduceMotion ? .default : AnimationTokens.springButton
    }

    private var hoverAnimation: Animation {
        reduceMotion ? .default : AnimationTokens.easeInOut
    }
}

// MARK: - Secondary Button Style

/// Secondary action button with surface background, violet stroke, subtle glow on hover
struct SecondaryButtonStyle: ButtonStyle {
    @Environment(\.isEnabled) private var isEnabled
    @Environment(\.accessibilityReduceMotion) private var reduceMotion
    @State private var isHovered = false

    var size: ButtonSize

    init(size: ButtonSize = .medium) {
        self.size = size
    }

    func makeBody(configuration: Configuration) -> some View {
        configuration.label
            .font(.system(size: size.fontSize, weight: size.fontWeight))
            .padding(.horizontal, size.horizontalPadding)
            .padding(.vertical, size.verticalPadding)
            .foregroundStyle(foregroundColor(isPressed: configuration.isPressed))
            .background(backgroundFill(isPressed: configuration.isPressed))
            .clipShape(RoundedRectangle(cornerRadius: size.cornerRadius, style: .continuous))
            .overlay(strokeOverlay(isPressed: configuration.isPressed))
            .shadow(
                color: isHovered && isEnabled ? Color.accentViolet.opacity(0.2) : .clear,
                radius: isHovered && isEnabled ? 12 : 0,
                x: 0,
                y: 0
            )
            .scaleEffect(configuration.isPressed && isEnabled ? 0.97 : 1.0)
            .animation(pressAnimation, value: configuration.isPressed)
            .animation(hoverAnimation, value: isHovered)
            .onHover { hovering in
                guard isEnabled else { return }
                isHovered = hovering
            }
    }

    private func foregroundColor(isPressed: Bool) -> Color {
        guard isEnabled else { return Color.textSecondary }
        return isPressed ? Color.accentGlow : (isHovered ? Color.textPrimary : Color.textAccent)
    }

    private func backgroundFill(isPressed: Bool) -> some ShapeStyle {
        if isEnabled {
            return Color.surfacePrimary.opacity(isPressed ? 0.6 : (isHovered ? 0.9 : 0.7))
        } else {
            return Color.surfacePrimary.opacity(0.3)
        }
    }

    private func strokeOverlay(isPressed: Bool) -> some View {
        RoundedRectangle(cornerRadius: size.cornerRadius, style: .continuous)
            .strokeBorder(
                strokeColor(isPressed: isPressed),
                lineWidth: isHovered && isEnabled ? 1.5 : 1
            )
    }

    private func strokeColor(isPressed: Bool) -> Color {
        guard isEnabled else { return Color.surfaceSecondary.opacity(0.3) }
        if isPressed { return Color.accentViolet.opacity(0.8) }
        return isHovered ? Color.accentViolet.opacity(0.6) : Color.accentViolet.opacity(0.3)
    }

    private var pressAnimation: Animation {
        reduceMotion ? .default : AnimationTokens.springButton
    }

    private var hoverAnimation: Animation {
        reduceMotion ? .default : AnimationTokens.easeInOut
    }
}

// MARK: - Ghost Button Style

/// Transparent button with violet text, underline on hover
struct GhostButtonStyle: ButtonStyle {
    @Environment(\.isEnabled) private var isEnabled
    @Environment(\.accessibilityReduceMotion) private var reduceMotion
    @State private var isHovered = false

    var size: ButtonSize

    init(size: ButtonSize = .medium) {
        self.size = size
    }

    func makeBody(configuration: Configuration) -> some View {
        configuration.label
            .font(.system(size: size.fontSize, weight: size.fontWeight))
            .padding(.horizontal, size.horizontalPadding / 2)
            .padding(.vertical, size.verticalPadding / 2)
            .foregroundStyle(foregroundColor(isPressed: configuration.isPressed))
            .background(
                isHovered && isEnabled
                    ? Color.accentViolet.opacity(0.08)
                    : Color.clear
            )
            .clipShape(RoundedRectangle(cornerRadius: size.cornerRadius, style: .continuous))
            .overlay(alignment: .bottom) {
                if isHovered && isEnabled {
                    Rectangle()
                        .fill(Color.accentViolet.opacity(0.6))
                        .frame(height: 1)
                        .padding(.horizontal, size.horizontalPadding / 2)
                        .transition(.opacity)
                }
            }
            .scaleEffect(configuration.isPressed && isEnabled ? 0.97 : 1.0)
            .animation(pressAnimation, value: configuration.isPressed)
            .animation(hoverAnimation, value: isHovered)
            .onHover { hovering in
                guard isEnabled else { return }
                isHovered = hovering
            }
    }

    private func foregroundColor(isPressed: Bool) -> Color {
        guard isEnabled else { return Color.textSecondary }
        if isPressed { return Color.accentGlow }
        return isHovered ? Color.accentViolet : Color.textAccent
    }

    private var pressAnimation: Animation {
        reduceMotion ? .default : AnimationTokens.springButton
    }

    private var hoverAnimation: Animation {
        reduceMotion ? .default : AnimationTokens.easeInOut
    }
}

// MARK: - Destructive Button Style

/// Red accent button for delete/cancel actions
struct DestructiveButtonStyle: ButtonStyle {
    @Environment(\.isEnabled) private var isEnabled
    @Environment(\.accessibilityReduceMotion) private var reduceMotion
    @State private var isHovered = false

    var size: ButtonSize

    init(size: ButtonSize = .medium) {
        self.size = size
    }

    /// Destructive red — consistent with system delete semantics
    private static let destructiveRed = Color(red: 0.94, green: 0.27, blue: 0.27)
    /// Darker press-state red
    private static let destructiveRedDark = Color(red: 0.78, green: 0.18, blue: 0.18)

    func makeBody(configuration: Configuration) -> some View {
        configuration.label
            .font(.system(size: size.fontSize, weight: size.fontWeight))
            .padding(.horizontal, size.horizontalPadding)
            .padding(.vertical, size.verticalPadding)
            .foregroundStyle(foregroundColor(isPressed: configuration.isPressed))
            .background(backgroundFill(isPressed: configuration.isPressed))
            .clipShape(RoundedRectangle(cornerRadius: size.cornerRadius, style: .continuous))
            .overlay(strokeOverlay(isPressed: configuration.isPressed))
            .shadow(
                color: isHovered && isEnabled ? Self.destructiveRed.opacity(0.3) : .clear,
                radius: isHovered && isEnabled ? 12 : 0,
                x: 0,
                y: 0
            )
            .scaleEffect(configuration.isPressed && isEnabled ? 0.96 : 1.0)
            .animation(pressAnimation, value: configuration.isPressed)
            .animation(hoverAnimation, value: isHovered)
            .onHover { hovering in
                guard isEnabled else { return }
                isHovered = hovering
            }
    }

    private func foregroundColor(isPressed: Bool) -> Color {
        guard isEnabled else { return Color.textSecondary }
        if isPressed { return .white }
        return isHovered ? .white : Self.destructiveRed
    }

    private func backgroundFill(isPressed: Bool) -> some ShapeStyle {
        if !isEnabled {
            return Color.surfacePrimary.opacity(0.3)
        }
        if isPressed {
            return Self.destructiveRedDark.opacity(0.9)
        }
        return isHovered ? Self.destructiveRed.opacity(0.85) : Self.destructiveRed.opacity(0.12)
    }

    private func strokeOverlay(isPressed: Bool) -> some View {
        RoundedRectangle(cornerRadius: size.cornerRadius, style: .continuous)
            .strokeBorder(
                strokeColor(isPressed: isPressed),
                lineWidth: isHovered && isEnabled ? 1.5 : 1
            )
    }

    private func strokeColor(isPressed: Bool) -> Color {
        guard isEnabled else { return Color.surfaceSecondary.opacity(0.3) }
        if isPressed || isHovered { return Self.destructiveRed.opacity(0.8) }
        return Self.destructiveRed.opacity(0.3)
    }

    private var pressAnimation: Animation {
        reduceMotion ? .default : AnimationTokens.springButton
    }

    private var hoverAnimation: Animation {
        reduceMotion ? .default : AnimationTokens.easeInOut
    }
}

// MARK: - View Extensions

extension View {
    func primaryButtonStyle(size: ButtonSize = .medium) -> some View {
        self.buttonStyle(PrimaryButtonStyle(size: size))
    }

    func secondaryButtonStyle(size: ButtonSize = .medium) -> some View {
        self.buttonStyle(SecondaryButtonStyle(size: size))
    }

    func ghostButtonStyle(size: ButtonSize = .medium) -> some View {
        self.buttonStyle(GhostButtonStyle(size: size))
    }

    func destructiveButtonStyle(size: ButtonSize = .medium) -> some View {
        self.buttonStyle(DestructiveButtonStyle(size: size))
    }
}
