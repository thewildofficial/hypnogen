import SwiftUI

// MARK: - Color Tokens
// Hardcoded values used instead of Color("Name") because named color
// lookups from Asset Catalogs fail silently at runtime (returning clear),
// even when the .car file contains correct color data.

extension Color {
    /// Deep ink navy background color (#0c0f2c)
    static let canvas = Color(red: 0.047, green: 0.059, blue: 0.173)

    /// Indigo surface color for cards and panels (#1e245c)
    static let surface = Color(red: 0.118, green: 0.141, blue: 0.361)

    /// Blue stroke/border color (#314f84)
    static let stroke = Color(red: 0.192, green: 0.310, blue: 0.518)

    /// Cyan-blue primary accent color (#5fa9c9)
    static let accentPrimary = Color(red: 0.373, green: 0.663, blue: 0.788)

    /// Bright cyan secondary accent color (#82cde0)
    static let accentSecondary = Color(red: 0.510, green: 0.812, blue: 0.878)

    /// Cyan highlight text color (#b6dded)
    static let textPrimary = Color(red: 0.714, green: 0.867, blue: 0.929)

    /// Secondary text color at 70% opacity (#82cde0)
    static let textSecondary = Color(red: 0.510, green: 0.812, blue: 0.878, opacity: 0.7)
}

// MARK: - Gradient Presets

extension LinearGradient {
    static var canvasGradient: LinearGradient {
        LinearGradient(
            colors: [Color.canvas, Color.black.opacity(0.3)],
            startPoint: .top,
            endPoint: .bottom
        )
    }
    
    static var accentGradient: LinearGradient {
        LinearGradient(
            colors: [Color.accentPrimary, Color.accentSecondary],
            startPoint: .leading,
            endPoint: .trailing
        )
    }
}
