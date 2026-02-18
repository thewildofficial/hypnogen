import SwiftUI

// MARK: - Color Tokens
// Hardcoded values used instead of Color("Name") because named color
// lookups from Asset Catalogs fail silently at runtime (returning clear),
// even when the .car file contains correct color data.
//
// Palette: "iPhone Rose Gold" — deep dusty rose with vibrant metallic pink accents
// Pinker, more saturated rose gold for a distinctly feminine, premium feel.

extension Color {
    // MARK: Backgrounds

    /// Deep dusty rose background with strong pink undertones (#1F1015)
    static let backgroundDeep = Color(red: 0.122, green: 0.063, blue: 0.082)

    /// Rich dusty rose mid-layer background (#2D1A22)
    static let backgroundMid = Color(red: 0.176, green: 0.102, blue: 0.133)

    /// Warm dusty rose elevated background (#422633)
    static let backgroundLight = Color(red: 0.259, green: 0.149, blue: 0.200)

    // MARK: Surfaces

    /// Rose-tinted surface for cards and panels (#523040)
    static let surfacePrimary = Color(red: 0.322, green: 0.188, blue: 0.251)

    /// Secondary surface for nested elements (#633A4D)
    static let surfaceSecondary = Color(red: 0.388, green: 0.227, blue: 0.302)

    // MARK: Accents

    /// Vibrant rose gold metallic primary accent — PINKER (#F2A4B8)
    static let accentViolet = Color(red: 0.949, green: 0.643, blue: 0.722)

    /// Bright pink accent for secondary highlights (#F9C2D4)
    static let accentIndigo = Color(red: 0.976, green: 0.761, blue: 0.831)

    /// Hot champagne pink glow for hover/active states (#FFD9E8)
    static let accentGlow = Color(red: 1.000, green: 0.851, blue: 0.910)

    // MARK: Text

    /// Blush white primary text (#FFF5F8)
    static let textPrimary = Color(red: 1.000, green: 0.961, blue: 0.973)

    /// Dusty rose secondary text (#E8B8C8)
    static let textSecondary = Color(red: 0.910, green: 0.722, blue: 0.784)

    /// Hot pink accent text (#FFB8D4)
    static let textAccent = Color(red: 1.000, green: 0.722, blue: 0.831)

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
    /// Deep canvas gradient from background deep to darker warm black
    static var canvasGradient: LinearGradient {
        LinearGradient(
            colors: [Color.backgroundDeep, Color(red: 0.063, green: 0.035, blue: 0.035)],
            startPoint: .top,
            endPoint: .bottom
        )
    }

    /// Rose gold metallic accent gradient
    static var accentGradient: LinearGradient {
        LinearGradient(
            colors: [Color.accentViolet, Color.accentIndigo],
            startPoint: .leading,
            endPoint: .trailing
        )
    }

    /// Soft champagne glow gradient for highlights
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
