import SwiftUI

// MARK: - Panel Padding

/// Padding variants for panel content density
enum PanelPadding {
    /// Compact — tight content (12pt)
    case compact
    /// Regular — standard content (24pt)
    case regular
    /// Spacious — breathing room for hero content (32pt)
    case spacious

    var value: CGFloat {
        switch self {
        case .compact:  return Spacing.md - 4   // 12pt
        case .regular:  return Spacing.lg
        case .spacious: return Spacing.xl
        }
    }
}

// MARK: - Panel Style

/// Primary panel with surface gradient background, subtle border, and soft shadow.
/// Use for standard content areas, settings groups, and form sections.
struct PanelStyle: ViewModifier {
    var padding: PanelPadding

    init(padding: PanelPadding = .regular) {
        self.padding = padding
    }

    func body(content: Content) -> some View {
        content
            .padding(padding.value)
            .background(
                GradientTokens.cardGradient
                    .opacity(0.8)
            )
            .clipShape(RoundedRectangle(cornerRadius: Radius.lg, style: .continuous))
            .overlay(
                RoundedRectangle(cornerRadius: Radius.lg, style: .continuous)
                    .strokeBorder(
                        Color.surfaceSecondary.opacity(0.3),
                        lineWidth: 1
                    )
            )
            .shadow(ShadowTokens.panel)
    }
}

// MARK: - Elevated Panel Style

/// Elevated panel with deeper shadow and stronger border for modals, popovers,
/// and content that floats above the main surface.
struct ElevatedPanelStyle: ViewModifier {
    var padding: PanelPadding

    init(padding: PanelPadding = .regular) {
        self.padding = padding
    }

    func body(content: Content) -> some View {
        content
            .padding(padding.value)
            .background(
                GradientTokens.cardGradient
            )
            .clipShape(RoundedRectangle(cornerRadius: Radius.lg, style: .continuous))
            .overlay(
                RoundedRectangle(cornerRadius: Radius.lg, style: .continuous)
                    .strokeBorder(
                        LinearGradient(
                            colors: [
                                Color.surfaceSecondary.opacity(0.5),
                                Color.surfaceSecondary.opacity(0.25),
                            ],
                            startPoint: .top,
                            endPoint: .bottom
                        ),
                        lineWidth: 1
                    )
            )
            .shadow(ShadowTokens.modal)
            .shadow(ShadowTokens.hero)
    }
}

// MARK: - Glass Panel Style

/// Frosted glass panel using ultra-thin material for overlays, tool palettes,
/// and HUD-style floating content. Features a luminous edge highlight.
struct GlassPanelStyle: ViewModifier {
    var padding: PanelPadding

    init(padding: PanelPadding = .regular) {
        self.padding = padding
    }

    func body(content: Content) -> some View {
        content
            .padding(padding.value)
            .background(.ultraThinMaterial)
            .clipShape(RoundedRectangle(cornerRadius: Radius.lg, style: .continuous))
            .overlay(
                RoundedRectangle(cornerRadius: Radius.lg, style: .continuous)
                    .strokeBorder(
                        LinearGradient(
                            colors: [
                                Color.white.opacity(0.2),
                                Color.white.opacity(0.05),
                                Color.accentGlow.opacity(0.1),
                            ],
                            startPoint: .topLeading,
                            endPoint: .bottomTrailing
                        ),
                        lineWidth: 1
                    )
            )
            .shadow(ShadowTokens.panel)
    }
}

// MARK: - Sidebar Panel Style

/// Panel styled for sidebar sections with the sidebar gradient background.
/// Use for grouped navigation items, filter groups, and sidebar section containers.
struct SidebarPanelStyle: ViewModifier {
    var padding: PanelPadding

    init(padding: PanelPadding = .compact) {
        self.padding = padding
    }

    func body(content: Content) -> some View {
        content
            .padding(padding.value)
            .background(
                GradientTokens.sidebarGradient
                    .opacity(0.6)
            )
            .clipShape(RoundedRectangle(cornerRadius: Radius.md, style: .continuous))
            .overlay(
                RoundedRectangle(cornerRadius: Radius.md, style: .continuous)
                    .strokeBorder(
                        Color.surfaceSecondary.opacity(0.2),
                        lineWidth: 0.5
                    )
            )
    }
}

// MARK: - View Extensions

extension View {
    /// Apply standard panel styling with surface gradient and soft shadow
    func panelStyle(padding: PanelPadding = .regular) -> some View {
        modifier(PanelStyle(padding: padding))
    }

    /// Apply elevated panel styling with deep shadow for modals and popovers
    func elevatedPanelStyle(padding: PanelPadding = .regular) -> some View {
        modifier(ElevatedPanelStyle(padding: padding))
    }

    /// Apply frosted glass panel styling for overlays and HUD content
    func glassPanelStyle(padding: PanelPadding = .regular) -> some View {
        modifier(GlassPanelStyle(padding: padding))
    }

    /// Apply sidebar panel styling for sidebar section groups
    func sidebarPanelStyle(padding: PanelPadding = .compact) -> some View {
        modifier(SidebarPanelStyle(padding: padding))
    }
}
