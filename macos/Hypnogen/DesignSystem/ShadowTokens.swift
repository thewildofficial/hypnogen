import SwiftUI

// MARK: - Shadow Tokens

/// Shadow presets for consistent elevation and glow effects
enum ShadowTokens {
    /// Card shadow — Subtle lift for cards
    static let card = ShadowStyle(
        color: Color.black.opacity(0.3),
        radius: 8,
        x: 0,
        y: 4
    )

    /// Panel shadow — Medium shadow for panels
    static let panel = ShadowStyle(
        color: Color.black.opacity(0.4),
        radius: 16,
        x: 0,
        y: 8
    )

    /// Modal shadow — Highest elevation
    static let modal = ShadowStyle(
        color: Color.black.opacity(0.25),
        radius: 16,
        x: 0,
        y: 8
    )

    /// Glow shadow — Violet glow effect using AccentGlow
    static let glow = ShadowStyle(
        color: Color.accentGlow.opacity(0.5),
        radius: 20,
        x: 0,
        y: 0
    )

    /// Hero shadow — Deep shadow for hero elements
    static let hero = ShadowStyle(
        color: Color.black.opacity(0.5),
        radius: 32,
        x: 0,
        y: 16
    )
}

// MARK: - Shadow Style

struct ShadowStyle {
    let color: Color
    let radius: CGFloat
    let x: CGFloat
    let y: CGFloat
}

// MARK: - Shadow Convenience

extension View {
    /// Apply shadow style
    func shadow(_ style: ShadowStyle) -> some View {
        self.shadow(
            color: style.color,
            radius: style.radius,
            x: style.x,
            y: style.y
        )
    }

    /// Apply card shadow — subtle lift
    func cardShadow() -> some View {
        self.shadow(ShadowTokens.card)
    }

    /// Apply panel shadow — medium elevation
    func panelShadow() -> some View {
        self.shadow(ShadowTokens.panel)
    }

    /// Apply glow shadow — violet glow effect
    func glowShadow() -> some View {
        self.shadow(ShadowTokens.glow)
    }

    /// Apply hero shadow — deep shadow for hero elements
    func heroShadow() -> some View {
        self.shadow(ShadowTokens.hero)
    }
}

// MARK: - Glow Hover Modifier

/// Animated glow effect for hover states
struct GlowHoverModifier: ViewModifier {
    @State private var isHovered = false

    func body(content: Content) -> some View {
        content
            .shadow(
                color: Color.accentGlow.opacity(isHovered ? 0.5 : 0),
                radius: isHovered ? 20 : 0,
                x: 0,
                y: 0
            )
            .animation(.easeInOut(duration: 0.25), value: isHovered)
            .onHover { hovering in
                isHovered = hovering
            }
    }
}

extension View {
    /// Apply animated glow effect on hover
    func glowOnHover() -> some View {
        self.modifier(GlowHoverModifier())
    }
}
