import SwiftUI

// MARK: - Shadow Tokens

/// Shadow presets for consistent elevation
enum ShadowTokens {
    /// Card shadow - subtle lift
    static let card = ShadowStyle(
        color: Color.black.opacity(0.2),
        radius: 8,
        x: 0,
        y: 4
    )
    
    /// Panel shadow - stronger elevation
    static let panel = ShadowStyle(
        color: Color.black.opacity(0.15),
        radius: 12,
        x: 0,
        y: 6
    )
    
    /// Modal shadow - highest elevation
    static let modal = ShadowStyle(
        color: Color.black.opacity(0.25),
        radius: 16,
        x: 0,
        y: 8
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
    
    /// Apply card shadow
    func cardShadow() -> some View {
        self.shadow(ShadowTokens.card)
    }
    
    /// Apply panel shadow
    func panelShadow() -> some View {
        self.shadow(ShadowTokens.panel)
    }
}
