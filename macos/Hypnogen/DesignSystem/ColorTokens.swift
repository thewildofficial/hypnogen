import SwiftUI

// MARK: - Color Tokens
// Hardcoded values used instead of Color("Name") because named color
// lookups from Asset Catalogs fail silently at runtime (returning clear),
// even when the .car file contains correct color data.

extension Color {
    // MARK: Backgrounds

    /// Near-black violet background (#0C0816)
    static let backgroundDeep = Color(red: 0.047, green: 0.031, blue: 0.086)

    /// Deep violet mid-layer background (#150E28)
    static let backgroundMid = Color(red: 0.082, green: 0.055, blue: 0.157)

    /// Mid violet elevated background (#1E1535)
    static let backgroundLight = Color(red: 0.118, green: 0.082, blue: 0.208)

    // MARK: Surfaces

    /// Elevated surface for cards and panels (#241A3D)
    static let surfacePrimary = Color(red: 0.141, green: 0.102, blue: 0.239)

    /// Secondary surface for nested elements (#2E2250)
    static let surfaceSecondary = Color(red: 0.180, green: 0.133, blue: 0.314)

    // MARK: Accents

    /// Bright violet primary accent (#8B5CF6)
    static let accentViolet = Color(red: 0.545, green: 0.361, blue: 0.965)

    /// Indigo accent for secondary highlights (#6366F1)
    static let accentIndigo = Color(red: 0.388, green: 0.400, blue: 0.945)

    /// Soft glow violet for hover/active states (#A78BFA)
    static let accentGlow = Color(red: 0.655, green: 0.545, blue: 0.980)

    // MARK: Text

    /// Warm white primary text (#F5F5FF)
    static let textPrimary = Color(red: 0.961, green: 0.961, blue: 1.0)

    /// Muted violet secondary text (#ADA0C4)
    static let textSecondary = Color(red: 0.678, green: 0.627, blue: 0.769)

    /// Light violet accent text (#C4B5FD)
    static let textAccent = Color(red: 0.769, green: 0.706, blue: 0.988)

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
            colors: [Color.backgroundDeep, Color(red: 0.027, green: 0.016, blue: 0.055)],
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
