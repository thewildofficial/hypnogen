import SwiftUI

// MARK: - Deep Violet/Indigo Palette

extension Color {
    // MARK: Backgrounds

    /// Near-black purple background (#0D0D1A)
    static let backgroundDeep = Color("BackgroundDeep")

    /// Deep violet mid-layer background (#1A1A2E)
    static let backgroundMid = Color("BackgroundMid")

    /// Mid violet elevated background (#2D2D4A)
    static let backgroundLight = Color("BackgroundLight")

    // MARK: Surfaces

    /// Elevated surface for cards and panels (#2A2A4A)
    static let surfacePrimary = Color("SurfacePrimary")

    /// Secondary surface for nested elements (#3D3D5C)
    static let surfaceSecondary = Color("SurfaceSecondary")

    // MARK: Accents

    /// Bright violet primary accent (#8B5CF6)
    static let accentViolet = Color("AccentViolet")

    /// Indigo accent for secondary highlights (#6366F1)
    static let accentIndigo = Color("AccentIndigo")

    /// Soft glow violet for hover/active states (#A78BFA)
    static let accentGlow = Color("AccentGlow")

    // MARK: Text

    /// Warm white primary text (#F5F5FF)
    static let textPrimary = Color("TextPrimary")

    /// Muted violet-gray secondary text (#A5A5C0)
    static let textSecondary = Color("TextSecondary")

    /// Light violet accent text (#C4B5FD)
    static let textAccent = Color("TextAccent")
}

// MARK: - Backward-Compatible Aliases

extension Color {
    /// Alias: canvas → backgroundDeep (was #0C0F2C, now #0D0D1A)
    static let canvas = Color("BackgroundDeep")

    /// Alias: surface → surfacePrimary (was #1E245C, now #2A2A4A)
    static let surface = Color("SurfacePrimary")

    /// Alias: stroke → surfaceSecondary (was #314F84, now #3D3D5C)
    static let stroke = Color("SurfaceSecondary")

    /// Alias: accentPrimary → accentViolet (was #5FA9C9, now #8B5CF6)
    static let accentPrimary = Color("AccentViolet")

    /// Alias: accentSecondary → accentIndigo (was #82CDE0, now #6366F1)
    static let accentSecondary = Color("AccentIndigo")
}

// MARK: - Gradient Presets

extension LinearGradient {
    /// Deep canvas gradient from background deep to darker
    static var canvasGradient: LinearGradient {
        LinearGradient(
            colors: [Color.backgroundDeep, Color.black.opacity(0.3)],
            startPoint: .top,
            endPoint: .bottom
        )
    }

    /// Violet accent gradient
    static var accentGradient: LinearGradient {
        LinearGradient(
            colors: [Color.accentViolet, Color.accentIndigo],
            startPoint: .leading,
            endPoint: .trailing
        )
    }

    /// Soft glow gradient for highlights
    static var glowGradient: LinearGradient {
        LinearGradient(
            colors: [Color.accentGlow, Color.accentViolet],
            startPoint: .topLeading,
            endPoint: .bottomTrailing
        )
    }

    /// Depth gradient for layered backgrounds
    static var depthGradient: LinearGradient {
        LinearGradient(
            colors: [Color.backgroundDeep, Color.backgroundMid],
            startPoint: .top,
            endPoint: .bottom
        )
    }
}
