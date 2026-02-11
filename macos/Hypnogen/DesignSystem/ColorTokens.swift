import SwiftUI

// MARK: - Color Tokens

extension Color {
    /// Deep ink navy background color (#0c0f2c)
    static let canvas = Color("Canvas")
    
    /// Indigo surface color for cards and panels (#1e245c)
    static let surface = Color("Surface")
    
    /// Blue stroke/border color (#314f84)
    static let stroke = Color("Stroke")
    
    /// Cyan-blue primary accent color (#5fa9c9)
    static let accentPrimary = Color("AccentPrimary")
    
    /// Bright cyan secondary accent color (#82cde0)
    static let accentSecondary = Color("AccentSecondary")
    
    /// Cyan highlight text color (#b6dded)
    static let textPrimary = Color("TextPrimary")
    
    /// Secondary text color at 70% opacity (#82cde0)
    static let textSecondary = Color("TextSecondary")
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
