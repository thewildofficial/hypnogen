import SwiftUI

// MARK: - Panel Style

/// Panel component style for primary content areas
struct PanelStyle: ViewModifier {
    func body(content: Content) -> some View {
        content
            .padding(Spacing.lg)
            .background(Color.canvas)
            .cornerRadius(Radius.lg)
            .overlay(
                RoundedRectangle(cornerRadius: Radius.lg)
                    .stroke(Color.stroke.opacity(0.5), lineWidth: 1)
            )
    }
}

// MARK: - Elevated Panel Style

/// Panel with stronger shadow for modals/overlays
struct ElevatedPanelStyle: ViewModifier {
    func body(content: Content) -> some View {
        content
            .padding(Spacing.lg)
            .background(Color.surface)
            .cornerRadius(Radius.lg)
            .overlay(
                RoundedRectangle(cornerRadius: Radius.lg)
                    .stroke(Color.stroke, lineWidth: 1)
            )
            .panelShadow()
    }
}

// MARK: - View Extensions

extension View {
    /// Apply standard panel styling
    func panelStyle() -> some View {
        modifier(PanelStyle())
    }
    
    /// Apply elevated panel styling with shadow
    func elevatedPanelStyle() -> some View {
        modifier(ElevatedPanelStyle())
    }
}
