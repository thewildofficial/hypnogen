import SwiftUI

// MARK: - Gradient Tokens

enum GradientTokens {

    // MARK: - Presets

    /// BackgroundDeep → BackgroundMid → BackgroundLight (vertical)
    static let backgroundGradient = LinearGradient(
        colors: [Color.backgroundDeep, Color.backgroundMid, Color.backgroundLight],
        startPoint: .top,
        endPoint: .bottom
    )

    /// BackgroundMid → BackgroundDeep (vertical)
    static let sidebarGradient = LinearGradient(
        colors: [Color.backgroundMid, Color.backgroundDeep],
        startPoint: .top,
        endPoint: .bottom
    )

    /// SurfacePrimary → SurfaceSecondary (subtle diagonal)
    static let cardGradient = LinearGradient(
        colors: [Color.surfacePrimary, Color.surfaceSecondary],
        startPoint: .topLeading,
        endPoint: .bottomTrailing
    )

    /// AccentViolet → AccentIndigo (horizontal)
    static let accentGradient = LinearGradient(
        colors: [Color.accentViolet, Color.accentIndigo],
        startPoint: .leading,
        endPoint: .trailing
    )

    /// AccentGlow → transparent (radial for glow effects)
    static let glowGradient = RadialGradient(
        colors: [Color.accentGlow, Color.accentGlow.opacity(0)],
        center: .center,
        startRadius: 0,
        endRadius: 120
    )

    /// Deep teal with subtle accent color stops
    static let heroGradient = LinearGradient(
        colors: [
            Color.backgroundDeep,
            Color.backgroundMid,
            Color.accentIndigo.opacity(0.15),
            Color.accentViolet.opacity(0.08),
            Color.backgroundDeep,
        ],
        startPoint: .topLeading,
        endPoint: .bottomTrailing
    )
}

// MARK: - LinearGradient Convenience

extension LinearGradient {

    static func vertical(_ top: Color, _ bottom: Color) -> LinearGradient {
        LinearGradient(colors: [top, bottom], startPoint: .top, endPoint: .bottom)
    }

    static func horizontal(_ leading: Color, _ trailing: Color) -> LinearGradient {
        LinearGradient(colors: [leading, trailing], startPoint: .leading, endPoint: .trailing)
    }

    static func vertical(_ colors: [Color]) -> LinearGradient {
        LinearGradient(colors: colors, startPoint: .top, endPoint: .bottom)
    }

    static func diagonal(_ colors: [Color]) -> LinearGradient {
        LinearGradient(colors: colors, startPoint: .topLeading, endPoint: .bottomTrailing)
    }
}

// MARK: - RadialGradient Convenience

extension RadialGradient {

    static func glow(
        _ inner: Color,
        _ outer: Color,
        radius: CGFloat = 120
    ) -> RadialGradient {
        RadialGradient(
            colors: [inner, outer],
            center: .center,
            startRadius: 0,
            endRadius: radius
        )
    }

    static func fade(_ color: Color, radius: CGFloat = 120) -> RadialGradient {
        RadialGradient(
            colors: [color, color.opacity(0)],
            center: .center,
            startRadius: 0,
            endRadius: radius
        )
    }
}

// MARK: - Breathing Animation

extension View {

    func breathingEffect(
        minOpacity: Double = 0.6,
        maxOpacity: Double = 1.0,
        duration: Double = 4
    ) -> some View {
        modifier(
            BreathingModifier(
                minOpacity: minOpacity,
                maxOpacity: maxOpacity,
                duration: duration
            )
        )
    }
}

private struct BreathingModifier: ViewModifier {
    let minOpacity: Double
    let maxOpacity: Double
    let duration: Double

    @State private var isBreathing = false

    func body(content: Content) -> some View {
        content
            .opacity(isBreathing ? maxOpacity : minOpacity)
            .animation(
                .easeInOut(duration: duration).repeatForever(autoreverses: true),
                value: isBreathing
            )
            .onAppear { isBreathing = true }
    }
}
