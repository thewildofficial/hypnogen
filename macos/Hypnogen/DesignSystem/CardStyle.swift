import SwiftUI

// MARK: - Card Elevation

/// Elevation levels controlling shadow depth for card components
enum CardElevation {
    /// Raised — subtle lift off the surface (default card shadow)
    case raised
    /// Floating — medium elevation, panels and popovers
    case floating
    /// Modal — highest elevation, dialogs and overlays
    case modal

    var shadow: ShadowStyle {
        switch self {
        case .raised:  return ShadowTokens.card
        case .floating: return ShadowTokens.panel
        case .modal:   return ShadowTokens.modal
        }
    }
}

// MARK: - Card Style

/// Premium card with surface gradient background, subtle border, and elevation shadow
struct CardStyle: ViewModifier {
    var elevation: CardElevation

    init(elevation: CardElevation = .raised) {
        self.elevation = elevation
    }

    func body(content: Content) -> some View {
        content
            .padding(Spacing.md)
            .background(GradientTokens.cardGradient)
            .clipShape(RoundedRectangle(cornerRadius: Radius.md, style: .continuous))
            .overlay(
                RoundedRectangle(cornerRadius: Radius.md, style: .continuous)
                    .strokeBorder(
                        Color.surfaceSecondary.opacity(0.4),
                        lineWidth: 1
                    )
            )
            .shadow(elevation.shadow)
    }
}

// MARK: - Interactive Card Style

/// Premium interactive card with glow border on hover and spring scale effect
struct InteractiveCardStyle: ViewModifier {
    var elevation: CardElevation

    @State private var isHovered = false
    @Environment(\.accessibilityReduceMotion) private var reduceMotion

    init(elevation: CardElevation = .raised) {
        self.elevation = elevation
    }

    func body(content: Content) -> some View {
        content
            .padding(Spacing.md)
            .background(GradientTokens.cardGradient)
            .clipShape(RoundedRectangle(cornerRadius: Radius.md, style: .continuous))
            .overlay(
                RoundedRectangle(cornerRadius: Radius.md, style: .continuous)
                    .strokeBorder(
                        isHovered
                            ? Color.accentGlow.opacity(0.7)
                            : Color.surfaceSecondary.opacity(0.4),
                        lineWidth: isHovered ? 1.5 : 1
                    )
            )
            .shadow(elevation.shadow)
            .shadow(
                color: Color.accentGlow.opacity(isHovered ? 0.3 : 0),
                radius: isHovered ? 16 : 0,
                x: 0,
                y: 0
            )
            .scaleEffect(isHovered ? 1.02 : 1.0)
            .animation(
                MotionSensitiveAnimation.resolve(AnimationTokens.springCard, reduceMotion: reduceMotion),
                value: isHovered
            )
            .onHover { hovering in
                isHovered = hovering
            }
    }
}

// MARK: - Glass Card Style

/// Frosted glass card using ultra-thin material with blur backdrop
struct GlassCardStyle: ViewModifier {
    var elevation: CardElevation

    init(elevation: CardElevation = .raised) {
        self.elevation = elevation
    }

    func body(content: Content) -> some View {
        content
            .padding(Spacing.md)
            .background(.ultraThinMaterial)
            .clipShape(RoundedRectangle(cornerRadius: Radius.md, style: .continuous))
            .overlay(
                RoundedRectangle(cornerRadius: Radius.md, style: .continuous)
                    .strokeBorder(
                        LinearGradient(
                            colors: [
                                Color.white.opacity(0.15),
                                Color.white.opacity(0.05),
                            ],
                            startPoint: .topLeading,
                            endPoint: .bottomTrailing
                        ),
                        lineWidth: 1
                    )
            )
            .shadow(elevation.shadow)
    }
}

// MARK: - Glow Card Style

/// Always-visible violet glow card for featured or highlighted content
struct GlowCardStyle: ViewModifier {
    var elevation: CardElevation

    @State private var isGlowing = false

    init(elevation: CardElevation = .raised) {
        self.elevation = elevation
    }

    func body(content: Content) -> some View {
        content
            .padding(Spacing.md)
            .background(GradientTokens.cardGradient)
            .clipShape(RoundedRectangle(cornerRadius: Radius.md, style: .continuous))
            .overlay(
                RoundedRectangle(cornerRadius: Radius.md, style: .continuous)
                    .strokeBorder(
                        LinearGradient(
                            colors: [
                                Color.accentViolet.opacity(0.6),
                                Color.accentIndigo.opacity(0.4),
                                Color.accentGlow.opacity(0.6),
                            ],
                            startPoint: .topLeading,
                            endPoint: .bottomTrailing
                        ),
                        lineWidth: 1.5
                    )
            )
            .shadow(elevation.shadow)
            .shadow(
                color: Color.accentGlow.opacity(isGlowing ? 0.5 : 0.25),
                radius: isGlowing ? 24 : 16,
                x: 0,
                y: 0
            )
            .animation(AnimationTokens.breathing, value: isGlowing)
            .onAppear { isGlowing = true }
    }
}

// MARK: - View Extensions

extension View {
    /// Apply standard premium card styling
    func cardStyle(elevation: CardElevation = .raised) -> some View {
        modifier(CardStyle(elevation: elevation))
    }

    /// Apply interactive card styling with glow hover and spring scale
    func interactiveCardStyle(elevation: CardElevation = .raised) -> some View {
        modifier(InteractiveCardStyle(elevation: elevation))
    }

    /// Apply frosted glass card styling
    func glassCardStyle(elevation: CardElevation = .raised) -> some View {
        modifier(GlassCardStyle(elevation: elevation))
    }

    /// Apply always-glowing card styling for featured content
    func glowCardStyle(elevation: CardElevation = .raised) -> some View {
        modifier(GlowCardStyle(elevation: elevation))
    }
}
