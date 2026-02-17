import SwiftUI

// MARK: - Glass Background

/// Performance: native `Material` is GPU-composited — no additional blur applied.
struct GlassBackground: ViewModifier {
    var tintOpacity: Double
    var cornerRadius: CGFloat

    @Environment(\.accessibilityReduceTransparency) private var reduceTransparency

    init(tintOpacity: Double = 0.08, cornerRadius: CGFloat = Radius.md) {
        self.tintOpacity = tintOpacity
        self.cornerRadius = cornerRadius
    }

    func body(content: Content) -> some View {
        let shape = RoundedRectangle(cornerRadius: cornerRadius, style: .continuous)

        content
            .background {
                if reduceTransparency {
                    shape.fill(Color.surfacePrimary)
                } else {
                    ZStack {
                        shape.fill(.ultraThinMaterial)
                        shape.fill(Color.accentViolet.opacity(tintOpacity))
                    }
                }
            }
            .clipShape(shape)
    }
}

// MARK: - Glass Border

/// White-to-violet gradient border mimicking light refraction along glass edge.
struct GlassBorder: ViewModifier {
    var cornerRadius: CGFloat
    var lineWidth: CGFloat

    init(cornerRadius: CGFloat = Radius.md, lineWidth: CGFloat = 1) {
        self.cornerRadius = cornerRadius
        self.lineWidth = lineWidth
    }

    func body(content: Content) -> some View {
        content.overlay(
            RoundedRectangle(cornerRadius: cornerRadius, style: .continuous)
                .strokeBorder(
                    LinearGradient(
                        stops: [
                            .init(color: Color.white.opacity(0.2), location: 0),
                            .init(color: Color.accentViolet.opacity(0.15), location: 0.5),
                            .init(color: Color.white.opacity(0.06), location: 1),
                        ],
                        startPoint: .topLeading,
                        endPoint: .bottomTrailing
                    ),
                    lineWidth: lineWidth
                )
        )
    }
}

// MARK: - Glass Glow

/// Performance: single shadow layer only — avoids stacking multiple blur passes.
struct GlassGlow: ViewModifier {
    var radius: CGFloat
    var opacity: Double

    init(radius: CGFloat = 16, opacity: Double = 0.25) {
        self.radius = radius
        self.opacity = opacity
    }

    func body(content: Content) -> some View {
        content.shadow(
            color: Color.accentGlow.opacity(opacity),
            radius: radius,
            x: 0,
            y: 0
        )
    }
}

// MARK: - Frosted Glass Composite

/// Combines `GlassBackground` + `GlassBorder` + `GlassGlow` into one modifier.
struct FrostedGlassModifier: ViewModifier {
    var tintOpacity: Double
    var cornerRadius: CGFloat
    var borderWidth: CGFloat
    var glowRadius: CGFloat
    var glowOpacity: Double

    @Environment(\.accessibilityReduceTransparency) private var reduceTransparency

    init(
        tintOpacity: Double = 0.08,
        cornerRadius: CGFloat = Radius.md,
        borderWidth: CGFloat = 1,
        glowRadius: CGFloat = 16,
        glowOpacity: Double = 0.25
    ) {
        self.tintOpacity = tintOpacity
        self.cornerRadius = cornerRadius
        self.borderWidth = borderWidth
        self.glowRadius = glowRadius
        self.glowOpacity = glowOpacity
    }

    func body(content: Content) -> some View {
        content
            .modifier(GlassBackground(tintOpacity: tintOpacity, cornerRadius: cornerRadius))
            .modifier(GlassBorder(cornerRadius: cornerRadius, lineWidth: borderWidth))
            .modifier(GlassGlow(radius: glowRadius, opacity: glowOpacity))
    }
}

// MARK: - Vibrancy Text Helpers

/// Contrast shadows for text legibility on translucent glass surfaces.
enum GlassVibrancy {
    static func primary(_ text: Text) -> some View {
        text
            .foregroundStyle(Color.textPrimary)
            .shadow(color: Color.black.opacity(0.3), radius: 1, x: 0, y: 1)
    }

