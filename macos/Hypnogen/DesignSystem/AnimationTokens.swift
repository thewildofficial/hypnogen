import SwiftUI

// MARK: - Animation Tokens

/// Consistent animation presets for the design system
enum AnimationTokens {
    /// Spring animation for card hover/selection
    static let springCard: Animation = .spring(response: 0.3, dampingFraction: 0.7)

    /// Spring animation for button press
    static let springButton: Animation = .spring(response: 0.2, dampingFraction: 0.8)

    /// Spring animation for smooth view transitions
    static let springTransition: Animation = .spring(response: 0.35, dampingFraction: 0.85)

    /// Spring animation for hover glow effects
    static let springGlow: Animation = .spring(response: 0.4, dampingFraction: 0.75)

    /// Standard ease-in-out transition
    static let easeInOut: Animation = .easeInOut(duration: 0.25)

    /// Exit transition
    static let easeOut: Animation = .easeOut(duration: 0.2)

    /// Breathing gradient animation (4s, repeats forever)
    static let breathing: Animation = .easeInOut(duration: 4.0).repeatForever(autoreverses: true)

    /// Subtle pulse for active states (2s, autoreverses)
    static let pulse: Animation = .easeInOut(duration: 2.0).repeatForever(autoreverses: true)
}

// MARK: - Reduce Motion Helpers

/// Resolves an animation respecting accessibility preferences
struct MotionSensitiveAnimation {
    /// Returns the given animation, or `.default` if Reduce Motion is enabled
    static func resolve(_ animation: Animation, reduceMotion: Bool) -> Animation {
        reduceMotion ? .default : animation
    }

    /// Returns `nil` if Reduce Motion is enabled, disabling the animation entirely
    static func resolveOptional(_ animation: Animation, reduceMotion: Bool) -> Animation? {
        reduceMotion ? nil : animation
    }
}

// MARK: - View Convenience

extension View {
    /// Animate with a token, respecting Reduce Motion
    func animateWithToken(
        _ token: Animation,
        reduceMotion: Bool,
        _ body: () -> Void
    ) {
        let resolved = MotionSensitiveAnimation.resolve(token, reduceMotion: reduceMotion)
        withAnimation(resolved) {
            body()
        }
    }

    /// Apply a repeating animation only when Reduce Motion is off
    func breathingAnimation(reduceMotion: Bool, value: some Equatable) -> some View {
        self.animation(
            reduceMotion ? nil : AnimationTokens.breathing,
            value: value
        )
    }

    /// Apply a pulse animation only when Reduce Motion is off
    func pulseAnimation(reduceMotion: Bool, value: some Equatable) -> some View {
        self.animation(
            reduceMotion ? nil : AnimationTokens.pulse,
            value: value
        )
    }
}

// MARK: - withAnimation Convenience

/// Perform an action with a design-system animation, respecting Reduce Motion
func withTokenAnimation(
    _ token: Animation,
    reduceMotion: Bool,
    _ body: () -> Void
) {
    if reduceMotion {
        withAnimation(.default) { body() }
    } else {
        withAnimation(token) { body() }
    }
}
