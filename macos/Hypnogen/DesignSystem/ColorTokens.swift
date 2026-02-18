import SwiftUI

// MARK: - Color Tokens
// Hardcoded values used instead of Color("Name") because named color
// lookups from Asset Catalogs fail silently at runtime (returning clear),
// even when the .car file contains correct color data.
//
// Palette: "Bioluminescent Deep" — deep teal/cyan inspired by
// ocean bioluminescence. Premium, calming, distinctive.

extension Color {
    // MARK: Backgrounds

    /// Near-black teal background (#060E12)
    static let backgroundDeep = Color(red: 0.024, green: 0.055, blue: 0.071)

    /// Dark teal mid-layer background (#0A1A22)
    static let backgroundMid = Color(red: 0.039, green: 0.102, blue: 0.133)

    /// Mid teal elevated background (#112A32)
    static let backgroundLight = Color(red: 0.067, green: 0.165, blue: 0.196)

    // MARK: Surfaces

    /// Elevated surface for cards and panels (#143038)
    static let surfacePrimary = Color(red: 0.078, green: 0.188, blue: 0.220)

    /// Secondary surface for nested elements (#1A3D45)
    static let surfaceSecondary = Color(red: 0.102, green: 0.239, blue: 0.271)

    // MARK: Accents

    /// Bright teal primary accent (#2DD4BF)
    static let accentViolet = Color(red: 0.176, green: 0.831, blue: 0.749)

    /// Cyan accent for secondary highlights (#22D3EE)
    static let accentIndigo = Color(red: 0.133, green: 0.827, blue: 0.933)

    /// Soft teal glow for hover/active states (#5EEAD4)
    static let accentGlow = Color(red: 0.369, green: 0.918, blue: 0.831)

    // MARK: Text

    /// Cool white primary text with teal tint (#F0FDFA)
    static let textPrimary = Color(red: 0.941, green: 0.992, blue: 0.980)

    /// Cool slate secondary text (#94A3B8)
    static let textSecondary = Color(red: 0.580, green: 0.639, blue: 0.722)

    /// Light teal accent text (#99F6E4)
    static let textAccent = Color(red: 0.600, green: 0.965, blue: 0.894)

    // MARK: Backward-Compatible Aliases

    /// Alias: canvas → backgroundDeep
    static let canvas = backgroundDeep

    /// Alias: surface → surfacePrimary
    static let surface = surfacePrimary

    /// Alias: stroke → surfaceSecondary
    static let stroke = surfaceSecondary

    /// Alias: accentPrimary → accentViolet
    static let accentPrimary = accentViolet

    /// Alias: accentSecondary → accentIndigo
    static let accentSecondary = accentIndigo
}

// MARK: - Gradient Presets

extension LinearGradient {
    /// Deep canvas gradient from background deep to darker
    static var canvasGradient: LinearGradient {
        LinearGradient(
            colors: [Color.backgroundDeep, Color(red: 0.012, green: 0.031, blue: 0.043)],
            startPoint: .top,
            endPoint: .bottom
        )
    }

    /// Teal-cyan accent gradient
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