    static func secondary(_ text: Text) -> some View {
        text
            .foregroundStyle(Color.textSecondary)
            .shadow(color: Color.black.opacity(0.2), radius: 1, x: 0, y: 1)
    }

    static func accent(_ text: Text) -> some View {
        text
            .foregroundStyle(Color.textAccent)
            .shadow(color: Color.accentGlow.opacity(0.4), radius: 4, x: 0, y: 0)
    }
}

// MARK: - Vibrancy View Modifier

struct GlassVibrancyModifier: ViewModifier {
    enum Level {
        case primary
        case secondary
        case accent
    }

    var level: Level

    func body(content: Content) -> some View {
        switch level {
        case .primary:
            content
                .foregroundStyle(Color.textPrimary)
                .shadow(color: Color.black.opacity(0.3), radius: 1, x: 0, y: 1)
        case .secondary:
            content
                .foregroundStyle(Color.textSecondary)
                .shadow(color: Color.black.opacity(0.2), radius: 1, x: 0, y: 1)
        case .accent:
            content
                .foregroundStyle(Color.textAccent)
                .shadow(color: Color.accentGlow.opacity(0.4), radius: 4, x: 0, y: 0)
        }
    }
}

// MARK: - Glass Intensity Presets

enum GlassIntensity {
    case subtle
    case standard
    case prominent

    var tintOpacity: Double {
        switch self {
        case .subtle:    return 0.04
        case .standard:  return 0.08
        case .prominent: return 0.14
        }
    }

    var borderWidth: CGFloat {
        switch self {
        case .subtle:    return 0.5
        case .standard:  return 1
        case .prominent: return 1.5
        }
    }

    var glowRadius: CGFloat {
        switch self {
        case .subtle:    return 8
        case .standard:  return 16
        case .prominent: return 24
        }
    }

    var glowOpacity: Double {
        switch self {
        case .subtle:    return 0.12
        case .standard:  return 0.25
        case .prominent: return 0.4
        }
    }
}

// MARK: - View Extensions

extension View {

    func frostedGlass(
        tintOpacity: Double = 0.08,
        cornerRadius: CGFloat = Radius.md,
        borderWidth: CGFloat = 1,
        glowRadius: CGFloat = 16,
        glowOpacity: Double = 0.25
    ) -> some View {
        modifier(FrostedGlassModifier(
            tintOpacity: tintOpacity,
            cornerRadius: cornerRadius,
            borderWidth: borderWidth,
            glowRadius: glowRadius,
            glowOpacity: glowOpacity
        ))
    }

    func frostedGlass(
        _ intensity: GlassIntensity,
        cornerRadius: CGFloat = Radius.md
    ) -> some View {
        modifier(FrostedGlassModifier(
            tintOpacity: intensity.tintOpacity,
            cornerRadius: cornerRadius,
            borderWidth: intensity.borderWidth,
            glowRadius: intensity.glowRadius,
            glowOpacity: intensity.glowOpacity
        ))
    }

    func glassBackground(
        tintOpacity: Double = 0.08,
        cornerRadius: CGFloat = Radius.md
    ) -> some View {
        modifier(GlassBackground(tintOpacity: tintOpacity, cornerRadius: cornerRadius))
    }

    func glassBorder(
        cornerRadius: CGFloat = Radius.md,
        lineWidth: CGFloat = 1
    ) -> some View {
        modifier(GlassBorder(cornerRadius: cornerRadius, lineWidth: lineWidth))
    }

    func glassGlow(
        radius: CGFloat = 16,
        opacity: Double = 0.25
    ) -> some View {
        modifier(GlassGlow(radius: radius, opacity: opacity))
    }

    func glassVibrancy(_ level: GlassVibrancyModifier.Level = .primary) -> some View {
        modifier(GlassVibrancyModifier(level: level))
    }
}
