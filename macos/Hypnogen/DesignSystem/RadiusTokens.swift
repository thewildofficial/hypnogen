import SwiftUI

// MARK: - Radius Tokens

/// Corner radius values for consistent rounded corners
enum Radius {
    /// Small radius (6pt) - buttons, small elements
    static let sm: CGFloat = 6
    
    /// Medium radius (12pt) - cards, panels
    static let md: CGFloat = 12
    
    /// Large radius (18pt) - sheets, large containers
    static let lg: CGFloat = 18
}

// MARK: - Corner Radius Convenience

extension View {
    /// Apply small corner radius
    func cornerRadiusSmall() -> some View {
        self.cornerRadius(Radius.sm)
    }
    
    /// Apply medium corner radius
    func cornerRadiusMedium() -> some View {
        self.cornerRadius(Radius.md)
    }
    
    /// Apply large corner radius
    func cornerRadiusLarge() -> some View {
        self.cornerRadius(Radius.lg)
    }
}
