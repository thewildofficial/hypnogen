import SwiftUI

// MARK: - Card Style

/// Card component style with surface background, stroke border, and shadow
struct CardStyle: ViewModifier {
    func body(content: Content) -> some View {
        content
            .padding(Spacing.md)
            .background(Color.surface)
            .cornerRadius(Radius.md)
            .overlay(
                RoundedRectangle(cornerRadius: Radius.md)
                    .stroke(Color.stroke, lineWidth: 1)
            )
            .cardShadow()
    }
}

// MARK: - Interactive Card Style

/// Card style with hover effect
struct InteractiveCardStyle: ViewModifier {
    @State private var isHovered = false
    
    func body(content: Content) -> some View {
        content
            .padding(Spacing.md)
            .background(Color.surface)
            .cornerRadius(Radius.md)
            .overlay(
                RoundedRectangle(cornerRadius: Radius.md)
                    .stroke(isHovered ? Color.accentPrimary : Color.stroke, lineWidth: isHovered ? 2 : 1)
            )
            .cardShadow()
            .scaleEffect(isHovered ? 1.02 : 1.0)
            .animation(.easeInOut(duration: 0.2), value: isHovered)
            .onHover { hovering in
                isHovered = hovering
            }
    }
}

// MARK: - View Extensions

extension View {
    /// Apply standard card styling
    func cardStyle() -> some View {
        modifier(CardStyle())
    }
    
    /// Apply interactive card styling with hover effects
    func interactiveCardStyle() -> some View {
        modifier(InteractiveCardStyle())
    }
}
