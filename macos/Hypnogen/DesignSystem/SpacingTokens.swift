import SwiftUI

// MARK: - Spacing Tokens

/// 8pt grid spacing system
enum Spacing {
    /// Extra small spacing (4pt)
    static let xs: CGFloat = 4
    
    /// Small spacing (8pt)
    static let sm: CGFloat = 8
    
    /// Medium spacing (16pt)
    static let md: CGFloat = 16
    
    /// Large spacing (24pt)
    static let lg: CGFloat = 24
    
    /// Extra large spacing (32pt)
    static let xl: CGFloat = 32
}

// MARK: - Padding Convenience

extension View {
    /// Apply standard padding on all sides
    func padded(_ size: CGFloat = Spacing.md) -> some View {
        self.padding(size)
    }
    
    /// Apply horizontal padding only
    func paddingHorizontal(_ size: CGFloat = Spacing.md) -> some View {
        self.padding(.horizontal, size)
    }
    
    /// Apply vertical padding only
    func paddingVertical(_ size: CGFloat = Spacing.md) -> some View {
        self.padding(.vertical, size)
    }
}
